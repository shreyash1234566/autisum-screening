import { format } from "date-fns";

const RISK_BADGE = {
  low:     "bg-green-100 text-green-800",
  medium:  "bg-yellow-100 text-yellow-800",
  high:    "bg-red-100 text-red-800",
  unknown: "bg-gray-100 text-gray-600",
};
const JUDGMENT_ICON = {
  typical: "✅", monitoring: "👁️", high_concern: "⚠️", refer_immediately: "🚨"
};

export default function CaseList({ sessions, selectedId, onSelect, loading }) {
  if (loading) return (
    <div className="flex items-center justify-center h-40 text-gray-400">
      Loading sessions…
    </div>
  );
  if (!sessions?.length) return (
    <div className="text-center text-gray-400 py-12">No sessions yet.</div>
  );

  return (
    <div className="space-y-2">
      {sessions.map(s => (
        <div
          key={s.id}
          onClick={() => onSelect(s.id)}
          className={`p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-md
            ${selectedId === s.id ? "border-blue-500 bg-blue-50" : "border-gray-100 bg-white"}`}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-gray-800">
                {s.child_name}
                {s.doctor_judgment && (
                  <span className="ml-2">{JUDGMENT_ICON[s.doctor_judgment]}</span>
                )}
              </p>
              <p className="text-xs text-gray-500">
                {s.child_age_months} months · {s.questionnaire_type?.replace("_", " ").toUpperCase()}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {s.started_at && format(new Date(s.started_at), "dd MMM yyyy, HH:mm")}
              </p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className={`text-xs font-bold px-2 py-1 rounded-full capitalize ${RISK_BADGE[s.risk_level] || RISK_BADGE.unknown}`}>
                {s.risk_level || s.processing_status}
              </span>
              {s.flagged && (
                <span className="text-xs text-red-600 font-semibold">🚩 Flagged</span>
              )}
              {s.combined_risk_score != null && (
                <span className="text-xs text-gray-500">
                  Score: {(s.combined_risk_score * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
