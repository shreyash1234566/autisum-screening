# Frontend Testing Guide

This document describes the structure, requirements, and execution of automated tests for the React doctor dashboard using **Vitest** and **React Testing Library (RTL)**.

---

## 1. Directory Structure

All frontend tests are stored in `tests/frontend/`.

```
tests/frontend/
├── setup.js               # Global testing setup (jest-dom matcher exports, mocks)
├── App.test.jsx           # Main sidebar navigation, toggle click handlers
├── CaseList.test.jsx      # Test row selections, list lengths, badge allocations
└── SessionDetail.test.jsx # Radar charts, questionnaire scorebars, notes submissions
```

---

## 2. Global Setup Configurations (`setup.js`)

Vitest requires global setups to mock browser interfaces (such as `ResizeObserver` or Canvas) that do not exist inside JS-DOM.

### Setup Mock File Example
```javascript
import { expect, afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";

// Extend Jest matchers
expect.extend(matchers);

// Cleanup render DOMs after each test
afterEach(() => {
  cleanup();
});

// Mock Recharts responsive containers
vi.mock("recharts", async () => {
  const original = await vi.importActual("recharts");
  return {
    ...original,
    ResponsiveContainer: ({ children }) => (
      <div style={{ width: 800, height: 800 }}>{children}</div>
    ),
  };
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
```

---

## 3. Scope of Testing

* **Rendering Isolation:** Tests verify layout grids, font configurations, and child info display.
* **Badge and Risk Color Logic:** Checks that case lists correctly color risk levels (e.g. green for low, yellow for medium, red for high).
* **Charts rendering:** Confirms that Recharts components render inside `<BehaviorScore />`.
* **State Updates:** Verifies that toggling the sidebar filters cases between flagged and typical categories.

---

## 4. Run Execution Commands

Execute tests inside the dashboard directory:
```bash
# Execute tests in watch mode
npm run test

# Run tests and output coverage reports
npm run test:coverage
```
The coverage output is generated inside the `dashboard/coverage/` directory.
