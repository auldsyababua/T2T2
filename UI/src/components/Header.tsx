import React from 'react';
import { ChevronLeft, Settings, LogOut, User } from 'lucide-react';

interface HeaderProps {
  step: number;
  onBack?: () => void;
  onEdit?: () => void;
  user?: any;
  onLogout?: () => void;
}

export function Header({
  step,
  onBack,
  onEdit,
  user,
  onLogout
}: HeaderProps) {
  const titles = ['Select Chats', 'Processing Data', 'Chat with AI'];
  
  return (
    <header className="sticky top-0 z-10 bg-[#1976d2] text-white p-4 shadow-sm">
      <div className="flex items-center justify-between max-w-md mx-auto">
        <div className="flex items-center">
          {onBack && (
            <button 
              onClick={onBack} 
              className="mr-3 p-1 rounded-full hover:bg-[#1565c0] transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
          )}
          <h1 className="text-lg font-medium">{titles[step]}</h1>
        </div>
        
        <div className="flex items-center gap-2">
          {user && (
            <div className="flex items-center gap-2 text-sm">
              <User size={16} />
              <span className="hidden sm:inline">
                {user.first_name || user.username || 'User'}
              </span>
            </div>
          )}
          
          {onEdit && (
            <button 
              onClick={onEdit} 
              className="p-1 rounded-full hover:bg-[#1565c0] transition-colors"
              title="Edit selection"
            >
              <Settings size={20} />
            </button>
          )}
          
          {onLogout && (
            <button 
              onClick={onLogout} 
              className="p-1 rounded-full hover:bg-[#1565c0] transition-colors"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}