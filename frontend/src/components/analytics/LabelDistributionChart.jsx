import { useTranslation } from "react-i18next";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const COLORS = {
  malicious: "#f87171",
  suspicious: "#fbbf24",
  benign: "#4ade80",
};

const RADIAN = Math.PI / 180;
function CustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.04) return null;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#e2e8f0" textAnchor="middle" dominantBaseline="central" fontSize={11}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export default function LabelDistributionChart({ data }) {
  const { t } = useTranslation();
  if (!data) return null;

  const { label_counts } = data;
  const chartData = [
    { name: t("analytics.malicious"), value: label_counts?.malicious || 0, key: "malicious" },
    { name: t("analytics.suspicious"), value: label_counts?.suspicious || 0, key: "suspicious" },
    { name: t("analytics.benign"), value: label_counts?.benign || 0, key: "benign" },
  ].filter((d) => d.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="card flex items-center justify-center h-48 text-text-dim text-sm">
        {t("analytics.empty")}
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
        {t("analytics.label_dist")}
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={52}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
            labelLine={false}
            label={<CustomLabel />}
          >
            {chartData.map((entry) => (
              <Cell key={entry.key} fill={COLORS[entry.key]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: "#1e2535", border: "1px solid #2a3347", borderRadius: 4 }}
            itemStyle={{ color: "#e2e8f0", fontSize: 12 }}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
