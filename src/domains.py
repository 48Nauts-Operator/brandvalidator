"""
Domain availability checking.
Uses DNS lookups and optional WHOIS for verification.
"""

import subprocess
import concurrent.futures
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class DomainStatus:
    tld: str
    available: Optional[bool]  # None = unknown
    has_dns: bool
    error: Optional[str] = None


def check_dns(name: str, tld: str, timeout: int = 3) -> DomainStatus:
    """
    Quick DNS check. No DNS records often means available.
    """
    domain = f"{name.lower()}.{tld}"
    
    try:
        result = subprocess.run(
            ['dig', '+short', domain],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout.strip()
        has_dns = len(output) > 0
        
        # No DNS = possibly available (but not guaranteed)
        return DomainStatus(
            tld=tld,
            available=not has_dns,  # Best guess
            has_dns=has_dns,
        )
        
    except subprocess.TimeoutExpired:
        return DomainStatus(tld=tld, available=None, has_dns=False, error="timeout")
    except Exception as e:
        return DomainStatus(tld=tld, available=None, has_dns=False, error=str(e))


def check_whois(name: str, tld: str, timeout: int = 5) -> DomainStatus:
    """
    WHOIS check for more accurate availability.
    """
    domain = f"{name.lower()}.{tld}"
    
    try:
        result = subprocess.run(
            ['whois', domain],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout.lower()
        
        # Common patterns indicating availability
        available_patterns = [
            'no match',
            'not found',
            'no entries found',
            'no data found',
            'status: free',
            'status: available',
        ]
        
        # Common patterns indicating registered
        taken_patterns = [
            'domain name:',
            'registrant:',
            'creation date:',
            'registered on:',
            'name server:',
        ]
        
        for pattern in available_patterns:
            if pattern in output:
                return DomainStatus(tld=tld, available=True, has_dns=False)
        
        for pattern in taken_patterns:
            if pattern in output:
                return DomainStatus(tld=tld, available=False, has_dns=True)
        
        # Unknown
        return DomainStatus(tld=tld, available=None, has_dns=False, error="unclear")
        
    except subprocess.TimeoutExpired:
        return DomainStatus(tld=tld, available=None, has_dns=False, error="timeout")
    except Exception as e:
        return DomainStatus(tld=tld, available=None, has_dns=False, error=str(e))


def check_all_domains(
    name: str,
    tlds: list[str] = ['ai', 'com', 'ch'],
    use_whois: bool = False,
    timeout: int = 3
) -> Dict[str, DomainStatus]:
    """
    Check multiple TLDs in parallel.
    """
    results = {}
    check_fn = check_whois if use_whois else check_dns
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tlds)) as executor:
        futures = {
            executor.submit(check_fn, name, tld, timeout): tld
            for tld in tlds
        }
        
        for future in concurrent.futures.as_completed(futures):
            tld = futures[future]
            try:
                results[tld] = future.result()
            except Exception as e:
                results[tld] = DomainStatus(
                    tld=tld, available=None, has_dns=False, error=str(e)
                )
    
    return results


def domain_score(results: Dict[str, DomainStatus]) -> int:
    """
    Calculate a score based on domain availability.
    """
    score = 0
    
    # Weight by TLD value
    weights = {'com': 30, 'ai': 25, 'ch': 20, 'io': 15, 'co': 10}
    
    for tld, status in results.items():
        if status.available:
            score += weights.get(tld, 10)
    
    return score
