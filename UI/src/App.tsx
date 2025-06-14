import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChatSelection } from './components/ChatSelection';
import { ProcessingScreen } from './components/ProcessingScreen';
import { AIChat } from './components/AIChat';
import { initTelegramWebApp } from './lib/api';

export function App() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [authError, setAuthError] = useState<string>('');
  const [step, setStep] = useState(0);
  const [selectedChats, setSelectedChats] = useState<string[]>([]);
  const [chatHistory, setChatHistory] = useState([{
    role: 'ai',
    content: "Hello! I've processed your chat history. You can now ask me anything about your Telegram conversations."
  }]);
  const [isEditing, setIsEditing] = useState(false);
  
  useEffect(() => {
    // Wait a bit for Telegram script to fully initialize
    const initializeApp = () => {
      const tg = initTelegramWebApp();
      
      if (!tg) {
        // Not running inside Telegram
        setAuthError('This app must be opened from within Telegram');
        return;
      }
      
      // Signal to Telegram that the app is ready FIRST
      tg.ready();
      
      // Small delay to ensure ready() is processed
      setTimeout(() => {
        // Debug: Log current state
        console.log('[DEBUG] Window hash:', window.location.hash);
        console.log('[DEBUG] Has tg.initData:', !!tg.initData);
        console.log('[DEBUG] initData length:', tg.initData?.length || 0);
        
        // Now check for initData
        if (!tg.initData) {
          setAuthError(`No authentication data available. Please open this app from the Telegram bot.\n\nDebug: Hash=${window.location.hash.substring(0, 50)}...\nVersion: 4.30AM LATEST\nURL: ${window.location.href}\nDeployment: ${new Date().toISOString()}`);
          return;
        }
        
        // We have valid Telegram auth data
        setIsInitialized(true);
        
        // Configure Telegram UI
        tg.expand();
        tg.MainButton.setText('Continue');
        tg.BackButton.onClick(() => handleBackStep());
        
        // Enable closing confirmation when data is being processed
        tg.enableClosingConfirmation();
      }, 100);
    };
    
    // Give Telegram script time to inject data
    if (document.readyState === 'complete') {
      initializeApp();
    } else {
      window.addEventListener('load', initializeApp);
    }
  }, []);
  
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
    
    // Update Telegram UI
    const tg = window.Telegram?.WebApp;
    if (tg) {
      if (step === 0) {
        tg.BackButton.show();
      }
      if (step === 1) {
        tg.MainButton.hide();
      }
    }
  };
  
  const handleBackStep = () => {
    if (step === 2 && !isEditing) {
      setIsEditing(true);
      setStep(0);
    } else {
      setStep(step - 1);
    }
    
    // Update Telegram UI
    const tg = window.Telegram?.WebApp;
    if (tg && step === 1) {
      tg.BackButton.hide();
      tg.MainButton.show();
    }
  };
  
  const handleEditComplete = () => {
    setIsEditing(false);
    setStep(2);
  };
  
  // Show error if not in Telegram
  if (authError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 text-red-700 dark:text-red-400 px-4 py-3 rounded max-w-md">
          <h2 className="font-bold mb-2">Authentication Error</h2>
          <p>{authError}</p>
          <p className="mt-2 text-sm">
            Please open this app by clicking the "Open App" button in @talk2telegrambot
          </p>
        </div>
      </div>
    );
  }
  
  // Show loading while initializing
  if (!isInitialized) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Initializing...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col w-full min-h-screen bg-[#F5F5F5] dark:bg-[#212121]">
      <Header 
        step={step} 
        onBack={step > 0 ? handleBackStep : undefined} 
        onEdit={step === 2 ? () => {
          setIsEditing(true);
          setStep(0);
        } : undefined} 
      />
      <main className="flex-1 w-full max-w-md mx-auto p-4">
        {step === 0 && (
          <ChatSelection 
            selectedChats={selectedChats} 
            onChatSelect={handleChatSelect} 
            onNext={handleNextStep} 
            isEditing={isEditing} 
            onEditComplete={handleEditComplete} 
          />
        )}
        {step === 1 && (
          <ProcessingScreen 
            selectedChats={selectedChats} 
            onComplete={handleNextStep} 
          />
        )}
        {step === 2 && (
          <AIChat 
            chatHistory={chatHistory} 
            setChatHistory={setChatHistory} 
          />
        )}
      </main>
    </div>
  );
}