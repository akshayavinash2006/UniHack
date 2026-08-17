"""Search service — wraps DuckDuckGo search from search_urls.py."""
from typing import List, Dict
from ddgs import DDGS


def search_part_urls(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Performs a DuckDuckGo search for the query and returns a list of results.
    
    Preserves the exact logic from search_urls.py.
    """
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
