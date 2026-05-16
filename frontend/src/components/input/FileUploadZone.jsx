import { useCallback, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import ModeSelector from "./ModeSelector";

function UploadIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-accent-muted">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

export default function FileUploadZone({ onSubmit, loading }) {
  const { t } = useTranslation();
  const [file, setFile] = useState(null);
  const [lineCount, setLineCount] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [mode, setMode] = useState("combined");
  const inputRef = useRef(null);

  const ACCEPTED = [".txt", ".log", ".csv"];

  async function countLines(f) {
    try {
      const text = await f.text();
      const count = text.split("\n").filter((l) => l.trim()).length;
      setLineCount(count);
    } catch {
      setLineCount(null);
    }
  }

  function handleFile(f) {
    if (!f) return;
    setFile(f);
    countLines(f);
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    handleFile(f);
  }, []);

  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = () => setDragging(false);

  function handleSubmit() {
    if (file && onSubmit) onSubmit(file, mode);
  }

  return (
    <div className="card space-y-4">
      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all ${
          dragging
            ? "border-accent-cyan bg-accent-cyan/5"
            : file
            ? "border-accent-green/50 bg-green-900/10"
            : "border-bg-border hover:border-accent-muted"
        }`}
      >
        <UploadIcon />
        {file ? (
          <div className="text-center">
            <p className="text-text-primary text-sm font-medium">{file.name}</p>
            {lineCount !== null && (
              <p className="text-text-dim text-xs font-mono mt-1">
                {t("input.lines_preview", { count: lineCount })}
              </p>
            )}
          </div>
        ) : (
          <div className="text-center">
            <p className="text-text-secondary text-sm">{t("input.drop_prompt")}</p>
            <p className="text-text-dim text-xs font-mono mt-1">{t("input.file_types")}</p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      <ModeSelector value={mode} onChange={setMode} />

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="btn-primary w-full"
      >
        {loading ? t("input.analyzing") : t("input.analyze")}
      </button>
    </div>
  );
}
