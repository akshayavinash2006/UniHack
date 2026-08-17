import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, API_BASE_URL } from '../api/client';
import type { BatchJob } from '../api/client';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Loader2, 
  Download, 
  Search,
  Filter,
  Cpu,
  ArrowRight
} from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<BatchJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Connect to SSE for live updates
  useEffect(() => {
    if (!jobId) return;

    // Initial fetch to get full state immediately
    api.getJobStatus(jobId)
      .then(data => {
        setJob(data);
        if (data.status === 'completed' || data.status === 'failed') {
          // If already done, fetch full results
          api.getJobResults(jobId).then(setJob).catch(console.error);
        } else {
          // Setup SSE if still running
          const eventSource = new EventSource(`${API_BASE_URL}/jobs/${jobId}/stream`);
          
          eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setJob(prev => ({ ...prev, ...data }));
            
            if (data.status === 'completed' || data.status === 'failed') {
              eventSource.close();
              // Fetch full results once complete
              api.getJobResults(jobId).then(setJob).catch(console.error);
            }
          };

          eventSource.onerror = () => {
            eventSource.close();
            // Fallback polling
            const interval = setInterval(async () => {
              try {
                const data = await api.getJobStatus(jobId);
                setJob(prev => ({ ...prev, ...data }));
                if (data.status === 'completed' || data.status === 'failed') {
                  clearInterval(interval);
                  api.getJobResults(jobId).then(setJob).catch(console.error);
                }
              } catch (e) {
                clearInterval(interval);
              }
            }, 2000);
            return () => clearInterval(interval);
          };

          return () => eventSource.close();
        }
      })
      .catch(err => {
        setError('Job not found or error loading job data.');
      });
  }, [jobId]);

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
        <h3 className="text-red-800 font-medium">Error Loading Job</h3>
        <p className="text-red-700 text-sm mt-1">{error}</p>
        <button onClick={() => navigate('/')} className="mt-4 text-sm text-red-600 hover:underline">Return to Dashboard</button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin mr-3" />
        <span className="font-medium text-lg">Loading Job Data...</span>
      </div>
    );
  }

  const isRunning = job.status === 'running' || job.status === 'pending';

  return (
    <div className="space-y-6 pb-20">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Batch Results</h2>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-mono font-medium bg-slate-200 text-slate-600 border border-slate-300">
              {job.job_id}
            </span>
          </div>
          <p className="text-sm text-slate-500">
            {isRunning 
              ? `Processing ${job.total_products} products in the background...`
              : `Completed enrichment of ${job.total_products} products.`}
          </p>
        </div>
        
        {!isRunning && (
          <div className="flex space-x-3">
            <a 
              href={`${API_BASE_URL}/results/${job.job_id}/export/csv`}
              download
              className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium py-2 px-4 rounded-lg shadow-sm flex items-center transition-colors"
            >
              <Download className="w-4 h-4 mr-2 text-slate-500" /> Export CSV
            </a>
          </div>
        )}
      </div>

      {/* Live Progress Bar */}
      {isRunning && (
        <div className="bg-white rounded-xl shadow-sm border border-blue-200 overflow-hidden p-6 relative">
          <div className="absolute top-0 left-0 w-full h-1 bg-blue-100">
            <div className="h-full bg-blue-500 transition-all duration-300" style={{ width: `${job.progress_percent}%` }}></div>
          </div>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-slate-800 mb-1 flex items-center">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin mr-2" />
                Pipeline Active
              </h3>
              <div className="flex items-end justify-between mt-4 mb-2">
                <span className="text-sm font-medium text-slate-600">
                  {job.processed_count} / {job.total_products} processed
                </span>
                <span className="text-2xl font-bold text-blue-600">{job.progress_percent}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3 border border-slate-200 overflow-hidden">
                <div className="bg-blue-500 h-3 rounded-full transition-all duration-300 relative" style={{ width: `${job.progress_percent}%` }}>
                  <div className="absolute inset-0 bg-white/20 animate-progress"></div>
                </div>
              </div>
            </div>
            
            <div className="md:w-64 flex-shrink-0 bg-slate-50 rounded-lg border border-slate-200 p-4">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Current Activity</div>
              <div className="text-sm font-medium text-slate-800 truncate" title={job.current_product}>
                PN: {job.current_product || 'Initializing...'}
              </div>
              <div className="flex items-center text-xs text-blue-600 mt-2 font-medium">
                <span className="relative flex h-2 w-2 mr-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                {job.current_stage === 'searching' ? 'Web Search & AI Analysis...' : 'Processing...'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">MFR URLs Found</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-slate-800">{job.matched_count + job.review_count}</div>
            <div className="text-sm font-medium text-slate-500 mb-1">
              {job.processed_count > 0 ? Math.round((job.matched_count + job.review_count) / job.processed_count * 100) : 0}%
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">High Confidence</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-green-600">{job.matched_count}</div>
            <CheckCircle2 className="w-6 h-6 text-green-500 mb-1 opacity-20" />
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">Needs Review</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-amber-600">{job.review_count}</div>
            <AlertTriangle className="w-6 h-6 text-amber-500 mb-1 opacity-20" />
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">AI Selected</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-blue-600">{job.gemini_selections}</div>
            <Cpu className="w-6 h-6 text-blue-500 mb-1 opacity-20" />
          </div>
        </div>
      </div>

      {/* Results Table */}
      {(!isRunning && job.results) && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-100 flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-slate-50/50">
            <h3 className="font-semibold text-slate-800">Enrichment Results Table</h3>
            <div className="flex space-x-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Search parts..." 
                  className="pl-9 pr-4 py-1.5 border border-slate-300 rounded-md shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500 w-full sm:w-64"
                />
              </div>
              <button className="p-1.5 border border-slate-300 rounded-md text-slate-500 bg-white hover:bg-slate-50 shadow-sm">
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">P/N</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Manufacturer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">URL</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Method</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {job.results.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors cursor-pointer group">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {r.status === 'matched' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700 border border-green-200">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Matched
                        </span>
                      ) : r.status === 'review' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700 border border-amber-200">
                          <AlertTriangle className="w-3 h-3 mr-1" /> Review
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 border border-red-200">
                          <XCircle className="w-3 h-3 mr-1" /> No Match
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap font-medium text-slate-900">{r.mfg_part_num}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-slate-600">{r.manufacturer}</td>
                    <td className="px-4 py-3 text-slate-500 truncate max-w-[200px]" title={r.description}>{r.description}</td>
                    <td className="px-4 py-3 text-slate-500 truncate max-w-[200px]">
                      {r.manufacturer_url ? (
                        <a href={r.manufacturer_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline" onClick={e => e.stopPropagation()}>
                          {r.manufacturer_url.replace(/^https?:\/\//, '')}
                        </a>
                      ) : (
                        <span className="text-slate-300 italic">None</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {r.confidence === 'high' ? <span className="text-green-600 font-medium">High</span> :
                       r.confidence === 'medium' ? <span className="text-amber-600 font-medium">Medium</span> :
                       r.confidence === 'low' ? <span className="text-red-600 font-medium">Low</span> : 
                       <span className="text-slate-400">N/A</span>}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {r.selection_method === 'gemini' ? <span className="text-blue-600 text-xs font-medium flex items-center"><Cpu className="w-3 h-3 mr-1"/> AI</span> :
                       r.selection_method === 'heuristic' ? <span className="text-slate-600 text-xs font-medium flex items-center"><Search className="w-3 h-3 mr-1"/> Heuristic</span> : 
                       <span className="text-slate-400 text-xs">-</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
