import { useCallback, useEffect, useRef, useState } from "react";
import { domToPng } from "modern-screenshot";
import type { ReportResult } from "../api";
import { useLanguage } from "../i18n/LanguageContext";
import OverviewCards from "./OverviewCards";
import ActivityCharts from "./ActivityCharts";
import BubbleCloud from "./BubbleCloud";
import HighlightReel from "./HighlightReel";
import RewriteAndLanguage from "./RewriteAndLanguage";

interface Props {
  report: ReportResult;
  onReupload: () => void;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function buildStandaloneHtml(title: string, sections: { title: string; dataUrl: string }[]): string {
  const sectionsHtml = sections
    .map(
      (s) => `
    <section style="margin-bottom:48px;">
      <h2 style="font-size:20px;font-weight:600;color:#f1f1f4;margin-bottom:16px;text-align:center;">${escapeHtml(s.title)}</h2>
      <img src="${s.dataUrl}" style="display:block;max-width:100%;margin:0 auto;border-radius:16px;" />
    </section>`,
    )
    .join("\n");

  return `<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8" />
<title>${escapeHtml(title)}</title>
<style>
  body { margin: 0; padding: 40px 16px; background: linear-gradient(to top, rgba(124,58,237,0.25), #1a1430, #0b0b12); color: #f1f1f4; font-family: system-ui, "Segoe UI", Roboto, sans-serif; }
  h1 { text-align: center; font-size: 28px; font-weight: 600; margin-bottom: 40px; }
  footer { text-align: center; color: rgba(255,255,255,0.4); font-size: 12px; margin-top: 40px; }
</style>
</head>
<body>
  <h1>${escapeHtml(title)}</h1>
  ${sectionsHtml}
  <footer>${escapeHtml(new Date().toLocaleDateString())}</footer>
</body>
</html>`;
}

function downloadHtml(filename: string, html: string): void {
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ArrowButton({
  direction,
  onClick,
  disabled,
  label,
}: {
  direction: "left" | "right";
  onClick: () => void;
  disabled: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={`fixed top-1/2 z-40 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white/80 backdrop-blur-md transition hover:bg-white/20 active:scale-95 disabled:pointer-events-none disabled:opacity-0 ${
        direction === "left" ? "left-3 sm:left-6" : "right-3 sm:right-6"
      }`}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        {direction === "left" ? (
          <path d="M15 18 9 12l6-6" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
        )}
      </svg>
    </button>
  );
}

export default function ReportView({ report, onReupload }: Props) {
  const { t } = useLanguage();
  const [page, setPage] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const pages = [
    { title: t.sections.overview, content: <OverviewCards overview={report.overview} /> },
    {
      title: t.sections.activity,
      content: (
        <ActivityCharts
          byHour={report.activity.by_hour}
          byWeekday={report.activity.by_weekday}
          byMonth={report.activity.by_month}
        />
      ),
    },
    {
      title: t.sections.habits,
      content: <RewriteAndLanguage rewriteRate={report.rewrite_rate} languageRatio={report.language_ratio} />,
    },
    { title: t.sections.topics, content: <BubbleCloud clusters={report.clusters} /> },
    { title: t.sections.highlights, content: <HighlightReel highlights={report.highlights} /> },
    {
      title: t.sections.ending,
      content: (
        <button
          type="button"
          onClick={onReupload}
          className="rounded-2xl bg-violet-500 px-6 py-3 text-sm font-medium text-white transition active:scale-[0.98] hover:bg-violet-400"
        >
          {t.reupload}
        </button>
      ),
    },
  ];

  const goPrev = useCallback(() => setPage((p) => Math.max(0, p - 1)), []);
  const goNext = useCallback(() => setPage((p) => Math.min(pages.length - 1, p + 1)), [pages.length]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (isExporting) return;
      if (e.key === "ArrowLeft") goPrev();
      if (e.key === "ArrowRight") goNext();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [goPrev, goNext, isExporting]);

  async function handleExport() {
    if (isExporting) return;
    setIsExporting(true);
    setExportError(null);
    const originalPage = page;
    const captures: { title: string; dataUrl: string }[] = [];
    try {
      // skip the last "ending" page — it's just the reupload button, not report content
      for (let i = 0; i < pages.length - 1; i++) {
        setPage(i);
        // give the page's mount animation (fade-up/pop-in) and any chart layout time to settle
        await new Promise((resolve) => setTimeout(resolve, 1200));
        if (!contentRef.current) continue;
        const dataUrl = await domToPng(contentRef.current, {
          backgroundColor: "#13101f",
          scale: 2,
        });
        captures.push({ title: pages[i].title, dataUrl });
      }
      downloadHtml("ai-usage-report.html", buildStandaloneHtml(t.title, captures));
    } catch (err) {
      console.error("HTML export failed:", err);
      setExportError(t.export.error);
    } finally {
      setPage(originalPage);
      setIsExporting(false);
    }
  }

  return (
    <div className="flex w-full flex-1 flex-col items-center justify-center gap-8 py-6">
      <ArrowButton direction="left" onClick={goPrev} disabled={page === 0 || isExporting} label={t.nav.prev} />
      <ArrowButton
        direction="right"
        onClick={goNext}
        disabled={page === pages.length - 1 || isExporting}
        label={t.nav.next}
      />

      <button
        type="button"
        onClick={handleExport}
        disabled={isExporting}
        className="fixed top-4 right-4 z-40 flex items-center gap-1.5 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs text-white/80 backdrop-blur-md transition hover:bg-white/20 disabled:opacity-60 sm:top-6 sm:right-6"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 3v12m0 0-4-4m4 4 4-4M5 21h14" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {isExporting ? t.export.generating : t.export.button}
      </button>
      {exportError && (
        <p className="fixed top-14 right-4 z-40 max-w-[200px] text-right text-xs text-red-400 sm:top-16 sm:right-6">
          {exportError}
        </p>
      )}

      <h2 key={`title-${page}`} className="fade-up-item text-xl font-semibold text-white/90">
        {pages[page].title}
      </h2>

      <div ref={contentRef} key={`content-${page}`} className="flex w-full flex-col items-center">
        {pages[page].content}
      </div>

      <div className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 gap-2">
        {pages.map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setPage(i)}
            disabled={isExporting}
            aria-label={`page ${i + 1}`}
            className={`h-1.5 rounded-full transition-all disabled:opacity-60 ${i === page ? "w-5 bg-white" : "w-1.5 bg-white/30"}`}
          />
        ))}
      </div>
    </div>
  );
}
