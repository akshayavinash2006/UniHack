"""Enrichment API — single product and batch enrichment endpoints."""
import uuid
import asyncio
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from ..models.schemas import (
    ProductInput, EnrichmentResult, BatchRequest, BatchJob, BatchConfig,
    JobStatus, DataQualityReport
)
from ..services.enrichment_service import enrich_single_product, enrich_batch
from ..utils.data_cleaning import parse_csv_content, analyze_data_quality

router = APIRouter()

# In-memory job storage
jobs: dict[str, BatchJob] = {}


def get_jobs_store() -> dict[str, BatchJob]:
    return jobs


@router.post("/enrich/single")
def enrich_single(product: ProductInput, max_results: int = 4, use_gemini: bool = True) -> EnrichmentResult:
    """Enrich a single product synchronously."""
    return enrich_single_product(product, max_results=max_results, use_gemini=use_gemini)


@router.post("/enrich/batch")
async def enrich_batch_endpoint(request: BatchRequest, background_tasks: BackgroundTasks):
    """Start a batch enrichment job in the background."""
    job_id = str(uuid.uuid4())[:8]
    job = BatchJob(
        job_id=job_id,
        total_products=len(request.products),
        config=request.config,
    )
    jobs[job_id] = job

    # Run enrichment in background
    background_tasks.add_task(
        enrich_batch,
        job,
        request.products,
    )

    return {"job_id": job_id, "status": "started", "total_products": len(request.products)}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and return preview + quality report."""
    content = await file.read()
    text = content.decode("utf-8")

    try:
        fieldnames, rows = parse_csv_content(text)
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

    # Validate required columns
    required = {"Mfg_Part_Num"}
    missing_cols = required - set(fieldnames)
    if missing_cols:
        return {"error": f"Missing required columns: {', '.join(missing_cols)}"}

    quality = analyze_data_quality(rows, file.filename or "uploaded.csv")

    return {
        "filename": file.filename,
        "columns": fieldnames,
        "total_rows": len(rows),
        "preview": rows[:20],
        "quality": quality,
        "all_rows": rows,
    }
