import React, { useState } from 'react';
import { Header } from './components/Header';
import { ChatSelection } from './components/ChatSelection';
import { ProcessingScreen } from './components/ProcessingScreen';
import { AIChat } from './components/AIChat';
export function App() {
  const [step, setStep] = useState(0);
  const [selectedChats, setSelectedChats] = useState<string[]>([]);
  const [chatHistory, setChatHistory] = useState([{
    role: 'ai',
    content: "Hello! I've processed your chat history. You can now ask me anything about your Telegram conversations."
  }]);
  const [isEditing, setIsEditing] = useState(false);
  const handleChatSelect = (chatId: string) => {
    if (selectedChats.includes(chatId)) {
      setSelectedChats(selectedChats.filter(id => id !== chatId));
    } else {
      setSelectedChats([...selectedChats, chatId]);
    }
  };
  const handleNextStep = () => {
    setStep(step + 1);
    setIsEditing(false);
  };
  const handleBackStep = () => {
    if (step === 2 && !isEditing) {
      setIsEditing(true);
      setStep(0);
    } else {
      setStep(step - 1);
    }
  };
  const handleEditComplete = () => {
    setIsEditing(false);
    setStep(2);
  };
  return <div className="flex flex-col w-full min-h-screen bg-[#F5F5F5] dark:bg-[#212121]">
      <Header step={step} onBack={step > 0 ? handleBackStep : undefined} onEdit={step === 2 ? () => {
      setIsEditing(true);
      setStep(0);
    } : undefined} />
      <main className="flex-1 w-full max-w-md mx-auto p-4">
        {step === 0 && <ChatSelection selectedChats={selectedChats} onChatSelect={handleChatSelect} onNext={handleNextStep} isEditing={isEditing} onEditComplete={handleEditComplete} />}
        {step === 1 && <ProcessingScreen selectedChats={selectedChats} onComplete={handleNextStep} />}
        {step === 2 && <AIChat chatHistory={chatHistory} setChatHistory={setChatHistory} />}
      </main>
    </div>;
}