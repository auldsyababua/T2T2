import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { queryMessages } from '../lib/api';
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
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSend = async () => {
    if (!message.trim() || isLoading) return;
    
    const userMessage = message;
    setChatHistory([...chatHistory, {
      role: 'user',
      content: userMessage
    }]);
    setMessage('');
    setIsLoading(true);
    
    try {
      const response = await queryMessages(userMessage);
      
      // Format the response with sources
      let aiResponse = response.answer;
      if (response.sources && response.sources.length > 0) {
        aiResponse += '\n\nSources:';
        response.sources.forEach((source, index) => {
          aiResponse += `\n${index + 1}. ${source.chat_title} - ${new Date(source.timestamp).toLocaleDateString()}`;
        });
      }
      
      setChatHistory(prev => [...prev, {
        role: 'ai',
        content: aiResponse
      }]);
    } catch (err: any) {
      setChatHistory(prev => [...prev, {
        role: 'ai',
        content: `Sorry, I encountered an error: ${err.message || 'Unknown error'}`
      }]);
    } finally {
      setIsLoading(false);
    }
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
        <button onClick={handleSend} disabled={!message.trim() || isLoading} className={`ml-2 p-2 rounded-full ${message.trim() && !isLoading ? 'text-[#1976d2] hover:bg-gray-100 dark:hover:bg-[#333333]' : 'text-gray-400 cursor-not-allowed'}`}>
          {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
        </button>
      </div>
    </div>;
}