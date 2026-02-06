#!/usr/bin/env python3
"""
REAL Name Validator - Actually searches the web for each name.
No more guessing. No more hardcoded lists.
"""

import subprocess
import json
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ValidationResult:
    name: str
    
    # Core checks
    exists_as_word: bool = False
    word_meaning: Optional[str] = None
    word_language: Optional[str] = None
    
    exists_as_acronym: bool = False
    acronym_meaning: Optional[str] = None
    
    exists_as_company: bool = False
    company_info: Optional[str] = None
    
    exists_as_product: bool = False
    product_info: Optional[str] = None
    
    # Domain status
    domains: dict = field(default_factory=dict)
    
    # Package registries
    npm_exists: bool = False
    pypi_exists: bool = False
    
    # Overall
    is_viable: bool = True
    rejection_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Raw search results for transparency
    search_snippets: List[str] = field(default_factory=list)


def web_search(query: str, num_results: int = 5) -> List[dict]:
    """
    Actually search the web using DuckDuckGo HTML.
    Returns list of {title, snippet, url}
    """
    results = []
    
    try:
        # URL encode the query
        encoded_query = query.replace(' ', '+').replace('"', '%22')
        
        cmd = [
            'curl', '-sL', '-A', 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            f'https://html.duckduckgo.com/html/?q={encoded_query}',
            '--max-time', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        html = result.stdout
        
        # Parse results - DuckDuckGo HTML format
        # Look for result blocks
        result_blocks = re.findall(
            r'class="result__body".*?</div>\s*</div>',
            html, re.DOTALL
        )
        
        for block in result_blocks[:num_results]:
            title_match = re.search(r'class="result__a"[^>]*>([^<]+)', block)
            snippet_match = re.search(r'class="result__snippet"[^>]*>([^<]+)', block)
            url_match = re.search(r'href="([^"]+)"', block)
            
            if title_match:
                results.append({
                    'title': title_match.group(1).strip(),
                    'snippet': snippet_match.group(1).strip() if snippet_match else '',
                    'url': url_match.group(1) if url_match else '',
                })
    
    except Exception as e:
        pass
    
    return results


def check_wiktionary(name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check Wiktionary for word definition.
    Returns (exists, meaning, language)
    """
    try:
        url = f'https://en.wiktionary.org/api/rest_v1/page/definition/{name.lower()}'
        cmd = ['curl', '-sL', url, '--max-time', '5']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        
        if result.returncode == 0 and '"definitions"' in result.stdout:
            data = json.loads(result.stdout)
            
            # Get first language and definition
            for lang, entries in data.items():
                if isinstance(entries, list) and entries:
                    for entry in entries:
                        if 'definitions' in entry and entry['definitions']:
                            defn = entry['definitions'][0].get('definition', '')
                            # Strip HTML
                            defn = re.sub(r'<[^>]+>', '', defn)
                            return True, defn[:200], lang
            
            return True, "Word exists (definition parsing failed)", "unknown"
    
    except:
        pass
    
    return False, None, None


def check_acronym(name: str) -> Tuple[bool, Optional[str]]:
    """
    Search for acronym meaning via multiple sources.
    """
    name_upper = name.upper()
    
    # 1. Check AcronymFinder.com - comprehensive acronym database
    try:
        cmd = ['curl', '-sL', f'https://www.acronymfinder.com/{name_upper}.html', '--max-time', '8']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'definitions of' in result.stdout.lower():
            # Extract definitions
            matches = re.findall(r'<td class="result-list__body__meaning"[^>]*>([^<]+)', result.stdout)
            if matches:
                meanings = [m.strip() for m in matches[:3]]
                return True, f"AcronymFinder: {'; '.join(meanings)}"
    except:
        pass
    
    # 2. Check TheFreeDictionary acronyms
    try:
        cmd = ['curl', '-sL', f'https://acronyms.thefreedictionary.com/{name_upper}', '--max-time', '8']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Look for definition table
            match = re.search(r'<td>([A-Z][^<]{10,100})</td>', result.stdout)
            if match:
                return True, f"FreeDictionary: {match.group(1).strip()}"
    except:
        pass
    
    # 3. Check Wikipedia API for page summary
    try:
        cmd = ['curl', '-sL', f'https://en.wikipedia.org/api/rest_v1/page/summary/{name_upper}', '--max-time', '5']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        
        if result.returncode == 0 and '"extract"' in result.stdout:
            data = json.loads(result.stdout)
            extract = data.get('extract', '')
            if extract and len(extract) > 20:
                return True, f"Wikipedia: {extract[:200]}"
    except:
        pass
    
    # 4. Check abbreviations.com
    try:
        cmd = ['curl', '-sL', f'https://www.abbreviations.com/{name_upper}', '--max-time', '5']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        
        if 'What does' in result.stdout and 'stand for' in result.stdout:
            match = re.search(r'<p class="desc"[^>]*>([^<]+)', result.stdout)
            if match:
                return True, f"Abbreviation: {match.group(1).strip()[:200]}"
    except:
        pass
    
    return False, None


def check_company_exists(name: str) -> Tuple[bool, Optional[str]]:
    """
    Search for existing companies with this name.
    """
    # Search for company
    results = web_search(f'"{name}" company')
    
    # Check if results strongly indicate a company
    company_indicators = ['inc', 'llc', 'ltd', 'corp', 'gmbh', 'ag', 'company', 'founded', 'ceo', 'startup']
    
    for r in results:
        snippet = r.get('snippet', '').lower()
        title = r.get('title', '').lower()
        
        # Skip if it's just our search term in a generic context
        if name.lower() in title:
            for indicator in company_indicators:
                if indicator in snippet or indicator in title:
                    return True, f"{r.get('title', '')}: {r.get('snippet', '')[:100]}"
    
    # Also check LinkedIn
    results = web_search(f'site:linkedin.com/company "{name}"')
    if results:
        return True, f"LinkedIn company page found: {results[0].get('title', '')}"
    
    return False, None


def check_product_exists(name: str) -> Tuple[bool, Optional[str]]:
    """
    Search for existing products/services with this name.
    """
    results = web_search(f'"{name}" product OR app OR software OR service')
    
    product_indicators = ['download', 'pricing', 'features', 'app', 'software', 'platform', 'tool', 'service']
    
    for r in results:
        snippet = r.get('snippet', '').lower()
        title = r.get('title', '').lower()
        
        if name.lower() in title:
            for indicator in product_indicators:
                if indicator in snippet:
                    return True, f"{r.get('title', '')}: {r.get('snippet', '')[:100]}"
    
    return False, None


def check_domain(name: str, tld: str) -> Tuple[bool, Optional[str]]:
    """
    Check domain availability via DNS + WHOIS.
    Returns (available, registrar_if_taken)
    """
    domain = f"{name.lower()}.{tld}"
    
    # Quick DNS check
    try:
        result = subprocess.run(
            ['dig', '+short', domain],
            capture_output=True, text=True, timeout=3
        )
        if result.stdout.strip():
            # Has DNS = taken
            return False, "Has DNS records"
    except:
        pass
    
    # WHOIS check
    try:
        result = subprocess.run(
            ['whois', domain],
            capture_output=True, text=True, timeout=8
        )
        output = result.stdout.lower()
        
        # Available patterns
        if any(p in output for p in ['no match', 'not found', 'no entries', 'status: free']):
            return True, None
        
        # Taken patterns
        if any(p in output for p in ['registrar:', 'creation date:', 'name server:']):
            # Extract registrar
            for line in result.stdout.split('\n'):
                if 'registrar:' in line.lower():
                    return False, line.split(':', 1)[1].strip()[:50]
            return False, "Registered"
    except:
        pass
    
    return None, "Unknown"  # Could not determine


def check_npm(name: str) -> bool:
    """Check if npm package exists."""
    try:
        cmd = ['curl', '-sL', f'https://registry.npmjs.org/{name.lower()}', '--max-time', '3']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return '"name"' in result.stdout and '"error"' not in result.stdout
    except:
        return False


def check_pypi(name: str) -> bool:
    """Check if PyPI package exists."""
    try:
        cmd = ['curl', '-sL', f'https://pypi.org/pypi/{name.lower()}/json', '--max-time', '3']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return '"info"' in result.stdout and '"message"' not in result.stdout
    except:
        return False


def validate_name(name: str, tlds: List[str] = None) -> ValidationResult:
    """
    Comprehensively validate a name through REAL web searches.
    """
    if tlds is None:
        tlds = ['com', 'ai', 'ch']
    
    result = ValidationResult(name=name)
    
    # 1. Check Wiktionary for word meaning
    exists, meaning, lang = check_wiktionary(name)
    result.exists_as_word = exists
    result.word_meaning = meaning
    result.word_language = lang
    
    if exists and meaning:
        # Check if meaning is negative
        negative_words = ['death', 'evil', 'bad', 'enemy', 'hate', 'war', 'kill', 'ugly', 'stupid']
        meaning_lower = meaning.lower()
        for neg in negative_words:
            if neg in meaning_lower:
                result.is_viable = False
                result.rejection_reasons.append(f"Negative meaning: {meaning}")
                break
        else:
            result.warnings.append(f"Has meaning in {lang}: {meaning}")
    
    # 2. Check if it's an acronym
    is_acronym, acronym_meaning = check_acronym(name)
    result.exists_as_acronym = is_acronym
    result.acronym_meaning = acronym_meaning
    
    if is_acronym:
        result.warnings.append(f"Acronym: {acronym_meaning}")
    
    # 3. Check for existing companies
    has_company, company_info = check_company_exists(name)
    result.exists_as_company = has_company
    result.company_info = company_info
    
    if has_company:
        result.is_viable = False
        result.rejection_reasons.append(f"Company exists: {company_info}")
    
    # 4. Check for existing products
    has_product, product_info = check_product_exists(name)
    result.exists_as_product = has_product
    result.product_info = product_info
    
    if has_product and not has_company:  # Don't double-count
        result.warnings.append(f"Product found: {product_info}")
    
    # 5. Check domains
    for tld in tlds:
        available, info = check_domain(name, tld)
        result.domains[tld] = {'available': available, 'info': info}
    
    # If no domains available, mark as warning
    available_domains = [tld for tld, d in result.domains.items() if d['available']]
    if not available_domains:
        result.warnings.append("No domains available")
    
    # 6. Check package registries
    result.npm_exists = check_npm(name)
    result.pypi_exists = check_pypi(name)
    
    if result.npm_exists:
        result.warnings.append("npm package exists")
    if result.pypi_exists:
        result.warnings.append("PyPI package exists")
    
    return result


def format_validation_report(result: ValidationResult) -> str:
    """Format a single validation result as a readable report."""
    lines = []
    
    status = "❌ REJECTED" if not result.is_viable else ("⚠️ CAUTION" if result.warnings else "✅ CLEAN")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"  {result.name.upper()}  —  {status}")
    lines.append(f"{'='*60}")
    
    if result.rejection_reasons:
        lines.append("\n🚨 REJECTED:")
        for r in result.rejection_reasons:
            lines.append(f"   • {r}")
    
    if result.warnings:
        lines.append("\n⚠️  WARNINGS:")
        for w in result.warnings:
            lines.append(f"   • {w}")
    
    # Word meaning
    if result.exists_as_word:
        lines.append(f"\n📖 DICTIONARY: {result.word_language}")
        lines.append(f"   {result.word_meaning}")
    else:
        lines.append("\n📖 DICTIONARY: Not a known word")
    
    # Acronym
    if result.exists_as_acronym:
        lines.append(f"\n🔤 ACRONYM: YES")
        lines.append(f"   {result.acronym_meaning}")
    else:
        lines.append("\n🔤 ACRONYM: None found")
    
    # Company
    if result.exists_as_company:
        lines.append(f"\n🏢 COMPANY: EXISTS")
        lines.append(f"   {result.company_info}")
    else:
        lines.append("\n🏢 COMPANY: None found")
    
    # Domains
    lines.append("\n🌐 DOMAINS:")
    for tld, info in result.domains.items():
        if info['available']:
            lines.append(f"   ✅ .{tld} — Available")
        elif info['available'] is False:
            lines.append(f"   ❌ .{tld} — Taken ({info['info']})")
        else:
            lines.append(f"   ❓ .{tld} — Unknown")
    
    # Packages
    lines.append("\n📦 PACKAGES:")
    lines.append(f"   npm: {'❌ Taken' if result.npm_exists else '✅ Available'}")
    lines.append(f"   PyPI: {'❌ Taken' if result.pypi_exists else '✅ Available'}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validator.py <name> [name2] [name3] ...")
        sys.exit(1)
    
    names = sys.argv[1:]
    
    for name in names:
        print(f"\n🔍 Validating: {name}...")
        result = validate_name(name)
        print(format_validation_report(result))
