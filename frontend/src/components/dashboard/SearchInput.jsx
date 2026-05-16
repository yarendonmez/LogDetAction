import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";

export default function SearchInput() {
  const { t } = useTranslation();
  const setSearchQuery = useAnalysisStore((s) => s.setSearchQuery);
  const [local, setLocal] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(local), 300);
    return () => clearTimeout(timer);
  }, [local, setSearchQuery]);

  return (
    <div className="relative">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 text-text-dim w-3.5 h-3.5"
        fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <input
        type="text"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder={t("dashboard.search_placeholder")}
        className="input-base pl-8 w-full sm:w-72"
      />
    </div>
  );
}
