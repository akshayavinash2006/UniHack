"""Ranking service — heuristic URL ranking from search_urls.py with score breakdown."""
import re
from typing import List, Dict, Tuple
from ..models.schemas import ScoreBreakdown, CandidateURL
from ..utils.data_cleaning import extract_domain

# Marketplace/avoid domains — identical to search_urls.py
AVOID_DOMAINS = [
    'amazon.com', 'ebay.com', 'walmart.com', 'homedepot.com', 'lowes.com',
    'wikipedia.org', 'youtube.com', 'youtu.be', 'facebook.com', 'twitter.com',
    'instagram.com', 'pinterest.com', 'linkedin.com', 'crazycattle3d.github.io',
    'calonote.com', 'mapsplatform.google.com', 'tv3.ru', 'dzen.ru'
]

MINIMUM_SCORE_THRESHOLD = 6


def score_candidate(
    mfg_part_num: str,
    manufacturer: str,
    part_desc: str,
    result: Dict[str, str]
) -> Tuple[int, ScoreBreakdown]:
    """Score a single candidate URL. Returns (total_score, breakdown).
    
    Preserves the exact scoring logic from rank_urls_heuristic() in search_urls.py,
    but returns a detailed breakdown.
    """
    manuf_lower = manufacturer.lower()
    part_lower = mfg_part_num.lower()
    desc_lower = part_desc.lower()

    href = result['href'].lower()
    title = result['title'].lower()
    body = result['body'].lower()

    breakdown = ScoreBreakdown()

    # Marketplace penalty
    for domain in AVOID_DOMAINS:
        if domain in href:
            breakdown.marketplace_penalty = -100
            break

    # Part number scoring
    if part_lower:
        clean_part = re.sub(r'[^a-zA-Z0-9]', '', part_lower)
        clean_href = re.sub(r'[^a-zA-Z0-9]', '', href)
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title)
        clean_body = re.sub(r'[^a-zA-Z0-9]', '', body)

        if part_lower in href:
            breakdown.part_number_in_url = 15
        elif clean_part and clean_part in clean_href:
            breakdown.clean_part_in_url = 10

        if part_lower in title:
            breakdown.part_number_in_title = 10
        elif clean_part and clean_part in clean_title:
            breakdown.clean_part_in_title = 5

        if part_lower in body:
            breakdown.part_number_in_body = 5
        elif clean_part and clean_part in clean_body:
            breakdown.clean_part_in_body = 2

    # Manufacturer scoring
    if manuf_lower:
        manuf_words = [w for w in re.split(r'\W+', manuf_lower) if len(w) > 2]
        for w in manuf_words:
            if w in href:
                breakdown.manufacturer_word_in_url += 5
            if w in title:
                breakdown.manufacturer_word_in_title += 3
        if manuf_lower in href:
            breakdown.manufacturer_in_url = 10
        if manuf_lower in title:
            breakdown.manufacturer_in_title = 5

    # Description term scoring
    desc_words = [w for w in re.split(r'\W+', desc_lower) if len(w) > 2 and w not in manuf_lower and w not in part_lower]
    desc_score = 0
    for w in desc_words[:5]:
        if w in title or w in body:
            desc_score += 2
    breakdown.description_term_matches = desc_score

    # PDF bonus
    if href.endswith('.pdf'):
        breakdown.pdf_bonus = 3

    # Calculate total
    total = (
        breakdown.part_number_in_url +
        breakdown.clean_part_in_url +
        breakdown.part_number_in_title +
        breakdown.clean_part_in_title +
        breakdown.part_number_in_body +
        breakdown.clean_part_in_body +
        breakdown.manufacturer_in_url +
        breakdown.manufacturer_word_in_url +
        breakdown.manufacturer_in_title +
        breakdown.manufacturer_word_in_title +
        breakdown.description_term_matches +
        breakdown.pdf_bonus +
        breakdown.marketplace_penalty
    )
    breakdown.total = total

    return total, breakdown


def rank_urls_heuristic(
    mfg_part_num: str,
    manufacturer: str,
    part_desc: str,
    search_results: List[Dict[str, str]]
) -> Tuple[str, List[CandidateURL]]:
    """Rank URLs using heuristic scoring. Returns (best_url, scored_candidates).
    
    Preserves the exact ranking logic and threshold from search_urls.py.
    """
    if not search_results:
        return "", []

    candidates = []
    best_url = ""
    best_score = -100

    for r in search_results:
        score, breakdown = score_candidate(mfg_part_num, manufacturer, part_desc, r)
        domain = extract_domain(r['href'])

        candidate = CandidateURL(
            url=r['href'],
            title=r.get('title', ''),
            snippet=r.get('body', ''),
            domain=domain,
            score=score,
            score_breakdown=breakdown,
            is_selected=False,
            is_manufacturer_domain=bool(manufacturer and manufacturer.lower().split()[0] in domain.lower()) if manufacturer else False,
            has_part_number=bool(mfg_part_num and mfg_part_num.lower() in r['href'].lower()),
            is_marketplace=breakdown.marketplace_penalty < 0,
            is_pdf=r['href'].lower().endswith('.pdf'),
        )
        candidates.append(candidate)

        if score > best_score:
            best_score = score
            best_url = r['href']

    # Apply minimum threshold — identical to search_urls.py
    if best_score < MINIMUM_SCORE_THRESHOLD:
        best_url = ""

    # Mark the selected candidate
    for c in candidates:
        if c.url == best_url and best_url:
            c.is_selected = True

    return best_url, candidates
