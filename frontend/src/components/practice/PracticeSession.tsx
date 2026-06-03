import { useState } from "react";
import { CheckCircle2, RotateCcw, XCircle } from "lucide-react";
import type { ItemRow } from "../../api/types";
import { choiceLetter, isMcqCorrect, type McqLetter } from "../../lib/answer";
import { MathContent } from "./MathContent";
import { VisualRenderer } from "./VisualRenderer";

interface PracticeSessionProps {
  item: ItemRow;
}

export function PracticeSession({ item }: PracticeSessionProps) {
  const [selected, setSelected] = useState<McqLetter | null>(null);
  const revealed = selected !== null;
  const correct = selected !== null && isMcqCorrect(selected, item.answer);

  function handleSelect(letter: McqLetter) {
    if (revealed) return;
    setSelected(letter);
  }

  function handleTryAgain() {
    setSelected(null);
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <p className="text-base leading-relaxed text-slate-800">
          <MathContent>{item.question}</MathContent>
        </p>

        <VisualRenderer visual={item.visual} />

        <ul className="mt-6 space-y-3">
          {item.choices.map((choice, index) => {
            const letter = choiceLetter(choice, index);
            const isSelected = selected === letter;
            const isCorrectOption = item.answer.trim().toUpperCase() === letter;
            let cardClass =
              "flex w-full cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 text-left text-sm transition";

            if (!revealed) {
              cardClass += isSelected
                ? " border-brand bg-brand-muted"
                : " border-slate-200 bg-white hover:border-brand/40 hover:bg-slate-50";
            } else {
              cardClass += " cursor-default";
              if (isCorrectOption) {
                cardClass += " border-success bg-emerald-50";
              } else if (isSelected) {
                cardClass += " border-error bg-red-50";
              } else {
                cardClass += " border-slate-200 bg-slate-50 opacity-80";
              }
            }

            return (
              <li key={letter}>
                <button
                  type="button"
                  disabled={revealed}
                  onClick={() => handleSelect(letter)}
                  className={cardClass}
                >
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                      isSelected && !revealed
                        ? "border-brand bg-brand text-white"
                        : "border-slate-200 bg-white text-slate-700"
                    }`}
                  >
                    {letter}
                  </span>
                  <span className="flex-1 pt-1 text-slate-800">
                    <MathContent>{choice}</MathContent>
                  </span>
                  {revealed && isSelected && correct && (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-success" aria-hidden />
                  )}
                  {revealed && isSelected && !correct && (
                    <XCircle className="h-5 w-5 shrink-0 text-error" aria-hidden />
                  )}
                </button>
              </li>
            );
          })}
        </ul>

        {revealed && (
          <p
            className={`mt-4 flex items-center gap-2 text-sm font-medium ${
              correct ? "text-success" : "text-error"
            }`}
          >
            {correct ? (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Correct
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4" />
                Incorrect — correct answer is {item.answer.toUpperCase()}
              </>
            )}
          </p>
        )}
      </section>

      {revealed && (
        <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Explanation</h2>
          <div className="mt-3 text-sm leading-relaxed text-slate-700">
            <MathContent>{item.explanation}</MathContent>
          </div>
        </section>
      )}

      {revealed && (
        <button
          type="button"
          onClick={handleTryAgain}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          <RotateCcw className="h-4 w-4" />
          Try again
        </button>
      )}
    </div>
  );
}
