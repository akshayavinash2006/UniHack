import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const ReviewQueue: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Review Queue</h2>
          <p className="text-sm text-slate-500 mt-1">Products flagged for manual review due to low confidence or missing data.</p>
        </div>
      </div>
      
      <div className="h-64 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 bg-slate-50/50">
        <AlertTriangle className="h-10 w-10 mb-3 opacity-20" />
        <p>No items currently in the review queue.</p>
      </div>
    </div>
  );
};
