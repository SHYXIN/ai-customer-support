import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { References, type Reference } from "./References";

const mockReferences: Reference[] = [
  {
    id: "1",
    content: "如何取消订单",
    response: "您可以登录账户，在订单管理中申请取消。",
    category: "ORDER",
    score: 0.92,
  },
  {
    id: "2",
    content: "取消订单的期限是多久",
    response: "订单在发货前均可取消。",
    category: "ORDER",
    score: 0.85,
  },
];

describe("References", () => {
  it("默认折叠，显示引用数量", () => {
    render(<References references={mockReferences} />);
    expect(screen.getByText(/参考来源/)).toBeInTheDocument();
    expect(screen.getByText(/2 条/)).toBeInTheDocument();
  });

  it("点击展开后显示引用列表", () => {
    render(<References references={mockReferences} />);
    fireEvent.click(screen.getByText(/参考来源/));
    expect(screen.getByText("如何取消订单")).toBeInTheDocument();
    expect(screen.getByText("取消订单的期限是多久")).toBeInTheDocument();
  });

  it("空引用列表不渲染", () => {
    const { container } = render(<References references={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("显示分类标签", () => {
    render(<References references={mockReferences} />);
    fireEvent.click(screen.getByText(/参考来源/));
    const badges = screen.getAllByText("ORDER");
    expect(badges.length).toBe(2);
  });
});
