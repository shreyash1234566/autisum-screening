import { useEffect, useState } from "react";
import { getSession } from "../services/api";
import BehaviorScore from "./BehaviorScore";
import QuestionnaireResult from "./QuestionnaireResult";
import DoctorJudgment from "./DoctorJudgment";
import { format } from "date-fns";

export default function SessionDetail({ sessionId }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    getSession(sessionId)
      .then(r => setSession(r.data))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (!sessionId) return (
    <div className="flex items-center justify-center h-full text-gray-400 text-lg">
      ← Select a case to review
    </div>
  );
  if (loading) return (
    <div className="flex items-center justify-center h-full text-gray-400">
      Loading…
    </div>
  );
  if (!session) return null;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-400 rounded-2xl p-6 text-white">
        <h2 className="text-2xl font-bold">{session.child_name || "Child"}</h2>
        <p className="text-blue-100">
          {session.child_age_months} months old ·{" "}
          {session.started_at && format(new Date(session.started_at), "dd MMM yyyy")}
        </p>
        <div className="mt-3 flex gap-2 flex-wrap">
          <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
            Session ID: {session.id?.slice(0, 8)}…
          </span>
          <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm capitalize">
            Status: {session.processing_status}
          </span>
        </div>
      </div>

      {/* Three-column cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BehaviorScore session={session} />
        <QuestionnaireResult session={session} />
      </div>

      {/* Doctor judgment — full width */}
      <DoctorJudgment
        sessionId={session.id}
        current={session.doctor_judgment}
        onSaved={(j) => setSession(s => ({ ...s, doctor_judgment: j }))}
      />

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <strong>⚕️ Clinical reminder:</strong> This is a screening support tool, not a diagnostic instrument.
        Thresholds are based on Western populations (Perochon et al. 2023 — US cohort, n=475).
        Indian-specific norms are pending clinical data collection.
        All clinical decisions rest with the clinician.
      </div>
    </div>
  );
}
