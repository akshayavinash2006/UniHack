import React, { useState } from 'react';
import { api } from '../api/client';
import { Upload, FileText, Settings, Play, Loader2, Database, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const BatchProcessing: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  // Config state
  const [config, setConfig] = useState({
    max_rows: 10,
    search_results_per_product: 4,
    search_delay: 1.5,
    gemini_enabled: true
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    
    setFile(selected);
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.uploadCsv(selected);
      if (data.error) {
        setError(data.error);
        setPreview(null);
      } else {
        setPreview(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload CSV');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSampleData();
      if (data.error) {
        setError(data.error);
      } else {
        setPreview({ ...data, all_rows: data.preview }); // Sample data provides all rows we need for demo
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load sample dataset');
    } finally {
      setLoading(false);
    }
  };

  const handleStartEnrichment = async () => {
    if (!preview || !preview.all_rows) return;
    
    setStarting(true);
    try {
      const productsToProcess = preview.all_rows.slice(0, config.max_rows);
      
      const res = await api.startBatch(
        productsToProcess.map((row: any) => ({
          mfg_part_num: row.Mfg_Part_Num || '',
          manufacturer: row.Part_Manuf || '',
          description: row.Part_Desc || '',
          e1_brand: row.E1_Brand || '',
          unilog_brand: row.Unilog_Brand || '',
          dib_brand: row.DIB_Brand || ''
        })),
        config
      );
      
      navigate(`/results/${res.job_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start batch job');
      setStarting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Batch Enrichment</h2>
          <p className="text-sm text-slate-500 mt-1">Process a CSV catalogue to discover manufacturer sources at scale.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload & Config (Left Column) */}
        <div className="lg:col-span-1 space-y-6">
          {/* Upload Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center">
              <Database className="w-5 h-5 text-slate-500 mr-2" />
              <h3 className="font-semibold text-slate-700">Data Source</h3>
            </div>
            
            <div className="p-5 space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 transition-colors">
                <input 
                  type="file" 
                  accept=".csv" 
                  onChange={handleFileUpload}
                  className="hidden" 
                  id="csv-upload" 
                />
                <label htmlFor="csv-upload" className="cursor-pointer flex flex-col items-center">
                  <Upload className="w-8 h-8 text-blue-500 mb-2" />
                  <span className="text-sm font-medium text-slate-700">Upload CSV File</span>
                  <span className="text-xs text-slate-500 mt-1">Drag and drop or click to browse</span>
                </label>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="h-px bg-slate-200 flex-1"></div>
                <span className="text-xs text-slate-400 font-medium uppercase">OR</span>
                <div className="h-px bg-slate-200 flex-1"></div>
              </div>
              
              <button 
                onClick={handleLoadSample}
                disabled={loading}
                className="w-full bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center justify-center"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileText className="w-4 h-4 mr-2 text-slate-500" />}
                Load Demo Dataset
              </button>
            </div>
          </div>

          {/* Config Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center">
              <Settings className="w-5 h-5 text-slate-500 mr-2" />
              <h3 className="font-semibold text-slate-700">Processing Configuration</h3>
            </div>
            
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1.5 flex justify-between">
                  <span>Number of Rows to Process</span>
                  <span className="text-blue-600 font-semibold">{config.max_rows}</span>
                </label>
                <input 
                  type="range" 
                  min="1" max="100" 
                  value={config.max_rows}
                  onChange={(e) => setConfig({...config, max_rows: parseInt(e.target.value)})}
                  className="w-full accent-blue-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>1</span>
                  <span>10 (MVP Default)</span>
                  <span>100</span>
                </div>
              </div>
              
              <div className="pt-3 border-t border-slate-100">
                <label className="flex items-center cursor-pointer">
                  <div className="relative">
                    <input 
                      type="checkbox" 
                      className="sr-only"
                      checked={config.gemini_enabled}
                      onChange={(e) => setConfig({...config, gemini_enabled: e.target.checked})}
                    />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${config.gemini_enabled ? 'bg-blue-500' : 'bg-slate-300'}`}></div>
                    <div className={`dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${config.gemini_enabled ? 'transform translate-x-4' : ''}`}></div>
                  </div>
                  <div className="ml-3">
                    <span className="block text-sm font-medium text-slate-700">Gemini AI Validation</span>
                    <span className="block text-xs text-slate-500 mt-0.5">Use LLM for semantic URL selection</span>
                  </div>
                </label>
              </div>
              
              <div className="pt-3 border-t border-slate-100 grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Search Results</label>
                  <select 
                    value={config.search_results_per_product}
                    onChange={(e) => setConfig({...config, search_results_per_product: parseInt(e.target.value)})}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
                  >
                    <option value="3">3 URLs</option>
                    <option value="4">4 URLs</option>
                    <option value="5">5 URLs</option>
                    <option value="10">10 URLs</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Search Delay (s)</label>
                  <select 
                    value={config.search_delay}
                    onChange={(e) => setConfig({...config, search_delay: parseFloat(e.target.value)})}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
                  >
                    <option value="0.5">0.5s</option>
                    <option value="1.0">1.0s</option>
                    <option value="1.5">1.5s (Safe)</option>
                    <option value="2.0">2.0s</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Data Preview & Action (Right Column) */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {!preview && !loading && !error && (
            <div className="h-[400px] border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 bg-slate-50/50">
              <Database className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-lg font-medium text-slate-600">No data loaded</p>
              <p className="text-sm mt-1">Upload a CSV or load the demo dataset to begin.</p>
            </div>
          )}
          
          {loading && !preview && (
            <div className="h-[400px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-4" />
              <p className="text-slate-600 font-medium">Reading data...</p>
            </div>
          )}

          {preview && (
            <>
              {/* Data Quality Report */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center">
                  <h3 className="font-semibold text-slate-800">Dataset Loaded: {preview.filename}</h3>
                  <span className="px-2.5 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-full border border-slate-200">
                    {preview.total_rows.toLocaleString()} rows total
                  </span>
                </div>
                
                <div className="p-5">
                  <h4 className="text-sm font-semibold text-slate-700 mb-3">Pre-processing Data Quality Inspection</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
                      <div className="text-amber-800 text-xl font-bold">{preview.quality.manufacturer_missing}</div>
                      <div className="text-amber-700 text-xs font-medium mt-1">Missing MFR</div>
                    </div>
                    <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
                      <div className="text-amber-800 text-xl font-bold">{preview.quality.placeholder_manufacturer}</div>
                      <div className="text-amber-700 text-xs font-medium mt-1">Placeholder MFR</div>
                    </div>
                    <div className="bg-red-50 border border-red-100 rounded-lg p-3">
                      <div className="text-red-800 text-xl font-bold">{preview.quality.part_number_missing}</div>
                      <div className="text-red-700 text-xs font-medium mt-1">Missing P/N</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                      <div className="text-blue-800 text-xl font-bold">{preview.quality.duplicate_part_numbers}</div>
                      <div className="text-blue-700 text-xs font-medium mt-1">Duplicate P/Ns</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Data Preview Table */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[400px]">
                <div className="px-5 py-3 border-b border-slate-100 bg-slate-50 flex justify-between items-center flex-shrink-0">
                  <h3 className="font-semibold text-slate-700 text-sm">Data Preview (First 5 rows)</h3>
                </div>
                <div className="overflow-auto flex-1 p-0">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50 sticky top-0">
                      <tr>
                        {preview.columns.map((col: string) => (
                          <th key={col} className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider whitespace-nowrap bg-slate-50">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                      {preview.preview.slice(0, 5).map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-50">
                          {preview.columns.map((col: string) => (
                            <td key={col} className="px-4 py-2.5 whitespace-nowrap text-slate-600 truncate max-w-xs" title={row[col]}>
                              {row[col] || <span className="text-slate-300 italic">null</span>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Action Button */}
              <button 
                onClick={handleStartEnrichment}
                disabled={starting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-md hover:shadow-lg flex items-center justify-center text-lg transform hover:-translate-y-0.5 disabled:opacity-70 disabled:hover:translate-y-0"
              >
                {starting ? (
                  <><Loader2 className="w-6 h-6 mr-3 animate-spin" /> Initializing Batch Job...</>
                ) : (
                  <><Play className="w-6 h-6 mr-3 fill-current" /> Start Enrichment ({config.max_rows} products)</>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
