import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the platform shell with live trading disabled", () => {
    render(<App />);

    expect(screen.getByText("QuantResearchCodex")).toBeTruthy();
    expect(screen.getByText("Live trading disabled")).toBeTruthy();
  });
});
