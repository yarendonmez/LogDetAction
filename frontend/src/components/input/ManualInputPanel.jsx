import { useState } from "react";
import { useTranslation } from "react-i18next";
import ModeSelector from "./ModeSelector";

export default function ManualInputPanel({ onSubmit, loading }) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [mode, setMode] = useState("combined");

  const lineCount = text.split("\n").filter((l) => l.trim()).length;

  function handleSubmit() {
    if (text.trim() && onSubmit) onSubmit(text, mode);
  }

  return (
    <div className="card space-y-4">
      <div className="space-y-1">
        <label className="text-xs text-text-secondary font-mono">{t("input.text_label")}</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("input.text_placeholder")}
          rows={10}
          className="input-base w-full resize-y font-mono text-xs leading-relaxed"
        />
        <p className="text-text-dim text-xs font-mono text-right">
          {text.trim() ? t("input.lines_preview", { count: lineCount }) : ""}
        </p>
      </div>

      <ModeSelector value={mode} onChange={setMode} />

      <div className="flex gap-2">
        <button
          onClick={() => setText("")}
          disabled={!text || loading}
          className="btn-ghost"
        >
          {t("input.clear")}
        </button>
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
          className="btn-primary flex-1"
        >
          {loading ? t("input.analyzing") : t("input.analyze")}
        </button>
      </div>
    </div>
  );
}
