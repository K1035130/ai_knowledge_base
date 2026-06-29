import type { ReportResult } from "../api";
import { useLanguage } from "../i18n/LanguageContext";

interface Props {
  overview: ReportResult["overview"];
}

export default function OverviewCards({ overview }: Props) {
  const { t } = useLanguage();
  const o = t.overview;

  const items = [
    { label: o.total_conversations, value: overview.total_conversations },
    { label: o.total_messages, value: overview.total_messages },
    { label: o.active_days, value: overview.active_days },
    { label: o.avg_session, value: `${overview.avg_session_minutes} ${o.minutes}` },
    { label: o.longest_session, value: `${overview.longest_session_minutes} ${o.minutes}` },
    { label: o.avg_thread_span, value: `${overview.avg_thread_span_hours} ${o.hours}` },
    { label: o.avg_response, value: `${overview.avg_response_seconds} ${o.seconds}` },
  ];

  return (
    <div className="grid w-full max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4">
      {items.map((item, i) => (
        <div
          key={item.label}
          className="fade-up-item rounded-xl bg-white/5 p-4 text-center"
          style={{ animationDelay: `${i * 70}ms` }}
        >
          <p className="text-2xl font-semibold text-violet-300">{item.value}</p>
          <p className="mt-1 text-xs text-white/50">{item.label}</p>
        </div>
      ))}
    </div>
  );
}
