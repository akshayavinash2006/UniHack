import os
import csv
import re
import asyncio
import time
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Try to import aiohttp and bs4, provide instructions if they are missing
try:
    # pyrefly: ignore [missing-import]
    import aiohttp
    from bs4 import BeautifulSoup
except ImportError:
    print("Required packages missing. Installing aiohttp and beautifulsoup4...")
    os.system("pip install aiohttp beautifulsoup4")
    # pyrefly: ignore [missing-import]
    import aiohttp
    from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

INPUT_CSV = "Unihack_ Output.csv"
OUTPUT_CSV = "Unihack_ Verified_Output.csv"
MAX_CONCURRENT_REQUESTS = 5  # limit concurrency to avoid IP blocking
TIMEOUT_SECONDS = 8

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def fetch_page_metadata(session: aiohttp.ClientSession, url: str) -> Dict[str, str]:
    """Fetches a URL asynchronously and returns its title, description, and h1 headers."""
    metadata = {"url": url, "title": "", "description": "", "h1": "", "status": "Error"}
    if not url or not url.startswith("http"):
        return metadata

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with session.get(url, headers=headers, timeout=TIMEOUT_SECONDS, allow_redirects=True) as response:
            metadata["status"] = str(response.status)
            if response.status == 200:
                html = await response.text(errors='ignore')
                soup = BeautifulSoup(html, "html.parser")
                
                # Title
                title_tag = soup.find("title")
                metadata["title"] = title_tag.text.strip() if title_tag else ""
                
                # Meta description
                desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                metadata["description"] = desc_tag.get("content", "").strip() if desc_tag else ""
                
                # H1 tags
                h1_tags = soup.find_all("h1")
                metadata["h1"] = " | ".join([h.text.strip() for h in h1_tags if h.text])[:200]
                
    except Exception as e:
        metadata["status"] = f"Failed ({type(e).__name__})"
        
    return metadata

def calculate_heuristic_score(mfg_part_num: str, manufacturer: str, part_desc: str, meta: Dict[str, str]) -> Tuple[float, List[str]]:
    """Calculates a validation score based on matching keywords in page metadata."""
    score = 0.0
    matches = []
    
    title = meta.get("title", "").lower()
    description = meta.get("description", "").lower()
    h1 = meta.get("h1", "").lower()
    
    part_lower = mfg_part_num.lower()
    manuf_lower = manufacturer.lower()
    
    # Exclude avoided domains/social media
    avoid_domains = ['wikipedia.org', 'youtube.com', 'youtu.be', 'facebook.com', 'twitter.com', 'instagram.com']
    for domain in avoid_domains:
        if domain in meta.get("url", "").lower():
            return -100.0, ["Disallowed Domain"]

    if not title and not description and not h1:
        return 0.0, ["No Metadata Extracted"]

    # 1. Check for Part Number (high importance)
    if part_lower:
        clean_part = re.sub(r'[^a-zA-Z0-9]', '', part_lower)
        
        # Exact check
        if part_lower in title:
            score += 40
            matches.append("Part # in Title")
        elif clean_part in re.sub(r'[^a-zA-Z0-9]', '', title):
            score += 30
            matches.append("Clean Part # in Title")
            
        if part_lower in h1:
            score += 30
            matches.append("Part # in H1")
            
        if part_lower in description:
            score += 20
            matches.append("Part # in Description")
            
    # 2. Check for Manufacturer
    if manuf_lower:
        manuf_words = [w for w in re.split(r'\W+', manuf_lower) if len(w) > 2]
        word_matches = 0
        for w in manuf_words:
            if w in title or w in h1 or w in description:
                word_matches += 1
        
        if word_matches > 0:
            score += min(20, word_matches * 10)
            matches.append(f"Mfr Keywords Match ({word_matches})")
            
    # 3. Check description terms
    desc_words = [w for w in re.split(r'\W+', part_desc.lower()) if len(w) > 3 and w not in manuf_lower and w not in part_lower]
    desc_matches = 0
    for w in desc_words[:5]:
        if w in title or w in description:
            score += 5
            desc_matches += 1
    if desc_matches > 0:
        matches.append(f"Desc Keywords Match ({desc_matches})")
        
    return score, matches

def ask_gemini_to_verify(mfg_part_num: str, manufacturer: str, part_desc: str, mfr_url: str, metadata_list: List[Dict[str, str]]) -> Tuple[str, str]:
    """Uses Gemini to perform the final cross-source consensus verification check."""
    if not api_key:
        return "UNVERIFIED", "Gemini API key not configured"
        
    try:
        sources_str = ""
        for i, meta in enumerate(metadata_list):
            sources_str += f"Source [{i+1}] (URL: {meta['url']}):\n"
            sources_str += f"  Status: {meta['status']}\n"
            sources_str += f"  Title: {meta['title']}\n"
            sources_str += f"  Description: {meta['description']}\n"
            sources_str += f"  H1: {meta['h1']}\n\n"
            
        prompt = f"""
You are a product verification agent. Your job is to verify if the primary manufacturer URL (MFR URL) actually links to the exact product specified below, by evaluating the scraped page details of the MFR URL and other reference sources.

Target Product Info:
- Part Number: {mfg_part_num}
- Manufacturer: {manufacturer}
- Description: {part_desc}
- Primary MFR URL to Verify: {mfr_url}

Scraped Data from all sources:
{sources_str}

Evaluate the evidence. You must output a JSON response in the following format:
{{
  "status": "VERIFIED" | "PARTIAL" | "MISMATCH" | "UNVERIFIED",
  "reason": "Detailed explanation of why this verdict was reached based on the source titles and details."
}}

Status Guidance:
- "VERIFIED": If the scraped metadata from the MFR URL (or strongly correlated reference pages) matches the exact part number and manufacturer name.
- "PARTIAL": If the URL points to the correct manufacturer site and brand category, but is a general landing page, collection, or search page rather than the specific product detail page.
- "MISMATCH": If the page title/description clearly refers to a completely different part number or product.
- "UNVERIFIED": If the page could not be loaded, returns a 404, or the information is too scarce to tell.

Return ONLY the raw JSON block. No markdown wrapper (do not wrap in ```json).
"""
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Basic JSON parsing
        import json
        # Clean potential markdown wrappers
        text_clean = re.sub(r'^```json\s*', '', text)
        text_clean = re.sub(r'\s*```$', '', text_clean).strip()
        
        data = json.loads(text_clean)
        return data.get("status", "UNVERIFIED"), data.get("reason", "No reason provided")
    except Exception as e:
        return "UNVERIFIED", f"Gemini Verification Error: {e}"

async def verify_row(session: aiohttp.ClientSession, row: Dict[str, str]) -> Dict[str, str]:
    """Runs the verification pipeline for a single CSV row."""
    part_num = row.get("Mfg_Part_Num", "").strip()
    manuf = row.get("Part_Manuf", "").strip()
    desc = row.get("Part_Desc", "").strip()
    mfr_url = row.get("MFR URL", "").strip()
    
    ref_urls = [
        row.get("Ref URL 1", "").strip(),
        row.get("Ref URL 2", "").strip(),
        row.get("Ref URL 3", "").strip()
    ]
    ref_urls = [u for u in ref_urls if u]
    
    # Output structure
    res_row = {**row, "Verification_Status": "UNVERIFIED", "Verification_Reason": "No URLs found"}
    
    if not mfr_url:
        return res_row

    # 1. Fetch metadata in parallel for MFR URL and active Reference URLs
    urls_to_fetch = [mfr_url] + ref_urls[:2] # fetch MFR URL and top 2 reference URLs
    tasks = [fetch_page_metadata(session, url) for url in urls_to_fetch]
    metadata_results = await asyncio.gather(*tasks)
    
    mfr_meta = metadata_results[0]
    
    # 2. Run Heuristic Verification on MFR URL
    mfr_score, mfr_matches = calculate_heuristic_score(part_num, manuf, desc, mfr_meta)
    
    # High confidence heuristic match
    if mfr_score >= 60:
        res_row["Verification_Status"] = "VERIFIED"
        res_row["Verification_Reason"] = f"Heuristics Match: {', '.join(mfr_matches)} (Score: {mfr_score})"
        return res_row
    
    # High confidence mismatch or dead link
    if mfr_score < 0:
        res_row["Verification_Status"] = "MISMATCH"
        res_row["Verification_Reason"] = f"Heuristics Rejected: {', '.join(mfr_matches)}"
        return res_row
        
    if "Failed" in mfr_meta["status"]:
        res_row["Verification_Status"] = "UNVERIFIED"
        res_row["Verification_Reason"] = f"Primary URL failed to load (HTTP {mfr_meta['status']})"
        return res_row

    # 3. If Heuristic is Ambiguous (Score 0-59), run AI Consensus Verification
    # (Only runs if Gemini API key is active, else falls back to status based on heuristics)
    ai_failed = False
    if api_key:
        status, reason = ask_gemini_to_verify(part_num, manuf, desc, mfr_url, metadata_results)
        # Check if the result indicates a rate limit/quota or general API error
        if "Error:" in reason or "429" in reason or "quota" in reason.lower() or (status == "UNVERIFIED" and "Error" in reason):
            ai_failed = True
        else:
            res_row["Verification_Status"] = status
            res_row["Verification_Reason"] = f"AI Verdict: {reason.replace('\n', ' ').replace('\r', ' ')}"
            
    if not api_key or ai_failed:
        # Fall back to rule-based criteria
        if mfr_score >= 30:
            res_row["Verification_Status"] = "PARTIAL"
            res_row["Verification_Reason"] = f"Heuristics Partial Match: {', '.join(mfr_matches)} (Score: {mfr_score})"
            if ai_failed:
                res_row["Verification_Reason"] += " [Gemini Quota Exceeded]"
        else:
            res_row["Verification_Status"] = "UNVERIFIED"
            res_row["Verification_Reason"] = f"Low Heuristics confidence (Score: {mfr_score})"
            if ai_failed:
                res_row["Verification_Reason"] += " [Gemini Quota Exceeded]"
            
    return res_row

async def main():
    print("Starting Multisource URL Verification Process...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Output file '{INPUT_CSV}' from crawler not found. Please run search_urls.py first.")
        return
        
    # Read output rows to verify
    input_rows = []
    with open(INPUT_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)
        
    # Resume verification progress
    verified_parts = set()
    output_rows = []
    
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "Mfg_Part_Num" in reader.fieldnames:
                    for row in reader:
                        verified_parts.add(row["Mfg_Part_Num"])
                        output_rows.append(row)
            print(f"Resuming verification. Already verified {len(verified_parts)} parts.")
        except Exception as e:
            print(f"Error reading existing verification file: {e}. Overwriting.")
            output_rows = []

    # Filter out already processed rows
    rows_to_process = [r for r in input_rows if r.get("Mfg_Part_Num") not in verified_parts]
    total_to_process = len(rows_to_process)
    
    if total_to_process == 0:
        print("All URLs are already verified.")
        return
        
    print(f"Total rows to verify: {total_to_process}")
    
    # Configure output CSV field names
    fieldnames = list(input_rows[0].keys())
    if "Verification_Status" not in fieldnames:
        fieldnames += ["Verification_Status", "Verification_Reason"]
        
    # Write headers if starting fresh
    if not verified_parts:
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # Process rows in batches to respect concurrency limits
    async with aiohttp.ClientSession() as session:
        for i in range(0, total_to_process, MAX_CONCURRENT_REQUESTS):
            batch = rows_to_process[i:i + MAX_CONCURRENT_REQUESTS]
            print(f"Processing batch {i // MAX_CONCURRENT_REQUESTS + 1} ({len(batch)} rows)...")
            
            tasks = [verify_row(session, row) for row in batch]
            results = await asyncio.gather(*tasks)
            
            # Write batch results immediately
            with open(OUTPUT_CSV, mode='a', encoding='utf-8', newline='') as out_f:
                writer = csv.DictWriter(out_f, fieldnames=fieldnames)
                for res_row in results:
                    writer.writerow(res_row)
                    print(f" - [{res_row['Mfg_Part_Num']}] Verdict: {res_row['Verification_Status']} ({res_row['Verification_Reason'][:60]}...)")
            
            # Delay to avoid hitting rate limits too aggressively
            await asyncio.sleep(1.0)
            
    print("Verification completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
