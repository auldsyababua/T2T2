import React, { useState } from 'react';
import { Send } from 'lucide-react';
interface Message {
  role: 'user' | 'ai';
  content: string;
}
interface AIChatProps {
  chatHistory: Message[];
  setChatHistory: React.Dispatch<React.SetStateAction<Message[]>>;
}
export function AIChat({
  chatHistory,
  setChatHistory
}: AIChatProps) {
  const [message, setMessage] = useState('');
  const handleSend = () => {
    if (!message.trim()) return;
    setChatHistory([...chatHistory, {
      role: 'user',
      content: message
    }]);
    setMessage('');
    // Simulate AI response (in a real app, this would be an API call)
    setTimeout(() => {
      setChatHistory(prev => [...prev, {
        role: 'ai',
        content: "I found that information in your chat history. Based on your conversations, here's what I know..."
      }]);
    }, 1000);
  };
  return <div className="flex flex-col h-full bg-white dark:bg-[#2A2A2A] rounded-lg overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {chatHistory.map((msg, index) => <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-[#1976d2] text-white rounded-br-none' : 'bg-gray-100 dark:bg-[#333333] rounded-bl-none'}`}>
                {msg.content}
              </div>
            </div>)}
        </div>
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 p-3 flex items-center">
        <input type="text" value={message} onChange={e => setMessage(e.target.value)} placeholder="Message" className="flex-1 bg-transparent outline-none" onKeyPress={e => {
        if (e.key === 'Enter') handleSend();
      }} />
        <button onClick={handleSend} disabled={!message.trim()} className={`ml-2 p-2 rounded-full ${message.trim() ? 'text-[#1976d2] hover:bg-gray-100 dark:hover:bg-[#333333]' : 'text-gray-400 cursor-not-allowed'}`}>
          <Send size={20} />
        </button>
      </div>
    </div>;
}