<div align="center">

# 🤖 AI Scraper

### Universal AI-Powered Web Data Extraction Engine

**Point at any website. Get structured data back. No custom parsers needed.**

AI Scraper uses headless Chrome + LLM intelligence to extract structured data from any webpage — no CSS selectors, no XPath, no brittle regex. Just describe what you want, and the AI figures out the rest.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![AI Powered](https://img.shields.io/badge/AI-LLM%20Powered-FF6F00?style=for-the-badge&logo=openai&logoColor=white)]()

---

```
   █████╗ ██╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗
  ██╔══██╗██║    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
  ███████║██║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
  ██╔══██║██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
  ██║  ██║██║    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
  ╚═╝  ╚═╝╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
```

</div>

---

## 🎯 Why AI Scraper?

Traditional scrapers break when websites change their HTML. AI Scraper doesn't care about HTML structure — it **reads the page like a human** and extracts exactly what you ask for.

| Traditional Scraping | AI Scraper |
|---------------------|------------|
| ❌ Write CSS selectors for every site | ✅ One tool for ALL websites |
| ❌ Breaks when HTML changes | ✅ Adapts automatically |
| ❌ Can't handle dynamic JS content | ✅ Full Chrome rendering |
| ❌ Blocked by WAF/anti-bot | ✅ Undetected Chrome bypass |
| ❌ Hours of maintenance | ✅ Zero maintenance |
| ❌ Same dumb mistakes every time | ✅ **Self-learning** — gets smarter with every scrape |

---

## ⚡ Quick Start

### Installation

```bash
git clone https://github.com/masood1996-geo/ai-scraper.git
cd ai-scraper
pip install -e .
```

### Your First Scrape (3 lines)

```python
from ai_scraper import AIScraper, Schema

with AIScraper(provider="openrouter", api_key="sk-or-v1-...") as scraper:
    results = scraper.scrape("https://example.com/listings", Schema.APARTMENTS)
    print(results)
```

### CLI Usage

```bash
# Scrape apartments
ai-scraper scrape https://immowelt.de/liste/berlin/wohnungen/mieten \
    --schema apartments --output results.json

# Scrape with custom fields
ai-scraper scrape https://example.com \
    --fields "name,price,rating,url" --output products.csv

# Ask a question about a page
ai-scraper ask https://example.com "What products are on sale?"

# Batch scrape multiple URLs
ai-scraper batch url1 url2 url3 --schema products --output all_products.json

# List all available schemas
ai-scraper schemas

# View learning brain stats
ai-scraper brain

# Diagnose a domain
ai-scraper diagnose www.immowelt.de
```

---

## 📋 Built-in Schemas

AI Scraper comes with 10 predefined schemas for common data types:

| Schema | Fields | Best For |
|--------|--------|----------|
| `APARTMENTS` | title, price, rooms, size, address, url | Real estate listings |
| `REAL_ESTATE_AGENTS` | name, phone, email, website, hours | Agent contact info |
| `JOB_LISTINGS` | title, company, location, salary, type | Job boards |
| `PRODUCTS` | name, price, rating, reviews, in_stock | E-commerce |
| `ARTICLES` | headline, author, date, summary, category | News sites |
| `PROFILES` | name, title, company, location, bio | Social/professional |
| `EVENTS` | name, date, location, price, description | Event listings |
| `RESTAURANTS` | name, cuisine, rating, price_range, phone | Restaurant reviews |
| `LINKS` | text, url, context | Link extraction |
| `CONTACTS` | name, phone, email, address, website | Contact pages |

### Custom Schemas

Don't see what you need? Define your own:

```python
my_schema = {
    "university_name": "Name of the university",
    "ranking": "Global ranking position",
    "tuition_fee": "Annual tuition with currency",
    "country": "Country location",
}

results = scraper.scrape(url, my_schema)
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AIScraper.scrape()                         │
│                                                               │
│  1. Check Memory ──→ 2. Chrome Fetch ──→ 3. HTML Clean       │
│     (learned settings)  (anti-bot bypass)  (+ learned rules) │
│                                                               │
│  4. LLM Extract ──→ 5. Quality Score ──→ 6. Output           │
│     (evolved prompts)  (auto-evaluate)    (JSON/CSV/table)   │
│                              │                                │
│                    ┌─────────▼──────────┐                    │
│                    │ Quality < 60%?     │                    │
│                    │   → Self-improve   │                    │
│                    │   → Retry with     │                    │
│                    │     better prompt  │                    │
│                    └────────────────────┘                    │
│                              │                                │
│                    ┌─────────▼──────────┐                    │
│                    │  💾 Learn & Store  │                    │
│                    │  Domain profiles   │                    │
│                    │  Evolved prompts   │                    │
│                    │  Optimal settings  │                    │
│                    └────────────────────┘                    │
└──────────────────────────────────────────────────────────────┘

Components:
├── core.py       — Orchestrator with self-learning pipeline
├── browser.py    — Headless Chrome with undetected_chromedriver
├── llm.py        — Multi-provider LLM client (OpenRouter/OpenAI/Kilo/Ollama)
├── memory.py     — SQLite-backed persistent learning memory
├── learner.py    — Quality scoring, prompt evolution, domain diagnostics
├── schemas.py    — 10 predefined extraction templates
└── cli.py        — Rich CLI with brain/diagnose commands
```

---

## 🤖 Supported AI Providers

| Provider | Setup | Free Tier? |
|----------|-------|------------|
| **OpenRouter** | [Get Key](https://openrouter.ai) | ✅ Free models available |
| **OpenAI** | [Get Key](https://platform.openai.com) | ❌ Paid only |
| **Kilo** | [Get Key](https://kilo.ai) | ❌ Paid only |
| **Ollama** | [Install](https://ollama.com) | ✅ Free (local) |

```bash
# Set API key via environment variable
export OPENROUTER_API_KEY="sk-or-v1-..."

# Or pass directly
ai-scraper scrape https://example.com --api-key "sk-or-v1-..." --schema products
```

---

## 📂 Project Structure

```
ai-scraper/
├── ai_scraper/
│   ├── __init__.py       # Package entry point
│   ├── core.py           # AIScraper main class + learning pipeline
│   ├── browser.py        # Headless Chrome engine
│   ├── llm.py            # LLM provider abstraction
│   ├── memory.py         # 🧠 SQLite persistent learning memory
│   ├── learner.py        # 🧠 Self-improvement engine
│   ├── schemas.py        # Predefined extraction schemas
│   └── cli.py            # CLI with brain/diagnose commands
├── examples/
│   ├── scrape_apartments.py
│   ├── scrape_jobs.py
│   └── custom_schema.py
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 🔧 Advanced Usage

### As a Python Library

```python
from ai_scraper import AIScraper

scraper = AIScraper(
    provider="openrouter",
    api_key="sk-or-v1-...",
    model="google/gemini-2.5-flash",
    headless=True,
    wait_seconds=3.0,  # Extra time for JS-heavy pages
)

# Scrape with extra instructions
results = scraper.scrape(
    url="https://example.com/products",
    schema={"name": "Product name", "price": "Price", "url": "Link"},
    instructions="Only extract items priced under $50",
)

# Ask a question about a page
answer = scraper.ask_page(
    "https://example.com/about",
    "What year was this company founded?"
)

# Save results
scraper.save_json(results, "output/products.json")
scraper.save_csv(results, "output/products.csv")

scraper.close()
```

### Batch Processing

```python
urls = [
    "https://site1.com/listings",
    "https://site2.com/listings",
    "https://site3.com/listings",
]

results = scraper.scrape_multiple(urls, Schema.APARTMENTS)
# Each result includes "_source_url" field
```

### Using Pre-Fetched HTML

```python
import requests
html = requests.get("https://example.com").text

results = scraper.scrape(
    url="https://example.com",
    schema=Schema.PRODUCTS,
    raw_html=html,  # Skip Chrome, use this HTML directly
)
```

---

## 🧠 Self-Learning System

AI Scraper has a persistent learning brain that gets smarter with every scrape:

### How It Works

| Feature | What It Does |
|---------|-------------|
| **Quality Scoring** | Auto-evaluates every extraction (fill rate, validity, uniqueness, content quality) |
| **Prompt Evolution** | When quality is low, asks the LLM to analyze WHY and generate better prompts |
| **Domain Profiling** | Remembers optimal settings per website (wait times, cleaning rules, success rates) |
| **Adaptive Wait Times** | Learns which sites need longer JS render time and adjusts automatically |
| **Self-Improvement Loop** | If score < 60%, retries with evolved strategy — no human intervention |
| **Trend Analysis** | Tracks whether your extraction quality is improving or declining over time |

### Brain Commands

```bash
# See what the brain has learned
ai-scraper brain

# Diagnose a specific domain
ai-scraper diagnose www.immowelt.de
```

### Python API

```python
scraper = AIScraper(provider="openrouter", api_key="...", learning=True)

# Scrape — learning happens automatically
results = scraper.scrape(url, Schema.APARTMENTS)

# Check what was learned
print(scraper.stats())
# → {"total_scrapes": 47, "unique_domains": 12, "avg_quality": 0.78, ...}

# Diagnose a domain
print(scraper.diagnose("www.immowelt.de"))
# → {"success_rate": 0.85, "trend": "improving ↑", "recommendations": [...]}

# Provide feedback to help it learn
scraper.feedback(url, Schema.APARTMENTS, "good")
scraper.feedback(url, Schema.APARTMENTS, "bad", "Prices were wrong")
```

### Learning Memory

All learning is stored in `~/.ai_scraper/memory.db` (SQLite). The brain persists across sessions — kill the process, restart your PC, it remembers everything.

---

## 📋 Changelog

### v1.1.0 — Self-Learning Engine
- 🧠 Persistent learning memory (SQLite)
- 🧠 Automatic quality scoring (fill rate, validity, uniqueness, content quality)
- 🧠 Self-improvement loop — retries with evolved prompts when quality is low
- 🧠 LLM-powered prompt evolution — AI writes better prompts for itself
- 🧠 Domain profiling — remembers optimal settings per website
- 🧠 Adaptive wait times — learns which sites need longer JS rendering
- 🧠 Trend analysis — tracks quality improvements over time
- 🧠 Domain diagnostics — `ai-scraper diagnose` command
- 🧠 Brain stats — `ai-scraper brain` command
- 🧠 User feedback API — teach the bot what's good/bad

### v1.0.0 — Initial Release
- ✅ Core scraping engine with browser + LLM pipeline
- ✅ Headless Chrome with anti-bot bypass (undetected_chromedriver)
- ✅ 4 LLM providers (OpenRouter, OpenAI, Kilo, Ollama)
- ✅ 10 predefined extraction schemas
- ✅ Custom schema support
- ✅ CLI with scrape, ask, batch, and schemas commands
- ✅ JSON and CSV output formats
- ✅ Rich terminal output with tables and progress
- ✅ Intelligent HTML cleaning pipeline
- ✅ Relative URL resolution
- ✅ Batch scraping with source tracking

---

<div align="center">

**Extracted from the [OpenHouse Bot](https://github.com/masood1996-geo/openhouse-bot) project**

*The AI scraping engine that powers global apartment hunting — now available as a standalone, self-learning tool.*

</div>
