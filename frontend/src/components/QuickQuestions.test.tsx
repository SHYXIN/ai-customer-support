import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QuickQuestions } from "./QuickQuestions";

describe("QuickQuestions", () => {
  it("renders all quick question buttons", () => {
    render(<QuickQuestions onSelect={vi.fn()} disabled={false} />);

    expect(screen.getByText("如何取消订单")).toBeDefined();
    expect(screen.getByText("查询物流")).toBeDefined();
    expect(screen.getByText("申请退款")).toBeDefined();
    expect(screen.getByText("退换货政策")).toBeDefined();
    expect(screen.getByText("支付方式")).toBeDefined();
    expect(screen.getByText("运费说明")).toBeDefined();
  });

  it("calls onSelect with the correct message when clicked", () => {
    const onSelect = vi.fn();
    render(<QuickQuestions onSelect={onSelect} disabled={false} />);

    fireEvent.click(screen.getByText("如何取消订单"));
    expect(onSelect).toHaveBeenCalledWith("如何取消订单？");
  });

  it("does not call onSelect when disabled", () => {
    const onSelect = vi.fn();
    render(<QuickQuestions onSelect={onSelect} disabled={true} />);

    fireEvent.click(screen.getByText("如何取消订单"));
    expect(onSelect).not.toHaveBeenCalled();
  });
});
