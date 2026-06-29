import { useEffect, useRef, useState } from "react";
import UploadDropzone from "./components/UploadDropzone";
import ExportGuide from "./components/ExportGuide";
import PrivacyNotice from "./components/PrivacyNotice";
import BackgroundBubbles from "./components/BackgroundBubbles";
import LanguageToggle from "./components/LanguageToggle";
import WaitingQuotes from "./components/WaitingQuotes";
import ReportView from "./components/ReportView";
import { uploadExports, getJobStatus, type ReportResult } from "./api";
import { useLanguage } from "./i18n/LanguageContext";

type Phase = "idle" | "running" | "done" | "error";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

function App() {
  const { t, lang } = useLanguage();
  const [phase, setPhase] = useState<Phase>("idle");
  const [step, setStep] = useState<string>("");
  const [report, setReport] = useState<ReportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPrivacyNotice, setShowPrivacyNotice] = useState(true);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, []);

  async function handleFiles(files: File[]) {
    setPhase("running");
    setError(null);
    setStep(t.processing);
    try {
      const jobId = await uploadExports(files, lang);
      pollRef.current = window.setInterval(async () => {
        try {
          const job = await getJobStatus(jobId);
          setStep(job.step);
          if (job.status === "done" && job.result) {
            setReport(job.result);
            setPhase("done");
            if (pollRef.current) window.clearInterval(pollRef.current);
          } else if (job.status === "error") {
            setError(job.error ?? "unknown error");
            setPhase("error");
            if (pollRef.current) window.clearInterval(pollRef.current);
          }
        } catch (err) {
          setError(errorMessage(err));
          setPhase("error");
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      }, 1500);
    } catch (err) {
      setError(String(err));
      setPhase("error");
    }
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center gap-6 overflow-hidden bg-gradient-to-t from-violet-600/40 via-[#1a1430] to-[#0b0b12] px-4 py-12">
      <BackgroundBubbles />

      {showPrivacyNotice && <PrivacyNotice onAcknowledge={() => setShowPrivacyNotice(false)} />}

      <div className="relative z-10 flex min-h-0 w-full flex-1 flex-col items-center gap-6">
        {phase === "idle" && (
          <div className="self-end">
            <LanguageToggle />
          </div>
        )}

        {phase !== "done" && <h1 className="text-3xl font-semibold tracking-tight">{t.title}</h1>}

        {phase === "idle" && (
          <div className="flex flex-col items-center gap-10">
            <UploadDropzone onFilesSelected={handleFiles} />
            <ExportGuide />
          </div>
        )}

        {phase === "running" && (
          <>
            <div className="fixed top-[25%] left-1/2 z-10 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-3 text-white/70">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-violet-400" />
              <p>{step || t.processing}</p>
              <p className="text-xs text-white/40">{t.processingHint}</p>
            </div>
            <div className="fixed top-1/2 left-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
              <WaitingQuotes />
            </div>
          </>
        )}

        {phase === "error" && (
          <div className="flex flex-col items-center gap-3 text-red-400">
            <p>
              {t.errorPrefix}
              {error}
            </p>
            <button
              type="button"
              onClick={() => setPhase("idle")}
              className="rounded-lg bg-white/10 px-4 py-2 text-sm text-white/80 hover:bg-white/20"
            >
              {t.retry}
            </button>
          </div>
        )}

        {phase === "done" && report && (
          <ReportView
            report={report}
            onReupload={() => {
              setPhase("idle");
              setReport(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App;
