import React from 'react';
import { Check } from 'lucide-react';
interface Chat {
  id: string;
  name: string;
  avatar: string;
  lastMessage: string;
}
interface ChatItemProps {
  chat: Chat;
  isSelected: boolean;
  onSelect: () => void;
}
export function ChatItem({
  chat,
  isSelected,
  onSelect
}: ChatItemProps) {
  return <div onClick={onSelect} className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${isSelected ? 'bg-[#1976d2]/10 dark:bg-[#1976d2]/20' : 'bg-white dark:bg-[#2A2A2A] hover:bg-gray-50 dark:hover:bg-[#333333]'}`}>
      <div className="relative">
        <img src={chat.avatar} alt={chat.name} className="w-12 h-12 rounded-full" />
        {isSelected && <div className="absolute -bottom-1 -right-1 bg-[#1976d2] rounded-full p-0.5">
            <Check size={14} className="text-white" />
          </div>}
      </div>
      <div className="ml-3 flex-1">
        <h3 className="font-medium">{chat.name}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
          {chat.lastMessage}
        </p>
      </div>
      <div className={`w-5 h-5 rounded-full border-2 ml-2 ${isSelected ? 'border-[#1976d2] bg-[#1976d2]' : 'border-gray-300 dark:border-gray-600'}`}>
        {isSelected && <Check size={12} className="text-white mx-auto" />}
      </div>
    </div>;
}