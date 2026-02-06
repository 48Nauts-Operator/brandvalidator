"""
Check package registries (npm, PyPI, crates.io, etc.) for name conflicts.
"""

import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PackageMatch:
    registry: str  # npm, pypi, crates, rubygems, etc.
    package_name: str
    description: Optional[str] = None
    url: Optional[str] = None
    downloads: Optional[int] = None


@dataclass
class PackageReport:
    name: str
    matches: List[PackageMatch] = field(default_factory=list)
    has_conflicts: bool = False
    summary: str = ""


def check_npm(name: str) -> Optional[PackageMatch]:
    """Check npm registry."""
    try:
        cmd = ['curl', '-sL', f'https://registry.npmjs.org/{name.lower()}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and '"name"' in result.stdout:
            data = json.loads(result.stdout)
            if 'error' not in data:
                return PackageMatch(
                    registry='npm',
                    package_name=data.get('name', name),
                    description=data.get('description', ''),
                    url=f"https://npmjs.com/package/{name.lower()}"
                )
    except:
        pass
    return None


def check_pypi(name: str) -> Optional[PackageMatch]:
    """Check PyPI registry."""
    try:
        cmd = ['curl', '-sL', f'https://pypi.org/pypi/{name.lower()}/json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and '"info"' in result.stdout:
            data = json.loads(result.stdout)
            if 'message' not in data:  # No error
                info = data.get('info', {})
                return PackageMatch(
                    registry='pypi',
                    package_name=info.get('name', name),
                    description=info.get('summary', ''),
                    url=f"https://pypi.org/project/{name.lower()}/"
                )
    except:
        pass
    return None


def check_crates(name: str) -> Optional[PackageMatch]:
    """Check crates.io (Rust) registry."""
    try:
        cmd = ['curl', '-sL', f'https://crates.io/api/v1/crates/{name.lower()}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and '"crate"' in result.stdout:
            data = json.loads(result.stdout)
            if 'errors' not in data:
                crate = data.get('crate', {})
                return PackageMatch(
                    registry='crates.io',
                    package_name=crate.get('name', name),
                    description=crate.get('description', ''),
                    url=f"https://crates.io/crates/{name.lower()}",
                    downloads=crate.get('downloads')
                )
    except:
        pass
    return None


def check_rubygems(name: str) -> Optional[PackageMatch]:
    """Check RubyGems registry."""
    try:
        cmd = ['curl', '-sL', f'https://rubygems.org/api/v1/gems/{name.lower()}.json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and '"name"' in result.stdout:
            data = json.loads(result.stdout)
            return PackageMatch(
                registry='rubygems',
                package_name=data.get('name', name),
                description=data.get('info', ''),
                url=f"https://rubygems.org/gems/{name.lower()}",
                downloads=data.get('downloads')
            )
    except:
        pass
    return None


def check_packagist(name: str) -> Optional[PackageMatch]:
    """Check Packagist (PHP) registry."""
    # Packagist requires vendor/package format, so we search instead
    try:
        cmd = ['curl', '-sL', f'https://packagist.org/search.json?q={name.lower()}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            results = data.get('results', [])
            # Check if exact match in name
            for pkg in results[:3]:
                if name.lower() in pkg.get('name', '').lower():
                    return PackageMatch(
                        registry='packagist',
                        package_name=pkg.get('name', name),
                        description=pkg.get('description', ''),
                        url=pkg.get('url', ''),
                        downloads=pkg.get('downloads')
                    )
    except:
        pass
    return None


def check_package_registries(name: str, registries: List[str] = None) -> PackageReport:
    """
    Check package registries for name conflicts.
    
    Args:
        name: The name to check
        registries: List of registries to check (default: all)
    
    Returns:
        PackageReport with findings
    """
    if registries is None:
        registries = ['npm', 'pypi', 'crates', 'rubygems']
    
    report = PackageReport(name=name)
    
    checkers = {
        'npm': check_npm,
        'pypi': check_pypi,
        'crates': check_crates,
        'rubygems': check_rubygems,
        'packagist': check_packagist,
    }
    
    for registry in registries:
        if registry in checkers:
            match = checkers[registry](name)
            if match:
                report.matches.append(match)
    
    # Determine if there are conflicts
    report.has_conflicts = len(report.matches) > 0
    
    # Generate summary
    if report.matches:
        regs = [m.registry for m in report.matches]
        report.summary = f"⚠️ Package exists on: {', '.join(regs)}"
    else:
        report.summary = "✅ No package registry conflicts"
    
    return report
