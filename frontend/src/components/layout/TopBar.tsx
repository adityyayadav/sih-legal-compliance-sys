import { useEffect, useState } from "react";

type FontSize = "sm" | "md" | "lg";
const KEY = "lm_fontsize";

function applyFontSize(fs: FontSize) {
  const root = document.documentElement;
  root.classList.remove("fs-sm", "fs-md", "fs-lg");
  root.classList.add(`fs-${fs}`);
}

export function TopBar() {
  const [fs, setFs] = useState<FontSize>(() => (localStorage.getItem(KEY) as FontSize) || "md");
  const [lang, setLang] = useState<"en" | "hi">("en");

  useEffect(() => {
    applyFontSize(fs);
    localStorage.setItem(KEY, fs);
  }, [fs]);

  return (
    <div className="gov-topbar">
      <div className="container">
        <div className="left">
          <span className="tricolor-dot" aria-hidden="true" />
          <span>भारत सरकार</span>
          <span>|</span>
          <span>Government of India</span>
        </div>
        <div className="right">
          <a href="#main-content" className="skip-inline">
            Skip to main content
          </a>
          <span className="fontsize-group" role="group" aria-label="Text size">
            <button aria-pressed={fs === "sm"} onClick={() => setFs("sm")} title="Decrease text size">
              A−
            </button>
            <button aria-pressed={fs === "md"} onClick={() => setFs("md")} title="Normal text size">
              A
            </button>
            <button aria-pressed={fs === "lg"} onClick={() => setFs("lg")} title="Increase text size">
              A+
            </button>
          </span>
          <button
            onClick={() => setLang((l) => (l === "en" ? "hi" : "en"))}
            title="Toggle language"
            aria-label="Toggle language"
          >
            {lang === "en" ? "हिंदी" : "English"}
          </button>
        </div>
      </div>
    </div>
  );
}
