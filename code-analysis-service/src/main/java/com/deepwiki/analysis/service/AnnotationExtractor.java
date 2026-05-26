package com.deepwiki.analysis.service;

import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.nodeTypes.NodeWithAnnotations;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class AnnotationExtractor {

    /**
     * Returns each annotation as its full source text, e.g.
     * "@GetMapping(\"/owners/{id}\")" or "@Transactional".
     * No framework knowledge — purely structural extraction.
     */
    public List<String> extractAnnotations(NodeWithAnnotations<?> node) {
        return node.getAnnotations().stream()
                .map(AnnotationExpr::toString)
                .collect(Collectors.toList());
    }
}
