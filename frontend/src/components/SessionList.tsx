import { useState, useRef, useEffect } from "react";
import { MessageSquare, Plus, Trash2, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Session {
  id: string;
  title: string;
  updatedAt: number;
}

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession?: (id: string, title: string) => void;
}

export function SessionList({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onRenameSession,
}: SessionListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 60_000) return "刚刚";
    if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`;
    if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`;
    return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  };

  const handleStartEdit = (session: Session) => {
    setEditingId(session.id);
    setEditValue(session.title);
  };

  const handleSubmitEdit = () => {
    if (editingId && editValue.trim() && onRenameSession) {
      onRenameSession(editingId, editValue.trim());
    }
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSubmitEdit();
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  return (
    <div className="flex h-full w-[260px] flex-col border-r bg-muted/30">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <span className="text-sm font-medium">会话列表</span>
        <button
          className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          onClick={onCreateSession}
          title="新建会话"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 && (
          <div className="flex h-full items-center justify-center px-4 text-center text-xs text-muted-foreground">
            暂无会话，点击 + 新建
          </div>
        )}

        {sessions.map((session) => {
          const isHovered = hoveredId === session.id;
          const isEditing = editingId === session.id;

          return (
            <div
              key={session.id}
              className={cn(
                "group relative mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                session.id === currentSessionId
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              onClick={() => {
                if (!isEditing) {
                  onSelectSession(session.id);
                }
              }}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />

              <div className="min-w-0 flex-1">
                {isEditing ? (
                  <input
                    ref={inputRef}
                    className="w-full rounded border bg-background px-1 py-0.5 text-xs outline-none"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onBlur={handleSubmitEdit}
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <>
                    <p className="truncate font-medium">{session.title}</p>
                    <p className="text-xs opacity-60">
                      {formatTime(session.updatedAt)}
                    </p>
                  </>
                )}
              </div>

              {!isEditing && isHovered && (
                <div className="absolute right-1 top-1/2 flex -translate-y-1/2 gap-0.5">
                  <button
                    className="flex h-6 w-6 items-center justify-center rounded hover:bg-muted"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(session);
                    }}
                    title="重命名"
                  >
                    <Pencil className="h-3 w-3" />
                  </button>
                  <button
                    className="flex h-6 w-6 items-center justify-center rounded hover:bg-destructive/10 hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    title="删除会话"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
