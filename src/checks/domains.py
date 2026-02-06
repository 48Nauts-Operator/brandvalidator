"""
Deep domain availability checking.
"""

import subprocess
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class DomainCheck:
    tld: str
    domain: str
    available: Optional[bool]  # None = unknown
    has_dns: bool = False
    registrar: Optional[str] = None
    expiry: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DomainReport:
    name: str
    checks: Dict[str, DomainCheck] = field(default_factory=dict)
    all_available: bool = False
    best_available: List[str] = field(default_factory=list)
    summary: str = ""


def check_dns(domain: str, timeout: int = 3) -> tuple[bool, str]:
    """Quick DNS check. Returns (has_records, raw_output)."""
    try:
        result = subprocess.run(
            ['dig', '+short', domain],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        return len(output) > 0, output
    except:
        return False, ""


def check_whois(domain: str, timeout: int = 8) -> dict:
    """WHOIS lookup for detailed info."""
    info = {
        'available': None,
        'registrar': None,
        'expiry': None,
        'raw': '',
    }
    
    try:
        result = subprocess.run(
            ['whois', domain],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.lower()
        info['raw'] = result.stdout[:1000]
        
        # Check availability patterns
        available_patterns = [
            'no match', 'not found', 'no entries found',
            'no data found', 'status: free', 'status: available',
            'domain not found', 'no object found',
        ]
        
        taken_patterns = [
            'domain name:', 'registrant:', 'creation date:',
            'registered on:', 'name server:', 'registrar:',
            'registry domain id:', 'updated date:',
        ]
        
        for pattern in available_patterns:
            if pattern in output:
                info['available'] = True
                return info
        
        for pattern in taken_patterns:
            if pattern in output:
                info['available'] = False
                
                # Try to extract registrar
                for line in result.stdout.split('\n'):
                    if 'registrar:' in line.lower():
                        info['registrar'] = line.split(':', 1)[1].strip()[:50]
                        break
                
                # Try to extract expiry
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    if any(x in line_lower for x in ['expir', 'renewal']):
                        info['expiry'] = line.split(':', 1)[1].strip()[:30] if ':' in line else None
                        break
                
                return info
                
    except Exception as e:
        info['error'] = str(e)
    
    return info


def check_single_domain(name: str, tld: str) -> DomainCheck:
    """Check a single domain."""
    domain = f"{name.lower()}.{tld}"
    
    # Quick DNS check first
    has_dns, _ = check_dns(domain)
    
    # If DNS exists, domain is taken
    if has_dns:
        return DomainCheck(
            tld=tld,
            domain=domain,
            available=False,
            has_dns=True,
        )
    
    # No DNS - do WHOIS check
    whois_info = check_whois(domain)
    
    return DomainCheck(
        tld=tld,
        domain=domain,
        available=whois_info.get('available'),
        has_dns=False,
        registrar=whois_info.get('registrar'),
        expiry=whois_info.get('expiry'),
    )


def check_domains_deep(
    name: str,
    tlds: List[str] = None,
    parallel: bool = True
) -> DomainReport:
    """
    Deep domain availability check with WHOIS.
    
    Args:
        name: The name to check
        tlds: List of TLDs (default: ai, com, ch, io, co)
        parallel: Run checks in parallel
    
    Returns:
        DomainReport with detailed findings
    """
    if tlds is None:
        tlds = ['ai', 'com', 'ch', 'io', 'co']
    
    report = DomainReport(name=name)
    
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tlds)) as executor:
            futures = {
                executor.submit(check_single_domain, name, tld): tld
                for tld in tlds
            }
            
            for future in concurrent.futures.as_completed(futures):
                tld = futures[future]
                try:
                    check = future.result()
                    report.checks[tld] = check
                except Exception as e:
                    report.checks[tld] = DomainCheck(
                        tld=tld, domain=f"{name}.{tld}",
                        available=None, error=str(e)
                    )
    else:
        for tld in tlds:
            report.checks[tld] = check_single_domain(name, tld)
    
    # Analyze results
    available = [tld for tld, check in report.checks.items() if check.available]
    taken = [tld for tld, check in report.checks.items() if check.available is False]
    unknown = [tld for tld, check in report.checks.items() if check.available is None]
    
    report.best_available = available
    report.all_available = len(available) == len(tlds) and len(unknown) == 0
    
    # Generate summary
    if report.all_available:
        report.summary = f"🎉 ALL DOMAINS AVAILABLE: {', '.join([f'.{t}' for t in tlds])}"
    elif available:
        report.summary = f"✅ Available: {', '.join([f'.{t}' for t in available])}"
        if taken:
            report.summary += f" | ❌ Taken: {', '.join([f'.{t}' for t in taken])}"
    elif taken:
        report.summary = f"❌ ALL TAKEN: {', '.join([f'.{t}' for t in taken])}"
    else:
        report.summary = f"❓ Unable to determine availability"
    
    return report
