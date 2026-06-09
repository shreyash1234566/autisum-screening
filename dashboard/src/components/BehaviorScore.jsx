import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";

const RISK_COLOR = { low: "#4CAF50", medium: "#FF9800", high: "#F44336" };

export default function BehaviorScore({ session }) {
  if (!session) return null;

  const toRisk = (v) => v == null ? null : v >= 0.7 ? "high" : v >= 0.4 ? "medium" : "low";

  const metrics = [
    { label: "Gaze (social)",   value: session.social_gaze_ratio,   invert: true  },
    { label: "Name Response",   value: session.name_response_rate,  invert: false },
    { label: "Expression",      value: session.expression_rate,     invert: false },
    { label: "Non-repetitive",  value: 1 - (session.repetitive_score ?? 0), invert: false },
  ];

  const radarData = metrics.map(m => ({
    subject: m.label,
    score: m.value != null
      ? Math.round((m.invert ? 1 - m.value : m.value) * 100)
      : 50,
  }));

  const combined = session.combined_risk_score;
  const level    = session.risk_level || "unknown";

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">Behavioral Scores</h3>

      {/* Combined risk badge */}
      <div className="flex items-center gap-3 mb-6">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg"
          style={{ background: RISK_COLOR[level] || "#9E9E9E" }}
        >
          {combined != null ? Math.round(combined * 100) : "–"}
        </div>
        <div>
          <p className="text-sm text-gray-500">Combined Risk Score</p>
          <p className="text-xl font-bold capitalize" style={{ color: RISK_COLOR[level] }}>
            {level} risk
          </p>
          {session.flagged && (
            <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
              🚩 Flagged for Review
            </span>
          )}
        </div>
      </div>

      {/* Radar chart */}
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={radarData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => `${v}%`} />
          <Radar
            name="Child" dataKey="score"
            stroke="#5B8DB8" fill="#5B8DB8" fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Individual metrics table */}
      <div className="mt-4 space-y-2">
        {[
          { label: "Social gaze ratio",  val: session.social_gaze_ratio,   unit: "", threshold: "≥0.55 typical" },
          { label: "Name response rate", val: session.name_response_rate,  unit: "", threshold: "≥0.67 typical" },
          { label: "Expression rate",    val: session.expression_rate,     unit: "", threshold: "≥0.30 typical" },
          { label: "Repetitive score",   val: session.repetitive_score,    unit: "", threshold: "≤0.20 typical" },
          { label: "Blink rate",         val: session.blink_rate_bpm,      unit: " bpm", threshold: "15-20 typical" },
        ].map(({ label, val, unit, threshold }) => (
          <div key={label} className="flex justify-between items-center py-1 border-b border-gray-100 text-sm">
            <span className="text-gray-600">{label}</span>
            <span>
              <span className="font-semibold">
                {val != null ? val.toFixed(3) : "–"}{unit}
              </span>
              <span className="text-gray-400 text-xs ml-2">({threshold})</span>
            </span>
          </div>
        ))}
      </div>

      {/* Research note */}
      <p className="text-xs text-gray-400 mt-4">
        Thresholds: Perochon et al. 2023 (NEJM Evidence) · Bradshaw et al. 2018 ·
        OpenFace 3.0 (CMU) · ASDMotion (Dinstein Lab)
      </p>
    </div>
  );
}
