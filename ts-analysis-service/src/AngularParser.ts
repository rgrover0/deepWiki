import {
  Project,
  SourceFile,
  ClassDeclaration,
  Decorator,
  SyntaxKind,
  Node,
} from "ts-morph";
import * as path from "path";

// ── Types ──────────────────────────────────────────────────

export interface HttpCall {
  method: string;          // GET | POST | PUT | DELETE | PATCH
  url: string;             // raw URL string from source
  normalized_url: string;  // after normaliseUrl()
  source_method: string;   // method where the call appears
}

export interface MethodResult {
  name: string;
  return_type: string;
  parameters: string[];
  annotations: string[];
  calls: CallResult[];
}

export interface CallResult {
  scope: string;
  method: string;
  resolved_type: string;
  confidence: number;
}

export interface FieldResult {
  name: string;
  type: string;
  annotations: string[];
}

export interface ClassResult {
  name: string;
  component_type: string;
  annotations: string[];
  methods: MethodResult[];
  fields: FieldResult[];
  http_calls: HttpCall[];
  api_contracts: object[];  // populated in Iteration 19 by api_matcher
  // Angular-specific metadata
  selector?: string;
  template_url?: string;
  injectable_scope?: string;
}

export interface FileResult {
  file: string;
  package: string;
  classes: ClassResult[];
}

// ── URL normaliser ─────────────────────────────────────────

export function normaliseUrl(raw: string): string {
  return raw
    .replace(/^\s*\$\{this\.\w+\}/, "")       // strip leading base ref: ${this.BASE}/... → /...
    .replace(/`?\s*\+\s*\w+\s*`?$/, "")       // strip trailing concat: url + var → url
    .replace(/\$\{[^}]+\}/g, "{param}")       // remaining template literals → {param}
    .replace(/'\s*\+\s*\w+/g, "/{param}")     // string concat: '/pets/' + id → /{param}
    .replace(/\/\d+/g, "/{id}")               // literal numbers: /42 → /{id}
    .replace(/\/$/, "");                       // trailing slash
}

// ── Decorator helpers ──────────────────────────────────────

function getDecoratorName(dec: Decorator): string {
  return dec.getName();
}

function getDecoratorArg(dec: Decorator, key: string): string | undefined {
  try {
    const args = dec.getArguments();
    if (!args.length) return undefined;
    const arg = args[0];
    if (Node.isObjectLiteralExpression(arg)) {
      const prop = arg.getProperty(key);
      if (!prop) return undefined;
      const init = (prop as any).getInitializer?.();
      if (!init) return undefined;
      return init.getText().replace(/['"]/g, "");
    }
  } catch {
    // ignore
  }
  return undefined;
}

function getDecoratorStringArg(dec: Decorator): string | undefined {
  try {
    const args = dec.getArguments();
    if (!args.length) return undefined;
    const text = args[0].getText().replace(/['"]/g, "");
    return text || undefined;
  } catch {
    return undefined;
  }
}

// ── Component type resolution ──────────────────────────────

function resolveComponentType(decorators: Decorator[]): string {
  const names = decorators.map(getDecoratorName);
  if (names.includes("Component"))   return "COMPONENT";
  if (names.includes("Injectable"))  return "SERVICE";
  if (names.includes("NgModule"))    return "MODULE";
  if (names.includes("Directive"))   return "DIRECTIVE";
  if (names.includes("Pipe"))        return "PIPE";
  return "UNKNOWN";
}

// ── HttpClient call extraction ─────────────────────────────

const HTTP_METHODS = new Set(["get", "post", "put", "delete", "patch", "head"]);

function extractHttpCalls(
  cls: ClassDeclaration,
  httpFields: Set<string>
): HttpCall[] {
  const results: HttpCall[] = [];

  for (const method of cls.getMethods()) {
    const methodName = method.getName();

    method.forEachDescendant((node) => {
      if (!Node.isCallExpression(node)) return;

      const expr = node.getExpression();
      if (!Node.isPropertyAccessExpression(expr)) return;

      const obj        = expr.getExpression();
      const methodPart = expr.getName();

      if (!HTTP_METHODS.has(methodPart.toLowerCase())) return;

      // Check if called on a known HttpClient field: this.http.get(...)
      let fieldName: string | undefined;
      if (Node.isPropertyAccessExpression(obj)) {
        // this.http → http
        fieldName = obj.getName();
      } else if (Node.isIdentifier(obj)) {
        fieldName = obj.getText();
      }

      if (!fieldName || !httpFields.has(fieldName)) return;

      const args = node.getArguments();
      if (!args.length) return;

      const rawUrl = args[0].getText().replace(/[`'"]/g, "").trim();
      const normalized = normaliseUrl(rawUrl);
      const httpMethod = methodPart.toUpperCase();

      results.push({
        method: httpMethod,
        url: rawUrl,
        normalized_url: normalized,
        source_method: methodName,
      });
    });
  }

  return results;
}

// ── Field extraction ───────────────────────────────────────

function extractFields(cls: ClassDeclaration): {
  fields: FieldResult[];
  httpFields: Set<string>;
} {
  const fields: FieldResult[] = [];
  const httpFields = new Set<string>();

  // Constructor parameter properties (common in Angular DI)
  const ctor = cls.getConstructors()[0];
  if (ctor) {
    for (const param of ctor.getParameters()) {
      const typeText = param.getTypeNode()?.getText() ?? "any";
      const name     = param.getName();
      const mods     = param.getModifiers().map((m) => m.getText());

      if (mods.some((m) => ["private", "public", "protected", "readonly"].includes(m))) {
        const annotations = param
          .getDecorators()
          .map((d) => `@${getDecoratorName(d)}`);
        fields.push({ name, type: typeText, annotations });
        if (typeText === "HttpClient") httpFields.add(name);
      }
    }
  }

  // Regular class properties
  for (const prop of cls.getProperties()) {
    const name      = prop.getName();
    const typeText  = prop.getTypeNode()?.getText() ?? "any";
    const annotations = prop
      .getDecorators()
      .map((d) => `@${getDecoratorName(d)}`);
    fields.push({ name, type: typeText, annotations });
    if (typeText === "HttpClient") httpFields.add(name);
  }

  return { fields, httpFields };
}

// ── Method extraction ──────────────────────────────────────

function extractMethods(
  cls: ClassDeclaration,
  httpFields: Set<string>
): MethodResult[] {
  const results: MethodResult[] = [];

  for (const method of cls.getMethods()) {
    const name        = method.getName();
    const returnType  = method.getReturnTypeNode()?.getText() ?? "void";
    const params      = method.getParameters().map(
      (p) => `${p.getName()}: ${p.getTypeNode()?.getText() ?? "any"}`
    );
    const annotations = method
      .getDecorators()
      .map((d) => `@${getDecoratorName(d)}`);

    const calls: CallResult[] = [];

    method.forEachDescendant((node) => {
      if (!Node.isCallExpression(node)) return;
      const expr = node.getExpression();
      if (!Node.isPropertyAccessExpression(expr)) return;

      const obj        = expr.getExpression();
      const methodName = expr.getName();

      let scope = "";
      if (Node.isPropertyAccessExpression(obj)) {
        scope = obj.getName();
      } else if (Node.isIdentifier(obj)) {
        scope = obj.getText();
      }
      if (!scope) return;

      const isHttp     = httpFields.has(scope);
      const confidence = isHttp ? 1.0 : 0.7;
      const resolved   = isHttp ? "HttpClient" : scope;

      calls.push({ scope, method: methodName, resolved_type: resolved, confidence });
    });

    results.push({ name, return_type: returnType, parameters: params, annotations, calls });
  }

  return results;
}

// ── Class extractor ────────────────────────────────────────

function extractClass(cls: ClassDeclaration): ClassResult {
  const decorators = cls.getDecorators();
  const decNames   = decorators.map(getDecoratorName);
  const annotations = decNames.map((n) => `@${n}`);
  const componentType = resolveComponentType(decorators);

  const { fields, httpFields } = extractFields(cls);
  const methods                = extractMethods(cls, httpFields);
  const httpCalls              = extractHttpCalls(cls, httpFields);

  const result: ClassResult = {
    name:           cls.getName() ?? "Anonymous",
    component_type: componentType,
    annotations,
    methods,
    fields,
    http_calls:     httpCalls,
    api_contracts:  [],
  };

  // @Component metadata
  const compDec = decorators.find((d) => getDecoratorName(d) === "Component");
  if (compDec) {
    const sel = getDecoratorArg(compDec, "selector");
    const tmpl = getDecoratorArg(compDec, "templateUrl");
    if (sel)  result.selector      = sel;
    if (tmpl) result.template_url  = tmpl;
  }

  // @Injectable scope
  const injDec = decorators.find((d) => getDecoratorName(d) === "Injectable");
  if (injDec) {
    const providedIn = getDecoratorArg(injDec, "providedIn");
    if (providedIn) result.injectable_scope = providedIn;
  }

  return result;
}

// ── File analyser ──────────────────────────────────────────

export function analyseFile(filePath: string): FileResult {
  const project = new Project({ skipAddingFilesFromTsConfig: true });
  const srcFile: SourceFile = project.addSourceFileAtPath(filePath);

  const dir    = path.dirname(filePath);
  const parts  = dir.split(path.sep);
  const srcIdx = parts.lastIndexOf("src");
  const pkg    = srcIdx >= 0
    ? parts.slice(srcIdx + 1).join(".")
    : parts[parts.length - 1];

  const classes: ClassResult[] = srcFile
    .getClasses()
    .map(extractClass);

  return {
    file:    filePath,
    package: pkg,
    classes,
  };
}

export function analyseFiles(filePaths: string[]): FileResult[] {
  return filePaths.map(analyseFile);
}
