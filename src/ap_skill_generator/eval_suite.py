from __future__ import annotations

from .evaluation import aggregate_metrics, evaluate_item
from .schema import GeneratedItem
from .storage import Storage


def run_offline_eval(storage: Storage) -> dict:
    rows = storage.list_items(page_size=50)["items"]
    evals = []
    for row in rows:
        item = GeneratedItem(
            question=row["question"],
            choices=row["choices"],
            answer=row["answer"],
            explanation=row["explanation"],
            metadata=row["metadata"],
        )
        evals.append(evaluate_item(item))
    metrics = aggregate_metrics(evals)
    metrics["acceptance_passed"] = metrics["schema_valid_rate"] >= 0.98
    return metrics
