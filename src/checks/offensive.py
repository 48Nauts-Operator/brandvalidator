"""
Comprehensive offensive word check across 20+ languages.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class OffenseMatch:
    language: str
    pattern: str
    severity: str  # mild, moderate, severe


@dataclass
class OffensiveReport:
    name: str
    matches: List[OffenseMatch] = field(default_factory=list)
    is_offensive: bool = False
    severity: str = "none"  # none, mild, moderate, severe
    summary: str = ""


# Comprehensive offensive patterns by language
# severity: 1=mild, 2=moderate, 3=severe
OFFENSIVE_PATTERNS = {
    'english': [
        (r'\bass\b', 3), (r'asshole', 3), (r'bastard', 2), (r'bitch', 3),
        (r'bollocks', 2), (r'bugger', 2), (r'bullshit', 2), (r'cock', 3),
        (r'crap', 1), (r'cunt', 3), (r'damn', 1), (r'dick', 3), (r'douche', 2),
        (r'fag', 3), (r'fuck', 3), (r'homo', 2), (r'jerk', 1),
        (r'nigga', 3), (r'nigger', 3), (r'penis', 2), (r'piss', 2),
        (r'prick', 2), (r'pussy', 3), (r'queer', 2), (r'rape', 3),
        (r'retard', 3), (r'shit', 2), (r'slut', 3), (r'tit\b', 2),
        (r'twat', 3), (r'vagina', 2), (r'wank', 2), (r'whore', 3),
    ],
    'german': [
        (r'arsch', 2), (r'fick', 3), (r'fotze', 3), (r'hurensohn', 3),
        (r'schei[sß]', 2), (r'schwanz', 2), (r'schwuchtel', 3),
        (r'wichser', 2), (r'nutte', 3), (r'hure', 3),
    ],
    'french': [
        (r'baise', 3), (r'bordel', 2), (r'connard', 2), (r'connasse', 3),
        (r'couille', 2), (r'cul\b', 2), (r'encul', 3), (r'merde', 2),
        (r'nique', 3), (r'pute', 3), (r'salaud', 2), (r'salope', 3),
    ],
    'spanish': [
        (r'cabr[oó]n', 2), (r'carajo', 2), (r'chingar', 3), (r'ching[ao]', 3),
        (r'cojones', 2), (r'culo', 2), (r'hostia', 1), (r'joder', 2),
        (r'mierda', 2), (r'pendejo', 2), (r'polla', 2), (r'puta', 3),
        (r'verga', 2), (r'coño', 2), (r'gilipollas', 2),
    ],
    'italian': [
        (r'cazzo', 3), (r'coglione', 2), (r'culo', 2), (r'figa', 2),
        (r'merda', 2), (r'minchia', 2), (r'porca', 2), (r'puttana', 3),
        (r'stronz', 2), (r'troia', 3), (r'vaffan', 2),
    ],
    'portuguese': [
        (r'buceta', 3), (r'caralho', 2), (r'foder', 3), (r'merda', 2),
        (r'porra', 2), (r'puta', 3), (r'viado', 3),
    ],
    'dutch': [
        (r'godverdomme', 2), (r'hoer', 3), (r'kut', 3), (r'lull?', 2),
        (r'neuk', 3), (r'pik\b', 2), (r'tering', 2), (r'tief', 2),
    ],
    'russian_translit': [
        (r'blyad', 3), (r'blyat', 3), (r'chlen', 2), (r'ebat', 3),
        (r'govno', 2), (r'khuy', 3), (r'khui', 3), (r'mudak', 2),
        (r'pidar', 3), (r'pizd', 3), (r'suka', 2), (r'zalupa', 2),
        (r'zhopa', 2),
    ],
    'polish': [
        (r'chuj', 3), (r'ciota', 3), (r'kurwa', 3), (r'pierdol', 2),
        (r'skurwysyn', 3), (r'dupa', 2),
    ],
    'turkish': [
        (r'amcik', 3), (r'orospu', 3), (r'sik\b', 3), (r'yarrak', 2),
        (r'got\b', 2),
    ],
    'arabic_translit': [
        (r'kuss', 3), (r'sharmouta', 3), (r'teez', 2), (r'zubi', 2),
        (r'kelb', 2), (r'ibn.*haram', 3),
    ],
    'hindi_urdu_translit': [
        (r'bhenchod', 3), (r'bhosdike', 3), (r'chod', 3), (r'choot', 3),
        (r'chutiya', 3), (r'gaand', 2), (r'harami', 2), (r'lund', 2),
        (r'madar', 3), (r'randi', 3),
    ],
    'japanese_romaji': [
        (r'\bbaka\b', 1), (r'chikan', 2), (r'kuso', 2), (r'yariman', 3),
        (r'ketsu', 1), (r'kichiku', 2),
    ],
    'chinese_pinyin': [
        (r'\bcao\b', 3), (r'diao', 2), (r'sha ?bi', 3), (r'tamade', 2),
        (r'niubi', 1),
    ],
    'korean_romanized': [
        (r'shibal', 3), (r'ssibal', 3), (r'gaesaekki', 3), (r'byeongsin', 2),
    ],
    'sounds_like_bad': [
        # Phonetic patterns that sound like bad words
        (r'^ass', 2), (r'ass$', 2), (r'sux', 2), (r'fuk', 3), (r'fuc', 3),
        (r'phuck', 3), (r'phuk', 3), (r'dik\b', 2), (r'\bkok', 2),
        (r'kum\b', 2), (r'\bcum', 2), (r'fag', 3), (r'dyke', 2),
        (r'whor', 3), (r'shyt', 2), (r'azz', 2),
    ],
    'violence_terror': [
        (r'\bkill', 3), (r'murder', 3), (r'terror', 3), (r'\bisis\b', 3),
        (r'qaeda', 3), (r'jihad', 2), (r'nazi', 3), (r'hitler', 3),
        (r'genocide', 3), (r'massacre', 3),
    ],
}

# Safe words that might trigger false positives
SAFE_WORDS = {
    'assist', 'assistant', 'bass', 'class', 'classic', 'grass',
    'mass', 'pass', 'passage', 'compass', 'bypass', 'trespass',
    'cockpit', 'peacock', 'hancock', 'shuttlecock',
    'scunthorpe', 'penistone', 'sussex', 'essex', 'middlesex',
    'analysis', 'analyst', 'canal', 'arsenal',
    'therapist', 'grape', 'drape', 'scrape',
    'hello', 'shell', 'dwell', 'swell',
    'assume', 'assembly', 'assess', 'asset',
    'cocoa', 'cocktail', 'hancock', 'hitchcock',
    'disco', 'mascot', 'rascal',
    'button', 'cotton', 'mutton',
}


def check_offensive_all_languages(name: str) -> OffensiveReport:
    """
    Check name for offensive content in all languages.
    
    Returns:
        OffensiveReport with findings
    """
    report = OffensiveReport(name=name)
    name_lower = name.lower()
    
    # Skip safe words
    if name_lower in SAFE_WORDS:
        report.summary = "✅ Clean (known safe word)"
        return report
    
    max_severity = 0
    
    for language, patterns in OFFENSIVE_PATTERNS.items():
        for pattern, severity in patterns:
            try:
                if re.search(pattern, name_lower):
                    # Check if it's a safe word context
                    is_safe = any(safe in name_lower for safe in SAFE_WORDS)
                    if not is_safe:
                        sev_str = {1: 'mild', 2: 'moderate', 3: 'severe'}[severity]
                        report.matches.append(OffenseMatch(
                            language=language,
                            pattern=pattern,
                            severity=sev_str,
                        ))
                        max_severity = max(max_severity, severity)
            except re.error:
                pass
    
    # Set overall status
    report.is_offensive = len(report.matches) > 0
    report.severity = {0: 'none', 1: 'mild', 2: 'moderate', 3: 'severe'}[max_severity]
    
    # Generate summary
    if report.matches:
        langs = list(set(m.language for m in report.matches))
        report.summary = f"🚨 OFFENSIVE ({report.severity}): Issues in {', '.join(langs[:3])}"
    else:
        report.summary = "✅ Clean across all languages"
    
    return report
