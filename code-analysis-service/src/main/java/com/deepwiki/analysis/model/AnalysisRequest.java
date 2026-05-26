package com.deepwiki.analysis.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AnalysisRequest {

    @JsonProperty("file_content")
    private String fileContent;

    @JsonProperty("filename")
    private String filename;

    public String getFileContent() { return fileContent; }
    public void setFileContent(String fileContent) { this.fileContent = fileContent; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }
}
