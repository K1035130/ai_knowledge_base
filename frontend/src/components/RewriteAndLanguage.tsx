import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ReportResult } from "../api";
import { useLanguage } from "../i18n/LanguageContext";

interface Props {
  rewriteRate: ReportResult["rewrite_rate"];
  languageRatio: Record<string, number>;
}

// Distinct hues (not just shades of the same color) so the slices are easy to tell apart at a glance.
const LANG_COLORS = ["#a78bfa", "#fb923c", "#2dd4bf", "#f472b6"];

interface PieTooltipProps {
  active?: boolean;
  payload?: { name: string; value: number }[];
}

function PieTooltip({ active, payload }: PieTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md bg-[#1c1c24] px-2 py-1 text-xs whitespace-nowrap text-white/90 shadow-lg">
      {payload[0].name}: {Math.round(payload[0].value * 100)}%
    </div>
  );
}

export default function RewriteAndLanguage({ rewriteRate, languageRatio }: Props) {
  const { t } = useLanguage();
  const pct = rewriteRate.total_conversations
    ? Math.round((rewriteRate.conversations_with_edits / rewriteRate.total_conversations) * 100)
    : 0;

  const pieData = Object.entries(languageRatio).map(([lang, ratio]) => ({
    name: t.language.labels[lang] ?? lang,
    value: ratio,
  }));

  return (
    <div className="flex w-full max-w-md flex-col gap-4">
      <div className="fade-up-item rounded-xl bg-white/5 p-4" style={{ animationDelay: "0ms" }}>
        <h3 className="mb-2 text-sm font-medium text-white/70">{t.rewrite.heading}</h3>
        <p className="text-sm text-white/80">
          {t.rewrite.summary(pct, rewriteRate.conversations_with_edits, rewriteRate.total_conversations)}
        </p>
        <p className="mt-1 text-xs text-white/50">
          {t.rewrite.detail(rewriteRate.user_edit_turns, rewriteRate.assistant_regen_turns)}
        </p>
      </div>

      <div className="fade-up-item rounded-xl bg-white/5 p-4" style={{ animationDelay: "150ms" }}>
        <h3 className="mb-2 text-sm font-medium text-white/70">{t.language.heading}</h3>
        <div className="flex items-center gap-4">
          <ResponsiveContainer width={120} height={120}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={32} outerRadius={55} paddingAngle={3}>
                {pieData.map((entry, i) => (
                  <Cell key={entry.name} fill={LANG_COLORS[i % LANG_COLORS.length]} stroke="none" />
                ))}
              </Pie>
              <Tooltip content={<PieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-col gap-1.5 text-xs text-white/70">
            {pieData.map((entry, i) => (
              <div key={entry.name} className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: LANG_COLORS[i % LANG_COLORS.length] }}
                />
                <span>
                  {entry.name}: {Math.round(entry.value * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
