package com.deepwiki.analysis.service;

import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.MethodCallExpr;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class MethodCallExtractor {

    /**
     * Traverses the method body AST and returns every method call found.
     *
     * Resolution strategy (field map lookup — no full symbol solver needed):
     *   scope matches a field name  → "FieldType.method"  confidence 1.0
     *   scope present but unknown   → "scope.method"      confidence 0.5
     *   no scope (internal call)    → "method"            confidence 0.7
     */
    public List<Map<String, Object>> extractCalls(MethodDeclaration method,
                                                   Map<String, String> fieldTypes) {
        List<Map<String, Object>> calls = new ArrayList<>();

        method.findAll(MethodCallExpr.class).forEach(callExpr -> {
            String methodName = callExpr.getNameAsString();
            int line = callExpr.getBegin().map(p -> p.line).orElse(0);

            String target;
            double confidence;

            if (callExpr.getScope().isPresent()) {
                String scope = callExpr.getScope().get().toString();
                if (fieldTypes.containsKey(scope)) {
                    // Strip generics: "List<Owner>" → "List"
                    String resolvedType = fieldTypes.get(scope).replaceAll("<.*>", "").trim();
                    target = resolvedType + "." + methodName;
                    confidence = 1.0;
                } else {
                    target = scope + "." + methodName;
                    confidence = 0.5;
                }
            } else {
                target = methodName;
                confidence = 0.7;
            }

            Map<String, Object> call = new LinkedHashMap<>();
            call.put("target", target);
            call.put("line", line);
            call.put("confidence", confidence);
            calls.add(call);
        });

        return calls;
    }
}
