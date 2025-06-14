import React, { useRef, useEffect, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ChatItem } from './ChatItem';
import { getUserChats, Chat } from '../lib/api';
import { Loader2 } from 'lucide-react';
interface ChatSelectionProps {
  selectedChats: string[];
  onChatSelect: (chatId: string) => void;
  onNext: () => void;
  isEditing?: boolean;
  onEditComplete?: () => void;
}
export function ChatSelection({
  selectedChats,
  onChatSelect,
  onNext,
  isEditing,
  onEditComplete
}: ChatSelectionProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  
  useEffect(() => {
    loadChats();
  }, []);
  
  const loadChats = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getUserChats();
      setChats(data);
    } catch (err: any) {
      // Enhanced error logging for debugging
      // @ts-ignore
      const tg = window.Telegram?.WebApp;
      const errorDetails = [
        `Error: ${err.message || 'Unknown error'}`,
        `API URL: ${import.meta.env.VITE_API_URL || 'not set'}`,
        `Type: ${err.name || 'Unknown'}`,
        `Has Telegram: ${!!tg}`,
        `Has InitData: ${!!(tg?.initData)}`,
      ];
      
      if (err.message?.includes('fetch')) {
        errorDetails.push('Network error - API might be unreachable');
      }
      
      setError(errorDetails.join('\n'));
    } finally {
      setLoading(false);
    }
  };
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: chats.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 76,
    overscan: 5 // number of items to render outside of the visible area
  });
  return <div className="flex flex-col h-full">
      <div className="mb-4 p-4 bg-white dark:bg-[#2A2A2A] rounded-lg shadow-sm">
        <h2 className="text-lg font-medium mb-2">
          {isEditing ? 'Edit Selected Chats' : 'Select Telegram Chats'}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {isEditing ? 'Update which chats you want your AI agent to learn from.' : 'Choose which chats you want your AI agent to learn from. You can select multiple chats.'}
        </p>
      </div>
      
      {loading && (
        <div className="flex flex-col items-center justify-center flex-1">
          <Loader2 className="animate-spin h-8 w-8 text-blue-500 mb-4" />
          <p className="text-gray-600 dark:text-gray-300">Loading your chats...</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4">
          <pre className="whitespace-pre-wrap text-xs font-mono">{error}</pre>
          <button onClick={loadChats} className="mt-2 text-sm underline hover:no-underline">
            Try again
          </button>
        </div>
      )}
      
      {!loading && !error && (
        <div ref={parentRef} className="flex-1 mb-4 overflow-auto">
          <div style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}>
            {virtualizer.getVirtualItems().map(virtualItem => {
            const chat = chats[virtualItem.index];
            return <div key={virtualItem.key} style={{
              position: 'absolute',
              top: 0,
              transform: `translateY(${virtualItem.start}px)`,
              padding: '6px 0',
              width: '100%'
            }}>
                  <ChatItem 
                    chat={{
                      id: chat.id,
                      name: chat.title,
                      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(chat.title)}&background=0088CC&color=fff`,
                      lastMessage: chat.message_count ? `${chat.message_count} messages` : 'No messages'
                    }} 
                    isSelected={selectedChats.includes(chat.id)} 
                    onSelect={() => onChatSelect(chat.id)} 
                  />
                </div>;
          })}
          </div>
        </div>
      )}
      <button onClick={isEditing ? onEditComplete : onNext} disabled={selectedChats.length === 0} className={`w-full py-3 rounded-lg text-white font-medium transition-colors ${selectedChats.length > 0 ? 'bg-[#1976d2] hover:bg-[#1565c0]' : 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'}`}>
        {isEditing ? 'Save Changes' : `Continue with ${selectedChats.length} ${selectedChats.length === 1 ? 'chat' : 'chats'}`}
      </button>
    </div>;
}