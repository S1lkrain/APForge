import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { deleteItem, listItems } from "../api/client";
import type { ItemRow } from "../api/types";
import { HistoryFilters } from "../components/history/HistoryFilters";
import { HistoryPageHeader } from "../components/history/HistoryPageHeader";
import { GenerationsTable } from "../components/history/GenerationsTable";
import { Pagination } from "../components/history/Pagination";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import {
  qualityFilterToParams,
  type SortOption,
} from "../lib/filterOptions";
import { useNavigate } from "../lib/router";

const PAGE_SIZE = 10;

export function GenerationHistoryPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [subject, setSubject] = useState("");
  const [skill, setSkill] = useState("");
  const [type, setType] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [quality, setQuality] = useState("");
  const [sort, setSort] = useState<SortOption>("newest");
  const [page, setPage] = useState(1);
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ItemRow | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, subject, skill, type, difficulty, quality, sort]);

  const queryParams = useMemo(() => {
    const qualityParams = qualityFilterToParams(quality);
    return {
      q: debouncedSearch || undefined,
      subject: subject || undefined,
      skill: skill || undefined,
      type: type || undefined,
      difficulty: difficulty ? Number(difficulty) : undefined,
      sort,
      page,
      page_size: PAGE_SIZE,
      ...qualityParams,
    };
  }, [debouncedSearch, subject, skill, type, difficulty, quality, sort, page]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["items", queryParams],
    queryFn: () => listItems(queryParams),
    placeholderData: keepPreviousData,
  });

  const total = data?.total ?? 0;

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [total, page]);

  const deleteMutation = useMutation({
    mutationFn: (runId: string) => deleteItem(runId),
    onMutate: (runId) => {
      setDeletingRunId(runId);
      setDeleteError(null);
    },
    onSettled: () => {
      setDeletingRunId(null);
    },
    onSuccess: () => {
      setPendingDelete(null);
      void queryClient.invalidateQueries({ queryKey: ["items"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (err: Error) => {
      setDeleteError(err.message || "Failed to delete generation.");
    },
  });

  function handleClearAll() {
    setSearch("");
    setDebouncedSearch("");
    setSubject("");
    setSkill("");
    setType("");
    setDifficulty("");
    setQuality("");
    setSort("newest");
    setPage(1);
  }

  function handleView(row: ItemRow) {
    navigate(`/practice/${row.run_id}`);
  }

  function handleDeleteRequest(row: ItemRow) {
    setDeleteError(null);
    setPendingDelete(row);
  }

  function handleDeleteConfirm() {
    if (!pendingDelete) return;
    deleteMutation.mutate(pendingDelete.run_id);
  }

  const rows = data?.items ?? [];

  return (
    <>
      <HistoryPageHeader />

      <HistoryFilters
        search={search}
        onSearchChange={setSearch}
        subject={subject}
        onSubjectChange={setSubject}
        skill={skill}
        onSkillChange={setSkill}
        type={type}
        onTypeChange={setType}
        difficulty={difficulty}
        onDifficultyChange={setDifficulty}
        quality={quality}
        onQualityChange={setQuality}
        sort={sort}
        onSortChange={setSort}
        onClearAll={handleClearAll}
      />

      {deleteError && (
        <p className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-error">
          {deleteError}
        </p>
      )}

      <section className="rounded-xl border border-slate-100 bg-white shadow-sm">
        <GenerationsTable
          rows={rows}
          isLoading={isLoading || (isFetching && rows.length === 0)}
          isError={isError}
          emptyMessage="No generations match your filters."
          showDelete
          onView={handleView}
          onDelete={handleDeleteRequest}
          deletingRunId={deletingRunId}
        />
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          onPageChange={setPage}
        />
      </section>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete generation?"
        message="This will permanently remove this generation. This cannot be undone."
        confirmLabel="Delete"
        isLoading={deleteMutation.isPending}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setPendingDelete(null)}
      />
    </>
  );
}
