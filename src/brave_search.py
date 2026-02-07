#!/usr/bin/env python3
"""
Brave Search API client with proper API key.
"""

import os
import json
import urllib.request
import urllib.parse
from typing import List, Optional
from dataclasses import dataclass

# API Key - stored here for the tool
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY', '')


@dataclass
class SearchResult:
    title: str
    url: str
    description: str


def brave_search(query: str, count: int = 5) -> List[SearchResult]:
    """
    Search using Brave Search API.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&count={count}"
    
    req = urllib.request.Request(url)
    req.add_header('X-Subscription-Token', BRAVE_API_KEY)
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for r in data.get('web', {}).get('results', []):
                results.append(SearchResult(
                    title=r.get('title', ''),
                    url=r.get('url', ''),
                    description=r.get('description', ''),
                ))
            
            return results
    
    except Exception as e:
        print(f"Search error: {e}")
        return []


import time

def check_name_exists(name: str, delay: float = 1.1) -> dict:
    """
    Check if a name exists as a word, acronym, or company.
    Returns dict with findings.
    """
    findings = {
        'name': name,
        'is_word': False,
        'word_meaning': None,
        'is_acronym': False,
        'acronym_meaning': None,
        'company_exists': False,
        'company_info': None,
        'product_exists': False,
        'product_info': None,
    }
    
    # 1. Check meaning/word
    results = brave_search(f'"{name}" meaning definition', 3)
    for r in results:
        desc = r.description.lower()
        if 'meaning' in desc or 'definition' in desc or 'means' in desc:
            if 'dictionary' in r.url or 'wiktionary' in r.url or 'names.org' in r.url:
                findings['is_word'] = True
                findings['word_meaning'] = r.description[:200]
                break
    
    # 2. Check acronym
    time.sleep(delay)
    results = brave_search(f'"{name.upper()}" acronym stands for', 3)
    for r in results:
        desc = r.description.lower()
        if 'stands for' in desc or 'abbreviation' in desc:
            findings['is_acronym'] = True
            findings['acronym_meaning'] = r.description[:200]
            break
    
    # 3. Check company
    time.sleep(delay)
    results = brave_search(f'"{name}" company', 3)
    for r in results:
        desc = r.description.lower()
        title = r.title.lower()
        if name.lower() in title:
            if any(x in desc for x in ['inc', 'llc', 'ltd', 'corp', 'gmbh', 'founded', 'company']):
                findings['company_exists'] = True
                findings['company_info'] = f"{r.title}: {r.description[:100]}"
                break
    
    # 4. Check product
    if not findings['company_exists']:
        time.sleep(delay)
        results = brave_search(f'"{name}" app software product', 3)
        for r in results:
            title = r.title.lower()
            desc = r.description.lower()
            if name.lower() in title:
                if any(x in desc for x in ['app', 'software', 'platform', 'download']):
                    findings['product_exists'] = True
                    findings['product_info'] = f"{r.title}: {r.description[:100]}"
                    break
    
    return findings


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python brave_search.py <name>")
        sys.exit(1)
    
    name = sys.argv[1]
    print(f"Checking: {name}")
    print("-" * 40)
    
    findings = check_name_exists(name)
    
    print(f"Is word: {findings['is_word']}")
    if findings['word_meaning']:
        print(f"  → {findings['word_meaning']}")
    
    print(f"Is acronym: {findings['is_acronym']}")
    if findings['acronym_meaning']:
        print(f"  → {findings['acronym_meaning']}")
    
    print(f"Company exists: {findings['company_exists']}")
    if findings['company_info']:
        print(f"  → {findings['company_info']}")
    
    print(f"Product exists: {findings['product_exists']}")
    if findings['product_info']:
        print(f"  → {findings['product_info']}")
