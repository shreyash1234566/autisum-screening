import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../../dashboard/src/App";
import * as api from "../../dashboard/src/services/api";

// Mock the API calls
vi.mock("../../dashboard/src/services/api", () => {
  return {
    getFlagged: vi.fn(),
    getAllSessions: vi.fn(),
    getSession: vi.fn(),
  };
});

const mockFlagged = [
  {
    id: "flagged-1",
    child_name: "Ravi Teja",
    child_age_months: 22,
    started_at: "2026-06-10T10:00:00.000Z",
    risk_level: "high",
    combined_risk_score: 0.65,
    flagged: true,
    processing_status: "done",
    questionnaire_type: "mchat_r"
  }
];

const mockAll = [
  ...mockFlagged,
  {
    id: "typical-1",
    child_name: "Sneha Reddy",
    child_age_months: 26,
    started_at: "2026-06-10T11:00:00.000Z",
    risk_level: "low",
    combined_risk_score: 0.22,
    flagged: false,
    processing_status: "done",
    questionnaire_type: "mchat_r"
  }
];

describe("Dashboard App Main Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("loads sidebar logo, defaults to flagged view and fetches flagged cases", async () => {
    vi.mocked(api.getFlagged).mockResolvedValue({ data: mockFlagged });
    
    render(<App />);

    expect(screen.getByText("AutiScreen")).toBeInTheDocument();
    expect(screen.getByText("Doctor Dashboard · India")).toBeInTheDocument();
    
    // Check loading text first
    expect(screen.getByText(/Loading sessions…/i)).toBeInTheDocument();

    // Verify loaded flagged child name appears
    await waitFor(() => {
      expect(screen.getByText("Ravi Teja")).toBeInTheDocument();
    });
    
    expect(screen.queryBG = screen.queryByText("Sneha Reddy")).not.toBeInTheDocument();
    expect(api.getFlagged).toHaveBeenCalledTimes(1);
  });

  test("clicking 'All Sessions' switches view and loads all cases", async () => {
    vi.mocked(api.getFlagged).mockResolvedValue({ data: mockFlagged });
    vi.mocked(api.getAllSessions).mockResolvedValue({ data: mockAll });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText("Ravi Teja")).toBeInTheDocument();
    });

    const allBtn = screen.getByRole("button", { name: /All Sessions/i });
    fireEvent.click(allBtn);

    // Verify loading and both records appear
    await waitFor(() => {
      expect(screen.getByText("Ravi Teja")).toBeInTheDocument();
      expect(screen.getByText("Sneha Reddy")).toBeInTheDocument();
    });

    expect(api.getAllSessions).toHaveBeenCalledTimes(1);
  });

  test("clicking Refresh updates case lists", async () => {
    vi.mocked(api.getFlagged).mockResolvedValue({ data: mockFlagged });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText("Ravi Teja")).toBeInTheDocument();
    });

    const refreshBtn = screen.getByText(/Refresh/i);
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(api.getFlagged).toHaveBeenCalledTimes(2);
    });
  });
});
