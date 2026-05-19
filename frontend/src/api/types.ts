export type Subject = "ap_precalculus";
export type QuestionType = "mcq" | "frq";

export interface GenerateRequest {
  subject: Subject;
  skill: string;
  difficulty: number;
  type: QuestionType;
  locale?: string;
}

export interface GenerateResponse {
  run_id: string;
  request_id: string;
  item: {
    question: string;
    choices: string[];
    answer: string;
    explanation: string;
    metadata: Record<string, unknown>;
  };
  metrics: Record<string, unknown>;
  harness: {
    status: string;
    policy_status: string;
    failure_reason_code: string;
  };
}

export interface ItemRow {
  run_id: string;
  created_at: string;
  subject: string;
  skill: string;
  difficulty: number;
  type: string;
  final_status: string;
  status: "Success" | "Warn" | "Rejected";
  quality_score: number | null;
  question: string;
  choices: string[];
  answer: string;
  explanation: string;
  metadata: Record<string, unknown>;
}

export type ItemsSort = "newest" | "oldest" | "quality_desc" | "quality_asc";

export interface ListItemsParams {
  run_id?: string;
  subject?: string;
  skill?: string;
  difficulty?: number;
  type?: string;
  status?: string;
  q?: string;
  quality_min?: number;
  quality_max?: number;
  has_quality?: boolean;
  sort?: ItemsSort;
  page?: number;
  page_size?: number;
}

export interface ItemsListResponse {
  items: ItemRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  total_generated: number;
  success_rate: number;
  avg_quality_score: number;
  total_runs: number;
  week_delta: {
    total_generated: number;
    success_rate: number;
    avg_quality_score: number;
    total_runs: number;
  };
}
