"""Data cleaning utilities — preserves logic from search_urls.py."""
import re
import csv
import io
from typing import List, Dict, Any, Tuple

# Placeholder values treated as empty
PLACEHOLDER_VALUES = {
    "--",
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "-",
    "",
    "n/a",
    "na",
    "none",
    "unknown",
}


def clean_manufacturer(manuf: str) -> str:
    """Cleans manufacturer names like 'Freud Inc (2435)' to 'Freud Inc'.
    
    Preserves the exact logic from search_urls.py.
    """
    if not manuf or manuf.strip().lower() in PLACEHOLDER_VALUES:
        return ""
    # Remove text in parenthesis at the end (numeric codes)
    cleaned = re.sub(r'\s*\(\d+\)\s*$', '', manuf)
    # Remove text in parenthesis at the end (alphanumeric codes like JAMIN)
    cleaned = re.sub(r'\s*\([A-Z0-9]+\)\s*$', '', cleaned)
    return cleaned.strip()


def is_placeholder(value: str) -> bool:
    """Check if a value is a known placeholder."""
    if not value:
        return True
    return value.strip().lower() in PLACEHOLDER_VALUES


def build_search_query(mfg_part_num: str, cleaned_manufacturer: str, description: str) -> str:
    """Build a search query from product fields.
    
    Preserves the exact logic from search_urls.py main().
    """
    query_parts = []
    if cleaned_manufacturer:
        query_parts.append(cleaned_manufacturer)
    if mfg_part_num:
        query_parts.append(mfg_part_num)

    # Clean description to avoid redundancy with part number
    clean_desc = description
    if mfg_part_num and clean_desc.lower().startswith(mfg_part_num.lower()):
        clean_desc = clean_desc[len(mfg_part_num):].strip()

    # Remove any leading special characters/whitespace
    clean_desc = re.sub(r'^[\s\-\"\']+', '', clean_desc).strip()
    if clean_desc:
        query_parts.append(clean_desc)

    return " ".join(query_parts)


def parse_csv_content(content: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Parse CSV content string and return (fieldnames, rows)."""
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []
    rows = list(reader)
    return list(fieldnames), rows


def parse_csv_file(filepath: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Parse a CSV file and return (fieldnames, rows)."""
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return list(fieldnames), rows


def extract_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def analyze_data_quality(rows: List[Dict[str, str]], filename: str = "") -> Dict[str, Any]:
    """Analyze input data quality and return a report."""
    total = len(rows)
    manuf_missing = 0
    part_missing = 0
    desc_missing = 0
    placeholder_manuf = 0
    placeholder_brand = 0
    part_numbers = []

    for row in rows:
        part_num = row.get("Mfg_Part_Num", "").strip()
        manuf = row.get("Part_Manuf", "").strip()
        desc = row.get("Part_Desc", "").strip()
        e1 = row.get("E1_Brand", "").strip()
        unilog = row.get("Unilog_Brand", "").strip()
        dib = row.get("DIB_Brand", "").strip()

        if not part_num:
            part_missing += 1
        else:
            part_numbers.append(part_num)

        if not manuf or manuf == "-":
            manuf_missing += 1
        elif is_placeholder(manuf):
            placeholder_manuf += 1

        if not desc:
            desc_missing += 1

        if is_placeholder(e1) or is_placeholder(unilog) or is_placeholder(dib):
            placeholder_brand += 1

    # Count duplicates
    seen = set()
    dupes = 0
    for pn in part_numbers:
        if pn in seen:
            dupes += 1
        seen.add(pn)

    return {
        "total_rows": total,
        "manufacturer_missing": manuf_missing,
        "part_number_missing": part_missing,
        "description_missing": desc_missing,
        "placeholder_manufacturer": placeholder_manuf,
        "placeholder_brand": placeholder_brand,
        "duplicate_part_numbers": dupes,
        "filename": filename,
    }
