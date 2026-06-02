/**
 * 会话管理 Hook
 * 会话列表和消息历史均从后端 API 获取
 * localStorage 仅作为离线缓存兜底
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { getSessions, getHistory, deleteSession as deleteSessionApi, renameSession as renameSessionApi } from "@/services/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  references?: Array<{
    content: string;
    response: string;
    category: string;
  }>;
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

const STORAGE_KEY = "ai_cs_sessions";
const ACTIVE_KEY = "ai_cs_active_session";

function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Session[];
    return parsed.map((session) => ({
      ...session,
      messages: session.messages.map((msg) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      })),
    }));
  } catch {
    return [];
  }
}

function saveSessions(sessions: Session[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function loadActiveId(): string | null {
  return localStorage.getItem(ACTIVE_KEY);
}

function saveActiveId(id: string | null) {
  if (id) {
    localStorage.setItem(ACTIVE_KEY, id);
  } else {
    localStorage.removeItem(ACTIVE_KEY);
  }
}

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>(loadSessions);
  const [activeId, setActiveId] = useState<string | null>(loadActiveId);
  const hasSynced = useRef(false);

  // 持久化到 localStorage
  useEffect(() => {
    saveSessions(sessions);
  }, [sessions]);

  useEffect(() => {
    saveActiveId(activeId);
  }, [activeId]);

  // 从后端同步会话列表（首次挂载时）
  useEffect(() => {
    if (hasSynced.current) return;
    hasSynced.current = true;

    getSessions().then((data) => {
      if (!data?.sessions?.length) return;

      const backendSessions: Session[] = data.sessions.map((s) => ({
        id: s.session_id,
        title: s.title,
        messages: [], // 消息在点击会话时再加载
        createdAt: new Date(s.createdAt).getTime(),
        updatedAt: new Date(s.updatedAt).getTime(),
      }));

      setSessions((prev) => {
        const existingIds = new Set(prev.map((s) => s.id));
        const newSessions = backendSessions.filter((s) => !existingIds.has(s.id));
        if (newSessions.length === 0) return prev;
        return [...newSessions, ...prev];
      });
    }).catch(() => {
      // 后端不可用时静默失败，继续使用 localStorage
    });
  }, []);

  // 确保 activeId 有效
  useEffect(() => {
    if (sessions.length === 0) return;
    if (!activeId || !sessions.find((s) => s.id === activeId)) {
      setActiveId(sessions[0].id);
    }
  }, [sessions, activeId]);

  // 切换会话时从后端加载消息
  const switchSession = useCallback((id: string) => {
    setActiveId(id);

    // 从后端获取消息历史
    getHistory(id).then((data) => {
      if (!data?.messages?.length) return;

      const messages: Message[] = data.messages.map((m, i) => ({
        id: `msg_${i}`,
        role: m.role === "ai" ? "assistant" : "user",
        content: m.content,
        timestamp: new Date(),
      }));

      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, messages } : s))
      );
    }).catch(() => {
      // 后端不可用时使用 localStorage 中的消息
    });
  }, []);

  // 新建会话
  const createSession = useCallback(() => {
    const id = `session_${Date.now()}`;
    const now = Date.now();
    const session: Session = {
      id,
      title: "新会话",
      messages: [
        {
          id: "welcome",
          role: "assistant",
          content: "您好，我是 AI 客服助手。请问有什么可以帮您？",
          timestamp: new Date(),
        },
      ],
      createdAt: now,
      updatedAt: now,
    };
    setSessions((prev) => [session, ...prev]);
    setActiveId(id);
    return session;
  }, []);

  // 删除会话（同时调后端 API）
  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeId === id) {
        const remaining = sessions.filter((s) => s.id !== id);
        setActiveId(remaining.length > 0 ? remaining[0].id : null);
      }
      // 通知后端删除
      deleteSessionApi(id).catch(() => {});
    },
    [activeId, sessions]
  );

  // 追加消息（本地更新，后端由 chat() 接口保存）
  const addMessage = useCallback((sessionId: string, message: Message) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const updatedMessages = [...s.messages, message];
        const firstUserMsg = updatedMessages.find((m) => m.role === "user");
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 15) + (firstUserMsg.content.length > 15 ? "…" : "")
          : s.title;
        return { ...s, messages: updatedMessages, title, updatedAt: Date.now() };
      })
    );
  }, []);

  // 重命名会话（同时调后端 API）
  const renameSession = useCallback((sessionId: string, title: string) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        return { ...s, title, updatedAt: Date.now() };
      })
    );
    // 通知后端重命名
    renameSessionApi(sessionId, title).catch(() => {});
  }, []);

  const activeSession = sessions.find((s) => s.id === activeId) || null;

  return {
    sessions,
    activeSession,
    activeId,
    createSession,
    deleteSession,
    switchSession,
    addMessage,
    renameSession,
  };
}
