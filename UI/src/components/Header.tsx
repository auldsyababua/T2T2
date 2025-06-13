import React from 'react';
import { ChevronLeft, Settings } from 'lucide-react';
interface HeaderProps {
  step: number;
  onBack?: () => void;
  onEdit?: () => void;
}
export function Header({
  step,
  onBack,
  onEdit
}: HeaderProps) {
  const titles = ['Select Chats', 'Processing Data', 'Chat with AI'];
  return <header className="sticky top-0 z-10 bg-[#1976d2] text-white p-4 shadow-sm">
      <div className="flex items-center justify-between max-w-md mx-auto">
        <div className="flex items-center">
          {onBack && <button onClick={onBack} className="mr-3 p-1 rounded-full hover:bg-[#1565c0] transition-colors">
              <ChevronLeft size={20} />
            </button>}
          <h1 className="text-lg font-medium">{titles[step]}</h1>
        </div>
        {onEdit && <button onClick={onEdit} className="p-1 rounded-full hover:bg-[#1565c0] transition-colors">
            <Settings size={20} />
          </button>}
      </div>
    </header>;
}