const RISK_COLOR = { low: "#4CAF50", medium: "#FF9800", high: "#F44336", unknown: "#9E9E9E" };

export default function QuestionnaireResult({ session }) {
  if (!session) return null;
  const { questionnaire_type, questionnaire_score, questionnaire_risk } = session;
  const color = RISK_COLOR[questionnaire_risk] || "#9E9E9E";

  const info = questionnaire_type === "mchat_r"
    ? { name: "M-CHAT-R", max: 20, low: "0–2", med: "3–7", high: "8–20",
        cite: "Robins et al. 2014, J Autism Dev Disord · Hindi validation: Juneja et al. 2024" }
    : questionnaire_type === "indt_asd"
    ? { name: "AIIMS INDT-ASD", max: 112, low: "<25", med: "25–35", high: "≥36",
        cite: "Malhotra et al. 2019, PLOS ONE · DOI: 10.1371/journal.pone.0213242" }
    : { name: "Unknown", max: 100, low: "–", med: "–", high: "–", cite: "–" };

  const pct = info.max ? ((questionnaire_score / info.max) * 100).toFixed(0) : 0;

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1">Questionnaire</h3>
      <p className="text-sm text-gray-500 mb-4">{info.name}</p>

      {/* Score bar */}
      <div className="flex items-center gap-4 mb-4">
        <div className="text-4xl font-bold" style={{ color }}>
          {questionnaire_score ?? "–"}
          <span className="text-lg text-gray-400">/{info.max}</span>
        </div>
        <div className="flex-1">
          <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${pct}%`, background: color }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1 capitalize">
            {questionnaire_risk} risk
          </p>
        </div>
      </div>

      {/* Thresholds */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs mb-4">
        {[
          { label: "Low Risk",    range: info.low,  color: "#4CAF50" },
          { label: "Medium Risk", range: info.med,  color: "#FF9800" },
          { label: "High Risk",   range: info.high, color: "#F44336" },
        ].map(b => (
          <div key={b.label} className="rounded-lg p-2 border" style={{ borderColor: b.color }}>
            <p className="font-semibold" style={{ color: b.color }}>{b.range}</p>
            <p className="text-gray-500">{b.label}</p>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400">Source: {info.cite}</p>
    </div>
  );
}
