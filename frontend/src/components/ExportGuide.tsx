import { useLanguage } from "../i18n/LanguageContext";

export default function ExportGuide() {
  const { t } = useLanguage();
  const steps = t.guide.steps;

  return (
    <div className="w-full max-w-md">
      <p className="mb-5 text-center text-xs font-medium tracking-wide text-white/40 uppercase">
        {t.guide.heading}
      </p>
      <div className="flex flex-col">
        {steps.map((step, i) => (
          <div key={step.title} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-xs font-semibold text-violet-300 ring-1 ring-violet-500/30">
                {i + 1}
              </div>
              {i < steps.length - 1 && <div className="my-1 w-px flex-1 bg-white/10" />}
            </div>
            <div className={i < steps.length - 1 ? "pb-5" : ""}>
              <p className="text-sm font-medium text-white/90">{step.title}</p>
              <p className="mt-0.5 text-xs leading-relaxed text-white/45">{step.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
