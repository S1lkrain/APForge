import { RotateCcw, Search } from "lucide-react";
import {
  DIFFICULTY_OPTIONS,
  QUALITY_OPTIONS,
  SORT_OPTIONS,
  SUBJECT_OPTIONS,
  TOPIC_FILTER_OPTIONS,
  TYPE_OPTIONS,
  type SortOption,
} from "../../lib/filterOptions";

const selectClass =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm transition-colors focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20";

interface HistoryFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  subject: string;
  onSubjectChange: (value: string) => void;
  skill: string;
  onSkillChange: (value: string) => void;
  type: string;
  onTypeChange: (value: string) => void;
  difficulty: string;
  onDifficultyChange: (value: string) => void;
  quality: string;
  onQualityChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  onClearAll: () => void;
}

export function HistoryFilters({
  search,
  onSearchChange,
  subject,
  onSubjectChange,
  skill,
  onSkillChange,
  type,
  onTypeChange,
  difficulty,
  onDifficultyChange,
  quality,
  onQualityChange,
  sort,
  onSortChange,
  onClearAll,
}: HistoryFiltersProps) {
  return (
    <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <label className="relative flex-1">
          <span className="sr-only">Search generations</span>
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            aria-hidden
          />
          <input
            type="search"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by keyword..."
            aria-label="Search generations"
            className="w-full rounded-lg border border-slate-200 py-2.5 pl-10 pr-3 text-sm shadow-sm transition-colors focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
          />
        </label>
        <button
          type="button"
          onClick={onClearAll}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900"
        >
          <RotateCcw className="h-4 w-4" />
          Clear All
        </button>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Subject</span>
          <select value={subject} onChange={(e) => onSubjectChange(e.target.value)} className={selectClass}>
            {SUBJECT_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Topic</span>
          <select value={skill} onChange={(e) => onSkillChange(e.target.value)} className={selectClass}>
            {TOPIC_FILTER_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Question Type</span>
          <select value={type} onChange={(e) => onTypeChange(e.target.value)} className={selectClass}>
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Difficulty</span>
          <select
            value={difficulty}
            onChange={(e) => onDifficultyChange(e.target.value)}
            className={selectClass}
          >
            {DIFFICULTY_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Quality Score</span>
          <select value={quality} onChange={(e) => onQualityChange(e.target.value)} className={selectClass}>
            {QUALITY_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-5 flex flex-wrap items-end gap-4">
        <label className="block min-w-[200px]">
          <span className="mb-1.5 block text-xs font-medium text-slate-muted">Sort By</span>
          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value as SortOption)}
            className={selectClass}
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
