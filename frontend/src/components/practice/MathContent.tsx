import { Fragment } from "react";
import { useKatexReady } from "../../lib/useKatexReady";

type Segment =
  | { kind: "text"; value: string }
  | { kind: "math"; value: string; display: boolean };

const DELIMITER_PATTERN =
  /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\$[^$\n]+?\$)/g;

function parseSegments(content: string): Segment[] {
  const segments: Segment[] = [];
  let lastIndex = 0;

  for (const match of content.matchAll(DELIMITER_PATTERN)) {
    const index = match.index ?? 0;
    if (index > lastIndex) {
      segments.push({ kind: "text", value: content.slice(lastIndex, index) });
    }

    const raw = match[0];
    let latex = raw;
    let display = false;

    if (raw.startsWith("$$") && raw.endsWith("$$")) {
      latex = raw.slice(2, -2);
      display = true;
    } else if (raw.startsWith("\\[") && raw.endsWith("\\]")) {
      latex = raw.slice(2, -2);
      display = true;
    } else if (raw.startsWith("\\(") && raw.endsWith("\\)")) {
      latex = raw.slice(2, -2);
    } else if (raw.startsWith("$") && raw.endsWith("$")) {
      latex = raw.slice(1, -1);
    }

    segments.push({ kind: "math", value: latex.trim(), display });
    lastIndex = index + raw.length;
  }

  if (lastIndex < content.length) {
    segments.push({ kind: "text", value: content.slice(lastIndex) });
  }

  return segments.length > 0 ? segments : [{ kind: "text", value: content }];
}

function renderMath(latex: string, display: boolean): string {
  const katex = window.katex;
  if (!katex) {
    return display ? `<pre>${latex}</pre>` : latex;
  }
  try {
    return katex.renderToString(latex, {
      displayMode: display,
      throwOnError: false,
      strict: "ignore",
    });
  } catch {
    return latex;
  }
}

interface MathContentProps {
  children: string;
  className?: string;
}

export function MathContent({ children, className = "" }: MathContentProps) {
  const katexReady = useKatexReady();
  const segments = parseSegments(children);

  return (
    <span className={`math-content whitespace-pre-wrap leading-relaxed ${className}`.trim()}>
      {segments.map((segment, index) => {
        if (segment.kind === "text") {
          return <Fragment key={index}>{segment.value}</Fragment>;
        }

        const html = renderMath(segment.value, segment.display);
        const mathKey = `${index}-${katexReady ? "rendered" : "pending"}`;
        if (segment.display) {
          return (
            <span
              key={mathKey}
              className="my-3 block overflow-x-auto"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        }

        return (
          <span key={mathKey} className="inline" dangerouslySetInnerHTML={{ __html: html }} />
        );
      })}
    </span>
  );
}
