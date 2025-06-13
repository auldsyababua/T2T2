import React, { useEffect, useState } from 'react';
import { ProgressIndicator } from './ProgressIndicator';
import { indexChats, getIndexingProgress } from '../lib/api';
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
  const [taskId, setTaskId] = useState<string>('');
  const [error, setError] = useState<string>('');
  const stages = ['Starting indexing...', 'Downloading messages...', 'Generating embeddings...', 'Indexing complete!'];
  
  useEffect(() => {
    startIndexing();
  }, []);
  
  useEffect(() => {
    if (taskId) {
      const interval = setInterval(checkProgress, 2000);
      return () => clearInterval(interval);
    }
  }, [taskId]);
  
  const startIndexing = async () => {
    try {
      setError('');
      const response = await indexChats(selectedChats);
      setTaskId(response.task_id);
    } catch (err: any) {
      setError(err.message || 'Failed to start indexing');
    }
  };
  
  const checkProgress = async () => {
    try {
      const response = await getIndexingProgress(taskId);
      const progressPercent = Math.round((response.processed / response.total) * 100);
      setProgress(progressPercent);
      
      // Update stage based on status
      if (response.status === 'downloading') setCurrentStage(1);
      else if (response.status === 'embedding') setCurrentStage(2);
      else if (response.status === 'completed') {
        setCurrentStage(3);
        setTimeout(onComplete, 1000);
      }
    } catch (err) {
      // Ignore errors during polling
    }
  };
  return <div className="flex flex-col items-center justify-center h-full">
      <div className="w-full max-w-md bg-white dark:bg-[#2A2A2A] p-6 rounded-lg shadow-sm">
        <h2 className="text-lg font-medium mb-6 text-center">
          Processing {selectedChats.length}{' '}
          {selectedChats.length === 1 ? 'chat' : 'chats'}
        </h2>
        
        {error ? (
          <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 text-red-700 dark:text-red-400 px-4 py-3 rounded">
            <p>{error}</p>
            <button onClick={startIndexing} className="mt-2 text-sm underline hover:no-underline">
              Try again
            </button>
          </div>
        ) : (
          <>
            <ProgressIndicator progress={progress} />
            <p className="mt-6 text-center text-gray-700 dark:text-gray-300">
              {stages[currentStage]}
            </p>
            <p className="mt-2 text-sm text-center text-gray-500 dark:text-gray-400">
              This may take a few minutes depending on the amount of chat history
            </p>
          </>
        )}
      </div>
    </div>;
}