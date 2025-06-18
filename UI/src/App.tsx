import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChatSelection } from './components/ChatSelection';
import { ProcessingScreen } from './components/ProcessingScreen';
import { AIChat } from './components/AIChat';
import { PhoneLogin } from './components/PhoneLogin';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);
  const [selectedChats, setSelectedChats] = useState<string[]>([]);
  const [chatHistory, setChatHistory] = useState([{
    role: 'ai',
    content: "Hello! I've processed your chat history. You can now ask me anything about your Telegram conversations."
  }]);
  const [isEditing, setIsEditing] = useState(false);
  
  useEffect(() => {
    // Check if user is already authenticated
    checkAuthStatus();
  }, []);
  
  const checkAuthStatus = async () => {
    console.log('[APP] Checking auth status');
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      console.log('[APP] No auth token found');
      setLoading(false);
      return;
    }
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://t2t2-production.up.railway.app'}/api/phone-auth/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('[APP] Auth status:', data);
        
        if (data.authenticated && data.user) {
          setIsAuthenticated(true);
          setUser(data.user);
        } else {
          // Token invalid, clear it
          localStorage.removeItem('auth_token');
        }
      } else {
        // Token invalid, clear it
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      console.error('[APP] Auth check error:', error);
      localStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };
  
  const handleLoginSuccess = (user: any) => {
    console.log('[APP] Login successful:', user);
    setIsAuthenticated(true);
    setUser(user);
  };
  
  const handleLogout = async () => {
    console.log('[APP] Logging out');
    
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        await fetch(`${import.meta.env.VITE_API_URL || 'https://t2t2-production.up.railway.app'}/api/phone-auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error('[APP] Logout error:', error);
      }
    }
    
    localStorage.removeItem('auth_token');
    setIsAuthenticated(false);
    setUser(null);
    setStep(0);
    setSelectedChats([]);
  };
  
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
  
  // Show loading while checking auth
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }
  
  // Show login if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="flex flex-col w-full min-h-screen bg-[#F5F5F5] dark:bg-[#212121]">
        <div className="flex-1 flex items-center justify-center p-4">
          <PhoneLogin onSuccess={handleLoginSuccess} />
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
        user={user}
        onLogout={handleLogout}
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