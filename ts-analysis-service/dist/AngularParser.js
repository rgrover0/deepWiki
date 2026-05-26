"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.normaliseUrl = normaliseUrl;
exports.analyseFile = analyseFile;
exports.analyseFiles = analyseFiles;
const ts_morph_1 = require("ts-morph");
const path = __importStar(require("path"));
// ── URL normaliser ─────────────────────────────────────────
function normaliseUrl(raw) {
    return raw
        .replace(/^\s*\$\{this\.\w+\}/, "") // strip leading base ref: ${this.BASE}/... → /...
        .replace(/`?\s*\+\s*\w+\s*`?$/, "") // strip trailing concat: url + var → url
        .replace(/\$\{[^}]+\}/g, "{param}") // remaining template literals → {param}
        .replace(/'\s*\+\s*\w+/g, "/{param}") // string concat: '/pets/' + id → /{param}
        .replace(/\/\d+/g, "/{id}") // literal numbers: /42 → /{id}
        .replace(/\/$/, ""); // trailing slash
}
// ── Decorator helpers ──────────────────────────────────────
function getDecoratorName(dec) {
    return dec.getName();
}
function getDecoratorArg(dec, key) {
    try {
        const args = dec.getArguments();
        if (!args.length)
            return undefined;
        const arg = args[0];
        if (ts_morph_1.Node.isObjectLiteralExpression(arg)) {
            const prop = arg.getProperty(key);
            if (!prop)
                return undefined;
            const init = prop.getInitializer?.();
            if (!init)
                return undefined;
            return init.getText().replace(/['"]/g, "");
        }
    }
    catch {
        // ignore
    }
    return undefined;
}
function getDecoratorStringArg(dec) {
    try {
        const args = dec.getArguments();
        if (!args.length)
            return undefined;
        const text = args[0].getText().replace(/['"]/g, "");
        return text || undefined;
    }
    catch {
        return undefined;
    }
}
// ── Component type resolution ──────────────────────────────
function resolveComponentType(decorators) {
    const names = decorators.map(getDecoratorName);
    if (names.includes("Component"))
        return "COMPONENT";
    if (names.includes("Injectable"))
        return "SERVICE";
    if (names.includes("NgModule"))
        return "MODULE";
    if (names.includes("Directive"))
        return "DIRECTIVE";
    if (names.includes("Pipe"))
        return "PIPE";
    return "UNKNOWN";
}
// ── HttpClient call extraction ─────────────────────────────
const HTTP_METHODS = new Set(["get", "post", "put", "delete", "patch", "head"]);
function extractHttpCalls(cls, httpFields) {
    const results = [];
    for (const method of cls.getMethods()) {
        const methodName = method.getName();
        method.forEachDescendant((node) => {
            if (!ts_morph_1.Node.isCallExpression(node))
                return;
            const expr = node.getExpression();
            if (!ts_morph_1.Node.isPropertyAccessExpression(expr))
                return;
            const obj = expr.getExpression();
            const methodPart = expr.getName();
            if (!HTTP_METHODS.has(methodPart.toLowerCase()))
                return;
            // Check if called on a known HttpClient field: this.http.get(...)
            let fieldName;
            if (ts_morph_1.Node.isPropertyAccessExpression(obj)) {
                // this.http → http
                fieldName = obj.getName();
            }
            else if (ts_morph_1.Node.isIdentifier(obj)) {
                fieldName = obj.getText();
            }
            if (!fieldName || !httpFields.has(fieldName))
                return;
            const args = node.getArguments();
            if (!args.length)
                return;
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
function extractFields(cls) {
    const fields = [];
    const httpFields = new Set();
    // Constructor parameter properties (common in Angular DI)
    const ctor = cls.getConstructors()[0];
    if (ctor) {
        for (const param of ctor.getParameters()) {
            const typeText = param.getTypeNode()?.getText() ?? "any";
            const name = param.getName();
            const mods = param.getModifiers().map((m) => m.getText());
            if (mods.some((m) => ["private", "public", "protected", "readonly"].includes(m))) {
                const annotations = param
                    .getDecorators()
                    .map((d) => `@${getDecoratorName(d)}`);
                fields.push({ name, type: typeText, annotations });
                if (typeText === "HttpClient")
                    httpFields.add(name);
            }
        }
    }
    // Regular class properties
    for (const prop of cls.getProperties()) {
        const name = prop.getName();
        const typeText = prop.getTypeNode()?.getText() ?? "any";
        const annotations = prop
            .getDecorators()
            .map((d) => `@${getDecoratorName(d)}`);
        fields.push({ name, type: typeText, annotations });
        if (typeText === "HttpClient")
            httpFields.add(name);
    }
    return { fields, httpFields };
}
// ── Method extraction ──────────────────────────────────────
function extractMethods(cls, httpFields) {
    const results = [];
    for (const method of cls.getMethods()) {
        const name = method.getName();
        const returnType = method.getReturnTypeNode()?.getText() ?? "void";
        const params = method.getParameters().map((p) => `${p.getName()}: ${p.getTypeNode()?.getText() ?? "any"}`);
        const annotations = method
            .getDecorators()
            .map((d) => `@${getDecoratorName(d)}`);
        const calls = [];
        method.forEachDescendant((node) => {
            if (!ts_morph_1.Node.isCallExpression(node))
                return;
            const expr = node.getExpression();
            if (!ts_morph_1.Node.isPropertyAccessExpression(expr))
                return;
            const obj = expr.getExpression();
            const methodName = expr.getName();
            let scope = "";
            if (ts_morph_1.Node.isPropertyAccessExpression(obj)) {
                scope = obj.getName();
            }
            else if (ts_morph_1.Node.isIdentifier(obj)) {
                scope = obj.getText();
            }
            if (!scope)
                return;
            const isHttp = httpFields.has(scope);
            const confidence = isHttp ? 1.0 : 0.7;
            const resolved = isHttp ? "HttpClient" : scope;
            calls.push({ scope, method: methodName, resolved_type: resolved, confidence });
        });
        results.push({ name, return_type: returnType, parameters: params, annotations, calls });
    }
    return results;
}
// ── Class extractor ────────────────────────────────────────
function extractClass(cls) {
    const decorators = cls.getDecorators();
    const decNames = decorators.map(getDecoratorName);
    const annotations = decNames.map((n) => `@${n}`);
    const componentType = resolveComponentType(decorators);
    const { fields, httpFields } = extractFields(cls);
    const methods = extractMethods(cls, httpFields);
    const httpCalls = extractHttpCalls(cls, httpFields);
    const result = {
        name: cls.getName() ?? "Anonymous",
        component_type: componentType,
        annotations,
        methods,
        fields,
        http_calls: httpCalls,
        api_contracts: [],
    };
    // @Component metadata
    const compDec = decorators.find((d) => getDecoratorName(d) === "Component");
    if (compDec) {
        const sel = getDecoratorArg(compDec, "selector");
        const tmpl = getDecoratorArg(compDec, "templateUrl");
        if (sel)
            result.selector = sel;
        if (tmpl)
            result.template_url = tmpl;
    }
    // @Injectable scope
    const injDec = decorators.find((d) => getDecoratorName(d) === "Injectable");
    if (injDec) {
        const providedIn = getDecoratorArg(injDec, "providedIn");
        if (providedIn)
            result.injectable_scope = providedIn;
    }
    return result;
}
// ── File analyser ──────────────────────────────────────────
function analyseFile(filePath) {
    const project = new ts_morph_1.Project({ skipAddingFilesFromTsConfig: true });
    const srcFile = project.addSourceFileAtPath(filePath);
    const dir = path.dirname(filePath);
    const parts = dir.split(path.sep);
    const srcIdx = parts.lastIndexOf("src");
    const pkg = srcIdx >= 0
        ? parts.slice(srcIdx + 1).join(".")
        : parts[parts.length - 1];
    const classes = srcFile
        .getClasses()
        .map(extractClass);
    return {
        file: filePath,
        package: pkg,
        classes,
    };
}
function analyseFiles(filePaths) {
    return filePaths.map(analyseFile);
}
