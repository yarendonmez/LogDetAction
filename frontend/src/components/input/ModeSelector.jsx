import { useTranslation } from "react-i18next";

export default function ModeSelector({ value, onChange }) {
  const { t } = useTranslation();

  return (
    <div className="space-y-1">
      <label className="text-xs text-text-secondary font-mono">{t("input.mode_label")}</label>
      <div className="flex gap-2">
        {["combined", "separate"].map((mode) => {
          const active = value === mode;
          return (
            <button
              key={mode}
              onClick={() => onChange(mode)}
              className={`flex-1 text-left px-3 py-2.5 rounded border text-xs transition-all ${
                active
                  ? "border-accent-cyan bg-accent-cyan/10 text-accent-cyan"
                  : "border-bg-border bg-bg-elevated text-text-secondary hover:border-accent-muted"
              }`}
            >
              <div className="font-semibold mb-0.5">
                {mode === "combined" ? t("input.mode_combined") : t("input.mode_separate")}
              </div>
              <div className="text-text-dim text-xs leading-snug">
                {mode === "combined" ? t("input.mode_combined_desc") : t("input.mode_separate_desc")}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
