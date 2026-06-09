import { useState, useEffect, useCallback } from "react";
import { getFlagged, getAllSessions } from "./services/api";
import CaseList from "./components/CaseList";
import SessionDetail from "./components/SessionDetail";

export default function App() {
  const [sessions, setSessions]  = useState([]);
  const [selected, setSelected]  = useState(null);
  const [view, setView]          = useState("flagged"); // flagged | all
  const [loading, setLoading]    = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    const req = view === "flagged" ? getFlagged() : getAllSessions(100);
    req.then(r => setSessions(r.data)).finally(() => setLoading(false));
  }, [view]);

  useEffect(() => { load(); }, [load]);

  const flagged = sessions.filter(s => s.flagged).length;

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      {/* ── SIDEBAR ── */}
      <aside className="w-80 flex-shrink-0 bg-white border-r border-gray-100 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-gray-100">
          <h1 className="text-xl font-bold text-blue-700">AutiScreen</h1>
          <p className="text-xs text-gray-500">Doctor Dashboard · India</p>
        </div>

        {/* View toggle */}
        <div className="flex p-3 gap-2 border-b border-gray-100">
          <button
            onClick={() => setView("flagged")}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all
              ${view === "flagged" ? "bg-red-100 text-red-700" : "text-gray-500 hover:bg-gray-100"}`}
          >
            🚩 Flagged {flagged > 0 && `(${flagged})`}
          </button>
          <button
            onClick={() => setView("all")}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all
              ${view === "all" ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"}`}
          >
            All Sessions
          </button>
        </div>

        {/* Refresh */}
        <button
          onClick={load}
          className="mx-3 mt-2 py-1.5 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          ↻ Refresh
        </button>

        {/* Case list */}
        <div className="flex-1 overflow-y-auto p-3">
          <CaseList
            sessions={sessions}
            selectedId={selected}
            onSelect={setSelected}
            loading={loading}
          />
        </div>

        {/* Stats footer */}
        <div className="p-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Total: {sessions.length} sessions</p>
          <p>Flagged: {flagged}</p>
          <p>Reviewed: {sessions.filter(s => s.doctor_judgment).length}</p>
        </div>
      </aside>

      {/* ── MAIN PANEL ── */}
      <main className="flex-1 overflow-hidden">
        <SessionDetail sessionId={selected} />
      </main>
    </div>
  );
}
