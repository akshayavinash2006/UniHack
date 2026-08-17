import os
import csv
import time
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
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
You are an expert product data assistant. Your task is to select the absolute best, most relevant manufacturer product page or official datasheet/documentation URL from the search results below for the target part.

Target Part Info:
- Part Number: {mfg_part_num}
- Manufacturer: {manufacturer}
- Description: {part_desc}

Search Results:
{results_str}

CRITICAL RULES:
1. The URL MUST be the official product page, datasheet, or official specification page for this exact part number/manufacturer.
2. DO NOT select generic links (e.g., Wikipedia, YouTube, Facebook, LinkedIn, Twitter, Pinterest, Instagram, main search engine homepages, or generic blog posts).
3. DO NOT select generic retail marketplaces (e.g., Amazon, eBay, Walmart, Home Depot, Lowe's) unless it is a highly specific direct manufacturer store page and no official manufacturer site is present.
4. If a result is for a completely different part, or if none of the search results are highly relevant/official product links for the specified part, you MUST output "None".
5. Do not invent, hallucinate, or construct any URLs. You must ONLY select from the exact links provided in the Search Results above.

Please reply with ONLY the chosen URL from the results, or "None" if there is no high-confidence match. Do not include any explanations, reasoning, or markdown formatting (e.g. do not wrap in backticks).
"""
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(prompt)
        url = response.text.strip()
        
        # Simple cleanup of response if it contains formatting
        if url.startswith("`") or "\n" in url or " " in url or "None" in url:
            # Try to extract the first URL found matching the search results hrefs
            urls = re.findall(r'https?://[^\s`]+', url)
            if urls:
                candidate = urls[0]
                # Ensure it's in the search results
                if any(candidate.lower() == r['href'].lower() for r in search_results):
                    url = candidate
                else:
                    url = "None"
            else:
                url = "None"
        
        return url if url != "None" else ""
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ""

def rank_urls_heuristic(mfg_part_num: str, manufacturer: str, part_desc: str, search_results: List[Dict[str, str]]) -> str:
    """Fallback heuristic to pick the best URL when Gemini API is not used."""
    if not search_results:
        return ""
        
    manuf_lower = manufacturer.lower()
    part_lower = mfg_part_num.lower()
    desc_lower = part_desc.lower()
    
    best_url = ""
    best_score = -100
    
    # Generic marketplaces or non-manufacturer sites to deprioritize heavily
    avoid_domains = [
        'amazon.com', 'ebay.com', 'walmart.com', 'homedepot.com', 'lowes.com',
        'wikipedia.org', 'youtube.com', 'youtu.be', 'facebook.com', 'twitter.com',
        'instagram.com', 'pinterest.com', 'linkedin.com', 'crazycattle3d.github.io',
        'calonote.com', 'mapsplatform.google.com', 'tv3.ru', 'dzen.ru'
    ]
    
    for r in search_results:
        href = r['href'].lower()
        title = r['title'].lower()
        body = r['body'].lower()
        
        score = 0
        
        # If the URL is in the avoid_domains list, heavily penalize it
        for domain in avoid_domains:
            if domain in href:
                score -= 100
                
        # Score based on containing part number
        if part_lower:
            clean_part = re.sub(r'[^a-zA-Z0-9]', '', part_lower)
            clean_href = re.sub(r'[^a-zA-Z0-9]', '', href)
            clean_title = re.sub(r'[^a-zA-Z0-9]', '', title)
            clean_body = re.sub(r'[^a-zA-Z0-9]', '', body)
            
            if part_lower in href:
                score += 15
            elif clean_part and clean_part in clean_href:
                score += 10
                
            if part_lower in title:
                score += 10
            elif clean_part and clean_part in clean_title:
                score += 5
                
            if part_lower in body:
                score += 5
            elif clean_part and clean_part in clean_body:
                score += 2
            
        # Score based on containing manufacturer name
        if manuf_lower:
            manuf_words = [w for w in re.split(r'\W+', manuf_lower) if len(w) > 2]
            for w in manuf_words:
                if w in href:
                    score += 5
                if w in title:
                    score += 3
            if manuf_lower in href:
                score += 10
            if manuf_lower in title:
                score += 5
                
        # Score based on matching description terms (to distinguish similar parts)
        desc_words = [w for w in re.split(r'\W+', desc_lower) if len(w) > 2 and w not in manuf_lower and w not in part_lower]
        for w in desc_words[:5]:
            if w in title or w in body:
                score += 2
                
        # Prioritize potential manufacturer sites or PDF datasheets
        if href.endswith('.pdf'):
            score += 3
            
        if score > best_score:
            best_score = score
            best_url = r['href']
            
    # Set a threshold to filter out random/irrelevant links (minimum score of 6 required)
    if best_score < 6:
        return ""
        
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
        input_rows = list(reader)[:100]  # Only process the first 10 rows for testing
        
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
        
        # Build search query using Manufacturer name, Mfg Part Number, and Part Description
        query_parts = []
        if cleaned_manuf:
            query_parts.append(cleaned_manuf)
        if part_num:
            query_parts.append(part_num)
        
        # Clean description to avoid redundancy with part number
        clean_desc = desc
        if part_num and clean_desc.lower().startswith(part_num.lower()):
            clean_desc = clean_desc[len(part_num):].strip()
        
        # Remove any leading special characters/whitespace
        clean_desc = re.sub(r'^[\s\-\"\']+', '', clean_desc).strip()
        if clean_desc:
            query_parts.append(clean_desc)
            
        query = " ".join(query_parts)
        print(f"[{idx+1}/{total_to_process}] Searching for: '{query}'")
        
        # Execute search
        search_results = search_part_urls(query, max_results=6)
        
        # Filter out YouTube links and Wikipedia links
        disallowed_domains = ['youtube.com', 'youtu.be', 'wikipedia.org']
        search_results = [
            r for r in search_results 
            if not any(domain in r['href'].lower() for domain in disallowed_domains)
        ]
        
        mfr_url = ""
        ref_urls = ["", "", ""]
        
        if search_results:
            # 1. Determine best MFR URL
            if gemini_active:
                mfr_url = pick_best_url_gemini(part_num, cleaned_manuf, desc, search_results)
                
            # If Gemini failed, returned empty, or wasn't active, fall back to heuristic
            if not mfr_url:
                mfr_url = rank_urls_heuristic(part_num, cleaned_manuf, desc, search_results)
                
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
