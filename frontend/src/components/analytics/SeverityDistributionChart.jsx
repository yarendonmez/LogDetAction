import { useTranslation } from "react-i18next";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const COLORS = {
  high: "#f87171",
  medium: "#fbbf24",
  low: "#4ade80",
  unknown: "#64748b",
};

export default function SeverityDistributionChart({ data }) {
  const { t } = useTranslation();
  if (!data) return null;

  const { severity_counts } = data;
  const chartData = [
    { name: "High",    value: severity_counts?.high    || 0, key: "high"    },
    { name: "Medium",  value: severity_counts?.medium  || 0, key: "medium"  },
    { name: "Low",     value: severity_counts?.low     || 0, key: "low"     },
    { name: "Unknown", value: severity_counts?.unknown || 0, key: "unknown" },
  ];

  const hasData = chartData.some((d) => d.value > 0);
  if (!hasData) {
    return (
      <div className="card flex items-center justify-center h-48 text-text-dim text-sm">
        {t("analytics.empty")}
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
        {t("analytics.severity_dist")}
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 20, top: 4, bottom: 4 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={58}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            contentStyle={{ backgroundColor: "#1e2535", border: "1px solid #2a3347", borderRadius: 4 }}
            itemStyle={{ color: "#e2e8f0", fontSize: 12 }}
          />
          <Bar dataKey="value" radius={[0, 3, 3, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.key} fill={COLORS[entry.key]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
