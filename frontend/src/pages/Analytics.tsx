import React from 'react';
import { BarChart2 } from 'lucide-react';

export const Analytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Analytics Dashboard</h2>
          <p className="text-sm text-slate-500 mt-1">Metrics and performance of the enrichment pipeline.</p>
        </div>
      </div>
      
      <div className="h-64 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 bg-slate-50/50">
        <BarChart2 className="h-10 w-10 mb-3 opacity-20" />
        <p>Analytics charts will be populated after processing data.</p>
      </div>
    </div>
  );
};
