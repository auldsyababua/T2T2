// API service for T2T2 backend integration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types matching our backend models
export interface Chat {
  id: string;
  title: string;
  type: string;
  indexed_at?: string;
  message_count?: number;
}

export interface User {
  id: string;
  telegram_id: string;
  username?: string;
  first_name?: string;
  last_name?: string;
}

export interface Timeline {
  id: string;
  title: string;
  query: string;
  created_at: string;
  messages: any[];
}

export interface QueryResponse {
  answer: string;
  sources: Array<{
    message_id: string;
    content: string;
    chat_title: string;
    timestamp: string;
    url: string;
    score: number;
  }>;
}

// Initialize the Telegram Mini App
export function initTelegramWebApp() {
  // @ts-ignore
  if (window.Telegram?.WebApp) {
    // @ts-ignore
    const tg = window.Telegram.WebApp;
    tg.ready();
    return tg;
  }
  return null;
}

// Get init data for authentication
export function getTelegramInitData(): string {
  // @ts-ignore
  const tg = window.Telegram?.WebApp;
  return tg?.initData || '';
}

// API client with auth headers
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const initData = getTelegramInitData();
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Authentication handled through Telegram bot - QR login removed

// Get user's chats
export async function getUserChats(): Promise<Chat[]> {
  return apiRequest('/api/telegram/chats');
}

// Index selected chats
export async function indexChats(chatIds: string[]) {
  return apiRequest('/api/telegram/index', {
    method: 'POST',
    body: JSON.stringify({ chat_ids: chatIds }),
  });
}

// Check indexing progress
export async function getIndexingProgress(taskId: string) {
  return apiRequest(`/api/telegram/progress/${taskId}`);
}

// Query the indexed messages
export async function queryMessages(query: string): Promise<QueryResponse> {
  return apiRequest('/api/query/', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

// Get similar messages
export async function getSimilarMessages(query: string, limit: number = 10) {
  return apiRequest('/api/query/similar', {
    method: 'POST',
    body: JSON.stringify({ query, limit }),
  });
}

// Generate timeline from query
export async function generateTimeline(query: string, title?: string) {
  return apiRequest('/api/timeline/generate', {
    method: 'POST',
    body: JSON.stringify({ query, title }),
  });
}

// Get saved timelines
export async function getSavedTimelines(): Promise<Timeline[]> {
  return apiRequest('/api/timeline/saved');
}

// Get timeline by ID
export async function getTimeline(id: string): Promise<Timeline> {
  return apiRequest(`/api/timeline/${id}`);
}

// Delete timeline
export async function deleteTimeline(id: string) {
  return apiRequest(`/api/timeline/${id}`, { method: 'DELETE' });
}