"""
Trademark conflict checking.
"""

import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TrademarkMatch:
    name: str
    country: str
    class_codes: List[str]  # Nice Classification
    status: str  # registered, pending, expired
    owner: Optional[str] = None
    risk_level: str = "medium"


@dataclass
class TrademarkReport:
    name: str
    matches: List[TrademarkMatch] = field(default_factory=list)
    has_conflicts: bool = False
    same_class: bool = False  # Class 9 (software) or 42 (SaaS)
    summary: str = ""


# Nice Classification codes relevant to software/SaaS
SOFTWARE_CLASSES = ['9', '35', '38', '42']

# Known trademark conflicts (offline check)
KNOWN_TRADEMARKS = {
    'meta': (['9', '35', '38', '42'], 'Meta Platforms', 'high'),
    'apple': (['9', '35', '38', '42'], 'Apple Inc', 'high'),
    'google': (['9', '35', '38', '42'], 'Google LLC', 'high'),
    'amazon': (['9', '35', '38', '42'], 'Amazon', 'high'),
    'microsoft': (['9', '35', '38', '42'], 'Microsoft', 'high'),
    'oracle': (['9', '42'], 'Oracle', 'high'),
    'slack': (['9', '38', '42'], 'Salesforce', 'high'),
    'notion': (['9', '42'], 'Notion Labs', 'high'),
    'zoom': (['9', '38', '42'], 'Zoom Video', 'high'),
    'stripe': (['9', '36', '42'], 'Stripe', 'high'),
    'docker': (['9', '42'], 'Docker', 'high'),
    'redis': (['9', '42'], 'Redis Ltd', 'high'),
    'openai': (['9', '42'], 'OpenAI', 'high'),
    'anthropic': (['9', '42'], 'Anthropic', 'high'),
    'stella': (['32', '33'], 'AB InBev (Stella Artois)', 'medium'),  # Beer
    'aurora': (['9', '12', '42'], 'Various', 'medium'),
    'nova': (['9', '12'], 'Various', 'medium'),
    'luna': (['9', '42'], 'Various', 'medium'),
    'nautical': (['9', '12', '42'], 'Various', 'low'),
    'nauticstar': (['12'], 'NauticStar Boats', 'low'),  # Class 12 = vehicles
}


def check_offline_trademarks(name: str) -> List[TrademarkMatch]:
    """Check against known trademark database."""
    matches = []
    name_lower = name.lower()
    
    # Direct match
    if name_lower in KNOWN_TRADEMARKS:
        classes, owner, risk = KNOWN_TRADEMARKS[name_lower]
        matches.append(TrademarkMatch(
            name=name,
            country='GLOBAL',
            class_codes=classes,
            status='registered',
            owner=owner,
            risk_level=risk,
        ))
    
    # Similar matches (contains)
    for tm, (classes, owner, risk) in KNOWN_TRADEMARKS.items():
        if tm != name_lower and len(name_lower) >= 4 and len(tm) >= 4:
            if name_lower.startswith(tm) or tm.startswith(name_lower):
                matches.append(TrademarkMatch(
                    name=tm,
                    country='GLOBAL',
                    class_codes=classes,
                    status='registered',
                    owner=owner,
                    risk_level='low',  # Partial match is lower risk
                ))
    
    return matches


def check_trademarks(name: str, classes: List[str] = None) -> TrademarkReport:
    """
    Check for trademark conflicts.
    
    Args:
        name: The name to check
        classes: Nice Classification codes to focus on (default: software/SaaS)
    
    Returns:
        TrademarkReport with findings
    """
    if classes is None:
        classes = SOFTWARE_CLASSES
    
    report = TrademarkReport(name=name)
    
    # Offline check
    offline_matches = check_offline_trademarks(name)
    report.matches.extend(offline_matches)
    
    # Check for software/SaaS class conflicts
    for match in report.matches:
        if match.risk_level == 'high':
            report.has_conflicts = True
        
        # Check if any matching classes overlap with our target classes
        for mc in match.class_codes:
            if mc in classes:
                report.same_class = True
                break
    
    # Generate summary
    if report.same_class and report.has_conflicts:
        report.summary = f"🚨 HIGH RISK: Trademark conflict in software class ({report.matches[0].owner})"
    elif report.has_conflicts:
        report.summary = f"⚠️ Trademark exists but different class"
    elif report.matches:
        report.summary = f"ℹ️ Similar trademark found (low risk)"
    else:
        report.summary = "✅ No known trademark conflicts"
    
    return report
