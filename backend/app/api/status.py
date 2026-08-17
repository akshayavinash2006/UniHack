"""Status API — system health and sample data."""
import os
from fastapi import APIRouter
from ..models.schemas import SystemStatus
from ..services.gemini_service import is_gemini_available
from ..utils.data_cleaning import parse_csv_file, analyze_data_quality

router = APIRouter()

# Resolve data directory relative to project root
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")


@router.get("/status")
def get_system_status() -> SystemStatus:
    """Get system health status."""
    return SystemStatus(
        search_engine_connected=True,
        gemini_connected=is_gemini_available(),
        gemini_api_key_present=is_gemini_available(),
    )


@router.get("/sample-data")
def get_sample_data():
    """Load the bundled sample dataset."""
    sample_path = os.path.join(DATA_DIR, "Unihack_ Sample Dataset - Input.csv")
    if not os.path.exists(sample_path):
        return {"error": "Sample dataset not found", "path": sample_path}

    fieldnames, rows = parse_csv_file(sample_path)
    quality = analyze_data_quality(rows, "Unihack_ Sample Dataset - Input.csv")

    return {
        "filename": "Unihack_ Sample Dataset - Input.csv",
        "columns": fieldnames,
        "total_rows": len(rows),
        "preview": rows[:20],
        "quality": quality,
    }


@router.get("/ground-truth")
def get_ground_truth():
    """Load the expected output for validation."""
    gt_path = os.path.join(DATA_DIR, "Unihack_ Expected Output - Delivery Format.csv")
    if not os.path.exists(gt_path):
        return {"available": False}

    fieldnames, rows = parse_csv_file(gt_path)
    return {
        "available": True,
        "total_rows": len(rows),
        "rows": rows,
    }
