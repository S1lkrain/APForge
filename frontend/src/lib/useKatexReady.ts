import { useEffect, useState } from "react";

export function useKatexReady(): boolean {
  const [ready, setReady] = useState(() => Boolean(window.katex));

  useEffect(() => {
    if (window.katex) {
      setReady(true);
      return;
    }

    const script = document.querySelector<HTMLScriptElement>('script[src*="katex.min.js"]');
    if (!script) return;

    function markReady() {
      if (window.katex) setReady(true);
    }

    script.addEventListener("load", markReady);
    const interval = window.setInterval(() => {
      if (window.katex) {
        setReady(true);
        window.clearInterval(interval);
      }
    }, 50);

    return () => {
      script.removeEventListener("load", markReady);
      window.clearInterval(interval);
    };
  }, []);

  return ready;
}
