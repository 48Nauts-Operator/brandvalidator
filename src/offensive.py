"""
Multi-language offensive word filter.
Checks against bad words in 20+ languages.
"""

import re
from typing import Set

# Comprehensive bad word patterns by language/category
# Using patterns instead of literal words for flexibility

BAD_PATTERNS = {
    'english': [
        r'\bass\b', r'\basses\b', r'asshole', r'bastard', r'bitch', r'bloody',
        r'bollocks', r'bugger', r'bullshit', r'cock', r'crap', r'cunt',
        r'damn', r'dick', r'douche', r'fag', r'fuck', r'hell', r'homo',
        r'jerk', r'nigga', r'nigger', r'penis', r'piss', r'prick', r'pussy',
        r'queer', r'rape', r'retard', r'sex', r'shit', r'slut', r'tit',
        r'twat', r'vagina', r'wank', r'whore',
    ],
    'german': [
        r'arsch', r'fick', r'fotze', r'hurensohn', r'schei[sß]', r'schwanz',
        r'schwuchtel', r'wichser', r'nutte', r'hure',
    ],
    'french': [
        r'baise', r'bordel', r'connard', r'conne', r'couille', r'cul',
        r'encul', r'merde', r'nique', r'pute', r'salaud', r'salope',
    ],
    'spanish': [
        r'cabr[oó]n', r'carajo', r'chingar', r'ching[ao]', r'cojones',
        r'culo', r'hostia', r'joder', r'mierda', r'pendejo', r'polla',
        r'puta', r'verga',
    ],
    'italian': [
        r'cazzo', r'coglione', r'culo', r'figa', r'merda', r'minchia',
        r'porca', r'puttana', r'stronz', r'troia', r'vaffan',
    ],
    'portuguese': [
        r'buceta', r'caralho', r'foder', r'merda', r'porra', r'puta',
        r'viado',
    ],
    'dutch': [
        r'godverdomme', r'hoer', r'kut', r'lull?', r'neuk', r'pik',
        r'tering', r'tief',
    ],
    'russian_translit': [
        r'blyad', r'blyat', r'chlen', r'ebat', r'govno', r'khuy', r'khui',
        r'mudak', r'pidar', r'pizd', r'suka', r'zalupa', r'zhopa',
    ],
    'polish': [
        r'chuj', r'ciota', r'kurwa', r'pierdol', r'skurwysyn',
    ],
    'turkish': [
        r'amcik', r'orospu', r'sik', r'yarrak',
    ],
    'arabic_translit': [
        r'kuss', r'sharmouta', r'teez', r'zubi',
    ],
    'hindi_urdu_translit': [
        r'bhenchod', r'bhosdike', r'chod', r'choot', r'chutiya', r'gaand',
        r'harami', r'lund', r'madar', r'randi',
        r'dushman', r'dushmani',  # enemy/enmity - not offensive but negative
    ],
    'japanese_romaji': [
        r'baka', r'chikan', r'kuso', r'yariman',
    ],
    'chinese_pinyin': [
        r'cao', r'diao', r'gou', r'sha ?bi', r'tamade',
    ],
    'korean_romanized': [
        r'shibal', r'ssibal', r'gaesaekki',
    ],
    'violence': [
        r'kill', r'murder', r'death', r'dead', r'terror', r'bomb',
        r'shoot', r'gun', r'knife', r'stab', r'blood', r'gore',
    ],
    'political': [
        r'nazi', r'hitler', r'isis', r'qaeda', r'taliban', r'jihad',
    ],
    'sounds_like': [
        # Words that sound like bad words
        r'^ass', r'ass$', r'sux', r'fuk', r'fuc', r'phuck', r'phuk',
        r'dik', r'kok', r'kum', r'cum', r'fag', r'dyke',
    ],
}

# Common false positives to allow
SAFE_WORDS = {
    'assist', 'assistant', 'bass', 'class', 'classic', 'grass',
    'mass', 'pass', 'passage', 'assassin', 'compass',
    'cockpit', 'peacock', 'hancock', 'scunthorpe',
    'analysis', 'analyst', 'canal',
    'therapist', 'grape', 'drape',
    'hello', 'shell', 'dwell',
    'assume', 'assembly',
}


def compile_patterns() -> list:
    """Compile all bad patterns into regex objects."""
    compiled = []
    for category, patterns in BAD_PATTERNS.items():
        for pattern in patterns:
            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), category))
            except re.error:
                pass  # Skip invalid patterns
    return compiled


_COMPILED_PATTERNS = None


def get_compiled_patterns() -> list:
    """Get cached compiled patterns."""
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = compile_patterns()
    return _COMPILED_PATTERNS


def is_offensive(name: str, strict: bool = True) -> tuple[bool, str]:
    """
    Check if name is offensive in any language.
    
    Returns:
        Tuple of (is_offensive: bool, reason: str)
    """
    name_lower = name.lower()
    
    # Check safe words first
    if name_lower in SAFE_WORDS:
        return False, ""
    
    # Check against all patterns
    for pattern, category in get_compiled_patterns():
        if pattern.search(name_lower):
            return True, f"Matched '{category}' pattern"
    
    # Additional checks for strict mode
    if strict:
        # Check if name contains "ass" not at word boundary
        if 'ass' in name_lower and name_lower not in SAFE_WORDS:
            # More specific check
            if not any(safe in name_lower for safe in ['class', 'pass', 'mass', 'bass', 'grass']):
                return True, "Contains 'ass' substring"
    
    return False, ""


def check_negative_meanings(name: str) -> tuple[bool, str]:
    """
    Check for words with negative meanings (not offensive, but bad for branding).
    """
    negative_words = {
        'war', 'hate', 'fear', 'pain', 'sick', 'fail', 'loss', 'lost',
        'dark', 'dead', 'doom', 'evil', 'ugly', 'poor', 'weak', 'slow',
        'dumb', 'fool', 'fake', 'scam', 'spam', 'junk', 'trash', 'waste',
        'enemy', 'enmi',  # Urdu for enmity
    }
    
    name_lower = name.lower()
    for word in negative_words:
        if word in name_lower:
            return True, f"Contains negative word: {word}"
    
    return False, ""
