import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-accent-cyan" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 2L3 6v6c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V6l-9-4z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

export default function Header() {
  const { t, i18n } = useTranslation();
  const health = useAnalysisStore((s) => s.health);

  const isOnline = health?.status === "ok";
  const statusText = health === null
    ? t("status.checking")
    : isOnline
    ? `${t("status.online")} · ${t("status.model_loaded")}`
    : `${t("status.offline")} · ${t("status.model_not_loaded")}`;

  function toggleLang() {
    const next = i18n.language === "en" ? "tr" : "en";
    i18n.changeLanguage(next);
    localStorage.setItem("lang", next);
  }

  return (
    <header className="bg-bg-surface border-b border-bg-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <ShieldIcon />
        <div>
          <h1 className="font-ui font-bold text-text-primary text-base tracking-tight">
            {t("nav.title")}
          </h1>
          <p className="text-text-dim text-xs font-mono">{t("nav.subtitle")}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* System status */}
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              health === null
                ? "bg-accent-muted animate-pulse"
                : isOnline
                ? "bg-accent-green"
                : "bg-accent-red animate-pulse"
            }`}
          />
          <span className="text-xs text-text-secondary font-mono hidden sm:block">
            {statusText}
          </span>
        </div>

        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="text-xs font-mono text-text-secondary border border-bg-border px-2 py-1 rounded hover:border-accent-cyan hover:text-accent-cyan transition-colors"
        >
          {i18n.language === "en" ? "TR" : "EN"}
        </button>
      </div>
    </header>
  );
}
