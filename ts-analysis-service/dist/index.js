"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const AngularParser_1 = require("./AngularParser");
const app = (0, express_1.default)();
const PORT = process.env.PORT ?? 8082;
app.use(express_1.default.json());
// POST /analyze — analyse one or many TypeScript files
app.post("/analyze", (req, res) => {
    const { file_path, file_paths } = req.body;
    const paths = [];
    if (file_path)
        paths.push(file_path);
    if (file_paths)
        paths.push(...file_paths);
    if (!paths.length) {
        return res.status(400).json({ error: "Provide file_path or file_paths" });
    }
    try {
        const results = (0, AngularParser_1.analyseFiles)(paths);
        return res.json(results);
    }
    catch (err) {
        return res.status(500).json({ error: err.message });
    }
});
// GET /health
app.get("/health", (_req, res) => {
    res.json({ status: "ok", service: "ts-analysis-service" });
});
app.listen(PORT, () => {
    console.log(`ts-analysis-service listening on port ${PORT}`);
});
