import React, { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ChatItem } from './ChatItem';
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
  // Mock chat data - in a real app, this would come from Telegram API
  const chats = Array.from({
    length: 1000
  }, (_, index) => ({
    id: index.toString(),
    name: `Chat ${index + 1}`,
    avatar: `https://placehold.co/200x200/0088CC/FFFFFF?text=${index + 1}`,
    lastMessage: `Last message from chat ${index + 1}`
  }));
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
                <ChatItem chat={chat} isSelected={selectedChats.includes(chat.id)} onSelect={() => onChatSelect(chat.id)} />
              </div>;
        })}
        </div>
      </div>
      <button onClick={isEditing ? onEditComplete : onNext} disabled={selectedChats.length === 0} className={`w-full py-3 rounded-lg text-white font-medium transition-colors ${selectedChats.length > 0 ? 'bg-[#1976d2] hover:bg-[#1565c0]' : 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'}`}>
        {isEditing ? 'Save Changes' : `Continue with ${selectedChats.length} ${selectedChats.length === 1 ? 'chat' : 'chats'}`}
      </button>
    </div>;
}