#!/usr/bin/env python3
"""
NameCraft CLI - Brand name generator.
"""

import argparse
import json
import sys
from typing import Optional

from .generator import generate_names, score_name, GeneratedName
from .domains import check_all_domains, domain_score
from .offensive import is_offensive, check_negative_meanings


def print_header():
    """Print the CLI header."""
    print()
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                     🔮 NAMECRAFT                               ║")
    print("║              AI-Powered Brand Name Generator                   ║")
    print("║                      by 48nauts                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()


def check_single_name(name: str, tlds: list[str] = ['ai', 'com', 'ch']):
    """Check a single name for issues and availability."""
    print(f"\nChecking: {name}")
    print("-" * 40)
    
    # Offensive check
    offensive, reason = is_offensive(name)
    if offensive:
        print(f"❌ OFFENSIVE: {reason}")
    else:
        print("✅ Not offensive")
    
    # Negative meaning check
    negative, neg_reason = check_negative_meanings(name)
    if negative:
        print(f"⚠️  NEGATIVE: {neg_reason}")
    else:
        print("✅ No negative meanings")
    
    # Domain check
    print("\nDomain availability:")
    domains = check_all_domains(name, tlds)
    for tld, status in domains.items():
        if status.available:
            print(f"  ✅ {name.lower()}.{tld} - Available")
        elif status.available is False:
            print(f"  ❌ {name.lower()}.{tld} - Taken")
        else:
            print(f"  ❓ {name.lower()}.{tld} - Unknown ({status.error})")


def run_generator(
    concept: str,
    count: int = 300,
    min_length: int = 4,
    max_length: int = 7,
    tlds: list[str] = ['ai', 'com', 'ch'],
    check_domains: bool = True,
    top_n: int = 20,
    output_file: Optional[str] = None,
):
    """Run the name generator."""
    
    print(f"Concept: {concept}")
    print(f"Length: {min_length}-{max_length} characters")
    print(f"TLDs: {', '.join(tlds)}")
    print()
    
    # Generate names
    print("Generating candidates...")
    names = generate_names(
        concept=concept,
        count=count,
        min_length=min_length,
        max_length=max_length,
    )
    print(f"Generated {len(names)} valid candidates")
    
    # Check domains if requested
    if check_domains:
        print(f"\nChecking domain availability (top {min(100, len(names))} names)...")
        for i, name in enumerate(names[:100]):
            domains = check_all_domains(name.name, tlds)
            name.domains = {tld: status.available for tld, status in domains.items()}
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  Checked {i + 1}/100...")
    
    # Score all names
    for name in names:
        score_name(name)
    
    # Sort by score
    names.sort(key=lambda x: x.score, reverse=True)
    
    # Filter to those with at least one available domain
    if check_domains:
        names = [n for n in names if any(n.domains.values())]
    
    # Print results
    print()
    print("=" * 70)
    print(f"{'NAME':<12} {'SCORE':<6} {'AI':<4} {'COM':<4} {'CH':<4} {'MEANING'}")
    print("=" * 70)
    
    for name in names[:top_n]:
        ai = '✅' if name.domains.get('ai') else '❌'
        com = '✅' if name.domains.get('com') else '❌'
        ch = '✅' if name.domains.get('ch') else '❌'
        meaning = name.meaning[:30] + '...' if name.meaning and len(name.meaning) > 30 else (name.meaning or '-')
        
        print(f"{name.name:<12} {name.score:<6} {ai:<4} {com:<4} {ch:<4} {meaning}")
    
    # Top recommendations
    print()
    print("=" * 70)
    print("🏆 TOP RECOMMENDATIONS:")
    print("=" * 70)
    
    for i, name in enumerate(names[:5], 1):
        print(f"\n{i}. {name.name}")
        print(f"   Score: {name.score}")
        
        domains_str = []
        for tld, available in name.domains.items():
            if available:
                domains_str.append(f"{name.name.lower()}.{tld} ✅")
        if domains_str:
            print(f"   Available: {', '.join(domains_str)}")
        
        if name.meaning:
            print(f"   Meaning: {name.meaning}")
    
    # Export if requested
    if output_file:
        export_data = [
            {
                'name': n.name,
                'score': n.score,
                'meaning': n.meaning,
                'domains': n.domains,
            }
            for n in names[:100]
        ]
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n📁 Results exported to: {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='NameCraft - AI-Powered Brand Name Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  namecraft "AI knowledge platform"
  namecraft "Swiss fintech startup" --length 4-6
  namecraft "Enterprise software" --tlds ai,com,io --output results.json
  namecraft --check "Verix"
        """
    )
    
    parser.add_argument(
        'concept',
        nargs='?',
        default='',
        help='Business concept description'
    )
    
    parser.add_argument(
        '--check', '-c',
        metavar='NAME',
        help='Check a specific name for issues and availability'
    )
    
    parser.add_argument(
        '--length', '-l',
        default='4-7',
        help='Name length range (default: 4-7)'
    )
    
    parser.add_argument(
        '--tlds', '-t',
        default='ai,com,ch',
        help='TLDs to check (default: ai,com,ch)'
    )
    
    parser.add_argument(
        '--count', '-n',
        type=int,
        default=300,
        help='Number of candidates to generate (default: 300)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=20,
        help='Number of results to show (default: 20)'
    )
    
    parser.add_argument(
        '--no-domains',
        action='store_true',
        help='Skip domain checking (faster)'
    )
    
    parser.add_argument(
        '--output', '-o',
        metavar='FILE',
        help='Export results to JSON file'
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Check single name mode
    if args.check:
        tlds = [t.strip() for t in args.tlds.split(',')]
        check_single_name(args.check, tlds)
        return
    
    # Need concept for generation
    if not args.concept:
        parser.print_help()
        print("\n❌ Error: Please provide a business concept or use --check NAME")
        sys.exit(1)
    
    # Parse length range
    try:
        if '-' in args.length:
            min_len, max_len = map(int, args.length.split('-'))
        else:
            min_len = max_len = int(args.length)
    except ValueError:
        print(f"❌ Invalid length format: {args.length}")
        sys.exit(1)
    
    # Parse TLDs
    tlds = [t.strip() for t in args.tlds.split(',')]
    
    # Run generator
    run_generator(
        concept=args.concept,
        count=args.count,
        min_length=min_len,
        max_length=max_len,
        tlds=tlds,
        check_domains=not args.no_domains,
        top_n=args.top,
        output_file=args.output,
    )


if __name__ == '__main__':
    main()
