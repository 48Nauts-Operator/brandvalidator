#!/usr/bin/env python3
"""
NameCraft Report Generator
Produces a comprehensive one-page report for any brand name.
"""

import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

from .checks.translations import check_translations, TranslationReport
from .checks.companies import check_existing_companies, CompanyReport
from .checks.domains import check_domains_deep, DomainReport
from .checks.trademarks import check_trademarks, TrademarkReport
from .checks.packages import check_package_registries, PackageReport
from .checks.offensive import check_offensive_all_languages, OffensiveReport
from .checks.phonetics import check_phonetic_conflicts, PhoneticReport


@dataclass
class NameReport:
    """Complete analysis report for a brand name."""
    name: str
    generated_at: str
    
    # Overall scores
    overall_score: int = 0
    overall_verdict: str = ""
    risk_level: str = "unknown"  # low, medium, high, critical
    
    # Individual reports
    translations: Optional[TranslationReport] = None
    companies: Optional[CompanyReport] = None
    domains: Optional[DomainReport] = None
    trademarks: Optional[TrademarkReport] = None
    packages: Optional[PackageReport] = None
    offensive: Optional[OffensiveReport] = None
    phonetics: Optional[PhoneticReport] = None
    
    # Quick reference
    available_domains: List[str] = field(default_factory=list)
    meanings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


def analyze_name(
    name: str,
    tlds: List[str] = None,
    check_web: bool = False,
    verbose: bool = False
) -> NameReport:
    """
    Run all checks on a name and produce a complete report.
    
    Args:
        name: The brand name to analyze
        tlds: TLDs to check (default: ai, com, ch, io)
        check_web: Whether to do web searches (slower)
        verbose: Print progress
    
    Returns:
        NameReport with all findings
    """
    if tlds is None:
        tlds = ['ai', 'com', 'ch', 'io']
    
    report = NameReport(
        name=name,
        generated_at=datetime.now().isoformat(),
    )
    
    # 1. Offensive Check (FIRST - if offensive, stop here)
    if verbose:
        print("  [1/7] Checking offensive content...")
    report.offensive = check_offensive_all_languages(name)
    
    if report.offensive.is_offensive and report.offensive.severity == 'severe':
        report.blockers.append(f"OFFENSIVE: {report.offensive.summary}")
        report.risk_level = "critical"
        report.overall_verdict = "❌ REJECTED - Offensive content detected"
        report.overall_score = 0
        return report
    elif report.offensive.is_offensive:
        report.warnings.append(report.offensive.summary)
    
    # 2. Translation/Meaning Check
    if verbose:
        print("  [2/7] Checking translations...")
    report.translations = check_translations(name)
    
    if report.translations.has_negative:
        report.warnings.append(report.translations.summary)
    elif report.translations.has_positive:
        report.meanings.append(report.translations.summary)
    
    # 3. Phonetics Check
    if verbose:
        print("  [3/7] Checking phonetics...")
    report.phonetics = check_phonetic_conflicts(name)
    
    if not report.phonetics.is_pronounceable:
        report.warnings.append(report.phonetics.summary)
    
    # 4. Domain Check
    if verbose:
        print("  [4/7] Checking domains...")
    report.domains = check_domains_deep(name, tlds)
    report.available_domains = report.domains.best_available
    
    # 5. Trademark Check
    if verbose:
        print("  [5/7] Checking trademarks...")
    report.trademarks = check_trademarks(name)
    
    if report.trademarks.same_class and report.trademarks.has_conflicts:
        report.blockers.append(report.trademarks.summary)
    elif report.trademarks.has_conflicts:
        report.warnings.append(report.trademarks.summary)
    
    # 6. Company Check
    if verbose:
        print("  [6/7] Checking existing companies...")
    report.companies = check_existing_companies(name, search_web=check_web)
    
    if report.companies.same_industry:
        report.blockers.append(report.companies.summary)
    elif report.companies.has_conflicts:
        report.warnings.append(report.companies.summary)
    
    # 7. Package Registry Check
    if verbose:
        print("  [7/7] Checking package registries...")
    report.packages = check_package_registries(name)
    
    if report.packages.has_conflicts:
        report.warnings.append(report.packages.summary)
    
    # Calculate overall score
    score = 100
    
    # Deductions
    if report.blockers:
        score -= 50 * len(report.blockers)
    if report.warnings:
        score -= 10 * len(report.warnings)
    
    # Bonuses
    if report.domains.all_available:
        score += 20
    elif len(report.available_domains) >= 2:
        score += 10
    
    if report.translations.has_positive and not report.translations.has_negative:
        score += 15
    
    if report.phonetics.is_pronounceable and not report.phonetics.matches:
        score += 10
    
    report.overall_score = max(0, min(100, score))
    
    # Determine risk level
    if report.blockers:
        report.risk_level = "critical" if len(report.blockers) > 1 else "high"
    elif len(report.warnings) >= 3:
        report.risk_level = "high"
    elif report.warnings:
        report.risk_level = "medium"
    else:
        report.risk_level = "low"
    
    # Generate verdict
    if report.overall_score >= 80:
        report.overall_verdict = "✅ EXCELLENT - Highly recommended"
    elif report.overall_score >= 60:
        report.overall_verdict = "👍 GOOD - Minor issues to consider"
    elif report.overall_score >= 40:
        report.overall_verdict = "⚠️ CAUTION - Significant concerns"
    else:
        report.overall_verdict = "❌ NOT RECOMMENDED - Major issues"
    
    return report


def format_report_text(report: NameReport) -> str:
    """Format report as readable text."""
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append(f"  🔮 NAMECRAFT REPORT: {report.name.upper()}")
    lines.append("=" * 70)
    lines.append(f"Generated: {report.generated_at[:19]}")
    lines.append("")
    
    # Overall verdict
    lines.append("┌─────────────────────────────────────────────────────────────────────┐")
    lines.append(f"│  SCORE: {report.overall_score}/100   |   RISK: {report.risk_level.upper():<10}                       │")
    lines.append(f"│  {report.overall_verdict:<63} │")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    lines.append("")
    
    # Quick summary
    if report.available_domains:
        lines.append(f"✅ AVAILABLE DOMAINS: {', '.join([f'.{d}' for d in report.available_domains])}")
    else:
        lines.append("❌ NO DOMAINS AVAILABLE")
    
    if report.meanings:
        lines.append(f"📖 MEANING: {report.meanings[0]}")
    
    lines.append("")
    
    # Blockers (critical issues)
    if report.blockers:
        lines.append("🚨 BLOCKERS (Must resolve):")
        for blocker in report.blockers:
            lines.append(f"   • {blocker}")
        lines.append("")
    
    # Warnings
    if report.warnings:
        lines.append("⚠️  WARNINGS:")
        for warning in report.warnings:
            lines.append(f"   • {warning}")
        lines.append("")
    
    # Detailed sections
    lines.append("─" * 70)
    lines.append("DETAILED CHECKS:")
    lines.append("─" * 70)
    
    # Offensive
    if report.offensive:
        status = "🚨 ISSUES" if report.offensive.is_offensive else "✅ CLEAN"
        lines.append(f"\n1. OFFENSIVE CONTENT: {status}")
        lines.append(f"   {report.offensive.summary}")
    
    # Translations
    if report.translations:
        status = "⚠️ NEGATIVE" if report.translations.has_negative else ("✅ POSITIVE" if report.translations.has_positive else "ℹ️ NEUTRAL")
        lines.append(f"\n2. TRANSLATIONS/MEANINGS: {status}")
        lines.append(f"   {report.translations.summary}")
        if report.translations.found_meanings:
            for m in report.translations.found_meanings[:3]:
                lines.append(f"   • {m.language}: {m.meaning} ({m.sentiment})")
    
    # Phonetics
    if report.phonetics:
        status = "✅ CLEAR" if report.phonetics.is_pronounceable else "⚠️ ISSUES"
        lines.append(f"\n3. PRONUNCIATION: {status}")
        lines.append(f"   {report.phonetics.summary}")
        lines.append(f"   Phonetic: {report.phonetics.phonetic_code}")
    
    # Domains
    if report.domains:
        lines.append(f"\n4. DOMAINS:")
        lines.append(f"   {report.domains.summary}")
        for tld, check in report.domains.checks.items():
            status = "✅ Available" if check.available else ("❌ Taken" if check.available is False else "❓ Unknown")
            extra = f" ({check.registrar})" if check.registrar else ""
            lines.append(f"   • {report.name.lower()}.{tld}: {status}{extra}")
    
    # Trademarks
    if report.trademarks:
        status = "🚨 CONFLICT" if report.trademarks.same_class else ("⚠️ EXISTS" if report.trademarks.has_conflicts else "✅ CLEAR")
        lines.append(f"\n5. TRADEMARKS: {status}")
        lines.append(f"   {report.trademarks.summary}")
        if report.trademarks.matches:
            for m in report.trademarks.matches[:2]:
                lines.append(f"   • {m.name} (Classes: {', '.join(m.class_codes)}) - {m.owner}")
    
    # Companies
    if report.companies:
        status = "🚨 CONFLICT" if report.companies.same_industry else ("⚠️ EXISTS" if report.companies.has_conflicts else "✅ CLEAR")
        lines.append(f"\n6. EXISTING COMPANIES: {status}")
        lines.append(f"   {report.companies.summary}")
    
    # Packages
    if report.packages:
        status = "⚠️ EXISTS" if report.packages.has_conflicts else "✅ AVAILABLE"
        lines.append(f"\n7. PACKAGE REGISTRIES: {status}")
        lines.append(f"   {report.packages.summary}")
        if report.packages.matches:
            for m in report.packages.matches:
                lines.append(f"   • {m.registry}: {m.package_name}")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("  Report generated by NameCraft | 48nauts.com")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def format_report_json(report: NameReport) -> str:
    """Format report as JSON."""
    # Convert dataclasses to dict
    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        else:
            return obj
    
    return json.dumps(to_dict(report), indent=2)


def format_report_markdown(report: NameReport) -> str:
    """Format report as Markdown."""
    lines = []
    
    lines.append(f"# 🔮 NameCraft Report: {report.name}")
    lines.append(f"\n*Generated: {report.generated_at[:19]}*")
    lines.append("")
    
    # Summary box
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| **Score** | {report.overall_score}/100 |")
    lines.append(f"| **Risk** | {report.risk_level.upper()} |")
    lines.append(f"| **Verdict** | {report.overall_verdict} |")
    lines.append(f"| **Available Domains** | {', '.join([f'.{d}' for d in report.available_domains]) or 'None'} |")
    lines.append("")
    
    if report.blockers:
        lines.append("### 🚨 Blockers")
        for b in report.blockers:
            lines.append(f"- {b}")
        lines.append("")
    
    if report.warnings:
        lines.append("### ⚠️ Warnings")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")
    
    lines.append("## Detailed Checks")
    lines.append("")
    
    checks = [
        ("Offensive Content", report.offensive.summary if report.offensive else "Not checked"),
        ("Translations", report.translations.summary if report.translations else "Not checked"),
        ("Pronunciation", report.phonetics.summary if report.phonetics else "Not checked"),
        ("Domains", report.domains.summary if report.domains else "Not checked"),
        ("Trademarks", report.trademarks.summary if report.trademarks else "Not checked"),
        ("Companies", report.companies.summary if report.companies else "Not checked"),
        ("Packages", report.packages.summary if report.packages else "Not checked"),
    ]
    
    lines.append("| Check | Result |")
    lines.append("|-------|--------|")
    for check, result in checks:
        lines.append(f"| {check} | {result} |")
    
    lines.append("")
    lines.append("---")
    lines.append("*Report by NameCraft | 48nauts.com*")
    
    return "\n".join(lines)


def main():
    """CLI entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate comprehensive brand name report'
    )
    parser.add_argument('name', help='Brand name to analyze')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'markdown'], 
                       default='text', help='Output format')
    parser.add_argument('--tlds', '-t', default='ai,com,ch,io',
                       help='TLDs to check (comma-separated)')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show progress')
    
    args = parser.parse_args()
    
    tlds = [t.strip() for t in args.tlds.split(',')]
    
    print(f"\n🔮 Analyzing: {args.name}")
    print("-" * 40)
    
    report = analyze_name(args.name, tlds=tlds, verbose=args.verbose)
    
    if args.format == 'json':
        output = format_report_json(report)
    elif args.format == 'markdown':
        output = format_report_markdown(report)
    else:
        output = format_report_text(report)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"\n📁 Report saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
