import { useMemo } from "react";
import { hierarchy, pack, type HierarchyCircularNode } from "d3-hierarchy";
import type { ClusterInfo } from "../api";

interface Props {
  clusters: ClusterInfo[];
}

interface BubbleDatum {
  children: ClusterInfo[];
}

const SIZE = 520;
const COLORS = ["#a78bfa", "#f472b6", "#60a5fa", "#34d399", "#fbbf24", "#fb7185", "#22d3ee", "#c084fc", "#f97316"];

// Average glyph width as a fraction of font-size — used to estimate how many characters
// fit on one line inside a circle of a given radius, so long English labels wrap instead
// of overflowing the bubble (Chinese 2-4 char labels rarely need more than one line).
const AVG_CHAR_WIDTH_EM = 0.56;

function wrapLabel(label: string, maxCharsPerLine: number): string[] {
  const words = label.split(" ");
  if (words.length === 1) return [label];

  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > maxCharsPerLine && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

export default function BubbleCloud({ clusters }: Props) {
  const nodes = useMemo(() => {
    const root = hierarchy<BubbleDatum | ClusterInfo>({ children: clusters }).sum(
      (d) => ("count" in d ? d.count : 0),
    );
    const layout = pack<BubbleDatum | ClusterInfo>().size([SIZE, SIZE]).padding(6);
    return layout(root).leaves() as HierarchyCircularNode<ClusterInfo>[];
  }, [clusters]);

  return (
    <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className="mx-auto max-w-full">
      {nodes.map((node, i) => {
        const label = node.data.label;
        // usable chord width inside the circle, leaving a little margin
        const usableWidth = node.r * 1.6;

        let fontSize = Math.min(15, Math.max(8, node.r / 3));
        let lines = wrapLabel(label, Math.max(4, Math.floor(usableWidth / (fontSize * AVG_CHAR_WIDTH_EM))));

        // if the longest line still doesn't fit at this font size, shrink the font until it does
        while (fontSize > 7) {
          const maxCharsPerLine = Math.max(4, Math.floor(usableWidth / (fontSize * AVG_CHAR_WIDTH_EM)));
          lines = wrapLabel(label, maxCharsPerLine);
          const longest = Math.max(...lines.map((line) => line.length));
          if (longest * fontSize * AVG_CHAR_WIDTH_EM <= usableWidth) break;
          fontSize -= 1;
        }

        const lineHeight = fontSize * 1.15;
        const labelBlockHeight = lines.length * lineHeight;
        const firstLineDy = -labelBlockHeight / 2 + fontSize * 0.4;
        const countFontSize = Math.min(12, Math.max(7, node.r / 4));

        return (
          <g key={node.data.id} transform={`translate(${node.x},${node.y})`}>
            <g className="pop-in-item" style={{ animationDelay: `${i * 90}ms` }}>
              <circle r={node.r} fill={COLORS[i % COLORS.length]} fillOpacity={0.85} />
              <text textAnchor="middle" fontSize={fontSize} fill="#0b0b12" fontWeight={600}>
                {lines.map((line, lineIdx) => (
                  <tspan key={lineIdx} x={0} dy={lineIdx === 0 ? firstLineDy : lineHeight}>
                    {line}
                  </tspan>
                ))}
              </text>
              <text
                textAnchor="middle"
                dy={labelBlockHeight / 2 + countFontSize}
                fontSize={countFontSize}
                fill="#0b0b12"
              >
                {node.data.count}
              </text>
            </g>
          </g>
        );
      })}
    </svg>
  );
}
