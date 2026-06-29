import { useEffect, useState } from "react";
import { waitingQuotes } from "../i18n/waitingQuotes";
import { useLanguage } from "../i18n/LanguageContext";

const CYCLE_MS = 4500;
const FADE_MS = 500;

function pickNextIndex(current: number, length: number): number {
  if (length < 2) return 0;
  let next = Math.floor(Math.random() * length);
  while (next === current) {
    next = Math.floor(Math.random() * length);
  }
  return next;
}

function splitQuote(quote: string): { main: string; attribution: string | null } {
  const match = quote.match(/^(.*?)\s*(-{2,}|—+)\s*(.*)$/);
  if (!match) return { main: quote, attribution: null };
  const [, main, dash, rest] = match;
  return { main: main.trim(), attribution: `${dash} ${rest}`.trim() };
}

export default function WaitingQuotes() {
  const { lang } = useLanguage();
  const quotes = waitingQuotes[lang];
  const [index, setIndex] = useState(() => Math.floor(Math.random() * Math.max(quotes.length, 1)));
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setIndex(Math.floor(Math.random() * Math.max(waitingQuotes[lang].length, 1)));
    setVisible(true);
  }, [lang]);

  useEffect(() => {
    if (quotes.length < 2) return;
    const timer = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex((i) => pickNextIndex(i, quotes.length));
        setVisible(true);
      }, FADE_MS);
    }, CYCLE_MS);
    return () => clearInterval(timer);
  }, [quotes.length]);

  if (quotes.length === 0) return null;

  const { main, attribution } = splitQuote(quotes[index]);

  return (
    <p
      className={`max-w-md px-4 text-center text-2xl text-violet-100/90 transition-opacity duration-500 sm:text-3xl ${
        visible ? "opacity-90" : "opacity-0"
      } ${lang === "zh" ? "font-zh-script" : "font-en-script"}`}
    >
      {main}
      {attribution && (
        <>
          <br />
          <span className="text-base opacity-70 sm:text-lg">{attribution}</span>
        </>
      )}
    </p>
  );
}
