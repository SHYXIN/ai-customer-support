import { useEffect, useRef } from "react";
import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { References, type Reference } from "./References";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  references?: Reference[];
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="flex h-full items-center justify-center text-muted-foreground">
          <p>请输入您的问题，AI 客服将为您解答</p>
        </div>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={cn(
            "flex gap-3",
            msg.role === "user" ? "flex-row-reverse" : "flex-row"
          )}
        >
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
              msg.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            )}
          >
            {msg.role === "user" ? (
              <User className="h-4 w-4" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
          </div>

          <div className="flex max-w-[75%] flex-col gap-2">
            <div
              className={cn(
                "rounded-lg px-4 py-3 text-sm",
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p className="mt-1 text-xs opacity-60">
                {(() => {
                  const ts = msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp);
                  return isNaN(ts.getTime()) ? "" : ts.toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  });
                })()}
              </p>
            </div>
            {msg.role === "assistant" && msg.references && msg.references.length > 0 && (
              <References references={msg.references} />
            )}
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Bot className="h-4 w-4" />
          </div>
          <div className="rounded-lg bg-muted px-4 py-3">
            <div className="flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:0ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:150ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
