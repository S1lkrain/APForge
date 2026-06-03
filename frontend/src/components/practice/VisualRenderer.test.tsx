import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { VisualSpec } from "../../api/types";
import { VisualRenderer } from "./VisualRenderer";

const lineVisual: VisualSpec = {
  type: "chart",
  chart_type: "line",
  title: "Enzyme Activity vs Temperature",
  x_label: "Temperature (°C)",
  y_label: "Activity",
  data: [
    { x: 10, y: 2 },
    { x: 20, y: 4 },
    { x: 30, y: 6 },
  ],
};

const barVisual: VisualSpec = {
  type: "chart",
  chart_type: "bar",
  title: "Treatment Comparison",
  x_label: "Treatment",
  y_label: "Growth Rate",
  data: [
    { x: "Control", y: 1.2 },
    { x: "Treatment A", y: 2.5 },
  ],
};

const scatterVisual: VisualSpec = {
  type: "chart",
  chart_type: "scatter",
  title: "Cell Count vs Time",
  x_label: "Time (hr)",
  y_label: "Cell Count",
  data: [
    { x: 0, y: 100 },
    { x: 2, y: 150 },
    { x: 4, y: 220 },
  ],
};

describe("VisualRenderer", () => {
  it("renders nothing when visual is null", () => {
    const { container } = render(<VisualRenderer visual={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders line chart with title", () => {
    render(<VisualRenderer visual={lineVisual} />);
    expect(screen.getByText("Enzyme Activity vs Temperature")).toBeInTheDocument();
  });

  it("renders bar chart with title", () => {
    render(<VisualRenderer visual={barVisual} />);
    expect(screen.getByText("Treatment Comparison")).toBeInTheDocument();
  });

  it("renders scatter chart with title", () => {
    render(<VisualRenderer visual={scatterVisual} />);
    expect(screen.getByText("Cell Count vs Time")).toBeInTheDocument();
  });
});
