#!/usr/bin/env python3
"""
NameCraft Full - Automated brand name generator and validator.

Usage:
  python namecraft_full.py "Your business concept"
  python namecraft_full.py --validate "SpecificName"
"""

import sys
import random
import re
import subprocess
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ============================================================
# CONFIG
# ============================================================

BRAVE_API_KEY = 'REMOVED'
RATE_LIMIT_DELAY = 1.1  # seconds between API calls

# ============================================================
# NAME GENERATION
# ============================================================

STARTS = ['a','e','i','o','u','ba','be','bi','bo','ca','ce','co','da','de','di','do',
          'fa','fe','fi','fo','ka','ke','ki','ko','la','le','li','lo','lu','ma','me','mi','mo',
          'na','ne','ni','no','nu','pa','pe','pi','po','ra','re','ri','ro','ru','sa','se','si','so',
          'ta','te','ti','to','va','ve','vi','vo','za','ze','zi','zo',
          'ax','ex','ix','ox','bex','dex','fex','kex','lex','mex','nex','pex','vex','zex']
MIDS = ['n','l','m','r','s','v','x','t','k']
ENDS = ['a','e','i','o','ia','io','is','ix','us','ta','te','ti','to','la','le','li','lo',
        'na','ne','no','ra','re','ri','ro','sa','se','va','ve','ka','ke','ki','ko','xa','xi','xo']
BAD = ['ass','shit','fuck','cunt','dick','cock','piss','bitch','nazi','porn','fick','puta',
       'culo','suka','kuso','anal','fag','sex','rape','cum','tit','gay']


def is_clean(name: str) -> bool:
    n = name.lower()
    for b in BAD:
        if b in n:
            return False
    return True


def is_pronounceable(name: str) -> bool:
    n = name.lower()
    if not re.search(r'[aeiou]', n):
        return False
    if re.search(r'[^aeiou]{4,}', n):
        return False
    if re.search(r'[aeiou]{3,}', n):
        return False
    return True


def generate_candidates(count: int = 200, min_len: int = 4, max_len: int = 7) -> List[str]:
    """Generate candidate names."""
    names = set()
    attempts = 0
    
    while len(names) < count and attempts < count * 100:
        attempts += 1
        s = random.randint(1, 5)
        
        if s == 1:
            n = random.choice(STARTS) + random.choice(ENDS)
        elif s == 2:
            n = random.choice(STARTS) + random.choice(MIDS) + random.choice(ENDS)
        elif s == 3:
            n = random.choice(STARTS) + random.choice(STARTS)
        elif s == 4:
            n = random.choice(['a','e','i','o','u']) + random.choice(MIDS) + random.choice(ENDS)
        else:
            n = random.choice(STARTS) + random.choice(['ll','rr','ss','nn']) + random.choice(['a','e','i','o'])
        
        n = n.capitalize()
        
        if min_len <= len(n) <= max_len and is_pronounceable(n) and is_clean(n):
            names.add(n)
    
    return list(names)


# ============================================================
# BRAVE SEARCH
# ============================================================

def brave_search(query: str, count: int = 3) -> List[dict]:
    """Search using Brave API."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&count={count}"
    
    req = urllib.request.Request(url)
    req.add_header('X-Subscription-Token', BRAVE_API_KEY)
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('web', {}).get('results', [])
    except:
        return []


# ============================================================
# DOMAIN CHECKING
# ============================================================

def check_domain_dns(name: str, tld: str) -> bool:
    """Check if domain has DNS (taken) or not (possibly available)."""
    try:
        result = subprocess.run(
            ['dig', '+short', f'{name.lower()}.{tld}'],
            capture_output=True, text=True, timeout=3
        )
        return len(result.stdout.strip()) == 0  # No DNS = possibly available
    except:
        return None


def check_domains(name: str, tlds: List[str] = ['ai', 'com', 'ch']) -> dict:
    """Check multiple domains."""
    results = {}
    for tld in tlds:
        results[tld] = check_domain_dns(name, tld)
    return results


# ============================================================
# PACKAGE REGISTRY CHECKING
# ============================================================

def check_npm(name: str) -> bool:
    """Check npm registry."""
    try:
        result = subprocess.run(
            ['curl', '-sL', f'https://registry.npmjs.org/{name.lower()}', '--max-time', '3'],
            capture_output=True, text=True, timeout=5
        )
        return not ('"name"' in result.stdout and '"error"' not in result.stdout)
    except:
        return None


def check_pypi(name: str) -> bool:
    """Check PyPI registry."""
    try:
        result = subprocess.run(
            ['curl', '-sL', f'https://pypi.org/pypi/{name.lower()}/json', '--max-time', '3'],
            capture_output=True, text=True, timeout=5
        )
        return not ('"info"' in result.stdout and '"message"' not in result.stdout)
    except:
        return None


# ============================================================
# FULL VALIDATION
# ============================================================

@dataclass
class ValidationResult:
    name: str
    score: int = 100
    
    # Search findings
    is_word: bool = False
    word_meaning: str = ""
    is_acronym: bool = False
    acronym_meaning: str = ""
    company_exists: bool = False
    company_info: str = ""
    
    # Domain status
    domains: dict = field(default_factory=dict)
    
    # Package status
    npm_available: bool = True
    pypi_available: bool = True
    
    # Verdict
    is_viable: bool = True
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_name(name: str, check_search: bool = True) -> ValidationResult:
    """Full validation of a name."""
    result = ValidationResult(name=name)
    
    # 1. Check domains first (fast, no API)
    result.domains = check_domains(name)
    available_domains = [tld for tld, avail in result.domains.items() if avail]
    
    if not available_domains:
        result.blockers.append("No domains available")
        result.is_viable = False
        result.score -= 50
        return result  # Skip expensive search if no domains
    
    # 2. Check packages
    result.npm_available = check_npm(name)
    result.pypi_available = check_pypi(name)
    
    if not result.npm_available:
        result.warnings.append("npm package exists")
        result.score -= 5
    if not result.pypi_available:
        result.warnings.append("PyPI package exists")
        result.score -= 5
    
    # 3. Search-based validation (with rate limiting)
    if check_search:
        # Check meaning
        results = brave_search(f'"{name}" meaning definition')
        for r in results:
            desc = r.get('description', '').lower()
            if 'meaning' in desc or 'definition' in desc:
                result.is_word = True
                result.word_meaning = r.get('description', '')[:150]
                result.warnings.append(f"Has meaning: {result.word_meaning[:50]}...")
                result.score -= 10
                break
        
        time.sleep(RATE_LIMIT_DELAY)
        
        # Check acronym
        results = brave_search(f'"{name.upper()}" acronym stands for')
        for r in results:
            desc = r.get('description', '').lower()
            if 'stands for' in desc or 'abbreviation' in desc or 'definitions' in desc:
                result.is_acronym = True
                result.acronym_meaning = r.get('description', '')[:150]
                result.blockers.append(f"Is acronym: {result.acronym_meaning[:50]}...")
                result.is_viable = False
                result.score -= 40
                break
        
        time.sleep(RATE_LIMIT_DELAY)
        
        # Check company
        results = brave_search(f'"{name}" company')
        for r in results:
            title = r.get('title', '').lower()
            desc = r.get('description', '').lower()
            if name.lower() in title:
                if any(x in desc for x in ['inc', 'llc', 'ltd', 'corp', 'gmbh', 'founded', 'company', 'employees']):
                    result.company_exists = True
                    result.company_info = f"{r.get('title', '')}: {r.get('description', '')[:80]}"
                    result.blockers.append(f"Company exists: {result.company_info[:60]}...")
                    result.is_viable = False
                    result.score -= 50
                    break
        
        time.sleep(RATE_LIMIT_DELAY)
    
    # Bonus for all domains available
    if len(available_domains) >= 3:
        result.score += 10
    
    result.score = max(0, min(100, result.score))
    
    return result


def format_report(result: ValidationResult) -> str:
    """Format a validation result as a report."""
    status = "❌ BLOCKED" if not result.is_viable else ("⚠️ WARNINGS" if result.warnings else "✅ VIABLE")
    
    lines = [
        f"┌{'─'*66}┐",
        f"│  {result.name.upper():<50} {result.score:>3}/100   │",
        f"├{'─'*66}┤",
    ]
    
    # Domains
    domain_str = " ".join([f"{'✅' if v else '❌'}.{k}" for k, v in result.domains.items()])
    lines.append(f"│  🌐 Domains:    {domain_str:<47} │")
    
    # Packages
    pkg_str = f"{'✅' if result.npm_available else '❌'} npm  {'✅' if result.pypi_available else '❌'} pypi"
    lines.append(f"│  📦 Packages:   {pkg_str:<47} │")
    
    # Meaning
    if result.is_word:
        lines.append(f"│  📖 Meaning:    {result.word_meaning[:47]:<47} │")
    else:
        lines.append(f"│  📖 Meaning:    None (invented word){' '*26} │")
    
    # Acronym
    if result.is_acronym:
        lines.append(f"│  🔤 Acronym:    {result.acronym_meaning[:47]:<47} │")
    else:
        lines.append(f"│  🔤 Acronym:    None found{' '*37} │")
    
    # Company
    if result.company_exists:
        lines.append(f"│  🏢 Company:    {result.company_info[:47]:<47} │")
    else:
        lines.append(f"│  🏢 Company:    None found{' '*37} │")
    
    # Verdict
    lines.append(f"├{'─'*66}┤")
    lines.append(f"│  {status:<64} │")
    lines.append(f"└{'─'*66}┘")
    
    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python namecraft_full.py 'Your business concept'")
        print("  python namecraft_full.py --validate 'SpecificName'")
        sys.exit(1)
    
    if sys.argv[1] == '--validate':
        if len(sys.argv) < 3:
            print("Usage: python namecraft_full.py --validate 'Name'")
            sys.exit(1)
        
        name = sys.argv[2]
        print(f"\n🔍 Validating: {name}\n")
        result = validate_name(name, check_search=True)
        print(format_report(result))
        sys.exit(0)
    
    concept = ' '.join(sys.argv[1:])
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  🔮 NAMECRAFT                                                        ║
║  AI-Powered Brand Name Generator                                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Concept: {concept[:56]:<56} ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    # Generate candidates
    print("📝 Generating candidates...")
    candidates = generate_candidates(100)
    print(f"   Generated {len(candidates)} candidates")
    
    # Quick domain filter
    print("\n🌐 Checking domains...")
    domain_viable = []
    for name in candidates:
        domains = check_domains(name)
        if any(domains.values()):
            domain_viable.append((name, domains))
    
    print(f"   {len(domain_viable)} have available domains")
    
    # Full validation of top candidates
    print("\n🔍 Deep validation (this takes ~4 sec per name)...")
    viable = []
    checked = 0
    
    for name, domains in domain_viable[:20]:  # Check top 20
        checked += 1
        print(f"   [{checked}/20] Checking {name}...", end=" ", flush=True)
        
        result = validate_name(name, check_search=True)
        
        if result.is_viable:
            viable.append(result)
            print("✅ VIABLE")
        else:
            print(f"❌ {result.blockers[0][:30] if result.blockers else 'blocked'}")
        
        if len(viable) >= 5:
            break
    
    # Output results
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  RESULTS: {len(viable)} VIABLE NAMES FOUND                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    for result in viable:
        print(format_report(result))
        print()
    
    if not viable:
        print("No viable names found. Try running again for different candidates.")


if __name__ == '__main__':
    main()
