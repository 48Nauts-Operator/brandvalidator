#!/usr/bin/env python3
"""
Deep Name Validator - Uses Brave Search API for comprehensive validation.
This script is meant to be called from the command line and outputs JSON.
"""

import subprocess
import json
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


@dataclass
class DeepValidationResult:
    name: str
    
    # Meaning/Definition
    has_meaning: bool = False
    meaning_source: str = ""
    meaning_text: str = ""
    meaning_sentiment: str = "neutral"  # positive, negative, neutral
    
    # Acronym
    is_acronym: bool = False
    acronym_full_form: str = ""
    acronym_source: str = ""
    
    # Existing Entity
    entity_exists: bool = False
    entity_type: str = ""  # company, product, organization, scientific term
    entity_description: str = ""
    
    # Domains
    domains: dict = field(default_factory=dict)
    
    # Packages
    packages: dict = field(default_factory=dict)
    
    # Overall
    is_viable: bool = True
    score: int = 100
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def brave_search(query: str, count: int = 5) -> List[dict]:
    """
    Call Brave Search API via curl with the API key from environment.
    """
    api_key = os.environ.get('BRAVE_API_KEY', '')
    
    if not api_key:
        # Try to get from a config file
        config_paths = [
            os.path.expanduser('~/.config/brave/api_key'),
            os.path.expanduser('~/.brave_api_key'),
        ]
        for path in config_paths:
            if os.path.exists(path):
                with open(path) as f:
                    api_key = f.read().strip()
                break
    
    if not api_key:
        return []
    
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        cmd = [
            'curl', '-sL',
            f'https://api.search.brave.com/res/v1/web/search?q={encoded_query}&count={count}',
            '-H', f'X-Subscription-Token: {api_key}',
            '-H', 'Accept: application/json',
            '--max-time', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            web_results = data.get('web', {}).get('results', [])
            return [
                {
                    'title': r.get('title', ''),
                    'url': r.get('url', ''),
                    'description': r.get('description', ''),
                }
                for r in web_results
            ]
    except Exception as e:
        pass
    
    return []


def check_meaning_and_acronym(name: str) -> Tuple[dict, dict]:
    """
    Search for meaning and acronym definitions.
    Returns (meaning_info, acronym_info)
    """
    meaning = {'found': False, 'text': '', 'source': '', 'sentiment': 'neutral'}
    acronym = {'found': False, 'text': '', 'source': ''}
    
    # Search 1: Is it a word with meaning?
    results = brave_search(f'"{name}" definition meaning')
    
    for r in results:
        desc = r.get('description', '').lower()
        title = r.get('title', '').lower()
        
        # Check for dictionary definitions
        if 'definition' in desc or 'meaning' in desc or 'means' in desc:
            if 'dictionary' in r.get('url', '').lower() or 'wiktionary' in r.get('url', '').lower():
                meaning['found'] = True
                meaning['text'] = r.get('description', '')[:300]
                meaning['source'] = r.get('url', '')
                break
    
    # Search 2: Is it an acronym?
    results = brave_search(f'"{name.upper()}" acronym stands for')
    
    for r in results:
        desc = r.get('description', '')
        
        if 'stands for' in desc.lower() or 'abbreviation' in desc.lower():
            acronym['found'] = True
            acronym['text'] = desc[:300]
            acronym['source'] = r.get('url', '')
            break
    
    # Search 3: Scientific/technical term check
    if not acronym['found']:
        results = brave_search(f'"{name.upper()}" index OR test OR method OR protocol')
        
        for r in results:
            desc = r.get('description', '')
            
            # Look for scientific/technical usage
            if any(w in desc.lower() for w in ['index', 'method', 'protocol', 'test', 'standard', 'epa', 'fda']):
                if name.upper() in r.get('title', '').upper():
                    acronym['found'] = True
                    acronym['text'] = f"Technical term: {desc[:300]}"
                    acronym['source'] = r.get('url', '')
                    break
    
    return meaning, acronym


def check_existing_entity(name: str) -> dict:
    """
    Check if name is an existing company, product, or organization.
    """
    entity = {'found': False, 'type': '', 'description': ''}
    
    # Search for company/product
    results = brave_search(f'"{name}" company OR product OR app OR software')
    
    company_indicators = ['inc', 'llc', 'ltd', 'corp', 'gmbh', 'founded', 'ceo', 'startup', 'company']
    product_indicators = ['app', 'software', 'platform', 'download', 'pricing', 'features']
    
    for r in results:
        title = r.get('title', '').lower()
        desc = r.get('description', '').lower()
        
        if name.lower() in title:
            # Check if it's a company
            if any(ind in desc for ind in company_indicators):
                entity['found'] = True
                entity['type'] = 'company'
                entity['description'] = r.get('description', '')[:200]
                return entity
            
            # Check if it's a product
            if any(ind in desc for ind in product_indicators):
                entity['found'] = True
                entity['type'] = 'product'
                entity['description'] = r.get('description', '')[:200]
                return entity
    
    return entity


def check_domains(name: str, tlds: List[str]) -> dict:
    """Check domain availability."""
    results = {}
    
    for tld in tlds:
        domain = f"{name.lower()}.{tld}"
        available = None
        info = ""
        
        # DNS check
        try:
            result = subprocess.run(
                ['dig', '+short', domain],
                capture_output=True, text=True, timeout=3
            )
            if result.stdout.strip():
                available = False
                info = "Has DNS"
        except:
            pass
        
        # WHOIS if no DNS
        if available is None:
            try:
                result = subprocess.run(
                    ['whois', domain],
                    capture_output=True, text=True, timeout=8
                )
                output = result.stdout.lower()
                
                if any(p in output for p in ['no match', 'not found', 'no entries', 'status: free']):
                    available = True
                elif any(p in output for p in ['registrar:', 'creation date:', 'name server:']):
                    available = False
                    # Try to get registrar
                    for line in result.stdout.split('\n'):
                        if 'registrar:' in line.lower():
                            info = line.split(':', 1)[1].strip()[:40]
                            break
            except:
                pass
        
        results[tld] = {'available': available, 'info': info}
    
    return results


def check_packages(name: str) -> dict:
    """Check package registries."""
    results = {}
    
    # npm
    try:
        cmd = ['curl', '-sL', f'https://registry.npmjs.org/{name.lower()}', '--max-time', '3']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        results['npm'] = '"name"' in result.stdout and '"error"' not in result.stdout
    except:
        results['npm'] = False
    
    # PyPI
    try:
        cmd = ['curl', '-sL', f'https://pypi.org/pypi/{name.lower()}/json', '--max-time', '3']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        results['pypi'] = '"info"' in result.stdout and '"message"' not in result.stdout
    except:
        results['pypi'] = False
    
    return results


def validate_name_deep(name: str, tlds: List[str] = None) -> DeepValidationResult:
    """
    Perform deep validation on a name using web search.
    """
    if tlds is None:
        tlds = ['com', 'ai', 'ch']
    
    result = DeepValidationResult(name=name)
    
    # 1. Check meaning and acronym
    meaning, acronym = check_meaning_and_acronym(name)
    
    result.has_meaning = meaning['found']
    result.meaning_text = meaning['text']
    result.meaning_source = meaning['source']
    
    result.is_acronym = acronym['found']
    result.acronym_full_form = acronym['text']
    result.acronym_source = acronym['source']
    
    if result.is_acronym:
        result.blockers.append(f"ACRONYM: {acronym['text'][:100]}")
        result.is_viable = False
        result.score -= 40
    
    if result.has_meaning:
        result.notes.append(f"Has meaning: {meaning['text'][:100]}")
    
    # 2. Check existing entities
    entity = check_existing_entity(name)
    
    result.entity_exists = entity['found']
    result.entity_type = entity['type']
    result.entity_description = entity['description']
    
    if entity['found']:
        result.blockers.append(f"{entity['type'].upper()}: {entity['description'][:100]}")
        result.is_viable = False
        result.score -= 50
    
    # 3. Check domains
    result.domains = check_domains(name, tlds)
    
    available = [tld for tld, d in result.domains.items() if d['available']]
    taken = [tld for tld, d in result.domains.items() if d['available'] is False]
    
    if not available:
        result.warnings.append(f"All checked domains taken: {', '.join(taken)}")
        result.score -= 20
    elif len(available) < len(tlds):
        result.notes.append(f"Available: {', '.join(available)}; Taken: {', '.join(taken)}")
    else:
        result.notes.append(f"All domains available: {', '.join(available)}")
        result.score += 10
    
    # 4. Check packages
    result.packages = check_packages(name)
    
    taken_packages = [pkg for pkg, exists in result.packages.items() if exists]
    if taken_packages:
        result.warnings.append(f"Package exists: {', '.join(taken_packages)}")
        result.score -= 5
    
    # Final score clamping
    result.score = max(0, min(100, result.score))
    
    return result


def format_result(result: DeepValidationResult) -> str:
    """Format result as readable text."""
    lines = []
    
    status = "❌ BLOCKED" if result.blockers else ("⚠️ WARNINGS" if result.warnings else "✅ VIABLE")
    
    lines.append(f"\n{'='*65}")
    lines.append(f"  {result.name.upper()}  |  Score: {result.score}/100  |  {status}")
    lines.append(f"{'='*65}")
    
    if result.blockers:
        lines.append("\n🚫 BLOCKERS:")
        for b in result.blockers:
            lines.append(f"   {b}")
    
    if result.warnings:
        lines.append("\n⚠️  WARNINGS:")
        for w in result.warnings:
            lines.append(f"   {w}")
    
    if result.notes:
        lines.append("\nℹ️  NOTES:")
        for n in result.notes:
            lines.append(f"   {n}")
    
    # Domains
    lines.append("\n🌐 DOMAINS:")
    for tld, info in result.domains.items():
        if info['available']:
            lines.append(f"   ✅ .{tld}")
        elif info['available'] is False:
            lines.append(f"   ❌ .{tld} — {info['info']}")
        else:
            lines.append(f"   ❓ .{tld}")
    
    # Packages
    lines.append("\n📦 PACKAGES:")
    for pkg, exists in result.packages.items():
        lines.append(f"   {'❌' if exists else '✅'} {pkg}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python deep_validator.py <name> [name2] ...")
        print("\nSet BRAVE_API_KEY environment variable for web search.")
        sys.exit(1)
    
    names = sys.argv[1:]
    
    for name in names:
        print(f"\n🔍 Deep validating: {name}...")
        result = validate_name_deep(name)
        print(format_result(result))
        
        # Also output JSON for programmatic use
        if '--json' in sys.argv:
            print("\n--- JSON ---")
            print(json.dumps(asdict(result), indent=2))
