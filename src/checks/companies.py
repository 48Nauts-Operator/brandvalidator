"""
Check for existing companies, brands, and products with similar names.
"""

import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CompanyMatch:
    name: str
    type: str  # company, product, brand, service
    industry: str
    url: Optional[str] = None
    description: Optional[str] = None
    risk_level: str = "low"  # low, medium, high


@dataclass
class CompanyReport:
    name: str
    matches: List[CompanyMatch] = field(default_factory=list)
    has_conflicts: bool = False
    same_industry: bool = False
    summary: str = ""


def search_web_for_company(name: str) -> List[dict]:
    """
    Search web for existing companies with this name.
    Uses curl to search DuckDuckGo HTML (no API needed).
    """
    results = []
    
    try:
        # Search for company
        search_query = f"{name} company"
        cmd = [
            'curl', '-sL', '-A', 'Mozilla/5.0',
            f'https://html.duckduckgo.com/html/?q={search_query}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        html = result.stdout
        
        # Extract result titles and snippets
        # Pattern for DuckDuckGo HTML results
        title_pattern = r'class="result__title"[^>]*>.*?<a[^>]*>([^<]+)</a>'
        snippet_pattern = r'class="result__snippet"[^>]*>([^<]+)'
        url_pattern = r'class="result__url"[^>]*>([^<]+)'
        
        titles = re.findall(title_pattern, html, re.DOTALL)
        snippets = re.findall(snippet_pattern, html, re.DOTALL)
        urls = re.findall(url_pattern, html, re.DOTALL)
        
        for i, title in enumerate(titles[:5]):
            results.append({
                'title': title.strip(),
                'snippet': snippets[i].strip() if i < len(snippets) else '',
                'url': urls[i].strip() if i < len(urls) else '',
            })
            
    except Exception as e:
        pass
    
    return results


# Known tech companies and products (offline fast check)
KNOWN_TECH_BRANDS = {
    'meta': ('Meta Platforms (Facebook)', 'tech', 'high'),
    'apple': ('Apple Inc', 'tech', 'high'),
    'google': ('Google/Alphabet', 'tech', 'high'),
    'amazon': ('Amazon', 'tech', 'high'),
    'microsoft': ('Microsoft', 'tech', 'high'),
    'oracle': ('Oracle Corporation', 'tech', 'high'),
    'salesforce': ('Salesforce', 'tech', 'high'),
    'slack': ('Slack (Salesforce)', 'tech', 'high'),
    'notion': ('Notion', 'tech', 'high'),
    'figma': ('Figma (Adobe)', 'tech', 'high'),
    'linear': ('Linear', 'tech', 'high'),
    'vercel': ('Vercel', 'tech', 'high'),
    'stripe': ('Stripe', 'fintech', 'high'),
    'plaid': ('Plaid', 'fintech', 'high'),
    'zoom': ('Zoom Video', 'tech', 'high'),
    'asana': ('Asana', 'tech', 'high'),
    'airtable': ('Airtable', 'tech', 'high'),
    'canva': ('Canva', 'tech', 'high'),
    'miro': ('Miro', 'tech', 'high'),
    'loom': ('Loom', 'tech', 'high'),
    'retool': ('Retool', 'tech', 'high'),
    'supabase': ('Supabase', 'tech', 'high'),
    'prisma': ('Prisma', 'tech', 'high'),
    'docker': ('Docker', 'tech', 'high'),
    'redis': ('Redis', 'tech', 'high'),
    'kafka': ('Apache Kafka', 'tech', 'medium'),
    'spark': ('Apache Spark', 'tech', 'medium'),
    'airflow': ('Apache Airflow', 'tech', 'medium'),
    
    # AI companies
    'openai': ('OpenAI', 'ai', 'high'),
    'anthropic': ('Anthropic', 'ai', 'high'),
    'cohere': ('Cohere', 'ai', 'high'),
    'huggingface': ('Hugging Face', 'ai', 'high'),
    'stability': ('Stability AI', 'ai', 'high'),
    'midjourney': ('Midjourney', 'ai', 'high'),
    'runway': ('Runway', 'ai', 'high'),
    'jasper': ('Jasper AI', 'ai', 'high'),
    'copy': ('Copy.ai', 'ai', 'medium'),
    'ema': ('Ema (Universal AI Employee)', 'ai', 'high'),
    
    # Social/Consumer
    'twitter': ('Twitter/X', 'social', 'high'),
    'instagram': ('Instagram', 'social', 'high'),
    'tiktok': ('TikTok', 'social', 'high'),
    'snapchat': ('Snapchat', 'social', 'high'),
    'discord': ('Discord', 'social', 'high'),
    'telegram': ('Telegram', 'social', 'high'),
    'signal': ('Signal', 'social', 'high'),
    'whatsapp': ('WhatsApp', 'social', 'high'),
    'spotify': ('Spotify', 'media', 'high'),
    'netflix': ('Netflix', 'media', 'high'),
    
    # Common word conflicts
    'mixi': ('Mixi (Japanese social network)', 'social', 'high'),
    'nool': ('Nool Company (towels)', 'textile', 'medium'),
    'ermi': ('ERMI (Environmental Relative Moldiness Index)', 'science', 'medium'),
    'enmi': ('Sounds like "enemy" in Hindi/Urdu', 'linguistic', 'medium'),
}


def check_offline_brands(name: str) -> List[CompanyMatch]:
    """Check against known brand database."""
    matches = []
    name_lower = name.lower()
    
    # Direct match
    if name_lower in KNOWN_TECH_BRANDS:
        desc, industry, risk = KNOWN_TECH_BRANDS[name_lower]
        matches.append(CompanyMatch(
            name=desc,
            type='company',
            industry=industry,
            risk_level=risk,
            description=f"Exact match with {desc}"
        ))
    
    # Partial/similar matches
    for brand, (desc, industry, risk) in KNOWN_TECH_BRANDS.items():
        if brand != name_lower:
            # Check if name is contained in brand or vice versa
            if len(name_lower) >= 4 and len(brand) >= 4:
                if name_lower in brand or brand in name_lower:
                    matches.append(CompanyMatch(
                        name=desc,
                        type='company',
                        industry=industry,
                        risk_level='low',
                        description=f"Similar to {desc}"
                    ))
    
    return matches


def check_existing_companies(name: str, search_web: bool = True) -> CompanyReport:
    """
    Check for existing companies with similar names.
    
    Args:
        name: The name to check
        search_web: Whether to search the web (slower)
    
    Returns:
        CompanyReport with findings
    """
    report = CompanyReport(name=name)
    
    # Offline brand check (fast)
    offline_matches = check_offline_brands(name)
    report.matches.extend(offline_matches)
    
    # Check for high-risk conflicts
    for match in report.matches:
        if match.risk_level == 'high':
            report.has_conflicts = True
            if match.industry in ['tech', 'ai', 'saas']:
                report.same_industry = True
    
    # Generate summary
    if report.same_industry:
        report.summary = f"🚨 HIGH RISK: Conflicts with {report.matches[0].name}"
    elif report.has_conflicts:
        report.summary = f"⚠️ CONFLICT: Similar to {report.matches[0].name}"
    elif report.matches:
        report.summary = f"ℹ️ {len(report.matches)} similar name(s) found (different industries)"
    else:
        report.summary = "✅ No known conflicts"
    
    return report
