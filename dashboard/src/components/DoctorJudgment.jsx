import { useState } from "react";
import { submitJudgment } from "../services/api";

const OPTIONS = [
  { value: "typical",           label: "✅ Typical Development",    color: "bg-green-100 border-green-400 text-green-800"   },
  { value: "monitoring",        label: "👁️ Needs Monitoring",       color: "bg-yellow-100 border-yellow-400 text-yellow-800" },
  { value: "high_concern",      label: "⚠️ High Concern",           color: "bg-orange-100 border-orange-400 text-orange-800" },
  { value: "refer_immediately", label: "🚨 Refer Immediately",       color: "bg-red-100 border-red-400 text-red-800"         },
];

export default function DoctorJudgment({ sessionId, current, onSaved }) {
  const [selected, setSelected] = useState(current || "");
  const [notes, setNotes]       = useState("");
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState(!!current);

  async function save() {
    if (!selected) return;
    setSaving(true);
    try {
      await submitJudgment(sessionId, selected, notes);
      setSaved(true);
      onSaved?.(selected);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1">Doctor Judgment</h3>
      <p className="text-sm text-gray-500 mb-4">
        Your clinical assessment is stored and used to improve the model.
      </p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {OPTIONS.map(opt => (
          <button
            key={opt.value}
            onClick={() => { setSelected(opt.value); setSaved(false); }}
            className={`p-3 rounded-xl border-2 text-left text-sm font-semibold transition-all
              ${selected === opt.value ? opt.color + " border-opacity-100" : "border-gray-200 text-gray-600 hover:border-gray-300"}`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <textarea
        className="w-full border border-gray-200 rounded-xl p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300 mb-3"
        rows={3}
        placeholder="Clinical notes (optional)…"
        value={notes}
        onChange={e => setNotes(e.target.value)}
      />

      <button
        onClick={save}
        disabled={!selected || saving}
        className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold disabled:opacity-40 hover:bg-blue-700 transition"
      >
        {saving ? "Saving…" : saved ? "✓ Saved" : "Save Judgment"}
      </button>

      <p className="text-xs text-gray-400 mt-3 text-center">
        All judgments become training labels for future Indian model retraining.
      </p>
    </div>
  );
}
