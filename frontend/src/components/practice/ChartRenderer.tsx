import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BarChartSpec, LineChartSpec, ScatterChartSpec, VisualSpec } from "../../api/types";

interface ChartRendererProps {
  visual: VisualSpec;
}

function ChartCaption({ caption }: { caption?: string | null }) {
  if (!caption) return null;
  return <p className="mt-2 text-center text-xs text-slate-500">{caption}</p>;
}

function renderLineChart(spec: LineChartSpec) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={spec.data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="number"
          scale="linear"
          domain={["dataMin", "dataMax"]}
          label={{ value: spec.x_label, position: "insideBottom", offset: -4 }}
        />
        <YAxis label={{ value: spec.y_label, angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Line type="monotone" dataKey="y" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function renderBarChart(spec: BarChartSpec) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={spec.data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="category"
          label={{ value: spec.x_label, position: "insideBottom", offset: -4 }}
        />
        <YAxis label={{ value: spec.y_label, angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Bar dataKey="y" fill="#2563eb" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function renderScatterChart(spec: ScatterChartSpec) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="number"
          name={spec.x_label}
          label={{ value: spec.x_label, position: "insideBottom", offset: -4 }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name={spec.y_label}
          label={{ value: spec.y_label, angle: -90, position: "insideLeft" }}
        />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
        <Scatter data={spec.data} fill="#2563eb" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ChartRenderer({ visual }: ChartRendererProps) {
  return (
    <figure className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-4">
      <figcaption className="mb-3 text-center text-sm font-semibold text-slate-800">
        {visual.title}
      </figcaption>
      {visual.chart_type === "line" && renderLineChart(visual)}
      {visual.chart_type === "bar" && renderBarChart(visual)}
      {visual.chart_type === "scatter" && renderScatterChart(visual)}
      <ChartCaption caption={visual.caption} />
    </figure>
  );
}
