export interface AskRequest {
  question: string;
  repo_id?: string;
  suite_id?: string;
  scope?: string;
  top_k?: number;
}

export interface AskResponse {
  answer: string;
  sources: string[];
  scores: number[];
  intent?: string;
  token_count?: number;
}

export interface SearchResult {
  name: string;
  component_type: string;
  wiki_summary?: string;
  score: number;
  repo_id?: string;
  unit_type?: string;
  class_name?: string;
  logic_summary?: string;
}

export interface FlowStep {
  step: number;
  layer: string;
  class_name: string;
  method_name: string;
  logic_summary?: string;
  repo_id?: string;
  repo_type?: 'frontend' | 'backend' | 'contract';
  component_type?: string;
}

export interface FlowTrace {
  entry_point: string;
  steps: FlowStep[];
  explanation: string;
  token_count: number;
  raw_token_estimate?: number;
  trace_mode?: 'cross_repo' | 'be_only' | 'none';
}

export interface PlanResponse {
  requirement: string;
  relevant_classes: { name: string; type: string; score: number }[];
  plan: string;
  tests?: string;
  token_usage?: Record<string, { total: number }>;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}
