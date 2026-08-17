"""Enrichment service — orchestrates the full pipeline for single and batch processing."""
import time
import asyncio
from typing import List, Dict, Any, Optional, Callable
from ..models.schemas import (
    ProductInput, EnrichmentResult, BatchJob, BatchConfig,
    ProductStatus, SelectionMethod, GeminiSignals, JobStatus,
    CandidateURL
)
from ..utils.data_cleaning import clean_manufacturer, build_search_query
from .search_service import search_part_urls
from .gemini_service import pick_best_url_gemini, is_gemini_available
from .ranking_service import rank_urls_heuristic, score_candidate
from .validation_service import classify_confidence, determine_status, check_needs_review
from ..utils.data_cleaning import extract_domain


def enrich_single_product(
    product: ProductInput,
    max_results: int = 4,
    use_gemini: bool = True,
) -> EnrichmentResult:
    """Run the full enrichment pipeline for a single product.
    
    Orchestrates: clean → query → search → AI/heuristic → validate → result
    """
    start_time = time.time()

    # Initialize result
    result = EnrichmentResult(
        mfg_part_num=product.mfg_part_num,
        manufacturer=product.manufacturer,
        description=product.description,
        e1_brand=product.e1_brand,
        unilog_brand=product.unilog_brand,
        dib_brand=product.dib_brand,
    )

    # Step 1: Clean manufacturer
    result.cleaned_manufacturer = clean_manufacturer(product.manufacturer)

    # Step 2: Build search query
    result.search_query = build_search_query(
        product.mfg_part_num,
        result.cleaned_manufacturer,
        product.description
    )

    if not result.search_query.strip():
        result.status = ProductStatus.ERROR
        result.error_message = "Cannot build search query — insufficient product data"
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        needs_review, reasons = check_needs_review(result)
        result.needs_review = needs_review
        result.review_reasons = reasons
        return result

    # Step 3: Web search
    try:
        search_results = search_part_urls(result.search_query, max_results=max_results)
    except Exception as e:
        result.status = ProductStatus.ERROR
        result.error_message = f"Search failed: {str(e)}"
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        needs_review, reasons = check_needs_review(result)
        result.needs_review = needs_review
        result.review_reasons = reasons
        return result

    if not search_results:
        result.status = ProductStatus.NO_MATCH
        result.error_message = "No search results returned"
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        needs_review, reasons = check_needs_review(result)
        result.needs_review = needs_review
        result.review_reasons = reasons
        return result

    # Step 4: Score all candidates (always do this for the UI)
    _, scored_candidates = rank_urls_heuristic(
        product.mfg_part_num,
        result.cleaned_manufacturer,
        product.description,
        search_results
    )
    result.candidates = scored_candidates
    result.candidate_count = len(scored_candidates)

    # Step 5: Try Gemini first if enabled
    mfr_url = ""
    selection_method = SelectionMethod.NONE

    if use_gemini and is_gemini_available():
        gemini_url, signals = pick_best_url_gemini(
            product.mfg_part_num,
            result.cleaned_manufacturer,
            product.description,
            search_results
        )
        if gemini_url:
            mfr_url = gemini_url
            selection_method = SelectionMethod.GEMINI
            if signals:
                result.gemini_signals = GeminiSignals(**signals)
            # Mark the Gemini-selected candidate
            for c in result.candidates:
                c.is_selected = (c.url == mfr_url)

    # Step 6: Fallback to heuristic if Gemini didn't select
    if not mfr_url:
        # Use the already-scored candidates
        best_score = -100
        for c in scored_candidates:
            if c.score > best_score:
                best_score = c.score
                mfr_url = c.url

        # Apply minimum threshold
        if best_score < 6:
            mfr_url = ""
        else:
            selection_method = SelectionMethod.HEURISTIC
            for c in result.candidates:
                c.is_selected = (c.url == mfr_url)

    # Step 7: Set URL and reference URLs
    result.manufacturer_url = mfr_url
    result.selection_method = selection_method

    # Reference URLs = all non-selected candidates
    ref_urls = []
    for c in scored_candidates:
        if c.url != mfr_url and len(ref_urls) < 3:
            ref_urls.append(c.url)
    result.reference_urls = ref_urls

    # Step 8: Classify confidence and status
    best_candidate_score = 0
    for c in scored_candidates:
        if c.url == mfr_url:
            best_candidate_score = c.score
            break

    result.confidence = classify_confidence(
        best_candidate_score, bool(mfr_url), selection_method
    )
    result.status = determine_status(result.confidence)

    # Step 9: Check review needs
    needs_review, reasons = check_needs_review(result)
    result.needs_review = needs_review
    result.review_reasons = reasons

    result.processing_time_ms = int((time.time() - start_time) * 1000)
    return result


async def enrich_batch(
    job: BatchJob,
    products: List[ProductInput],
    on_progress: Optional[Callable] = None,
):
    """Run enrichment for a batch of products asynchronously.
    
    Updates the job object in-place with progress.
    """
    job.status = JobStatus.RUNNING
    job.total_products = len(products)

    # Deduplicate by part number
    seen_parts = set()
    unique_products = []
    for p in products:
        if p.mfg_part_num and p.mfg_part_num not in seen_parts:
            seen_parts.add(p.mfg_part_num)
            unique_products.append(p)
        elif not p.mfg_part_num:
            unique_products.append(p)

    job.total_products = len(unique_products)

    for i, product in enumerate(unique_products):
        job.current_product = product.mfg_part_num or f"Product {i+1}"
        job.current_stage = "searching"

        try:
            # Run enrichment in thread pool to not block the event loop
            result = await asyncio.to_thread(
                enrich_single_product,
                product,
                job.config.search_results_per_product,
                job.config.gemini_enabled,
            )

            job.results.append(result)
            job.processed_count = i + 1

            # Update counters
            if result.status == ProductStatus.MATCHED:
                job.matched_count += 1
            elif result.status == ProductStatus.NO_MATCH:
                job.no_match_count += 1
            elif result.status == ProductStatus.REVIEW:
                job.review_count += 1
            elif result.status == ProductStatus.ERROR:
                job.error_count += 1

            if result.selection_method == SelectionMethod.GEMINI:
                job.gemini_selections += 1
            elif result.selection_method == SelectionMethod.HEURISTIC:
                job.heuristic_selections += 1

            if result.needs_review:
                job.review_count = sum(1 for r in job.results if r.needs_review)

            job.current_stage = "completed"

        except Exception as e:
            error_result = EnrichmentResult(
                mfg_part_num=product.mfg_part_num,
                manufacturer=product.manufacturer,
                description=product.description,
                status=ProductStatus.ERROR,
                error_message=str(e),
            )
            job.results.append(error_result)
            job.processed_count = i + 1
            job.error_count += 1

        # Respect search delay
        if i < len(unique_products) - 1:
            await asyncio.sleep(job.config.search_delay)

    job.status = JobStatus.COMPLETED
    job.completed_at = time.time()
    job.current_product = ""
    job.current_stage = "done"
