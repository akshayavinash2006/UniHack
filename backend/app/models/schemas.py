"""Pydantic models for the enrichment API."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import time


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_MATCH = "no_match"


class SelectionMethod(str, Enum):
    GEMINI = "gemini"
    HEURISTIC = "heuristic"
    NONE = "none"


class ProductStatus(str, Enum):
    MATCHED = "matched"
    REVIEW = "review"
    NO_MATCH = "no_match"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Input Models ---

class ProductInput(BaseModel):
    mfg_part_num: str = ""
    manufacturer: str = ""
    description: str = ""
    e1_brand: str = ""
    unilog_brand: str = ""
    dib_brand: str = ""


class BatchConfig(BaseModel):
    max_rows: int = 10
    search_results_per_product: int = 4
    search_delay: float = 1.5
    gemini_enabled: bool = True


class BatchRequest(BaseModel):
    products: List[ProductInput]
    config: BatchConfig = BatchConfig()


# --- Scoring Models ---

class ScoreBreakdown(BaseModel):
    part_number_in_url: int = 0
    clean_part_in_url: int = 0
    part_number_in_title: int = 0
    clean_part_in_title: int = 0
    part_number_in_body: int = 0
    clean_part_in_body: int = 0
    manufacturer_in_url: int = 0
    manufacturer_word_in_url: int = 0
    manufacturer_in_title: int = 0
    manufacturer_word_in_title: int = 0
    description_term_matches: int = 0
    pdf_bonus: int = 0
    marketplace_penalty: int = 0
    total: int = 0


class CandidateURL(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""
    domain: str = ""
    score: int = 0
    score_breakdown: ScoreBreakdown = ScoreBreakdown()
    is_selected: bool = False
    is_manufacturer_domain: bool = False
    has_part_number: bool = False
    is_marketplace: bool = False
    is_pdf: bool = False


class GeminiSignals(BaseModel):
    exact_part_match: bool = False
    manufacturer_source: bool = False
    product_specific_page: bool = False
    not_marketplace: bool = False
    raw_response: str = ""


# --- Result Models ---

class EnrichmentResult(BaseModel):
    mfg_part_num: str
    manufacturer: str
    description: str
    cleaned_manufacturer: str = ""
    search_query: str = ""
    manufacturer_url: str = ""
    reference_urls: List[str] = []
    status: ProductStatus = ProductStatus.PENDING
    confidence: ConfidenceLevel = ConfidenceLevel.NO_MATCH
    selection_method: SelectionMethod = SelectionMethod.NONE
    candidate_count: int = 0
    candidates: List[CandidateURL] = []
    gemini_signals: Optional[GeminiSignals] = None
    processing_time_ms: int = 0
    error_message: str = ""
    needs_review: bool = False
    review_reasons: List[str] = []

    # Original input fields preserved
    e1_brand: str = ""
    unilog_brand: str = ""
    dib_brand: str = ""


# --- Job Models ---

class BatchJob(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    total_products: int = 0
    processed_count: int = 0
    matched_count: int = 0
    no_match_count: int = 0
    review_count: int = 0
    error_count: int = 0
    gemini_selections: int = 0
    heuristic_selections: int = 0
    results: List[EnrichmentResult] = []
    config: BatchConfig = BatchConfig()
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    current_product: str = ""
    current_stage: str = ""


# --- Data Quality Models ---

class DataQualityReport(BaseModel):
    total_rows: int = 0
    manufacturer_missing: int = 0
    part_number_missing: int = 0
    description_missing: int = 0
    placeholder_manufacturer: int = 0
    placeholder_brand: int = 0
    duplicate_part_numbers: int = 0
    detected_columns: List[str] = []
    filename: str = ""


# --- Status Models ---

class SystemStatus(BaseModel):
    search_engine_connected: bool = True
    gemini_connected: bool = False
    gemini_api_key_present: bool = False


# --- Analytics Models ---

class AnalyticsSummary(BaseModel):
    total_processed: int = 0
    matched: int = 0
    no_match: int = 0
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    gemini_selected: int = 0
    heuristic_selected: int = 0
    needs_review: int = 0
    manufacturer_source: int = 0
    pdf_source: int = 0
    other_source: int = 0
    marketplace_rejected: int = 0
