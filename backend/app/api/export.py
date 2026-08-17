"""Export API — CSV and JSON export of results."""
import csv
import io
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


def _get_jobs_store():
    from .enrichment import jobs
    return jobs


@router.get("/results/{job_id}/export/csv")
def export_csv(job_id: str):
    """Export results as CSV."""
    jobs = _get_jobs_store()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    output = io.StringIO()

    fieldnames = [
        "Mfg_Part_Num", "Part_Manuf", "Part_Desc", "MFR URL",
        "Ref URL 1", "Ref URL 2", "Ref URL 3",
        "Confidence", "Selection Method", "Search Query", "Status"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for result in job.results:
        ref_urls = result.reference_urls + [""] * 3
        writer.writerow({
            "Mfg_Part_Num": result.mfg_part_num,
            "Part_Manuf": result.manufacturer,
            "Part_Desc": result.description,
            "MFR URL": result.manufacturer_url,
            "Ref URL 1": ref_urls[0],
            "Ref URL 2": ref_urls[1],
            "Ref URL 3": ref_urls[2],
            "Confidence": result.confidence.value,
            "Selection Method": result.selection_method.value,
            "Search Query": result.search_query,
            "Status": result.status.value,
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=enrichment_results_{job_id}.csv"}
    )


@router.get("/results/{job_id}/export/json")
def export_json(job_id: str):
    """Export results as JSON."""
    jobs = _get_jobs_store()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    data = {
        "job_id": job.job_id,
        "total_products": job.total_products,
        "results": [r.model_dump() for r in job.results],
    }

    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=enrichment_results_{job_id}.json"}
    )
