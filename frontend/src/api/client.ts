export const API_BASE_URL = 'http://localhost:8000/api';

export interface ProductInput {
  mfg_part_num: string;
  manufacturer: string;
  description: string;
  e1_brand?: string;
  unilog_brand?: string;
  dib_brand?: string;
}

export interface ScoreBreakdown {
  part_number_in_url: number;
  clean_part_in_url: number;
  part_number_in_title: number;
  clean_part_in_title: number;
  part_number_in_body: number;
  clean_part_in_body: number;
  manufacturer_in_url: number;
  manufacturer_word_in_url: number;
  manufacturer_in_title: number;
  manufacturer_word_in_title: number;
  description_term_matches: number;
  pdf_bonus: number;
  marketplace_penalty: number;
  total: number;
}

export interface CandidateURL {
  url: string;
  title: string;
  snippet: string;
  domain: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  is_selected: boolean;
  is_manufacturer_domain: boolean;
  has_part_number: boolean;
  is_marketplace: boolean;
  is_pdf: boolean;
}

export interface GeminiSignals {
  exact_part_match: boolean;
  manufacturer_source: boolean;
  product_specific_page: boolean;
  not_marketplace: boolean;
  raw_response: string;
}

export interface EnrichmentResult {
  mfg_part_num: string;
  manufacturer: string;
  description: string;
  cleaned_manufacturer: string;
  search_query: string;
  manufacturer_url: string;
  reference_urls: string[];
  status: 'matched' | 'review' | 'no_match' | 'error' | 'pending' | 'processing';
  confidence: 'high' | 'medium' | 'low' | 'no_match';
  selection_method: 'gemini' | 'heuristic' | 'none';
  candidate_count: number;
  candidates: CandidateURL[];
  gemini_signals?: GeminiSignals;
  processing_time_ms: number;
  error_message: string;
  needs_review: boolean;
  review_reasons: string[];
}

export interface BatchJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_products: number;
  processed_count: number;
  matched_count: number;
  no_match_count: number;
  review_count: number;
  error_count: number;
  gemini_selections: number;
  heuristic_selections: number;
  results?: EnrichmentResult[];
  current_product: string;
  current_stage: string;
  progress_percent: number;
  latest_result?: Partial<EnrichmentResult>;
}

export interface SystemStatus {
  search_engine_connected: boolean;
  gemini_connected: boolean;
  gemini_api_key_present: boolean;
}

// API methods
export const api = {
  getStatus: async (): Promise<SystemStatus> => {
    const res = await fetch(`${API_BASE_URL}/status`);
    return res.json();
  },

  getSampleData: async () => {
    const res = await fetch(`${API_BASE_URL}/sample-data`);
    return res.json();
  },

  enrichSingle: async (product: ProductInput, maxResults = 4, useGemini = true): Promise<EnrichmentResult> => {
    const res = await fetch(`${API_BASE_URL}/enrich/single?max_results=${maxResults}&use_gemini=${useGemini}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product),
    });
    return res.json();
  },

  uploadCsv: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },

  startBatch: async (products: ProductInput[], config: any) => {
    const res = await fetch(`${API_BASE_URL}/enrich/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products, config }),
    });
    return res.json();
  },

  getJobStatus: async (jobId: string): Promise<BatchJob> => {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    return res.json();
  },

  getJobResults: async (jobId: string) => {
    const res = await fetch(`${API_BASE_URL}/results/${jobId}`);
    return res.json();
  },
};
