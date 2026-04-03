<div align="center">

# 🕷️ AI Scraper

**Point at any website. Get structured data back. No custom parsers needed.**

AI Scraper combines headless Chrome with LLM intelligence and a **self-learning engine** to extract structured data from any webpage — no CSS selectors, no XPath, no brittle regex. Describe what you want, and the AI figures out the rest. The more you use it, the smarter it gets.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![AI Powered](https://img.shields.io/badge/AI-LLM%20Powered-FF6F00?style=for-the-badge&logo=openai&logoColor=white)]()
[![Self Learning](https://img.shields.io/badge/Self--Learning-Adaptive%20AI-blueviolet?style=for-the-badge)]()
[![Open WebUI](https://img.shields.io/badge/Open_WebUI-GUI_Ready-00C7B7?style=for-the-badge&logo=openai&logoColor=white)]()

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

## Why AI Scraper?

Traditional scrapers break when websites change their HTML. AI Scraper doesn't care about HTML structure — it **reads the page like a human**, extracts exactly what you ask for, and **learns from every interaction** to get better over time.

| Traditional Scraping | AI Scraper |
|---------------------|------------|
| ❌ Write CSS selectors for every site | ✅ One tool for ALL websites |
| ❌ Breaks when HTML changes | ✅ Adapts automatically |
| ❌ Can't handle dynamic JS content | ✅ Full Chrome rendering |
| ❌ Blocked by WAF/anti-bot | ✅ Undetected Chrome bypass |
| ❌ Hours of maintenance | ✅ Zero maintenance |
| ❌ Same dumb mistakes every time | ✅ **Self-learning** — gets smarter with every scrape |
| ❌ Manual tuning per domain | ✅ **Auto-learns** optimal settings per site |
| ❌ Static extraction prompts | ✅ **Evolving prompts** — AI writes better prompts for itself |

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

## 🧠 Auto-Learning Engine — The Brain

> **This is what makes AI Scraper fundamentally different from every other scraping tool.**

AI Scraper features a **persistent self-learning engine** that improves extraction quality autonomously — no manual tuning, no rule-writing, no maintenance. The system builds a growing knowledge base in a local SQLite database (`~/.ai_scraper/memory.db`) that persists across sessions, reboots, and restarts.

### How the Learning Loop Works

Every scrape triggers a 6-stage autonomous learning cycle:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     THE SELF-LEARNING PIPELINE                      │
│                                                                     │
│  ① CHECK MEMORY ──→ ② CHROME FETCH ──→ ③ INTELLIGENT CLEAN         │
│     Recall domain       Anti-bot bypass    Apply learned rules      │
│     profiles, evolved   with undetected    + standard HTML          │
│     prompts, optimal    chromedriver       stripping pipeline       │
│     wait times                                                      │
│                                                                     │
│  ④ LLM EXTRACT ──→ ⑤ QUALITY SCORE ──→ ⑥ LEARN & STORE            │
│     Use evolved         Auto-evaluate       Update domain profile   │
│     prompts with        using 5 metrics     Store evolved prompts   │
│     domain-specific     (see below)         Adjust wait times       │
│     instructions                            Log all diagnostics     │
│                              │                                      │
│                    ┌─────────▼──────────┐                           │
│                    │  Quality < 60%?    │                           │
│                    │   → Generate new   │                           │
│                    │     strategy       │                           │
│                    │   → Retry with     │                           │
│                    │     evolved prompt │                           │
│                    └────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

### The 5 Quality Metrics

Every extraction is automatically scored across five weighted dimensions:

| Metric | Weight | What It Measures |
|--------|--------|-----------------|
| **Field Fill Rate** | 35% | Percentage of schema fields that have values (non-empty, non-N/A) |
| **Data Validity** | 30% | Whether values are meaningful — not garbage, not the field name repeated, not placeholder text |
| **Uniqueness** | 15% | De-duplication check — are extracted items actually distinct from each other? |
| **Content Quality** | 10% | Detects lorem ipsum, placeholder text, navigation artifacts, and other non-data content |
| **Result Count** | 10% | Bonus for finding multiple items — capped at 5 items for full credit |

Quality thresholds:
- ⭐ **Excellent** (≥ 85%) — Optimal extraction, no action needed
- ✅ **Good** (≥ 60%) — Acceptable quality, results returned as-is
- ⚠️ **Poor** (≥ 35%) — Triggers the self-improvement loop
- ❌ **Failure** (< 35%) — Aggressive retry with evolved strategy

### Self-Improvement: What Happens When Quality Is Low

When the quality score drops below 60%, the engine enters **self-improvement mode** — an autonomous retry loop that diagnoses the problem and generates a better extraction strategy:

1. **Issue Detection** — Identifies the specific failure mode:
   - `NO_RESULTS` → Page may need longer JS rendering time
   - `LOW_FILL_RATE` → LLM can't map fields to page content
   - `GARBAGE_CONTENT` → Extracting nav items / footer content instead of data
   - `MANY_DUPLICATES` → Same item extracted multiple times
   - `ONLY_ONE_RESULT` → Pagination or content loading issues

2. **Rule-Based Fixes** (instant, no LLM cost):
   - Auto-increases wait time for JS-heavy sites (+3s for `NO_RESULTS`)
   - Adds multilingual field mapping hints (e.g., "price" → "Miete", "Preis")
   - Tells the LLM to ignore navigation / footer artifacts
   - Adds de-duplication instructions

3. **LLM-Powered Prompt Evolution** (when fill rate < 50%):
   - Sends a **meta-prompt** to the LLM with: the original schema, the failed results, quality diagnostics, and a sample of the page content
   - The LLM analyzes *why* extraction was poor and generates domain-specific instructions
   - The evolved prompt is **versioned and stored** in the learning database for future use
   - Each subsequent scrape of the same domain starts with the best-performing prompt

4. **Adaptive Wait Times**:
   - Poor quality on a domain → automatically increases page load wait (up to 15s)
   - Excellent quality → gradually reduces wait time (saves time on fast sites)
   - Wait time adjustments are stored per-domain and applied on future visits

### What Gets Learned & Stored

The learning memory (`~/.ai_scraper/memory.db`) contains five SQLite tables:

| Table | What It Stores | How It's Used |
|-------|---------------|---------------|
| `domain_profiles` | Per-site settings: optimal wait time, avg quality, success/failure rates, cleaning strategy | Pre-apply optimal settings before scraping a known domain |
| `extraction_history` | Full log of every scrape: URL, quality score, fill rate, duration, model used, issues encountered | Trend analysis, diagnostics, pattern detection |
| `prompt_refinements` | Versioned evolved prompts per domain+schema pair, plus quality scores and usage counts | Auto-select the best-performing prompt for each domain/schema combo |
| `cleaning_rules` | Domain-specific HTML cleaning rules (CSS class, ID, or tag selectors to remove) | Strip site-specific noise before sending content to the LLM |
| `feedback` | User-provided quality corrections (`good`, `bad`, `correction`) | Train the system with human feedback |

### Using the Learning System

```python
# Learning is ON by default
scraper = AIScraper(provider="openrouter", api_key="...", learning=True)

# Scrape — learning happens automatically behind the scenes
results = scraper.scrape(url, Schema.APARTMENTS)

# Check what the brain has learned
print(scraper.stats())
# → {"total_scrapes": 47, "unique_domains": 12, "avg_quality": 0.78, ...}

# Diagnose a specific domain
print(scraper.diagnose("www.immowelt.de"))
# → {"success_rate": 0.85, "trend": "improving ↑", "recommendations": [...]}

# Provide feedback to accelerate learning
scraper.feedback(url, Schema.APARTMENTS, "good")
scraper.feedback(url, Schema.APARTMENTS, "bad", "Prices were wrong")
```

```bash
# CLI: view everything the brain has learned
ai-scraper brain

# CLI: diagnose a specific domain
ai-scraper diagnose www.immowelt.de
```

### Key Characteristics

- 🔄 **Fully autonomous** — no human intervention required for self-improvement
- 💾 **Persistent** — all learning survives restarts, crashes, and reboots
- 📈 **Trend-aware** — tracks whether quality is improving or declining per domain
- 🧬 **Prompt evolution** — the AI literally writes better prompts *for itself*
- ⏱️ **Adaptive timing** — learns the optimal page load delay per website
- 🧹 **Learned cleaning** — discovers and remembers domain-specific HTML noise patterns
- 🎯 **User-trainable** — accepts human feedback to correct and reinforce good behavior

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
┌──────────────────────────────────────────────────────────────────────┐
│                      AIScraper.scrape()                              │
│                                                                      │
│  core.py ─── Orchestrator with self-learning pipeline                │
│    ├── browser.py ── Headless Chrome (undetected_chromedriver)        │
│    ├── llm.py ────── Multi-provider LLM client                       │
│    │                 (OpenRouter / OpenAI / Kilo / Ollama)            │
│    ├── memory.py ─── SQLite-backed persistent learning memory        │
│    ├── learner.py ── Quality scoring, prompt evolution, diagnostics   │
│    ├── schemas.py ── 10 predefined extraction templates              │
│    └── cli.py ────── Rich CLI with brain/diagnose commands           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Open WebUI Integration (GUI)

AI Scraper includes a ready-to-use **Open WebUI Tool** that gives you a full GUI interface — just paste the tool file and start scraping through your chat interface.

### Setup

1. **Install AI Scraper** on your Open WebUI server:
   ```bash
   pip install openai>=1.0 beautifulsoup4>=4.12 lxml>=4.9 requests>=2.31 undetected-chromedriver>=3.5
   ```

2. **Open WebUI → Workspace → Tools → "+"**

3. **Paste** the contents of [`open_webui_tool.py`](open_webui_tool.py) into the editor

4. **Configure** your API key and provider in Tool Settings (Valves):
   - `llm_provider`: `openrouter`, `openai`, `kilo`, or `ollama`
   - `api_key`: Your API key
   - `model`: Specific model (or leave empty for default)

5. **Enable** the tool on your model in Workspace → Models

### Available Tool Methods

| Tool Method | What It Does | Example Prompt |
|-------------|-------------|----------------|
| `scrape_url` | Extract data using a predefined schema | *"Scrape job listings from https://example.com/jobs"* |
| `scrape_with_custom_fields` | Extract custom fields you define | *"Scrape name, price, rating from https://example.com/products"* |
| `ask_page` | Ask a question about any webpage | *"What products are listed on https://example.com?"* |
| `list_schemas` | Show all available schemas | *"What schemas can I use for scraping?"* |
| `show_brain_stats` | View learning statistics | *"Show me the scraper brain stats"* |

### Example Chat Prompts

```
💬 "Scrape all apartment listings from https://immowelt.de/berlin using the apartments schema"

💬 "Extract job title, company, salary, and location from https://indeed.com/jobs?q=python"

💬 "What is the main topic of https://example.com/about?"

💬 "List all available scraping schemas"

💬 "How is the AI scraper's brain performing?"
```

### Valves Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `llm_provider` | LLM provider to use | `openrouter` |
| `api_key` | API key for the provider | *(empty — set via env var or here)* |
| `model` | Specific model | *(provider default)* |
| `page_load_timeout` | Page load timeout (seconds) | `30` |
| `wait_after_load` | Wait for JS rendering (seconds) | `2.0` |

---

## 🤖 Supported AI Providers

| Provider | Setup | Free Tier? | Free Model |
|----------|-------|------------|------------|
| **OpenRouter** | [Get Key](https://openrouter.ai) | ✅ Free models available | Various free models |
| **OpenAI** | [Get Key](https://platform.openai.com) | ❌ Paid only | — |
| **Kilo** | [Get Key](https://kilo.ai) | ✅ Free models available | `kilocode/kilo-auto/free` |
| **Ollama** | [Install](https://ollama.com) | ✅ Free (local) | Any local model |

```bash
# Set API key via environment variable
export OPENROUTER_API_KEY="sk-or-v1-..."

# Or pass directly
ai-scraper scrape https://example.com --api-key "sk-or-v1-..." --schema products

# Use Kilo with the free model
ai-scraper scrape https://example.com --provider kilo --model kilocode/kilo-auto/free --schema products
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
├── open_webui_tool.py    # 🖥️ Open WebUI GUI tool (paste into Workspace)
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 💻 Advanced Usage

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

## 📝 Changelog

### v1.2.0 — Open WebUI GUI Integration
- 🖥️ Full Open WebUI Tool with 5 tool methods (scrape, custom scrape, ask, schemas, brain stats)
- 🖥️ Configurable Valves for API key, provider, model, and timing settings
- 🖥️ Self-contained tool file — no package installation required (just pip dependencies)
- 🖥️ Formatted markdown output with expandable raw JSON data
- 🖥️ Custom field extraction via chat prompts

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

MIT License · Built with 🧠 by [@masood1996-geo](https://github.com/masood1996-geo)

</div>
