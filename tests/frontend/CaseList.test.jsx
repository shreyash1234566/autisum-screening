import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import CaseList from "../../dashboard/src/components/CaseList";

const mockSessions = [
  {
    id: "sess-1",
    child_name: "Aarav Sharma",
    child_age_months: 24,
    started_at: "2026-06-10T10:00:00.000Z",
    risk_level: "high",
    combined_risk_score: 0.72,
    flagged: true,
    processing_status: "done",
    questionnaire_type: "mchat_r"
  },
  {
    id: "sess-2",
    child_name: "Diya Patel",
    child_age_months: 36,
    started_at: "2026-06-10T11:00:00.000Z",
    risk_level: "low",
    combined_risk_score: 0.18,
    flagged: false,
    processing_status: "done",
    questionnaire_type: "indt_asd"
  }
];

describe("CaseList Component Tests", () => {
  test("renders loading state correctly", () => {
    render(<CaseList loading={true} />);
    expect(screen.getByText(/Loading sessions…/i)).toBeInTheDocument();
  });

  test("renders empty sessions text correctly", () => {
    render(<CaseList sessions={[]} loading={false} />);
    expect(screen.getByText(/No sessions yet./i)).toBeInTheDocument();
  });

  test("renders lists of child profiles with names, ages, and risk labels", () => {
    render(<CaseList sessions={mockSessions} loading={false} selectedId="" />);
    
    // Check names
    expect(screen.getByText("Aarav Sharma")).toBeInTheDocument();
    expect(screen.getByText("Diya Patel")).toBeInTheDocument();
    
    // Check descriptions
    expect(screen.getByText(/24 months · M-CHAT-R/i)).toBeInTheDocument();
    expect(screen.getByText(/36 months · INDT ASD/i)).toBeInTheDocument();

    // Check risk level texts
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("low")).toBeInTheDocument();

    // Check flagged badge
    expect(screen.getByText(/Flagged/i)).toBeInTheDocument();
    
    // Check risk percentage scores
    expect(screen.getByText("Score: 72%")).toBeInTheDocument();
    expect(screen.getByText("Score: 18%")).toBeInTheDocument();
  });

  test("clicking on a session triggers onSelect callback with correct ID", () => {
    const onSelectMock = vi.fn();
    render(<CaseList sessions={mockSessions} loading={false} selectedId="" onSelect={onSelectMock} />);
    
    const firstCase = screen.getByText("Aarav Sharma");
    fireEvent.click(firstCase);
    
    expect(onSelectMock).toHaveBeenCalledTimes(1);
    expect(onSelectMock).toHaveBeenCalledWith("sess-1");
  });
});
