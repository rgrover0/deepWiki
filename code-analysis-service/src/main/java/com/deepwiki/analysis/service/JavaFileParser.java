package com.deepwiki.analysis.service;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class JavaFileParser {

    // Annotation name → component type (mirrors Python static_analysis.py)
    private static final Map<String, String> COMPONENT_MAP = Map.of(
            "RestController",  "REST_CONTROLLER",
            "Controller",      "CONTROLLER",
            "Service",         "SERVICE",
            "Repository",      "REPOSITORY",
            "Entity",          "ENTITY",
            "Component",       "COMPONENT",
            "Configuration",   "CONFIGURATION"
    );

    @Autowired private AnnotationExtractor  annotationExtractor;
    @Autowired private MethodCallExtractor  methodCallExtractor;
    @Autowired private ApiContractExtractor apiContractExtractor;

    public Map<String, Object> parse(String fileContent, String filename) {
        // New instance per call — safe for concurrent requests
        JavaParser javaParser = new JavaParser();
        ParseResult<CompilationUnit> parseResult = javaParser.parse(fileContent);

        if (!parseResult.isSuccessful() || parseResult.getResult().isEmpty()) {
            String problems = parseResult.getProblems().stream()
                    .map(Object::toString)
                    .collect(Collectors.joining("; "));
            throw new IllegalArgumentException("Parse failed: " + problems);
        }

        CompilationUnit cu = parseResult.getResult().get();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("file", filename);
        result.put("package", cu.getPackageDeclaration()
                .map(pd -> pd.getNameAsString()).orElse(""));

        List<Map<String, Object>> classes = new ArrayList<>();

        // getTypes() returns only top-level type declarations
        cu.getTypes().forEach(typeDecl -> {
            if (!(typeDecl instanceof ClassOrInterfaceDeclaration classDecl)) return;

            List<String> classAnnotations = annotationExtractor.extractAnnotations(classDecl);

            // Build field-type map used by MethodCallExtractor for CALLS resolution
            Map<String, String> fieldTypes = new LinkedHashMap<>();
            List<Map<String, Object>> fields = new ArrayList<>();

            for (FieldDeclaration fieldDecl : classDecl.getFields()) {
                String typeName = fieldDecl.getElementType().asString();
                List<String> fieldAnnotations = annotationExtractor.extractAnnotations(fieldDecl);

                fieldDecl.getVariables().forEach(var -> {
                    fieldTypes.put(var.getNameAsString(), typeName);

                    Map<String, Object> fieldMap = new LinkedHashMap<>();
                    fieldMap.put("name",        var.getNameAsString());
                    fieldMap.put("type",        typeName);
                    fieldMap.put("annotations", fieldAnnotations);
                    fields.add(fieldMap);
                });
            }

            List<Map<String, Object>> methods = new ArrayList<>();
            for (MethodDeclaration method : classDecl.getMethods()) {
                Map<String, Object> methodMap = new LinkedHashMap<>();
                methodMap.put("name",        method.getNameAsString());
                methodMap.put("return_type", method.getType().asString());
                methodMap.put("parameters",  method.getParameters().stream()
                        .map(p -> p.getTypeAsString() + " " + p.getNameAsString())
                        .collect(Collectors.toList()));
                methodMap.put("annotations", annotationExtractor.extractAnnotations(method));
                methodMap.put("calls",       methodCallExtractor.extractCalls(method, fieldTypes));
                methods.add(methodMap);
            }

            Map<String, Object> classMap = new LinkedHashMap<>();
            classMap.put("name",           classDecl.getNameAsString());
            classMap.put("component_type", determineComponentType(classAnnotations));
            classMap.put("annotations",    classAnnotations);
            classMap.put("extends",        classDecl.getExtendedTypes().isEmpty()
                    ? null
                    : classDecl.getExtendedTypes().get(0).getNameAsString());
            classMap.put("implements",     classDecl.getImplementedTypes().stream()
                    .map(t -> t.getNameAsString())
                    .collect(Collectors.toList()));
            classMap.put("fields",         fields);
            classMap.put("methods",        methods);
            classMap.put("api_contracts",  apiContractExtractor.extractContracts(
                    classDecl, classDecl.getNameAsString()));
            classes.add(classMap);
        });

        result.put("classes", classes);
        return result;
    }

    private String determineComponentType(List<String> annotations) {
        for (String ann : annotations) {
            for (Map.Entry<String, String> entry : COMPONENT_MAP.entrySet()) {
                if (ann.contains(entry.getKey())) return entry.getValue();
            }
        }
        return "CLASS";
    }
}
