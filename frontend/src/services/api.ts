/**
 * API 服务
 * 封装与后端 FastAPI 的通信
 *
 * 后端地址通过环境变量 VITE_API_BASE 配置：
 *   开发环境 .env.development → http://localhost:8000/api
 *   生产环境 .env.production  → https://your-domain.com/api
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface Reference {
  id: string;
  content: string;
  response: string;
  category: string;
  score: number;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  category: string;
  references: Reference[];
}

export interface StatsResponse {
  total_documents: number;
  collection_name: string;
}

/** 发送对话请求 */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`请求失败: ${res.status}`);
  return res.json();
}

/** 获取系统统计信息 */
export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/admin/stats`);
  if (!res.ok) throw new Error(`请求失败: ${res.status}`);
  return res.json();
}

/** 健康检查 */
export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

/** 获取会话列表 */
export interface SessionItem {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SessionsResponse {
  sessions: SessionItem[];
  total: number;
}

export async function getSessions(): Promise<SessionsResponse> {
  const res = await fetch(`${API_BASE}/chat/sessions`);
  if (!res.ok) throw new Error(`请求失败: ${res.status}`);
  return res.json();
}

/** 获取会话历史消息 */
export interface HistoryMessage {
  role: string;
  content: string;
}

export interface HistoryResponse {
  session_id: string;
  messages: HistoryMessage[];
}

export async function getHistory(sessionId: string): Promise<HistoryResponse> {
  const res = await fetch(`${API_BASE}/chat/history/${sessionId}`);
  if (!res.ok) throw new Error(`请求失败: ${res.status}`);
  return res.json();
}

/** 删除会话 */
export async function deleteSession(sessionId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
  return res.ok;
}

/** 重命名会话 */
export async function renameSession(sessionId: string, title: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}/rename`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return res.ok;
}
