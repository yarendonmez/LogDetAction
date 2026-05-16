import { useTranslation } from "react-i18next";

const BARS = 8;

export default function LoadingOverlay({ visible }) {
  const { t } = useTranslation();
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-bg-base/90 backdrop-blur-sm">
      <div className="flex items-end gap-1 mb-6">
        {Array.from({ length: BARS }).map((_, i) => (
          <div
            key={i}
            className="w-1.5 bg-accent-cyan rounded-sm opacity-80"
            style={{
              height: `${12 + Math.sin((i / BARS) * Math.PI) * 20}px`,
              animation: `pulse 1.2s ease-in-out ${i * 0.12}s infinite alternate`,
            }}
          />
        ))}
      </div>
      <p className="font-mono text-accent-cyan text-sm tracking-widest">
        {t("input.analyzing")}
      </p>
      <p className="text-text-dim text-xs mt-2">
        {t("input.analyzing")} this may take a moment.
      </p>
      <style>{`
        @keyframes pulse {
          from { transform: scaleY(0.4); opacity: 0.5; }
          to   { transform: scaleY(1.0); opacity: 1.0; }
        }
      `}</style>
    </div>
  );
}
