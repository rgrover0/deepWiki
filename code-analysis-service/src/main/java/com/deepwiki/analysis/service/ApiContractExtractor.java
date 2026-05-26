package com.deepwiki.analysis.service;

import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.*;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class ApiContractExtractor {

    private static final Map<String, String> MAPPING_HTTP = Map.of(
            "GetMapping",    "GET",
            "PostMapping",   "POST",
            "PutMapping",    "PUT",
            "DeleteMapping", "DELETE",
            "PatchMapping",  "PATCH"
    );

    private static final Pattern PATH_VAR = Pattern.compile("\\{([^}]+)}");

    /** Extract the class-level base path from @RequestMapping, or "". */
    public String extractClassPath(ClassOrInterfaceDeclaration classDecl) {
        return classDecl.getAnnotations().stream()
                .filter(a -> a.getNameAsString().equals("RequestMapping"))
                .map(this::extractPath)
                .findFirst()
                .orElse("");
    }

    /**
     * Return one APIContract map per HTTP-mapped method in the class.
     * Combines class-level @RequestMapping prefix with method-level mapping.
     */
    public List<Map<String, Object>> extractContracts(ClassOrInterfaceDeclaration classDecl,
                                                       String className) {
        String classPath = extractClassPath(classDecl);
        List<Map<String, Object>> contracts = new ArrayList<>();

        for (MethodDeclaration method : classDecl.getMethods()) {
            for (AnnotationExpr ann : method.getAnnotations()) {
                String annName = ann.getNameAsString();
                String httpMethod = MAPPING_HTTP.get(annName);

                if (httpMethod == null && annName.equals("RequestMapping")) {
                    httpMethod = extractRequestMethod(ann);
                }

                if (httpMethod != null) {
                    String methodPath = extractPath(ann);
                    String fullPath   = combinePaths(classPath, methodPath);

                    Map<String, Object> contract = new LinkedHashMap<>();
                    contract.put("http_method",        httpMethod);
                    contract.put("path",               fullPath);
                    contract.put("path_variables",     extractPathVariables(fullPath));
                    contract.put("request_body_type",  extractRequestBodyType(method));
                    contract.put("return_type",        method.getType().asString());
                    contract.put("controller_method",  method.getNameAsString());
                    contract.put("controller_class",   className);
                    contracts.add(contract);
                    break; // one mapping annotation per method is enough
                }
            }
        }
        return contracts;
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private String extractPath(AnnotationExpr ann) {
        if (ann instanceof SingleMemberAnnotationExpr s) {
            return cleanValue(s.getMemberValue().toString());
        }
        if (ann instanceof NormalAnnotationExpr n) {
            return n.getPairs().stream()
                    .filter(p -> p.getNameAsString().equals("value")
                              || p.getNameAsString().equals("path"))
                    .map(p -> cleanValue(p.getValue().toString()))
                    .findFirst()
                    .orElse("");
        }
        // MarkerAnnotationExpr (bare @PostMapping) → no path
        return "";
    }

    private String extractRequestMethod(AnnotationExpr ann) {
        if (ann instanceof NormalAnnotationExpr n) {
            return n.getPairs().stream()
                    .filter(p -> p.getNameAsString().equals("method"))
                    .map(p -> {
                        String v = p.getValue().toString();
                        // RequestMethod.GET → GET; {RequestMethod.GET} → GET
                        v = v.replaceAll("[{}]", "");
                        return v.contains(".") ? v.substring(v.lastIndexOf('.') + 1) : v;
                    })
                    .findFirst()
                    .orElse("GET");
        }
        return "GET";
    }

    /** Strip wrapping quotes, curly braces, and array notation. */
    private String cleanValue(String raw) {
        raw = raw.trim();
        // Array literal → take first element: {"a","b"} → "a"
        if (raw.startsWith("{")) {
            int comma = raw.indexOf(',');
            raw = comma > 0 ? raw.substring(1, comma) : raw.substring(1, raw.length() - 1);
            raw = raw.trim();
        }
        // Remove surrounding quotes
        if (raw.startsWith("\"") && raw.endsWith("\"")) {
            raw = raw.substring(1, raw.length() - 1);
        }
        return raw;
    }

    private String combinePaths(String base, String method) {
        if (base.isEmpty())   return method.isEmpty() ? "/" : method;
        if (method.isEmpty()) return base;
        return base.replaceAll("/$", "") + "/" + method.replaceAll("^/", "");
    }

    private List<String> extractPathVariables(String path) {
        List<String> vars = new ArrayList<>();
        Matcher m = PATH_VAR.matcher(path);
        while (m.find()) vars.add(m.group(1));
        return vars;
    }

    private String extractRequestBodyType(MethodDeclaration method) {
        return method.getParameters().stream()
                .filter(p -> p.getAnnotations().stream()
                        .anyMatch(a -> a.getNameAsString().equals("RequestBody")))
                .map(p -> p.getTypeAsString())
                .findFirst()
                .orElse(null);
    }
}
