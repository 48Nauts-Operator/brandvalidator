"""
Syllable banks for name generation.
Optimized for international pronunciation and pleasing combinations.
"""

# Soft, universally pronounceable starts
VOWEL_STARTS = ['a', 'e', 'i', 'o', 'u', 'ai', 'au', 'ei', 'ou']

SOFT_CONSONANT_STARTS = [
    'ba', 'be', 'bi', 'bo', 'bu',
    'da', 'de', 'di', 'do', 'du',
    'fa', 'fe', 'fi', 'fo', 'fu',
    'ka', 'ke', 'ki', 'ko', 'ku',
    'la', 'le', 'li', 'lo', 'lu',
    'ma', 'me', 'mi', 'mo', 'mu',
    'na', 'ne', 'ni', 'no', 'nu',
    'pa', 'pe', 'pi', 'po', 'pu',
    'ra', 're', 'ri', 'ro', 'ru',
    'sa', 'se', 'si', 'so', 'su',
    'ta', 'te', 'ti', 'to', 'tu',
    'va', 've', 'vi', 'vo', 'vu',
    'za', 'ze', 'zi', 'zo', 'zu',
]

# Tech/modern feeling
TECH_STARTS = [
    'ax', 'ex', 'ix', 'ox', 'ux',
    'cy', 'sy', 'zy',
    'al', 'el', 'il', 'ol', 'ul',
    'an', 'en', 'in', 'on', 'un',
    'ar', 'er', 'ir', 'or', 'ur',
    'co', 'neo', 'pro', 'syn',
]

# Knowledge/wisdom themed
WISDOM_STARTS = [
    'cog', 'men', 'sap', 'ver', 'lum',
    'ora', 'log', 'lex', 'nex', 'cor',
]

# Star/navigation themed
STELLAR_STARTS = [
    'ast', 'cel', 'lun', 'nav', 'ori',
    'pol', 'sol', 'ste', 'voy', 'zen',
]

# Middle connectors
MIDDLES = [
    '', 'n', 'l', 'm', 'r', 's', 'v', 'x', 't', 'k',
    'na', 'la', 'ma', 'ra', 'sa', 'va', 'ta', 'ka',
    'ne', 'le', 'me', 're', 'se', 've', 'te', 'ke',
    'ni', 'li', 'mi', 'ri', 'si', 'vi', 'ti', 'ki',
    'no', 'lo', 'mo', 'ro', 'so', 'vo', 'to', 'ko',
    'nu', 'lu', 'mu', 'ru', 'su', 'vu', 'tu', 'ku',
]

# Pleasing endings
ENDINGS = [
    # Vowel endings (soft, international)
    'a', 'e', 'i', 'o', 'u',
    'ia', 'io', 'ie', 'ea', 'eo',
    
    # Consonant + vowel (clear pronunciation)
    'ta', 'te', 'ti', 'to',
    'la', 'le', 'li', 'lo',
    'na', 'ne', 'ni', 'no',
    'ra', 're', 'ri', 'ro',
    'sa', 'se', 'si', 'so',
    'va', 've', 'vi', 'vo',
    'ka', 'ke', 'ki', 'ko',
    'ma', 'me', 'mi', 'mo',
    'xa', 'xi', 'xo',
    'ya', 'yo',
    'za', 'ze', 'zo',
    
    # Latin/Greek endings (sophisticated)
    'is', 'us', 'os', 'ix', 'ax', 'ex',
    'um', 'on', 'or', 'ar', 'er',
]

# Complete real-word roots with meanings
MEANINGFUL_ROOTS = {
    # Latin
    'lux': 'light',
    'vox': 'voice',
    'rex': 'king',
    'lex': 'law',
    'pax': 'peace',
    'via': 'way/path',
    'ora': 'speak/pray',
    'cor': 'heart',
    'sol': 'sun',
    'lumen': 'light',
    'vita': 'life',
    'vera': 'truth',
    'nova': 'new',
    'aura': 'breeze/atmosphere',
    'opus': 'work',
    'nexus': 'connection',
    'apex': 'peak',
    'axis': 'center line',
    'fons': 'source',
    'mens': 'mind',
    
    # Greek  
    'nous': 'mind/intellect',
    'logos': 'word/reason',
    'sophia': 'wisdom',
    'gnosis': 'knowledge',
    'telos': 'purpose/end',
    'arche': 'origin/principle',
    'kosmos': 'order/universe',
    'psyche': 'soul',
    'kairos': 'right moment',
    'arete': 'excellence',
    
    # Other languages
    'kai': 'ocean (Japanese)',
    'kira': 'light beam (Japanese)',
    'mira': 'wonderful (Latin) / look (Spanish)',
    'alba': 'dawn (Spanish/Italian)',
    'sora': 'sky (Japanese)',
    'tara': 'star (Sanskrit)',
    'zara': 'princess/star (Arabic)',
    'noor': 'light (Arabic)',
    'ayla': 'moonlight (Turkish)',
    'luna': 'moon (Latin/Spanish)',
    
    # Modern tech-friendly
    'sync': 'synchronize',
    'flux': 'flow/change',
    'core': 'center',
    'node': 'connection point',
    'arc': 'curved path',
    'zen': 'meditation/peace',
    'neo': 'new',
    'meta': 'beyond',
    'omni': 'all',
    'uni': 'one',
    'poly': 'many',
}

def get_concept_syllables(concept: str) -> dict:
    """Return syllable banks relevant to concept keywords."""
    concept_lower = concept.lower()
    
    banks = {
        'starts': VOWEL_STARTS + SOFT_CONSONANT_STARTS,
        'middles': MIDDLES,
        'endings': ENDINGS,
    }
    
    # Add themed syllables based on concept
    if any(w in concept_lower for w in ['tech', 'ai', 'software', 'digital', 'data', 'code']):
        banks['starts'].extend(TECH_STARTS)
    
    if any(w in concept_lower for w in ['knowledge', 'wisdom', 'learn', 'memory', 'intelligence', 'mind']):
        banks['starts'].extend(WISDOM_STARTS)
    
    if any(w in concept_lower for w in ['star', 'navigate', 'guide', 'space', 'explore', 'light']):
        banks['starts'].extend(STELLAR_STARTS)
    
    return banks
