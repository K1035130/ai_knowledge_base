import type { ReactNode } from "react";
import { Bar, BarChart, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useLanguage } from "../i18n/LanguageContext";

interface Props {
  byHour: Record<string, number>;
  byWeekday: Record<string, number>;
  byMonth: Record<string, number>;
}

const WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

interface TooltipProps {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

function CompactTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md bg-[#1c1c24] px-2 py-1 text-xs whitespace-nowrap text-white/90 shadow-lg">
      {label} : {payload[0].value}
    </div>
  );
}

function ChartCard({
  title,
  children,
  wide,
  delay = 0,
}: {
  title: string;
  children: ReactNode;
  wide?: boolean;
  delay?: number;
}) {
  return (
    <div
      className={`fade-up-item rounded-xl bg-white/5 p-4 ${wide ? "sm:col-span-2" : ""}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <h3 className="mb-2 text-sm font-medium text-white/70">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export default function ActivityCharts({ byHour, byWeekday, byMonth }: Props) {
  const { t } = useLanguage();
  const weekdayLabel: Record<string, string> = Object.fromEntries(
    WEEKDAY_ORDER.map((day, i) => [day, t.charts.weekdays[i]]),
  );

  const hourData = Object.entries(byHour)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([hour, count]) => ({ hour, count }));
  const weekdayData = WEEKDAY_ORDER.map((day) => ({ day: weekdayLabel[day], count: byWeekday[day] ?? 0 }));
  const monthData = Object.entries(byMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, count]) => ({ month, count }));

  return (
    <div className="grid w-full max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2">
      <ChartCard title={t.charts.byHour} delay={0}>
        <BarChart data={hourData}>
          <XAxis dataKey="hour" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip content={<CompactTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
          <Bar dataKey="count" fill="#a78bfa" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ChartCard>
      <ChartCard title={t.charts.byWeekday} delay={120}>
        <BarChart data={weekdayData}>
          <XAxis dataKey="day" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip content={<CompactTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
          <Bar dataKey="count" fill="#60a5fa" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ChartCard>
      <ChartCard title={t.charts.byMonth} wide delay={240}>
        <LineChart data={monthData}>
          <XAxis dataKey="month" tick={{ fill: "#9ca3af", fontSize: 10 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip content={<CompactTooltip />} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
          <Line type="monotone" dataKey="count" stroke="#34d399" strokeWidth={2} dot={false} />
        </LineChart>
      </ChartCard>
    </div>
  );
}
