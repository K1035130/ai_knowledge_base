import { translations } from "../i18n/translations";

interface Props {
  onAcknowledge: () => void;
}

export default function PrivacyNotice({ onAcknowledge }: Props) {
  const zh = translations.zh.privacy;
  const en = translations.en.privacy;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 backdrop-blur-md">
      <div className="w-full max-w-sm rounded-3xl bg-[#1c1c24]/95 p-6 text-center shadow-2xl ring-1 ring-white/10">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-violet-500/15 text-violet-300">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z" strokeLinejoin="round" />
            <path d="M12 8v5M12 16h.01" strokeLinecap="round" />
          </svg>
        </div>

        <h2 className="text-lg font-semibold text-white">{zh.heading}</h2>
        <p className="mt-3 text-sm leading-relaxed whitespace-pre-line text-white/65">{zh.body}</p>

        <div className="my-4 h-px bg-white/10" />

        <h2 className="text-lg font-semibold text-white">{en.heading}</h2>
        <p className="mt-3 text-sm leading-relaxed whitespace-pre-line text-white/65">{en.body}</p>

        <button
          type="button"
          onClick={onAcknowledge}
          className="mt-5 w-full rounded-2xl bg-violet-500 py-2.5 text-sm font-medium text-white transition active:scale-[0.98] hover:bg-violet-400"
        >
          {zh.ack} / {en.ack}
        </button>
      </div>
    </div>
  );
}
