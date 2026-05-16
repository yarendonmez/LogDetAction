const STATUS_LABELS = {
  no_action: "No Action",
  context_required: "Context Required",
  label_not_extracted: "Parse Error",
  invalid_analysis_mode: "Invalid Mode",
};

function getLabel(status) {
  if (!status) return "Unknown";
  if (status.startsWith("analysis_generated_")) {
    const mode = status.replace("analysis_generated_", "");
    return `Generated (${mode})`;
  }
  return STATUS_LABELS[status] ?? status;
}

export default function StatusBadge({ status }) {
  const label = getLabel(status);
  const isGenerated = status?.startsWith("analysis_generated_");
  const cls = isGenerated
    ? "bg-violet-900/30 text-accent-violet border border-violet-800/40"
    : status === "no_action"
    ? "bg-bg-elevated text-text-dim border border-bg-border"
    : status === "context_required"
    ? "bg-amber-900/20 text-accent-amber border border-amber-900/30"
    : "bg-bg-elevated text-text-secondary border border-bg-border";

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${cls}`}>
      {label}
    </span>
  );
}
