import { TOPIC_OPTIONS } from "./format";

export const SUBJECT_OPTIONS = [
  { value: "", label: "All Subjects" },
  { value: "ap_precalculus", label: "AP Precalculus" },
  { value: "ap_calculus_ab", label: "AP Calculus AB" },
  { value: "ap_calculus_bc", label: "AP Calculus BC" },
  { value: "ap_statistics", label: "AP Statistics" },
];

export const TOPIC_FILTER_OPTIONS = [
  { value: "", label: "All Topics" },
  ...TOPIC_OPTIONS,
];

export const TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "mcq", label: "MCQ" },
  { value: "frq", label: "FRQ" },
];

export const DIFFICULTY_OPTIONS = [
  { value: "", label: "All Difficulties" },
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3", label: "3" },
  { value: "4", label: "4" },
  { value: "5", label: "5" },
];

export const QUALITY_OPTIONS = [
  { value: "", label: "All Scores" },
  { value: "high", label: "80+" },
  { value: "medium", label: "60–79" },
  { value: "low", label: "Below 60" },
  { value: "none", label: "No score" },
];

export const SORT_OPTIONS = [
  { value: "newest", label: "Newest First" },
  { value: "oldest", label: "Oldest First" },
  { value: "quality_desc", label: "Highest Quality" },
  { value: "quality_asc", label: "Lowest Quality" },
] as const;

export type SortOption = (typeof SORT_OPTIONS)[number]["value"];

export function qualityFilterToParams(quality: string): {
  quality_min?: number;
  quality_max?: number;
  has_quality?: boolean;
} {
  switch (quality) {
    case "high":
      return { quality_min: 80 };
    case "medium":
      return { quality_min: 60, quality_max: 79.9 };
    case "low":
      return { quality_max: 59.9 };
    case "none":
      return { has_quality: false };
    default:
      return {};
  }
}
