import os
import csv
import time
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from ddgs import DDGS

# Load environment variables (for GEMINI_API_KEY if available)
load_dotenv()

INPUT_CSV = "Unihack_ Sample Dataset - Input.csv"
OUTPUT_CSV = "Unihack_ Output.csv"
DELAY_BETWEEN_SEARCHES = 1.5  # delay in seconds to prevent rate limiting

def clean_manufacturer(manuf: str) -> str:
    """Cleans manufacturer names like 'Freud Inc (2435)' to 'Freud Inc'."""
    if not manuf or manuf.strip() in ["--", ""]:
        return ""
    # Remove text in parenthesis at the end
    cleaned = re.sub(r'\s*\(\d+\)\s*$', '', manuf)
    cleaned = re.sub(r'\s*\([A-Z0-9]+\)\s*$', '', cleaned)
    return cleaned.strip()

def search_part_urls(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Performs a DuckDuckGo search for the query and returns a list of results."""
    results = []
    try:
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(query, max_results=max_results)
            if ddgs_gen:
                for r in ddgs_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")
                    })
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
    return results

def pick_best_url_gemini(mfg_part_num: str, manufacturer: str, part_desc: str, search_results: List[Dict[str, str]]) -> str:
    """Uses Gemini API to select the most relevant manufacturer product page URL."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Structure the prompt
        results_str = ""
        for i, r in enumerate(search_results):
            results_str += f"[{i}] Link: {r['href']}\nTitle: {r['title']}\nSnippet: {r['body']}\n\n"
            
        prompt = f"""
You are a product data assistant. Your job is to select the absolute best/most relevant product URL or manufacturer URL from the search results below for the given part.

Target Part Info:
- Part Number: {mfg_part_num}
- Manufacturer: {manufacturer}
- Description: {part_desc}

Search Results:
{results_str}

Please reply with ONLY the URL (href) of the most relevant manufacturer product page or official documentation page. Do not include any explanation or other text. If none of the URLs are relevant or official, output "None".
"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        url = response.text.strip()
        
        # Simple cleanup of response if it contains formatting
        if url.startswith("`") or "\n" in url or " " in url:
            # Try to extract the first URL found
            urls = re.findall(r'https?://[^\s`]+', url)
            if urls:
                url = urls[0]
            else:
                url = "None"
        
        return url if url != "None" else ""
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ""

def rank_urls_heuristic(mfg_part_num: str, manufacturer: str, search_results: List[Dict[str, str]]) -> str:
    """Fallback heuristic to pick the best URL when Gemini API is not used."""
    if not search_results:
        return ""
        
    manuf_lower = manufacturer.lower()
    part_lower = mfg_part_num.lower()
    
    best_url = ""
    best_score = -1
    
    # Generic marketplaces to deprioritize
    avoid_domains = ['amazon.com', 'ebay.com', 'walmart.com', 'homedepot.com', 'lowes.com']
    
    for r in search_results:
        href = r['href'].lower()
        title = r['title'].lower()
        body = r['body'].lower()
        
        score = 0
        
        # Score based on containing part number
        if part_lower in href:
            score += 10
        if part_lower in title:
            score += 5
            
        # Score based on containing manufacturer name
        if manuf_lower and manuf_lower in href:
            score += 8
        if manuf_lower and manuf_lower in title:
            score += 4
            
        # Deprioritize general stores
        for domain in avoid_domains:
            if domain in href:
                score -= 15
                
        # Prioritize potential manufacturer sites or PDF datasheets
        if href.endswith('.pdf'):
            score += 2
            
        if score > best_score:
            best_score = score
            best_url = r['href']
            
    # Default to the first search result if scores are very low or equal
    if not best_url or best_score < 0:
        best_url = search_results[0]['href']
        
    return best_url

def main():
    print("Starting URL Search Scraper...")
    
    # Check what rows have already been processed to support resuming
    processed_parts = set()
    output_rows = []
    
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "Mfg_Part_Num" in reader.fieldnames:
                    for row in reader:
                        processed_parts.add(row["Mfg_Part_Num"])
                        output_rows.append(row)
            print(f"Resuming search. Already processed {len(processed_parts)} parts.")
        except Exception as e:
            print(f"Error reading existing output file: {e}. Will overwrite.")
            output_rows = []
            
    # Read the input CSV
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input file {INPUT_CSV} not found.")
        return
        
    with open(INPUT_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)[:10]  # Only process the first 10 rows for testing
        
    # Open output file for writing/appending
    fieldnames = ["Mfg_Part_Num", "Part_Manuf", "Part_Desc", "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3"]
    
    # Write headers if starting fresh
    if not processed_parts:
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
    total_to_process = len(input_rows)
    print(f"Total rows in input: {total_to_process}")
    
    gemini_active = bool(os.environ.get("GEMINI_API_KEY"))
    if gemini_active:
        print("Gemini API key detected. Using Gemini AI for relevance filtering.")
    else:
        print("No Gemini API key found. Using heuristic filter.")
        
    count = 0
    for idx, row in enumerate(input_rows):
        part_num = row.get("Mfg_Part_Num", "").strip()
        if not part_num or part_num in processed_parts:
            continue
            
        manuf = row.get("Part_Manuf", "").strip()
        cleaned_manuf = clean_manufacturer(manuf)
        desc = row.get("Part_Desc", "").strip()
        
        # Build search query using ONLY Mfg Part Number
        query = part_num
        print(f"[{idx+1}/{total_to_process}] Searching for: '{query}'")
        
        # Execute search
        search_results = search_part_urls(query, max_results=4)
        
        mfr_url = ""
        ref_urls = ["", "", ""]
        
        if search_results:
            # 1. Determine best MFR URL
            if gemini_active:
                mfr_url = pick_best_url_gemini(part_num, cleaned_manuf, desc, search_results)
                
            # If Gemini failed, returned empty, or wasn't active, fall back to heuristic
            if not mfr_url:
                mfr_url = rank_urls_heuristic(part_num, cleaned_manuf, search_results)
                
            # Fill other reference URLs from search results
            ref_idx = 0
            for r in search_results:
                href = r['href']
                if href != mfr_url and ref_idx < 3:
                    ref_urls[ref_idx] = href
                    ref_idx += 1
        
        # Write/Append row to output CSV immediately to preserve progress
        output_row = {
            "Mfg_Part_Num": part_num,
            "Part_Manuf": manuf,
            "Part_Desc": desc,
            "MFR URL": mfr_url,
            "Ref URL 1": ref_urls[0],
            "Ref URL 2": ref_urls[1],
            "Ref URL 3": ref_urls[2]
        }
        
        with open(OUTPUT_CSV, mode='a', encoding='utf-8', newline='') as out_f:
            writer = csv.DictWriter(out_f, fieldnames=fieldnames)
            writer.writerow(output_row)
            
        processed_parts.add(part_num)
        count += 1
        
        # Small delay to respect rate limits
        time.sleep(DELAY_BETWEEN_SEARCHES)
        
    print(f"Completed processing. New parts searched: {count}")

if __name__ == "__main__":
    main()
