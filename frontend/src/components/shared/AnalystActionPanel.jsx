import { useTranslation } from "react-i18next";

const ACTIONS_FOR = {
  malicious: [
    "actions.review_source",
    "actions.correlate_session",
    "actions.escalate",
    "actions.extract_ioc",
  ],
  suspicious: [
    "actions.review_source",
    "actions.correlate_session",
    "actions.extract_ioc",
  ],
};

function ActionRow({ labelKey }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between py-2 border-b border-bg-border last:border-0">
      <span className="text-text-secondary text-xs">{t(labelKey)}</span>
      <span className="text-xs font-mono text-accent-amber border border-amber-800/40 bg-amber-900/20 px-2 py-0.5 rounded">
        {t("actions.pending")}
      </span>
    </div>
  );
}

export default function AnalystActionPanel({ label }) {
  const { t } = useTranslation();
  const actions = ACTIONS_FOR[label];
  if (!actions) return null;

  return (
    <div className="mt-4 bg-bg-elevated border border-bg-border rounded-lg p-4">
      <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
        {t("actions.title")}
      </h4>
      <div>
        {actions.map((key) => (
          <ActionRow key={key} labelKey={key} />
        ))}
      </div>
      <p className="mt-3 text-text-dim text-xs italic">{t("actions.disclaimer")}</p>
    </div>
  );
}
