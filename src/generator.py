"""
Core name generation engine.
"""

import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

from .syllables import (
    get_concept_syllables,
    MEANINGFUL_ROOTS,
    VOWEL_STARTS,
    SOFT_CONSONANT_STARTS,
)
from .offensive import is_offensive, check_negative_meanings


@dataclass
class GeneratedName:
    name: str
    score: int = 0
    meaning: Optional[str] = None
    domains: Dict[str, bool] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


def is_pronounceable(name: str) -> bool:
    """
    Check if name is easily pronounceable across languages.
    """
    name = name.lower()
    
    # Must have vowels
    vowels = set('aeiou')
    if not any(c in vowels for c in name):
        return False
    
    # No more than 3 consonants in a row
    consonant_count = 0
    for c in name:
        if c not in vowels:
            consonant_count += 1
            if consonant_count > 3:
                return False
        else:
            consonant_count = 0
    
    # No more than 2 vowels in a row (except common combos)
    vowel_count = 0
    for c in name:
        if c in vowels:
            vowel_count += 1
            if vowel_count > 2:
                return False
        else:
            vowel_count = 0
    
    return True


def check_meaning(name: str) -> Optional[str]:
    """
    Check if name has a known positive meaning.
    """
    name_lower = name.lower()
    
    # Direct match
    if name_lower in MEANINGFUL_ROOTS:
        return MEANINGFUL_ROOTS[name_lower]
    
    # Starts with meaningful root
    for root, meaning in MEANINGFUL_ROOTS.items():
        if len(root) >= 3:
            if name_lower.startswith(root):
                return f"From '{root}': {meaning}"
            if root.startswith(name_lower):
                return f"Short for '{root}': {meaning}"
    
    return None


def generate_names(
    concept: str = "",
    count: int = 500,
    min_length: int = 4,
    max_length: int = 7,
    require_meaning: bool = False,
) -> List[GeneratedName]:
    """
    Generate candidate brand names.
    """
    syllables = get_concept_syllables(concept)
    starts = syllables['starts']
    middles = syllables['middles']
    endings = syllables['endings']
    
    names: Set[str] = set()
    results: List[GeneratedName] = []
    
    # Also include meaningful roots directly
    for root in MEANINGFUL_ROOTS.keys():
        if min_length <= len(root) <= max_length:
            names.add(root.capitalize())
    
    # Generate combinations
    attempts = 0
    max_attempts = count * 50
    
    while len(names) < count and attempts < max_attempts:
        attempts += 1
        
        # Various generation strategies
        strategy = random.randint(1, 7)
        
        if strategy == 1:
            # start + ending
            name = random.choice(starts) + random.choice(endings)
        
        elif strategy == 2:
            # start + middle + ending
            name = random.choice(starts) + random.choice(middles) + random.choice(endings)
        
        elif strategy == 3:
            # Two starts
            name = random.choice(starts) + random.choice(starts)
        
        elif strategy == 4:
            # Vowel start (softer)
            name = random.choice(VOWEL_STARTS) + random.choice(middles) + random.choice(endings)
        
        elif strategy == 5:
            # Double consonant middle (stronger)
            doubles = ['ll', 'rr', 'ss', 'tt', 'nn', 'mm']
            name = random.choice(starts) + random.choice(doubles) + random.choice(['a', 'e', 'i', 'o'])
        
        elif strategy == 6:
            # Meaningful root + ending
            root = random.choice(list(MEANINGFUL_ROOTS.keys()))
            if len(root) < max_length - 1:
                name = root + random.choice(['a', 'i', 'o', 'ia', 'io'])
            else:
                name = root
        
        else:
            # Three syllables for longer names
            name = random.choice(VOWEL_STARTS) + random.choice(middles) + random.choice(middles) + random.choice(['a', 'e', 'o'])
        
        name = name.capitalize()
        
        # Validate
        if not (min_length <= len(name) <= max_length):
            continue
        
        if name in names:
            continue
        
        if not is_pronounceable(name):
            continue
        
        # Check offensive
        offensive, reason = is_offensive(name)
        if offensive:
            continue
        
        # Check negative meanings
        negative, neg_reason = check_negative_meanings(name)
        if negative:
            continue
        
        names.add(name)
        
        # Get meaning
        meaning = check_meaning(name)
        
        # Skip if meaning required but none found
        if require_meaning and not meaning:
            continue
        
        results.append(GeneratedName(
            name=name,
            meaning=meaning,
        ))
    
    return results


def score_name(name: GeneratedName) -> int:
    """
    Calculate overall score for a name.
    """
    score = 0
    
    # Length (shorter is better)
    length = len(name.name)
    if length <= 4:
        score += 25
    elif length <= 5:
        score += 20
    elif length <= 6:
        score += 15
    elif length <= 7:
        score += 10
    else:
        score += 5
    
    # Has meaning
    if name.meaning:
        score += 30
    
    # Starts with vowel (softer, friendlier)
    if name.name[0].lower() in 'aeiou':
        score += 5
    
    # Ends with vowel (easier to say)
    if name.name[-1].lower() in 'aeiou':
        score += 5
    
    # Domain availability
    for tld, available in name.domains.items():
        if available:
            if tld == 'com':
                score += 30
            elif tld == 'ai':
                score += 25
            elif tld == 'ch':
                score += 20
            else:
                score += 10
    
    name.score = score
    return score
