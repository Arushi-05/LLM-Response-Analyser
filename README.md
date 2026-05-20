# LLM Response Analyzer

A production-grade LLM evaluation pipeline built from scratch to test and score AI-generated responses using keyword matching, semantic similarity, and structured eval reporting.

Built as part of a hands-on AI QA engineering learning journey — documenting the full iteration cycle from 26.7% to 100% pass rate across three eval runs.

---

## What It Does

- Sends questions to Claude (Anthropic API) and collects responses
- Scores each response using a custom two-component scorer:
  - **Keyword matching** — checks if expected terms appear in the response
  - **Semantic similarity** — uses sentence embeddings + cosine similarity to measure meaning alignment
- Generates a rich HTML eval report with per-question score breakdowns, keyword pills, and pass/fail filtering
- Traces every run in LangSmith for full observability

---

## Project Structure

```
LLM Response Analyzer/
├── src/
│   ├── llm_client.py        # Main eval runner — calls Claude, scores, reports
│   ├── scorer.py            # Keyword + semantic scoring logic
│   ├── embedder.py          # Sentence embeddings via sentence-transformers
│   └── reporter.py          # HTML report generator
├── test/
│   └── test_scorer.py       # pytest unit tests for scorer
├── data/
│   └── testQuestions.json   # Golden dataset — 15 questions with expected answers
├── results/
│   └── eval_report.html     # Generated eval report (open in browser)
├── conftest.py              # pytest path configuration
├── .env                     # API keys (not committed)
└── README.md
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Anthropic Claude API | LLM being evaluated |
| sentence-transformers (`all-MiniLM-L6-v2`) | Generating text embeddings |
| scikit-learn | Cosine similarity calculation |
| LangSmith | Run tracing and observability |
| pytest | Unit testing for scorer logic |
| python-dotenv | Environment variable management |
| Custom HTML reporter | Eval report generation |

---

## Scoring Formula

Each response is scored across two dimensions and combined into a final score:

```
Final Score = (0.2 × keyword_score) + (0.8 × embedding_score)
```

- **Keyword Score** — fraction of expected keywords found in the response (0–1)
- **Embedding Score** — cosine similarity between response and expected answer embeddings (0–1)
- **Pass threshold** — Final score ≥ 75%

The 80/20 weighting intentionally favours semantic correctness over exact vocabulary matching, since LLMs express correct answers in varied language.

---

## Setup

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Anthropic API key → [console.anthropic.com](https://console.anthropic.com)
- LangSmith API key → [smith.langchain.com](https://smith.langchain.com) (optional but recommended)

### Installation

```bash
git clone https://github.com/yourusername/llm-response-analyzer
cd llm-response-analyzer

# Install dependencies
uv sync
# or: pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file at the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
HF_TOKEN=hf_...                        # HuggingFace token (optional, silences rate limit warning)
LANGCHAIN_TRACING_V2=true              # Enable LangSmith tracing
LANGCHAIN_API_KEY=ls__...              # LangSmith API key
LANGCHAIN_PROJECT=llm-response-analyzer
```

---

## Running the Eval

```bash
uv run src/llm_client.py
```

Output:
```
✓ API key loaded: sk-ant-api03-...
✓ LangSmith tracing enabled → project: llm-response-analyzer
Running eval on 15 questions...

[1/15] Why do orcas sometimes attack great white sharks...
  ✓ PASS — 78.7%
[2/15] How do snow leopards survive in extreme Himalayan...
  ✓ PASS — 73.2%
...

========================================
RESULTS: 15/15 passed
Accuracy: 100.00%
========================================

✓ HTML report written to: results/eval_report.html
```

Open the report:
```bash
open results/eval_report.html
```

---

## Running Tests

Unit tests for the scorer:

```bash
uv run pytest test/test_scorer.py -v
```

```
test/test_scorer.py::TestKeywordScore::test_all_keywords_matched_returns_perfect_score PASSED
test/test_scorer.py::TestKeywordScore::test_empty_response_returns_zero PASSED
test/test_scorer.py::TestKeywordScore::test_case_insensitive_matching PASSED
test/test_scorer.py::TestFinalScore::test_final_score_weighted_average_is_correct PASSED
...
✅ 25 tests passing
```

Tests cover:
- Keyword matching — case sensitivity, word boundaries, empty inputs, unicode
- Score scaling correctness — 0–1 range, no double scaling bug
- Weighted average formula validation
- Edge cases — None inputs, special characters, empty keyword lists

---

## The Dataset

`data/testQuestions.json` contains 15 questions across two domains:

- **Wildlife & Biology** (Q1–Q5) — orcas, snow leopards, bison, axolotls, elephants
- **Skincare & Dermatology** (Q6–Q15) — retinol, hyaluronic acid, acne, sunscreen, collagen

Each question has:
- `question` — the prompt sent to Claude
- `expected_keywords` — terms that should appear in a correct answer
- `expected_answer` — a detailed reference answer used for semantic similarity scoring

---

## Eval Run History

Three documented iterations showing the full QA improvement cycle:

### Run 1 — Baseline
| Metric | Value |
|---|---|
| Pass rate | 26.7% (4/15) |
| Avg score | ~71.5% |

**Root causes identified:**
- `max_tokens=150` was cutting responses mid-sentence
- Expected answers were 1-sentence summaries — style mismatch with Claude's detailed responses
- Embedding scorer penalising verbosity, not quality

### Run 2 — After Fixes
| Metric | Value |
|---|---|
| Pass rate | 80.0% (12/15) |
| Avg score | ~80.3% |

**Changes made:**
- Increased `max_tokens` to 400
- Rewrote expected answers to match Claude's response depth and vocabulary
- Added system prompt to normalise response format

### Run 3 — Final
| Metric | Value |
|---|---|
| Pass rate | 100% (15/15) |
| Avg score | 81.0% |
| Score range | 71.6% – 90.1% |

**Key finding:** Keyword scores are consistently low (11–89%) while semantic scores are consistently high (83–94%). Claude answers correctly but uses different vocabulary than keyword lists — semantic similarity is the reliable signal.

---

## Key Findings

**Finding 1 — Keyword scorer systematically underperforms on semantic equivalents**
The keyword scorer penalises correct answers that use synonyms or rephrasings. "Enlarged nasal cavities" vs "low oxygen", "cell turnover" vs "skin renewal". Recommendation: keyword lists should include synonym variants, or keyword weight should be reduced below 20%.

**Finding 2 — Semantic scorer is the reliable signal**
Embedding similarity (all-MiniLM-L6-v2) correctly identifies correct answers across all 15 questions with scores ranging 83–94%. This is the primary quality signal in this pipeline.

**Finding 3 — Golden dataset quality determines everything**
The biggest improvement came not from changing the model or prompt — but from improving the expected answers in the test dataset. Eval quality is a data quality problem before it's a model quality problem.

---

## HTML Report Features

The generated report includes:

- **Dashboard** — total questions, pass/fail counts, pass rate, average score
- **Score distribution bar** — visual breakdown across Excellent / Pass / Poor / Fail bands
- **Filter buttons** — view all, passed only, or failed only
- **Per-question cards** — question text, pass/fail status, three score bars (keyword, semantic, final), keyword pills (green = matched, red strikethrough = missed), side-by-side model response vs expected answer

---

## What's Next — Phase 2

- Integrate **DeepEval** for industry-standard eval metrics (HallucinationMetric, AnswerRelevancyMetric, FaithfulnessMetric)
- Add **RAGAS** for RAG pipeline evaluation
- Build a **ChromaDB** vector store and test retrieval quality with Recall@K
- Add **red-teaming** — prompt injection and adversarial input test cases
- Set up **CI/CD eval gate** via GitHub Actions

---

## Skills Demonstrated

`LLM Evaluation` · `Eval Pipeline Design` · `Golden Dataset Creation` · `Semantic Scoring` · `Embedding-based Similarity` · `LangSmith Tracing` · `Unit Testing` · `Root Cause Analysis` · `Iterative Quality Improvement` · `HTML Report Generation` · `AI QA Engineering`

---

## Author

Built by a Senior QA Engineer transitioning into AI Quality Engineering.

Part of a structured learning journey toward AI QA roles — documenting every project, finding, and iteration publicly.