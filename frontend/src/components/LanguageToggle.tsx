import { useLanguage } from "../i18n/LanguageContext";

export default function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="inline-flex rounded-full bg-white/10 p-1 text-xs">
      <button
        type="button"
        onClick={() => setLang("zh")}
        className={`rounded-full px-3 py-1 transition ${lang === "zh" ? "bg-white text-black" : "text-white/60"}`}
      >
        中文
      </button>
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`rounded-full px-3 py-1 transition ${lang === "en" ? "bg-white text-black" : "text-white/60"}`}
      >
        EN
      </button>
    </div>
  );
}
