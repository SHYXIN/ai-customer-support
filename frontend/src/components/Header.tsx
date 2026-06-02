import { Headset, PanelLeft } from "lucide-react";

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export function Header({ onToggleSidebar }: HeaderProps) {
  return (
    <header className="flex items-center gap-3 border-b bg-card px-4 py-3">
      {onToggleSidebar && (
        <button
          className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          onClick={onToggleSidebar}
          title="切换侧边栏"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      )}
      <Headset className="h-5 w-5 text-primary" />
      <div>
        <h1 className="text-sm font-semibold">AI 智能客服</h1>
        <p className="text-xs text-muted-foreground">基于 LangGraph 的客服系统</p>
      </div>
    </header>
  );
}
