import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the platform shell with live trading disabled", () => {
    render(<App />);

    expect(screen.getByText("QuantResearchCodex")).toBeTruthy();
    expect(screen.getByText("Live trading disabled")).toBeTruthy();
  });

  it("switches console panels from the nav", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Strategies" }));

    expect(screen.getByRole("heading", { name: "Strategy lifecycle" })).toBeTruthy();
    expect(screen.getByText("Cross-Asset Momentum")).toBeTruthy();
  });
});
