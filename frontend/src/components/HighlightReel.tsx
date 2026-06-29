import type { Highlight } from "../api";

export default function HighlightReel({ highlights }: { highlights: Highlight[] }) {
  return (
    <div className="grid w-full max-w-4xl grid-cols-1 gap-3 sm:grid-cols-2">
      {highlights.map((h, i) => (
        <div
          key={h.month}
          className="fade-up-item rounded-xl bg-gradient-to-br from-violet-500/15 to-pink-500/10 p-4"
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <p className="text-xs font-medium text-violet-300">{h.month}</p>
          <p className="mt-1 text-sm text-white/90">{h.text}</p>
        </div>
      ))}
    </div>
  );
}
