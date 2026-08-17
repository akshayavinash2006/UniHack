"""Jobs API — job status, SSE streaming, and results."""
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import BatchJob, JobStatus

router = APIRouter()


def _get_jobs_store():
    """Import jobs store from enrichment API."""
    from .enrichment import jobs
    return jobs


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get job status and progress."""
    jobs = _get_jobs_store()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_products": job.total_products,
        "processed_count": job.processed_count,
        "matched_count": job.matched_count,
        "no_match_count": job.no_match_count,
        "review_count": job.review_count,
        "error_count": job.error_count,
        "gemini_selections": job.gemini_selections,
        "heuristic_selections": job.heuristic_selections,
        "current_product": job.current_product,
        "current_stage": job.current_stage,
        "progress_percent": round(job.processed_count / job.total_products * 100, 1) if job.total_products > 0 else 0,
    }


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """SSE stream for live progress updates."""
    jobs = _get_jobs_store()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_count = -1
        while True:
            job = jobs.get(job_id)
            if not job:
                break

            if job.processed_count != last_count or job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                last_count = job.processed_count
                data = {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "total_products": job.total_products,
                    "processed_count": job.processed_count,
                    "matched_count": job.matched_count,
                    "no_match_count": job.no_match_count,
                    "review_count": job.review_count,
                    "error_count": job.error_count,
                    "gemini_selections": job.gemini_selections,
                    "heuristic_selections": job.heuristic_selections,
                    "current_product": job.current_product,
                    "current_stage": job.current_stage,
                    "progress_percent": round(job.processed_count / job.total_products * 100, 1) if job.total_products > 0 else 0,
                }
                # Include latest result if available
                if job.results:
                    latest = job.results[-1]
                    data["latest_result"] = {
                        "mfg_part_num": latest.mfg_part_num,
                        "manufacturer": latest.manufacturer,
                        "status": latest.status.value,
                        "confidence": latest.confidence.value,
                        "manufacturer_url": latest.manufacturer_url,
                        "selection_method": latest.selection_method.value,
                        "candidate_count": latest.candidate_count,
                    }

                yield f"data: {json.dumps(data)}\n\n"

                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/results/{job_id}")
def get_job_results(job_id: str):
    """Get full results for a completed job."""
    jobs = _get_jobs_store()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_products": job.total_products,
        "processed_count": job.processed_count,
        "matched_count": job.matched_count,
        "no_match_count": job.no_match_count,
        "review_count": job.review_count,
        "error_count": job.error_count,
        "gemini_selections": job.gemini_selections,
        "heuristic_selections": job.heuristic_selections,
        "results": [r.model_dump() for r in job.results],
        "config": job.config.model_dump(),
    }
