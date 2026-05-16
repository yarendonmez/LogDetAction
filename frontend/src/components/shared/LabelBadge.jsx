const configs = {
  malicious: "bg-red-900/40 text-accent-red border border-red-800/50",
  suspicious: "bg-amber-900/30 text-accent-amber border border-amber-800/40",
  benign: "bg-green-900/30 text-accent-green border border-green-800/40",
  unknown: "bg-bg-elevated text-text-dim border border-bg-border",
};

export default function LabelBadge({ label }) {
  const cls = configs[label] ?? configs.unknown;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono uppercase tracking-wide ${cls}`}>
      {label ?? "unknown"}
    </span>
  );
}
