import React, { useState } from 'react';
import { api } from '../api/client';
import type { ProductInput, EnrichmentResult } from '../api/client';
import { Search, Loader2, CheckCircle2, AlertTriangle, XCircle, ChevronRight, ExternalLink, Cpu } from 'lucide-react';

export const SingleProduct: React.FC = () => {
  const [input, setInput] = useState<ProductInput>({
    mfg_part_num: 'PDSH4816AF',
    manufacturer: 'Frigidaire',
    description: 'PDSH4816AF Dishwasher SS - Display Only'
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EnrichmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEnrich = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.enrichSingle(input);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to enrich product');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'high': return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700 border border-green-200">High Confidence</span>;
      case 'medium': return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-700 border border-amber-200">Medium Confidence</span>;
      case 'low': return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700 border border-red-200">Low Confidence</span>;
      default: return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">No Match</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Single Product Enrichment</h2>
          <p className="text-sm text-slate-500 mt-1">Manually inspect the URL discovery pipeline for a single item.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
              <h3 className="font-semibold text-slate-700">Input Data</h3>
            </div>
            <form onSubmit={handleEnrich} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Manufacturer</label>
                <input 
                  type="text" 
                  value={input.manufacturer}
                  onChange={(e) => setInput({...input, manufacturer: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Part Number</label>
                <input 
                  type="text" 
                  value={input.mfg_part_num}
                  onChange={(e) => setInput({...input, mfg_part_num: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Description</label>
                <textarea 
                  value={input.description}
                  onChange={(e) => setInput({...input, description: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm min-h-[80px]"
                />
              </div>
              <button 
                type="submit" 
                disabled={loading}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center shadow-sm disabled:opacity-70"
              >
                {loading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing Pipeline...</>
                ) : (
                  <><Search className="w-4 h-4 mr-2" /> Find Manufacturer Source</>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md mb-6">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="h-full min-h-[300px] border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 bg-slate-50/50">
              <Search className="h-10 w-10 mb-3 opacity-20" />
              <p>Enter product details and search to view pipeline results.</p>
            </div>
          )}

          {loading && (
            <div className="h-full min-h-[300px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col items-center justify-center space-y-4">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-4 border-slate-100"></div>
                <div className="w-12 h-12 rounded-full border-4 border-blue-600 border-t-transparent animate-spin absolute inset-0"></div>
              </div>
              <div className="text-center">
                <h3 className="text-sm font-semibold text-slate-700">Enrichment Pipeline Active</h3>
                <div className="flex items-center text-xs text-slate-500 mt-2 space-x-2">
                  <span>Query Generation</span> <ChevronRight className="w-3 h-3" />
                  <span>Web Search</span> <ChevronRight className="w-3 h-3" />
                  <span>AI Scoring</span>
                </div>
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-6">
              {/* Final Decision Card */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                  <h3 className="font-semibold text-slate-700 flex items-center">
                    <CheckCircle2 className={`w-5 h-5 mr-2 ${result.status === 'matched' ? 'text-green-500' : 'text-amber-500'}`} />
                    Final Result
                  </h3>
                  {getConfidenceBadge(result.confidence)}
                </div>
                
                <div className="p-5">
                  <div className="mb-4">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Search Query</span>
                    <div className="mt-1 p-2 bg-slate-50 rounded text-sm text-slate-700 font-mono border border-slate-100">
                      {result.search_query}
                    </div>
                  </div>

                  <div className="flex flex-col space-y-4">
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Manufacturer URL</span>
                      {result.manufacturer_url ? (
                        <a href={result.manufacturer_url} target="_blank" rel="noreferrer" className="mt-1 flex items-center text-sm font-medium text-blue-600 hover:underline break-all">
                          {result.manufacturer_url} <ExternalLink className="w-3 h-3 ml-1 flex-shrink-0" />
                        </a>
                      ) : (
                        <p className="mt-1 text-sm text-slate-500 italic">No valid manufacturer source found.</p>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-xs text-slate-500 block">Selection Method</span>
                        <div className="mt-1 flex items-center">
                          {result.selection_method === 'gemini' ? (
                            <><Cpu className="w-4 h-4 text-blue-600 mr-1.5" /> <span className="text-sm font-medium text-slate-700">AI Semantic Validation</span></>
                          ) : result.selection_method === 'heuristic' ? (
                            <><Search className="w-4 h-4 text-slate-600 mr-1.5" /> <span className="text-sm font-medium text-slate-700">Heuristic Ranking</span></>
                          ) : (
                            <span className="text-sm font-medium text-slate-700">None</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-xs text-slate-500 block">Processing Time</span>
                        <span className="mt-1 text-sm font-medium text-slate-700 block">{result.processing_time_ms}ms</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Needs Review Alert */}
              {result.needs_review && (
                <div className="bg-amber-50 rounded-xl shadow-sm border border-amber-200 p-5">
                  <h3 className="font-semibold text-amber-800 flex items-center mb-3">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Flagged for Human Review
                  </h3>
                  <ul className="list-disc list-inside text-sm text-amber-700 space-y-1">
                    {result.review_reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Candidate Results */}
              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-3">Candidate Sources ({result.candidate_count})</h3>
                <div className="space-y-4">
                  {result.candidates.map((c, i) => (
                    <div key={i} className={`p-4 rounded-xl border transition-all ${c.is_selected ? 'bg-blue-50/50 border-blue-200 shadow-sm' : 'bg-white border-slate-200 hover-card'}`}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1 min-w-0 pr-4">
                          {c.is_selected && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-700 mb-2 border border-blue-200">
                              Selected Source
                            </span>
                          )}
                          <h4 className="font-medium text-slate-800 text-sm line-clamp-1" title={c.title}>{c.title}</h4>
                          <a href={c.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline break-all line-clamp-1 mt-0.5">{c.url}</a>
                          <p className="text-xs text-slate-500 mt-2 line-clamp-2">{c.snippet}</p>
                        </div>
                        
                        <div className="flex flex-col items-end flex-shrink-0">
                          <div className="text-xs font-semibold text-slate-500 mb-1">Score</div>
                          <div className={`text-xl font-bold ${c.score > 20 ? 'text-green-600' : c.score > 5 ? 'text-amber-600' : 'text-slate-400'}`}>
                            {c.score}
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <div className="flex items-center text-xs">
                          {c.has_part_number ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mr-1.5" /> : <XCircle className="w-3.5 h-3.5 text-slate-300 mr-1.5" />}
                          <span className={c.has_part_number ? 'text-slate-700' : 'text-slate-400'}>Part No. Match</span>
                        </div>
                        <div className="flex items-center text-xs">
                          {c.is_manufacturer_domain ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mr-1.5" /> : <XCircle className="w-3.5 h-3.5 text-slate-300 mr-1.5" />}
                          <span className={c.is_manufacturer_domain ? 'text-slate-700' : 'text-slate-400'}>MFR Domain</span>
                        </div>
                        <div className="flex items-center text-xs">
                          {c.is_marketplace ? <XCircle className="w-3.5 h-3.5 text-red-500 mr-1.5" /> : <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mr-1.5" />}
                          <span className={c.is_marketplace ? 'text-red-600 line-through' : 'text-slate-700'}>Marketplace</span>
                        </div>
                        <div className="flex items-center text-xs">
                          {c.is_pdf ? <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 mr-1.5" /> : <XCircle className="w-3.5 h-3.5 text-slate-300 mr-1.5" />}
                          <span className={c.is_pdf ? 'text-slate-700' : 'text-slate-400'}>PDF File</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
};
