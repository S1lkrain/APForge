import type { VisualSpec } from "../../api/types";
import { ChartRenderer } from "./ChartRenderer";

interface VisualRendererProps {
  visual?: VisualSpec | null;
}

export function VisualRenderer({ visual }: VisualRendererProps) {
  if (!visual) return null;
  if (visual.type !== "chart") return null;
  return <ChartRenderer visual={visual} />;
}
