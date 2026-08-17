"""Validation service — confidence classification, review flagging, ground-truth comparison."""
from typing import List, Dict, Optional
from ..models.schemas import (
    ConfidenceLevel, ProductStatus, EnrichmentResult, SelectionMethod
)


def classify_confidence(score: int, has_url: bool, method: SelectionMethod) -> ConfidenceLevel:
    """Classify confidence level based on score and selection method."""
    if not has_url:
        return ConfidenceLevel.NO_MATCH
    if method == SelectionMethod.GEMINI:
        return ConfidenceLevel.HIGH
    # Heuristic thresholds
    if score >= 25:
        return ConfidenceLevel.HIGH
    elif score >= 15:
        return ConfidenceLevel.MEDIUM
    elif score >= 6:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.NO_MATCH


def determine_status(confidence: ConfidenceLevel) -> ProductStatus:
    """Map confidence level to product status."""
    if confidence == ConfidenceLevel.HIGH:
        return ProductStatus.MATCHED
    elif confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW):
        return ProductStatus.REVIEW
    return ProductStatus.NO_MATCH


def check_needs_review(result: EnrichmentResult) -> tuple[bool, List[str]]:
    """Check if a product needs human review and provide reasons."""
    reasons = []

    if not result.manufacturer_url:
        reasons.append("No manufacturer URL could be identified")
    
    if result.confidence == ConfidenceLevel.LOW:
        reasons.append("Low confidence score — URL may not be the official source")
    
    if result.confidence == ConfidenceLevel.NO_MATCH:
        reasons.append("No matching manufacturer source found in search results")
    
    if not result.cleaned_manufacturer:
        reasons.append("Manufacturer name is missing or unrecognizable")
    
    if not result.mfg_part_num:
        reasons.append("Part number is missing")
    
    if result.candidate_count > 0 and not result.manufacturer_url:
        reasons.append(f"{result.candidate_count} candidate URLs found but none met confidence threshold")

    if result.selection_method == SelectionMethod.HEURISTIC and result.confidence == ConfidenceLevel.MEDIUM:
        reasons.append("Selected via heuristic ranking — AI validation unavailable")

    needs_review = len(reasons) > 0
    return needs_review, reasons


def compare_with_ground_truth(
    results: List[EnrichmentResult],
    ground_truth: List[Dict[str, str]]
) -> Dict:
    """Compare enrichment results with expected output for validation metrics."""
    # Build lookup by part number
    gt_lookup = {}
    for row in ground_truth:
        pn = row.get("Mfg_Part_Num", "").strip()
        if pn:
            gt_lookup[pn] = row.get("MFR URL", "").strip()

    total_compared = 0
    url_matches = 0
    no_match_agreements = 0
    total_no_match = 0

    for result in results:
        if result.mfg_part_num in gt_lookup:
            total_compared += 1
            expected_url = gt_lookup[result.mfg_part_num]

            if expected_url and result.manufacturer_url:
                # Check if URLs match (domain-level comparison)
                if result.manufacturer_url.lower() == expected_url.lower():
                    url_matches += 1
                elif _domain_match(result.manufacturer_url, expected_url):
                    url_matches += 1
            elif not expected_url and not result.manufacturer_url:
                no_match_agreements += 1
                total_no_match += 1
            elif not expected_url:
                total_no_match += 1

    return {
        "total_compared": total_compared,
        "url_matches": url_matches,
        "url_match_rate": round(url_matches / total_compared * 100, 1) if total_compared > 0 else 0,
        "no_match_agreements": no_match_agreements,
        "no_match_agreement_rate": round(no_match_agreements / total_no_match * 100, 1) if total_no_match > 0 else 0,
    }


def _domain_match(url1: str, url2: str) -> bool:
    """Check if two URLs are from the same domain."""
    try:
        from urllib.parse import urlparse
        d1 = urlparse(url1).netloc.replace("www.", "")
        d2 = urlparse(url2).netloc.replace("www.", "")
        return d1 == d2
    except Exception:
        return False
