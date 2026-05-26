package com.deepwiki.analysis.controller;

import com.deepwiki.analysis.model.AnalysisRequest;
import com.deepwiki.analysis.service.JavaFileParser;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class AnalyzeController {

    @Autowired
    private JavaFileParser javaFileParser;

    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyze(@RequestBody AnalysisRequest request) {
        try {
            Map<String, Object> result = javaFileParser.parse(
                    request.getFileContent(),
                    request.getFilename()
            );
            return ResponseEntity.ok(result);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of("status", "ok", "service", "code-analysis-service"));
    }
}
