"""
Phonetic analysis and conflict checking.
Checks if name sounds like existing brands or problematic words.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PhoneticMatch:
    similar_to: str
    type: str  # brand, word, offensive
    phonetic_code: str
    description: Optional[str] = None


@dataclass
class PhoneticReport:
    name: str
    phonetic_code: str
    matches: List[PhoneticMatch] = field(default_factory=list)
    is_pronounceable: bool = True
    pronunciation_notes: List[str] = field(default_factory=list)
    summary: str = ""


def soundex(name: str) -> str:
    """
    Generate Soundex code for a name.
    Soundex encodes names by sound, ignoring vowels after first letter.
    """
    if not name:
        return ""
    
    name = name.upper()
    
    # Soundex coding
    coding = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',
    }
    
    # Keep first letter
    result = name[0]
    
    # Encode rest
    prev_code = coding.get(name[0], '')
    for char in name[1:]:
        code = coding.get(char, '')
        if code and code != prev_code:
            result += code
        prev_code = code if code else prev_code
    
    # Pad/truncate to 4 characters
    result = (result + '000')[:4]
    
    return result


def metaphone(name: str) -> str:
    """
    Simple Metaphone encoding for phonetic matching.
    More accurate than Soundex for modern names.
    """
    if not name:
        return ""
    
    name = name.upper()
    result = []
    i = 0
    
    # Simple rules
    while i < len(name):
        c = name[i]
        next_c = name[i + 1] if i + 1 < len(name) else ''
        
        if c in 'AEIOU':
            if i == 0:
                result.append(c)
        elif c == 'B':
            if i == len(name) - 1 and name[i-1:i] == 'M':
                pass  # Silent B after M
            else:
                result.append('B')
        elif c in 'CK':
            if c == 'C' and next_c == 'H':
                result.append('X')
                i += 1
            elif c == 'C' and next_c in 'IEY':
                result.append('S')
            else:
                result.append('K')
        elif c == 'D':
            if next_c == 'G':
                result.append('J')
                i += 1
            else:
                result.append('T')
        elif c in 'FJ':
            result.append(c)
        elif c == 'G':
            if next_c in 'IEY':
                result.append('J')
            else:
                result.append('K')
        elif c == 'H':
            if i == 0 or name[i-1] not in 'AEIOU':
                result.append('H')
        elif c == 'L':
            result.append('L')
        elif c in 'MN':
            result.append(c)
        elif c == 'P':
            if next_c == 'H':
                result.append('F')
                i += 1
            else:
                result.append('P')
        elif c == 'Q':
            result.append('K')
        elif c == 'R':
            result.append('R')
        elif c == 'S':
            if next_c == 'H':
                result.append('X')
                i += 1
            else:
                result.append('S')
        elif c == 'T':
            if next_c == 'H':
                result.append('0')  # TH sound
                i += 1
            else:
                result.append('T')
        elif c == 'V':
            result.append('F')
        elif c == 'W':
            if next_c in 'AEIOU':
                result.append('W')
        elif c == 'X':
            result.append('KS')
        elif c == 'Y':
            if next_c in 'AEIOU':
                result.append('Y')
        elif c == 'Z':
            result.append('S')
        
        i += 1
    
    return ''.join(result)


# Known brand phonetics for comparison
BRAND_PHONETICS = {
    'M300': [('Meta', 'tech giant')],
    'A140': [('Apple', 'tech giant')],
    'G240': [('Google', 'tech giant')],
    'S420': [('Slack', 'messaging'), ('Stack', 'tech')],
    'N350': [('Notion', 'productivity')],
    'Z500': [('Zoom', 'video')],
    'S361': [('Stripe', 'payments')],
    'O624': [('Oracle', 'database')],
}


def check_pronounceability(name: str) -> tuple[bool, List[str]]:
    """Check if name is easily pronounceable."""
    notes = []
    is_ok = True
    name_lower = name.lower()
    
    # Check for difficult consonant clusters
    hard_clusters = ['xk', 'zx', 'qx', 'xq', 'zk', 'kz', 'xz', 'zxz', 'xzx']
    for cluster in hard_clusters:
        if cluster in name_lower:
            notes.append(f"Difficult cluster: '{cluster}'")
            is_ok = False
    
    # Check consonant run length
    consonants = 0
    for c in name_lower:
        if c not in 'aeiou':
            consonants += 1
            if consonants > 3:
                notes.append("Too many consecutive consonants")
                is_ok = False
                break
        else:
            consonants = 0
    
    # Check for ambiguous pronunciations
    ambiguous = {
        'gh': 'GH can be silent or F sound',
        'ough': 'OUGH has multiple pronunciations',
        'ei': 'EI can be AY or EE',
        'ie': 'IE can be EE or AY',
    }
    for pattern, note in ambiguous.items():
        if pattern in name_lower:
            notes.append(note)
    
    return is_ok, notes


def check_phonetic_conflicts(name: str) -> PhoneticReport:
    """
    Check for phonetic conflicts with existing brands.
    
    Returns:
        PhoneticReport with findings
    """
    report = PhoneticReport(name=name, phonetic_code='')
    
    # Generate phonetic codes
    sdx = soundex(name)
    mph = metaphone(name)
    report.phonetic_code = f"Soundex: {sdx}, Metaphone: {mph}"
    
    # Check pronounceability
    report.is_pronounceable, report.pronunciation_notes = check_pronounceability(name)
    
    # Check against known brands
    if sdx in BRAND_PHONETICS:
        for brand, desc in BRAND_PHONETICS[sdx]:
            report.matches.append(PhoneticMatch(
                similar_to=brand,
                type='brand',
                phonetic_code=sdx,
                description=f"Sounds like {brand} ({desc})"
            ))
    
    # Generate summary
    if not report.is_pronounceable:
        report.summary = f"⚠️ Pronunciation issues: {'; '.join(report.pronunciation_notes[:2])}"
    elif report.matches:
        similar = report.matches[0].similar_to
        report.summary = f"ℹ️ Sounds similar to: {similar}"
    else:
        report.summary = "✅ Clear pronunciation, no conflicts"
    
    return report
