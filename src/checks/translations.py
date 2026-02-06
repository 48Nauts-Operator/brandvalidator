"""
Translation and meaning checks across multiple languages.
"""

import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class TranslationResult:
    language: str
    meaning: Optional[str]
    is_word: bool  # Is it a real word in this language?
    sentiment: str  # positive, negative, neutral, unknown
    source: str  # Where we found this


@dataclass 
class TranslationReport:
    name: str
    found_meanings: List[TranslationResult] = field(default_factory=list)
    has_negative: bool = False
    has_positive: bool = False
    summary: str = ""


# Known word dictionaries (offline fast check)
KNOWN_WORDS = {
    'english': {
        'nova': ('new, star explosion', 'positive'),
        'luna': ('moon', 'positive'),
        'vera': ('truth', 'positive'),
        'vita': ('life', 'positive'),
        'core': ('center, essential', 'positive'),
        'apex': ('peak, highest point', 'positive'),
        'flux': ('flow, change', 'neutral'),
        'node': ('connection point', 'neutral'),
        'sync': ('synchronize', 'neutral'),
        'meta': ('beyond, self-referential', 'neutral'),
        'void': ('empty, nothing', 'negative'),
        'null': ('nothing, zero', 'negative'),
        'dead': ('not alive', 'negative'),
        'fail': ('not succeed', 'negative'),
    },
    'latin': {
        'lux': ('light', 'positive'),
        'vox': ('voice', 'positive'),
        'rex': ('king', 'positive'),
        'lex': ('law', 'neutral'),
        'pax': ('peace', 'positive'),
        'via': ('way, path', 'positive'),
        'ora': ('speak, pray', 'positive'),
        'cor': ('heart', 'positive'),
        'sol': ('sun', 'positive'),
        'mens': ('mind', 'positive'),
        'opus': ('work, masterpiece', 'positive'),
        'nexus': ('connection', 'positive'),
        'axis': ('center line', 'neutral'),
        'fons': ('source, fountain', 'positive'),
        'mors': ('death', 'negative'),
        'bellum': ('war', 'negative'),
    },
    'spanish': {
        'sol': ('sun', 'positive'),
        'luna': ('moon', 'positive'),
        'alba': ('dawn', 'positive'),
        'vida': ('life', 'positive'),
        'amor': ('love', 'positive'),
        'luz': ('light', 'positive'),
        'oro': ('gold', 'positive'),
        'rio': ('river', 'positive'),
        'mar': ('sea', 'positive'),
        'mal': ('bad, evil', 'negative'),
        'feo': ('ugly', 'negative'),
        'culo': ('butt (vulgar)', 'negative'),
        'puta': ('prostitute', 'negative'),
    },
    'italian': {
        'vita': ('life', 'positive'),
        'sole': ('sun', 'positive'),
        'alba': ('dawn', 'positive'),
        'brio': ('vigor, vivacity', 'positive'),
        'coda': ('tail, ending', 'neutral'),
        'alto': ('high', 'positive'),
        'bella': ('beautiful', 'positive'),
        'cazzo': ('penis (vulgar)', 'negative'),
        'merda': ('shit', 'negative'),
    },
    'german': {
        'licht': ('light', 'positive'),
        'kraft': ('power, strength', 'positive'),
        'stern': ('star', 'positive'),
        'wald': ('forest', 'positive'),
        'zeit': ('time', 'neutral'),
        'tod': ('death', 'negative'),
        'krieg': ('war', 'negative'),
        'arsch': ('ass', 'negative'),
    },
    'french': {
        'vie': ('life', 'positive'),
        'sol': ('ground, soil', 'neutral'),
        'eau': ('water', 'positive'),
        'feu': ('fire', 'neutral'),
        'roi': ('king', 'positive'),
        'loi': ('law', 'neutral'),
        'mal': ('bad, pain', 'negative'),
        'merde': ('shit', 'negative'),
    },
    'japanese_romaji': {
        'kai': ('ocean, change', 'positive'),
        'kira': ('sparkle, glitter', 'positive'),
        'sora': ('sky', 'positive'),
        'hana': ('flower', 'positive'),
        'yuki': ('snow', 'positive'),
        'neko': ('cat', 'positive'),
        'baka': ('idiot', 'negative'),
        'kuso': ('shit', 'negative'),
    },
    'arabic_translit': {
        'noor': ('light', 'positive'),
        'zara': ('princess, star', 'positive'),
        'amir': ('prince', 'positive'),
        'salaam': ('peace', 'positive'),
        'haram': ('forbidden', 'negative'),
    },
    'hindi_urdu': {
        'dil': ('heart', 'positive'),
        'pyar': ('love', 'positive'),
        'jaan': ('life, beloved', 'positive'),
        'dushman': ('enemy', 'negative'),
        'enmi': ('enmity', 'negative'),  # The one we caught!
    },
    'tamil': {
        'nool': ('thread, yarn', 'neutral'),
        'sol': ('word', 'neutral'),
        'kan': ('eye', 'neutral'),
    },
    'portuguese': {
        'sol': ('sun', 'positive'),
        'lua': ('moon', 'positive'),
        'vida': ('life', 'positive'),
        'amor': ('love', 'positive'),
    },
    'dutch': {
        'zon': ('sun', 'positive'),
        'licht': ('light', 'positive'),
        'kut': ('vulgar term', 'negative'),
    },
    'russian_translit': {
        'mir': ('peace, world', 'positive'),
        'svet': ('light', 'positive'),
        'noch': ('night', 'neutral'),
        'suka': ('bitch', 'negative'),
    },
    'chinese_pinyin': {
        'ming': ('bright', 'positive'),
        'hua': ('flower, China', 'positive'),
        'long': ('dragon', 'positive'),
        'si': ('death (四 sì)', 'negative'),
    },
    'korean_romanized': {
        'hana': ('one, flower', 'positive'),
        'dal': ('moon', 'positive'),
        'sarang': ('love', 'positive'),
    },
    'turkish': {
        'ayla': ('moonlight', 'positive'),
        'deniz': ('sea', 'positive'),
        'gul': ('rose', 'positive'),
    },
    'greek_translit': {
        'zoe': ('life', 'positive'),
        'sofia': ('wisdom', 'positive'),
        'kosmos': ('order, universe', 'positive'),
        'logos': ('word, reason', 'positive'),
        'nous': ('mind, intellect', 'positive'),
    },
}


def check_offline_dictionaries(name: str) -> List[TranslationResult]:
    """Check against our offline word dictionaries."""
    results = []
    name_lower = name.lower()
    
    for language, words in KNOWN_WORDS.items():
        # Direct match
        if name_lower in words:
            meaning, sentiment = words[name_lower]
            results.append(TranslationResult(
                language=language,
                meaning=meaning,
                is_word=True,
                sentiment=sentiment,
                source='offline_dictionary'
            ))
        
        # Partial match (name contains or is contained by word)
        for word, (meaning, sentiment) in words.items():
            if len(word) >= 3 and word != name_lower:
                if name_lower.startswith(word) or word.startswith(name_lower):
                    results.append(TranslationResult(
                        language=language,
                        meaning=f"Similar to '{word}': {meaning}",
                        is_word=False,
                        sentiment=sentiment,
                        source='offline_partial'
                    ))
    
    return results


def check_translations(name: str, use_api: bool = False) -> TranslationReport:
    """
    Check name for meanings across multiple languages.
    
    Args:
        name: The name to check
        use_api: Whether to use online translation APIs (slower but more comprehensive)
    
    Returns:
        TranslationReport with all findings
    """
    report = TranslationReport(name=name)
    
    # Offline dictionary check (fast)
    offline_results = check_offline_dictionaries(name)
    report.found_meanings.extend(offline_results)
    
    # Check for negatives/positives
    for result in report.found_meanings:
        if result.sentiment == 'negative':
            report.has_negative = True
        elif result.sentiment == 'positive':
            report.has_positive = True
    
    # Generate summary
    if report.has_negative:
        neg_langs = [r.language for r in report.found_meanings if r.sentiment == 'negative']
        report.summary = f"⚠️ NEGATIVE meanings found in: {', '.join(neg_langs)}"
    elif report.has_positive:
        pos = [r for r in report.found_meanings if r.sentiment == 'positive']
        if pos:
            report.summary = f"✅ Positive meaning: {pos[0].meaning} ({pos[0].language})"
    elif report.found_meanings:
        report.summary = f"ℹ️ Found in {len(report.found_meanings)} language(s)"
    else:
        report.summary = "✅ No known meanings (invented word)"
    
    return report
