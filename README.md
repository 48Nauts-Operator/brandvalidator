# NameCraft 🔮

**AI-Powered Brand Name Generator**

Generate short, catchy, globally-friendly brand names that are:
- ✅ Easy to pronounce in any language
- ✅ Free of offensive meanings worldwide
- ✅ Available as domains (.ai, .com, .ch)
- ✅ Optionally meaningful (real words or roots)
- ✅ Aligned with your business concept

## Features

- **Concept-aware generation** — Input your business description, get relevant names
- **Multi-language safety** — Checks against offensive words in 20+ languages
- **Domain checking** — Real-time availability for .ai, .com, .ch, .io
- **Meaning discovery** — Finds names with positive meanings in various languages
- **Trademark search** — Basic conflict detection
- **Scoring system** — Ranks names by availability, pronounceability, meaning

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate names for your concept
python -m namecraft "Enterprise AI knowledge platform with Swiss precision"

# Or use the interactive mode
python -m namecraft --interactive
```

## Usage

```bash
# Basic usage
namecraft "Your business concept here"

# With options
namecraft "AI assistant" --length 4-6 --tlds ai,com,ch --count 50

# Export results
namecraft "Knowledge platform" --output results.json
```

## How It Works

1. **Syllable Generation** — Combines phonetically pleasing syllables
2. **Offensive Filtering** — Checks against 20+ language bad-word lists
3. **Pronunciation Check** — Ensures global speakability
4. **Domain Lookup** — Parallel DNS/WHOIS checks
5. **Meaning Search** — Dictionary API lookups
6. **Scoring** — Ranks by composite score

## Built by 48nauts

Part of the 48nauts tooling ecosystem.

---

*"Finding the perfect name shouldn't take forever."*
