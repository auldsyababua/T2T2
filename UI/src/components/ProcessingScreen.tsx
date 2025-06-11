import React, { useEffect, useState } from 'react';
import { ProgressIndicator } from './ProgressIndicator';
interface ProcessingScreenProps {
  selectedChats: string[];
  onComplete: () => void;
}
export function ProcessingScreen({
  selectedChats,
  onComplete
}: ProcessingScreenProps) {
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const stages = ['Requesting access to chats...', 'Downloading messages...', 'Processing data...', 'Training AI agent...'];
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = Math.min(prev + 1, 100);
        // Change stage based on progress
        if (newProgress === 15) setCurrentStage(1);
        if (newProgress === 45) setCurrentStage(2);
        if (newProgress === 75) setCurrentStage(3);
        // If we've reached 100%, clear the interval and trigger completion
        if (newProgress === 100) {
          clearInterval(interval);
          setTimeout(onComplete, 500);
        }
        return newProgress;
      });
    }, 50);
    return () => clearInterval(interval);
  }, [onComplete]);
  return <div className="flex flex-col items-center justify-center h-full">
      <div className="w-full max-w-md bg-white dark:bg-[#2A2A2A] p-6 rounded-lg shadow-sm">
        <h2 className="text-lg font-medium mb-6 text-center">
          Processing {selectedChats.length}{' '}
          {selectedChats.length === 1 ? 'chat' : 'chats'}
        </h2>
        <ProgressIndicator progress={progress} />
        <p className="mt-6 text-center text-gray-700 dark:text-gray-300">
          {stages[currentStage]}
        </p>
        <p className="mt-2 text-sm text-center text-gray-500 dark:text-gray-400">
          This may take a few minutes depending on the amount of chat history
        </p>
      </div>
    </div>;
}