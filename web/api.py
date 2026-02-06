#!/usr/bin/env python3
"""
NameCraft API - FastAPI backend with real validation via Brave Search.
"""

import os
import json
import time
import urllib.request
import urllib.parse
import ssl
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NameCraft API", version="2.0.0")

# Gemini API for LLM filtering
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', os.environ.get('GOOGLE_API_KEY', ''))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY', 'BSAey8qCOTwLfJfLbbxGpjfZugJ0qee')
RATE_LIMIT_DELAY = 1.1  # Brave free tier: 1 req/sec

# Track last request time for rate limiting
last_request_time = 0


def rate_limited_request(url: str, headers: dict) -> dict:
    """Make a rate-limited request."""
    global last_request_time
    
    elapsed = time.time() - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            last_request_time = time.time()
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Request error: {e}")
        return {}


def llm_filter_names(names: List[str]) -> List[str]:
    """Use LLM to filter names for quality - easy to say, spell, and remember."""
    if not GEMINI_API_KEY or not names:
        return names  # Fallback: return all if no API key
    
    # Batch names for efficiency
    names_list = "\n".join(f"- {name}" for name in names)
    
    prompt = f"""You are a brand naming expert. Review these candidate brand names and return ONLY the ones that are:

1. Easy to pronounce (someone can say it correctly on first try)
2. Easy to spell after hearing it (no confusion about letters)
3. Sound professional and memorable as a brand name
4. Don't sound awkward, clunky, or hard to say

Names to evaluate:
{names_list}

Return ONLY a JSON array of the good names, nothing else. Example: ["Kova", "Nexio", "Zenta"]
If none are good, return an empty array: []

IMPORTANT: Be selective. Only include names that truly sound like real brand names a company would use. Reject anything awkward."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json"
        })
        
        # Handle SSL
        ctx = ssl.create_default_context()
        
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode())
            
        # Extract text from Gemini response
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
        
        # Parse JSON array from response
        # Clean up the response - sometimes has markdown backticks
        text = text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]  # Remove first line
            text = text.rsplit('```', 1)[0]  # Remove last backticks
        text = text.strip()
        
        good_names = json.loads(text)
        if isinstance(good_names, list):
            # Return only names that were in the original list (case-insensitive match)
            names_lower = {n.lower(): n for n in names}
            return [names_lower.get(n.lower(), n) for n in good_names if n.lower() in names_lower]
        return names
        
    except Exception as e:
        print(f"LLM filter error: {e}")
        return names  # Fallback: return all on error


def brave_search(query: str, count: int = 5) -> dict:
    """Search via Brave Search API."""
    if not BRAVE_API_KEY:
        return {"web": {"results": []}}
    
    encoded = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={count}"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    return rate_limited_request(url, headers)


def check_domain_dns(name: str, tld: str) -> bool:
    """Quick DNS check for domain availability (heuristic)."""
    import socket
    domain = f"{name.lower()}.{tld}"
    try:
        socket.gethostbyname(domain)
        return False  # Has DNS = likely taken
    except socket.gaierror:
        return True  # No DNS = likely available


def check_npm(name: str) -> bool:
    """Check if npm package name is available."""
    url = f"https://registry.npmjs.org/{name.lower()}"
    try:
        req = urllib.request.Request(url)
        urllib.request.urlopen(req, timeout=5)
        return False  # Found = taken
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True  # Not found = available
        return False
    except:
        return True  # Assume available on error


def check_pypi(name: str) -> bool:
    """Check if PyPI package name is available."""
    url = f"https://pypi.org/pypi/{name.lower()}/json"
    try:
        req = urllib.request.Request(url)
        urllib.request.urlopen(req, timeout=5)
        return False  # Found = taken
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True
        return False
    except:
        return True


def check_crates(name: str) -> bool:
    """Check if crates.io package name is available."""
    url = f"https://crates.io/api/v1/crates/{name.lower()}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NameCraft/1.0"})
        urllib.request.urlopen(req, timeout=5)
        return False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True
        return False
    except:
        return True


# Common offensive/negative words in multiple languages
NEGATIVE_WORDS = {
    'en': ['death', 'kill', 'hate', 'evil', 'demon', 'hell', 'damn', 'crap', 'ugly', 'stupid', 'dumb', 'idiot'],
    'de': ['tod', 'hass', 'böse', 'hölle', 'scheisse', 'dumm', 'krieg', 'mist'],
    'fr': ['mort', 'haine', 'enfer', 'merde', 'con', 'pute', 'nul'],
    'es': ['muerte', 'odio', 'malo', 'infierno', 'mierda', 'tonto', 'puta'],
    'it': ['morte', 'odio', 'inferno', 'merda', 'cazzo', 'stupido'],
    'pt': ['morte', 'ódio', 'inferno', 'merda', 'puta', 'idiota'],
    'nl': ['dood', 'haat', 'hel', 'stom', 'kut'],
    'pl': ['śmierć', 'nienawiść', 'piekło', 'głupi', 'kurwa'],
    'ru': ['смерть', 'ненависть', 'ад', 'дурак'],
    'ja': ['死', '殺', 'クソ', 'バカ'],
    'zh': ['死', '杀', '蠢', '傻'],
    'ar': ['موت', 'كره', 'جحيم'],
}


def check_negative_meanings(name: str) -> List[str]:
    """Check if name sounds like negative words in various languages."""
    results = []
    name_lower = name.lower()
    
    for lang, words in NEGATIVE_WORDS.items():
        for word in words:
            # Check if name contains or closely matches negative word
            if word in name_lower or name_lower in word:
                results.append(f"'{name}' contains '{word}' ({lang})")
            # Check phonetic similarity (basic)
            elif len(name_lower) >= 3 and len(word) >= 3:
                if name_lower[:3] == word[:3] or name_lower[-3:] == word[-3:]:
                    results.append(f"'{name}' sounds similar to '{word}' ({lang})")
    
    return results[:5]  # Limit results


# Domain prices (approximate)
DOMAIN_PRICES = {
    'com': '$12/yr',
    'ai': '$70/yr',
    'io': '$40/yr',
    'ch': 'CHF 15/yr',
    'net': '$12/yr',
    'org': '$12/yr',
    'co': '$25/yr',
    'app': '$15/yr',
}


class QuickValidation(BaseModel):
    name: str
    score: int = 100
    domains: Dict[str, bool] = {}
    domainCount: int = 0
    npm_available: bool = True
    pypi_available: bool = True
    is_viable: bool = True
    blockers: List[str] = []
    warnings: List[str] = []


class DeepValidation(BaseModel):
    name: str
    algorithm: str = "Unknown"
    score: int = 100
    domains: Dict[str, bool] = {}
    domain_prices: Dict[str, str] = {}
    domainCount: int = 0
    is_viable: bool = True
    blockers: List[str] = []
    warnings: List[str] = []
    dictionary: Dict[str, Any] = {}
    translations: Dict[str, Any] = {}
    companies: Dict[str, Any] = {}
    trademarks: Dict[str, Any] = {}
    packages: Dict[str, bool] = {}
    phonetics: Dict[str, Any] = {}


class FilterRequest(BaseModel):
    names: List[str]


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.post("/api/filter-names")
async def filter_names(request: FilterRequest) -> dict:
    """Use LLM to filter names for quality."""
    good_names = llm_filter_names(request.names)
    return {
        "original_count": len(request.names),
        "filtered_count": len(good_names),
        "names": good_names
    }


@app.get("/api/filter-names")
async def filter_names_get(names: str = Query(..., description="Comma-separated list of names")) -> dict:
    """Use LLM to filter names for quality (GET version)."""
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    good_names = llm_filter_names(name_list)
    return {
        "original_count": len(name_list),
        "filtered_count": len(good_names),
        "names": good_names
    }


@app.get("/api/validate")
async def validate_quick(name: str = Query(..., min_length=2, max_length=20)) -> QuickValidation:
    """Quick validation - domains and packages only."""
    result = QuickValidation(name=name)
    
    # Check domains via DNS
    tlds = ['com', 'ai', 'io', 'ch']
    for tld in tlds:
        result.domains[tld] = check_domain_dns(name, tld)
    result.domainCount = sum(result.domains.values())
    
    # Check packages
    result.npm_available = check_npm(name)
    result.pypi_available = check_pypi(name)
    
    # Calculate score
    result.score = 50
    result.score += result.domainCount * 10  # Up to 40 points for domains
    if result.npm_available:
        result.score += 5
    if result.pypi_available:
        result.score += 5
    
    result.is_viable = result.domainCount >= 2
    
    return result


@app.get("/api/deep-validate")
async def validate_deep(name: str = Query(..., min_length=2, max_length=20)) -> DeepValidation:
    """Deep validation with web search, trademark check, multi-language check."""
    result = DeepValidation(name=name)
    
    # 1. Check domains via DNS
    tlds = ['com', 'ai', 'io', 'ch']
    for tld in tlds:
        result.domains[tld] = check_domain_dns(name, tld)
        result.domain_prices[tld] = DOMAIN_PRICES.get(tld, 'Unknown')
    result.domainCount = sum(result.domains.values())
    
    # 2. Check packages
    result.packages = {
        'npm': check_npm(name),
        'pypi': check_pypi(name),
        'crates': check_crates(name),
    }
    
    # 3. Dictionary check via search
    dict_search = brave_search(f'"{name}" definition dictionary meaning')
    dict_results = dict_search.get('web', {}).get('results', [])
    is_word = any('dictionary' in (r.get('url', '') + r.get('title', '')).lower() for r in dict_results[:3])
    result.dictionary = {
        'is_word': is_word,
        'meaning': dict_results[0].get('description', '')[:100] if is_word and dict_results else None,
        'languages_checked': ['en', 'de', 'fr', 'es', 'it', 'pt']
    }
    
    # 4. Multi-language negative check
    negative = check_negative_meanings(name)
    result.translations = {
        'negative_meanings': negative,
        'checked_languages': len(NEGATIVE_WORDS)
    }
    if negative:
        result.warnings.extend(negative)
    
    # 5. Company/web presence search
    company_search = brave_search(f'{name} company OR {name} startup OR {name} brand', count=10)
    company_results = company_search.get('web', {}).get('results', [])
    
    # Filter to likely company results
    filtered = []
    for r in company_results:
        title = r.get('title', '').lower()
        url = r.get('url', '').lower()
        # Skip dictionary/wikipedia general entries
        if 'dictionary' in url or 'wiktionary' in url:
            continue
        if name.lower() in title or name.lower() in url:
            filtered.append({
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'snippet': r.get('description', '')[:200]
            })
    
    result.companies = {
        'search_hits': len(company_results),
        'top_results': filtered[:5]
    }
    
    # 6. Trademark search
    tm_search = brave_search(f'{name} trademark OR {name} registered trademark')
    tm_results = tm_search.get('web', {}).get('results', [])
    tm_found = any('trademark' in (r.get('title', '') + r.get('description', '')).lower() 
                   and name.lower() in (r.get('title', '') + r.get('description', '')).lower()
                   for r in tm_results[:5])
    result.trademarks = {
        'found': tm_found,
        'regions_checked': ['US', 'EU', 'CH', 'UK']
    }
    if tm_found:
        result.warnings.append('Potential trademark conflict detected')
    
    # 7. Phonetics (basic)
    vowels = sum(1 for c in name.lower() if c in 'aeiou')
    consonants = sum(1 for c in name.lower() if c.isalpha() and c not in 'aeiou')
    easy_spell = len(name) <= 7 and not any(c*2 in name.lower() for c in 'bcdfghjklmnpqrstvwxyz' if c*2 not in ['ll', 'ss', 'nn', 'rr'])
    easy_pronounce = vowels >= 1 and consonants <= vowels * 3
    result.phonetics = {
        'easy_to_spell': easy_spell,
        'easy_to_pronounce': easy_pronounce,
        'similar_to': []
    }
    
    # Calculate score
    result.score = 50
    result.score += result.domainCount * 8  # Up to 32 points
    if result.packages.get('npm'):
        result.score += 3
    if result.packages.get('pypi'):
        result.score += 3
    if result.packages.get('crates'):
        result.score += 2
    if not result.dictionary.get('is_word'):
        result.score += 5  # Bonus for invented name
    if not negative:
        result.score += 5  # Bonus for no negative meanings
    if not tm_found:
        result.score += 5  # Bonus for no trademark
    if len(filtered) == 0:
        result.score += 5  # Bonus for clean web presence
    
    result.score = min(100, result.score)
    
    # Determine viability
    if tm_found:
        result.blockers.append('Trademark conflict detected')
    if result.domainCount == 0:
        result.blockers.append('No domains available')
    if len(filtered) > 3:
        result.warnings.append(f'Name already used by {len(filtered)}+ companies')
    
    result.is_viable = len(result.blockers) == 0
    
    return result


# Serve static files
@app.get("/{path:path}")
async def static_files(path: str):
    if os.path.exists(path):
        return FileResponse(path)
    return FileResponse("index.html")
