import { expect, afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Clean up DOM after each test
afterEach(() => {
  cleanup();
});

// Mock Canvas & ResizeObserver which JSDOM doesn't support natively
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Recharts throws exceptions in JSDOM due to missing SVG dimensions.
// We mock Recharts components to render basic fallback HTML containers.
vi.mock("recharts", () => {
  return {
    ResponsiveContainer: ({ children }) => <div className="recharts-responsive-container">{children}</div>,
    RadarChart: ({ children }) => <div className="recharts-radar-chart">{children}</div>,
    PolarGrid: () => <div className="recharts-polar-grid" />,
    PolarAngleAxis: ({ dataKey }) => <div className="recharts-polar-angle-axis" data-key={dataKey} />,
    Radar: ({ name, dataKey }) => <div className="recharts-radar" data-name={name} data-key={dataKey} />,
    Tooltip: () => <div className="recharts-tooltip" />,
  };
});
