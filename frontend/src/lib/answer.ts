export type McqLetter = "A" | "B" | "C" | "D";

const LETTERS: McqLetter[] = ["A", "B", "C", "D"];

export function choiceLetter(choice: string, index: number): McqLetter {
  const match = choice.trim().match(/^([A-D])[.)]\s/i);
  if (match) {
    return match[1].toUpperCase() as McqLetter;
  }
  return LETTERS[index] ?? "A";
}

export function isMcqCorrect(selected: string, answer: string): boolean {
  return selected.trim().toUpperCase() === answer.trim().toUpperCase();
}
