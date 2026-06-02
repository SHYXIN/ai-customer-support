import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SessionList } from "./SessionList";

const mockSessions = [
  { id: "1", title: "如何取消订单", updatedAt: Date.now() - 60000 },
  { id: "2", title: "查询物流信息", updatedAt: Date.now() - 3600000 },
];

const defaultProps = {
  sessions: mockSessions,
  currentSessionId: "1",
  onSelectSession: vi.fn(),
  onCreateSession: vi.fn(),
  onDeleteSession: vi.fn(),
  onRenameSession: vi.fn(),
};

/** 辅助：找到包含文本的会话项容器 */
function findSessionItem(text: string) {
  const el = screen.getByText(text);
  // 向上找 3 层，找到 group 容器
  return el.closest(".group") || el.parentElement?.parentElement;
}

describe("SessionList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("渲染会话列表", () => {
    render(<SessionList {...defaultProps} />);
    expect(screen.getByText("如何取消订单")).toBeInTheDocument();
    expect(screen.getByText("查询物流信息")).toBeInTheDocument();
  });

  it("点击会话触发 onSelectSession", () => {
    render(<SessionList {...defaultProps} />);
    fireEvent.click(screen.getByText("查询物流信息"));
    expect(defaultProps.onSelectSession).toHaveBeenCalledWith("2");
  });

  it("点击新建按钮触发 onCreateSession", () => {
    render(<SessionList {...defaultProps} />);
    fireEvent.click(screen.getByTitle("新建会话"));
    expect(defaultProps.onCreateSession).toHaveBeenCalled();
  });

  it("悬停显示删除和编辑按钮", async () => {
    render(<SessionList {...defaultProps} />);
    const item = findSessionItem("如何取消订单");
    expect(item).toBeTruthy();

    if (item) {
      fireEvent.mouseEnter(item);
      await waitFor(() => {
        expect(screen.getByTitle("删除会话")).toBeInTheDocument();
        expect(screen.getByTitle("重命名")).toBeInTheDocument();
      });
    }
  });

  it("点击编辑按钮进入编辑模式", async () => {
    render(<SessionList {...defaultProps} />);
    const item = findSessionItem("如何取消订单");

    if (item) {
      fireEvent.mouseEnter(item);
      await waitFor(() => {
        fireEvent.click(screen.getByTitle("重命名"));
      });

      const input = screen.getByDisplayValue("如何取消订单");
      expect(input).toBeInTheDocument();
    }
  });

  it("编辑模式下按 Enter 提交新名称", async () => {
    render(<SessionList {...defaultProps} />);
    const item = findSessionItem("如何取消订单");

    if (item) {
      fireEvent.mouseEnter(item);
      await waitFor(() => {
        fireEvent.click(screen.getByTitle("重命名"));
      });

      const input = screen.getByDisplayValue("如何取消订单");
      fireEvent.change(input, { target: { value: "新名称" } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(defaultProps.onRenameSession).toHaveBeenCalledWith("1", "新名称");
    }
  });

  it("编辑模式下按 Esc 取消编辑", async () => {
    render(<SessionList {...defaultProps} />);
    const item = findSessionItem("如何取消订单");

    if (item) {
      fireEvent.mouseEnter(item);
      await waitFor(() => {
        fireEvent.click(screen.getByTitle("重命名"));
      });

      const input = screen.getByDisplayValue("如何取消订单");
      fireEvent.change(input, { target: { value: "新名称" } });
      fireEvent.keyDown(input, { key: "Escape" });

      expect(screen.getByText("如何取消订单")).toBeInTheDocument();
      expect(defaultProps.onRenameSession).not.toHaveBeenCalled();
    }
  });
});
