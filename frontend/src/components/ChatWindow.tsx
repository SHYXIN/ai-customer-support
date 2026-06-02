import { useState, useCallback } from "react";
import { MessageList, type Message } from "./MessageList";
import { InputBox } from "./InputBox";
import { QuickQuestions } from "./QuickQuestions";
import { chat } from "@/services/api";

interface ChatWindowProps {
  sessionId: string;
  messages: Message[];
  onAddMessage: (message: Message) => void;
}

export function ChatWindow({ sessionId, messages, onAddMessage }: ChatWindowProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = useCallback(
    async (content: string) => {
      const userMsg: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date(),
      };
      onAddMessage(userMsg);

      setIsLoading(true);

      try {
        const res = await chat({
          message: content,
          session_id: sessionId,
        });

        const aiMsg: Message = {
          id: `ai_${Date.now()}`,
          role: "assistant",
          content: res.response,
          timestamp: new Date(),
          references: res.references || [],
        };
        onAddMessage(aiMsg);
      } catch {
        const errMsg: Message = {
          id: `err_${Date.now()}`,
          role: "assistant",
          content: "抱歉，服务暂时不可用，请稍后重试。",
          timestamp: new Date(),
        };
        onAddMessage(errMsg);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, onAddMessage]
  );

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} isLoading={isLoading} />
      <QuickQuestions onSelect={handleSend} disabled={isLoading} />
      <InputBox onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
