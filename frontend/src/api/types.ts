export type Subject = "ap_precalculus" | "ap_biology";
export type QuestionType = "mcq" | "frq";

export interface NumericChartDataPoint {
  x: number;
  y: number;
}

export interface CategoryChartDataPoint {
  x: string;
  y: number;
}

export interface LineChartSpec {
  type: "chart";
  chart_type: "line";
  title: string;
  x_label: string;
  y_label: string;
  data: NumericChartDataPoint[];
  caption?: string | null;
}

export interface ScatterChartSpec {
  type: "chart";
  chart_type: "scatter";
  title: string;
  x_label: string;
  y_label: string;
  data: NumericChartDataPoint[];
  caption?: string | null;
}

export interface BarChartSpec {
  type: "chart";
  chart_type: "bar";
  title: string;
  x_label: string;
  y_label: string;
  data: CategoryChartDataPoint[];
  caption?: string | null;
}

export type VisualSpec = LineChartSpec | ScatterChartSpec | BarChartSpec;

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
    visual?: VisualSpec | null;
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
  visual?: VisualSpec | null;
}

export type ItemsSort = "newest" | "oldest" | "quality_desc" | "quality_asc";

export interface ListItemsParams {
  run_id?: string;
  sample_id?: string;
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

export interface PublicConfig {
  api_auth_required: boolean;
  llm_configured: boolean;
  core_configured: boolean;
  free_sample_available: boolean;
  byok_connected: boolean;
  free_max_repair: number;
  byok_max_repair: number;
  free_sample_size: number;
  free_sample_min_usable: number;
}

export interface ValidationReport {
  total: number;
  usable_count: number;
  status_counts: Record<string, number>;
  failure_reason_codes: string[];
  repair_classes: string[];
  judge_scores: Record<string, unknown>[];
}

export interface SampleGenerateResponse {
  sample_id: string;
  items: GenerateResponse[];
  validation_report: ValidationReport;
  claim_status: string;
  usable_count: number;
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
