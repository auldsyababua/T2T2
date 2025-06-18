// API service for T2T2 backend integration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://t2t2-production.up.railway.app';

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
    // Don't call ready() here - let the app control when to call it
    return tg;
  }
  return null;
}

// Get init data for authentication
export function getTelegramInitData(): string {
  // @ts-ignore
  const tg = window.Telegram?.WebApp;
  const initData = tg?.initData || '';
  
  // Debug: Show init data status in error messages
  if (!tg) {
    console.error('[API] Telegram WebApp not available');
    console.error('[API] window.Telegram:', window.Telegram);
  } else if (!initData) {
    console.error('[API] No initData from Telegram');
    console.error('[API] WebApp object:', tg);
    console.error('[API] WebApp version:', tg.version);
    console.error('[API] WebApp platform:', tg.platform);
    // Try to get initDataUnsafe as fallback
    console.error('[API] initDataUnsafe:', tg.initDataUnsafe);
  } else {
    console.log('[API] Got initData, length:', initData.length);
  }
  
  return initData;
}

// API client with auth headers
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const initData = getTelegramInitData();
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log('[API] Request:', {
    url,
    endpoint,
    method: options.method || 'GET',
    hasInitData: !!initData,
    initDataLength: initData.length,
  });
  
  // Get auth token if available
  const authToken = localStorage.getItem('auth_token');
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Only add X-Telegram-Init-Data if we have valid initData
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }
  
  // Add Authorization header if we have a token
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });

  console.log('[API] Response:', {
    status: response.status,
    ok: response.ok,
    statusText: response.statusText,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    console.error('[API] Error:', error);
    
    // If error has debug info, include it in the message
    if (error.detail && typeof error.detail === 'object' && error.detail.debug) {
      const debug = error.detail.debug;
      const debugMessage = `${error.detail.error || 'Unknown error'}

=== AUTH DEBUG INFO ===
Hash Match: ${debug.hash_match}
Bot Token Last 4: ${debug.bot_token_last4}

RECEIVED HASH:
${debug.received_hash || 'none'}

CALCULATED HASH:
${debug.calculated_hash || 'none'}

DATA CHECK STRING:
${debug.data_check_string_preview || 'none'}

PARSED PARAMS:
${JSON.stringify(debug.parsed_params || [])}`;
      
      const err = new Error(debugMessage);
      (err as any).debug = debug;
      throw err;
    }
    
    throw new Error(typeof error.detail === 'string' ? error.detail : (error.detail?.error || `HTTP ${response.status}`));
  }

  const data = await response.json();
  console.log('[API] Success:', { endpoint, dataLength: Array.isArray(data) ? data.length : 'not-array' });
  return data;
}

// Authentication handled through Telegram bot - QR login removed

// Authenticate with Telegram Mini App data
export async function authenticateWithTelegram() {
  const response = await apiRequest('/api/auth/telegram-webapp-auth', {
    method: 'POST',
  });
  
  // Store the token for future requests
  if (response.access_token) {
    localStorage.setItem('auth_token', response.access_token);
  }
  
  return response;
}

// Get user's chats
export async function getUserChats(): Promise<Chat[]> {
  // First ensure we're authenticated
  const token = localStorage.getItem('auth_token');
  if (!token) {
    console.log('[API] No auth token, attempting to authenticate...');
    try {
      await authenticateWithTelegram();
      console.log('[API] Authentication successful');
    } catch (error) {
      console.error('[API] Authentication failed:', error);
      throw new Error(`Authentication failed: ${error.message}`);
    }
  } else {
    console.log('[API] Using existing auth token');
  }
  
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