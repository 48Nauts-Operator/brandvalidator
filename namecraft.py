#!/usr/bin/env python3
"""
NameCraft - Brand Name Validator
Standalone script that outputs commands for OpenClaw to execute.

Usage: 
  python namecraft.py generate "business concept"
  python namecraft.py validate "NameToCheck"
"""

import sys
import random
import re
import subprocess
import json
from typing import List, Tuple

# ============================================================
# SYLLABLE GENERATION
# ============================================================

STARTS = [
    'a', 'e', 'i', 'o', 'u', 'ai', 'au', 'ei',
    'ba', 'be', 'bi', 'bo', 'bu', 'ca', 'ce', 'ci', 'co', 'cu',
    'da', 'de', 'di', 'do', 'du', 'fa', 'fe', 'fi', 'fo', 'fu',
    'ga', 'ge', 'gi', 'go', 'gu', 'ha', 'he', 'hi', 'ho', 'hu',
    'ka', 'ke', 'ki', 'ko', 'ku', 'la', 'le', 'li', 'lo', 'lu',
    'ma', 'me', 'mi', 'mo', 'mu', 'na', 'ne', 'ni', 'no', 'nu',
    'pa', 'pe', 'pi', 'po', 'pu', 'ra', 're', 'ri', 'ro', 'ru',
    'sa', 'se', 'si', 'so', 'su', 'ta', 'te', 'ti', 'to', 'tu',
    'va', 've', 'vi', 'vo', 'vu', 'za', 'ze', 'zi', 'zo', 'zu',
    'al', 'el', 'il', 'ol', 'ul', 'an', 'en', 'in', 'on', 'un',
    'ar', 'er', 'ir', 'or', 'ur', 'ax', 'ex', 'ix', 'ox', 'ux',
]

MIDS = ['', 'n', 'l', 'm', 'r', 's', 'v', 'x', 't', 'k',
        'na', 'la', 'ma', 'ra', 'sa', 'va', 'ta', 'ka',
        'ne', 'le', 'me', 're', 'se', 've', 'te', 'ke',
        'ni', 'li', 'mi', 'ri', 'si', 'vi', 'ti', 'ki',
        'no', 'lo', 'mo', 'ro', 'so', 'vo', 'to', 'ko']

ENDS = ['a', 'e', 'i', 'o', 'ia', 'io', 'is', 'ix', 'us', 'os',
        'ta', 'te', 'ti', 'to', 'la', 'le', 'li', 'lo',
        'na', 'ne', 'ni', 'no', 'ra', 're', 'ri', 'ro',
        'sa', 'se', 'si', 'so', 'va', 've', 'vi', 'vo',
        'ka', 'ke', 'ki', 'ko', 'ma', 'me', 'mi', 'mo',
        'xa', 'xi', 'xo', 'ya', 'yo', 'za', 'ze', 'zo']

BAD_PATTERNS = [
    r'ass', r'shit', r'fuck', r'cunt', r'dick', r'cock', r'piss',
    r'bitch', r'whore', r'slut', r'nazi', r'isis', r'porn',
    r'fick', r'fotze', r'schei', r'merde', r'pute', r'cazzo',
    r'puta', r'mierda', r'culo', r'suka', r'blyat', r'kurwa',
    r'kuso', r'baka', r'sux', r'fuk', r'dik', r'kok', r'kum',
]


def is_clean(name: str) -> bool:
    """Quick offensive check."""
    n = name.lower()
    for p in BAD_PATTERNS:
        if re.search(p, n):
            return False
    return True


def is_pronounceable(name: str) -> bool:
    """Check basic pronounceability."""
    n = name.lower()
    # Must have vowels
    if not re.search(r'[aeiou]', n):
        return False
    # No 4+ consonants in a row
    if re.search(r'[^aeiou]{4,}', n):
        return False
    return True


def generate_names(count: int = 100, min_len: int = 4, max_len: int = 7) -> List[str]:
    """Generate candidate names."""
    names = set()
    attempts = 0
    
    while len(names) < count and attempts < count * 50:
        attempts += 1
        
        # Random strategy
        s = random.randint(1, 4)
        if s == 1:
            name = random.choice(STARTS) + random.choice(ENDS)
        elif s == 2:
            name = random.choice(STARTS) + random.choice(MIDS) + random.choice(ENDS)
        elif s == 3:
            name = random.choice(STARTS) + random.choice(STARTS)
        else:
            name = random.choice(['a','e','i','o','u']) + random.choice(MIDS) + random.choice(ENDS)
        
        name = name.capitalize()
        
        if min_len <= len(name) <= max_len and is_pronounceable(name) and is_clean(name):
            names.add(name)
    
    return sorted(names, key=lambda x: (len(x), x))


def check_domain(name: str, tld: str) -> Tuple[bool, str]:
    """Check domain via DNS."""
    try:
        r = subprocess.run(['dig', '+short', f'{name.lower()}.{tld}'],
                          capture_output=True, text=True, timeout=3)
        has_dns = bool(r.stdout.strip())
        return not has_dns, 'Has DNS' if has_dns else 'No DNS'
    except:
        return None, 'Error'


def check_npm(name: str) -> bool:
    """Check npm registry."""
    try:
        r = subprocess.run(['curl', '-sL', f'https://registry.npmjs.org/{name.lower()}', '--max-time', '3'],
                          capture_output=True, text=True, timeout=5)
        return '"name"' in r.stdout and '"error"' not in r.stdout
    except:
        return False


def check_pypi(name: str) -> bool:
    """Check PyPI registry."""
    try:
        r = subprocess.run(['curl', '-sL', f'https://pypi.org/pypi/{name.lower()}/json', '--max-time', '3'],
                          capture_output=True, text=True, timeout=5)
        return '"info"' in r.stdout and '"message"' not in r.stdout
    except:
        return False


def validate_quick(name: str) -> dict:
    """Quick validation without web search."""
    result = {
        'name': name,
        'domains': {},
        'npm': check_npm(name),
        'pypi': check_pypi(name),
    }
    
    for tld in ['com', 'ai', 'ch']:
        avail, info = check_domain(name, tld)
        result['domains'][tld] = {'available': avail, 'info': info}
    
    return result


def print_validation(name: str, result: dict):
    """Print validation result."""
    print(f"\n{'='*50}")
    print(f"  {name.upper()}")
    print(f"{'='*50}")
    
    print("\n🌐 DOMAINS:")
    for tld, info in result['domains'].items():
        if info['available']:
            print(f"   ✅ .{tld}")
        elif info['available'] is False:
            print(f"   ❌ .{tld}")
        else:
            print(f"   ❓ .{tld}")
    
    print("\n📦 PACKAGES:")
    print(f"   npm:  {'❌ Taken' if result['npm'] else '✅ Free'}")
    print(f"   PyPI: {'❌ Taken' if result['pypi'] else '✅ Free'}")
    
    print("\n⚠️  MANUAL CHECKS NEEDED:")
    print(f"   • Search: \"{name}\" meaning")
    print(f"   • Search: \"{name.upper()}\" acronym stands for")
    print(f"   • Search: \"{name}\" company")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python namecraft.py generate")
        print("  python namecraft.py validate <name>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'generate':
        names = generate_names(50)
        print(f"Generated {len(names)} candidates:\n")
        for i, name in enumerate(names, 1):
            print(f"{i:3}. {name}")
    
    elif cmd == 'validate':
        if len(sys.argv) < 3:
            print("Usage: python namecraft.py validate <name>")
            sys.exit(1)
        
        name = sys.argv[2]
        result = validate_quick(name)
        print_validation(name, result)
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
