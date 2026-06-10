import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SessionDetail from "../../dashboard/src/components/SessionDetail";
import * as api from "../../dashboard/src/services/api";

// Mock the API service module
vi.mock("../../dashboard/src/services/api", () => {
  return {
    getSession: vi.fn(),
    submitJudgment: vi.fn(),
  };
});

const mockSession = {
  id: "session-xyz",
  child_name: "Karan Patel",
  child_age_months: 29,
  started_at: "2026-06-10T12:00:00.000Z",
  processing_status: "done",
  risk_level: "medium",
  flagged: true,
  combined_risk_score: 0.42,
  social_gaze_ratio: 0.51,
  name_response_rate: 0.33,
  expression_rate: 0.10,
  repetitive_score: 0.45,
  blink_rate_bpm: 12.5,
  questionnaire_score: 4,
  questionnaire_type: "mchat_r",
  questionnaire_risk: "medium",
  doctor_judgment: null
};

describe("SessionDetail Component Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders prompt state when no session ID is selected", () => {
    render(<SessionDetail sessionId={null} />);
    expect(screen.getByText(/Select a case to review/i)).toBeInTheDocument();
  });

  test("fetches and renders session header metadata, scores, and charts", async () => {
    vi.mocked(api.getSession).mockResolvedValue({ data: mockSession });
    
    render(<SessionDetail sessionId="session-xyz" />);
    
    // Check loading indicator first (it is active immediately)
    expect(screen.getByText(/Loading…/i)).toBeInTheDocument();
    
    // Wait for the data load and verify header content
    await waitFor(() => {
      expect(screen.getByText("Karan Patel")).toBeInTheDocument();
    });
    expect(screen.getByText(/29 months old/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: done/i)).toBeInTheDocument();
    
    // Verify Questionnaire data exists
    expect(screen.getByText("M-CHAT-R")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("/20")).toBeInTheDocument();
    
    // Verify Radar Chart container class is present
    const container = document.querySelector(".recharts-responsive-container");
    expect(container).toBeInTheDocument();

    // Verify Metrics lists
    expect(screen.getByText("Social gaze ratio")).toBeInTheDocument();
    expect(screen.getByText("0.510")).toBeInTheDocument(); // formatted to 3 decimals
    expect(screen.getByText("Name response rate")).toBeInTheDocument();
    expect(screen.getByText("0.330")).toBeInTheDocument();
  });

  test("submitting doctor judgment invokes the API and triggers callback", async () => {
    vi.mocked(api.getSession).mockResolvedValue({ data: mockSession });
    vi.mocked(api.submitJudgment).mockResolvedValue({ data: { ok: true } });
    
    const onSavedMock = vi.fn();
    render(<SessionDetail sessionId="session-xyz" onSaved={onSavedMock} />);
    
    await waitFor(() => {
      expect(screen.getByText("Karan Patel")).toBeInTheDocument();
    });

    // Select the typical development option
    const judgmentBtn = screen.getByText(/Needs Monitoring/i);
    fireEvent.click(judgmentBtn);
    
    // Write some notes
    const textarea = screen.getByPlaceholderText(/Clinical notes/i);
    fireEvent.change(textarea, { target: { value: "Child showed low response latency" } });

    // Click save
    const saveBtn = screen.getByText(/Save Judgment/i);
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(api.submitJudgment).toHaveBeenCalledWith(
        "session-xyz",
        "monitoring",
        "Child showed low response latency"
      );
    });
  });
});
