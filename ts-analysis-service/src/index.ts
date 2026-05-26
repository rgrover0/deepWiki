import express, { Request, Response } from "express";
import { analyseFile, analyseFiles } from "./AngularParser";

const app  = express();
const PORT = process.env.PORT ?? 8082;

app.use(express.json());

// POST /analyze — analyse one or many TypeScript files
app.post("/analyze", (req: Request, res: Response) => {
  const { file_path, file_paths } = req.body as {
    file_path?: string;
    file_paths?: string[];
  };

  const paths: string[] = [];
  if (file_path)  paths.push(file_path);
  if (file_paths) paths.push(...file_paths);

  if (!paths.length) {
    return res.status(400).json({ error: "Provide file_path or file_paths" });
  }

  try {
    const results = analyseFiles(paths);
    return res.json(results);
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
});

// GET /health
app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok", service: "ts-analysis-service" });
});

app.listen(PORT, () => {
  console.log(`ts-analysis-service listening on port ${PORT}`);
});
