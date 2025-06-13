import React from 'react';
interface ProgressIndicatorProps {
  progress: number;
}
export function ProgressIndicator({
  progress
}: ProgressIndicatorProps) {
  return <div className="w-full">
      <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full bg-[#1976d2] transition-all duration-300 ease-out" style={{
        width: `${progress}%`
      }} />
      </div>
      <div className="mt-2 text-right text-sm text-gray-600 dark:text-gray-400">
        {progress}%
      </div>
    </div>;
}