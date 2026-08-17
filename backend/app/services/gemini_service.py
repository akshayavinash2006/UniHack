"""Gemini service — wraps Gemini API selection from search_urls.py."""
import os
import re
from typing import List, Dict, Tuple, Optional


def pick_best_url_gemini(
    mfg_part_num: str,
    manufacturer: str,
    part_desc: str,
    search_results: List[Dict[str, str]]
) -> Tuple[str, Optional[Dict]]:
    """Uses Gemini API to select the most relevant manufacturer product page URL.
    
    Preserves the exact logic from search_urls.py.
    Returns (url, signals_dict) where signals_dict contains reasoning signals.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "", None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

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
        chat = client.chats.create(model="gemini-3.6-flash")
        response = chat.send_message(prompt)
        url = response.text.strip()

        # Build signals from analysing the response
        signals = {
            "exact_part_match": mfg_part_num.lower() in url.lower() if url and url != "None" else False,
            "manufacturer_source": manufacturer.lower().split()[0] in url.lower() if url and url != "None" and manufacturer else False,
            "product_specific_page": url != "None" and url != "",
            "not_marketplace": True,
            "raw_response": response.text.strip()[:500],
        }

        # Check for marketplaces in Gemini response
        marketplaces = ['amazon.com', 'ebay.com', 'walmart.com', 'homedepot.com', 'lowes.com']
        for mp in marketplaces:
            if mp in url.lower():
                signals["not_marketplace"] = False

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

        final_url = url if url != "None" else ""
        return final_url, signals if final_url else None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "", None


def is_gemini_available() -> bool:
    """Check if Gemini API key is configured."""
    return bool(os.environ.get("GEMINI_API_KEY"))
