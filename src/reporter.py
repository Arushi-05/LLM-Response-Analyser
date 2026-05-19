import csv
import json
from datetime import datetime
from pathlib import Path


def write_csv(results: list, output_path: str = "results/eval_report.csv"):
    """Legacy CSV writer — kept for backwards compatibility."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "question", "response", "expected_answer",
        "matched_keywords", "keyword_score_percent",
        "embedding_score_percent", "score", "passed"
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[k for k in fieldnames if k in (results[0] if results else {})] )
        writer.writeheader()
        writer.writerows(results)


def write_html_report(results: list, output_path: str = "results/eval_report.html"):
    """
    Generates a rich, readable HTML eval report.
    Opens in any browser — no server needed.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0
    avg_score = sum(r.get("score", 0) for r in results) / total if total else 0

    # Score distribution buckets
    excellent = sum(1 for r in results if r.get("score", 0) >= 85)
    good      = sum(1 for r in results if 75 <= r.get("score", 0) < 85)
    poor      = sum(1 for r in results if 60 <= r.get("score", 0) < 75)
    bad       = sum(1 for r in results if r.get("score", 0) < 60)

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

    # Build question cards HTML
    cards_html = ""
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        passed_val = r.get("passed", False)
        kw_score = r.get("keyword_score_percent", 0)
        emb_score = r.get("embedding_score_percent", 0)
        matched = r.get("matched_keywords", [])
        question = r.get("question", "")
        response = r.get("response", "").replace("\n", "<br>").replace("##", "").replace("**", "")
        expected = r.get("expected_answer", "").replace("\n", "<br>")

        if score >= 85:
            badge_class = "badge-excellent"
            badge_text = "Excellent"
        elif score >= 75:
            badge_class = "badge-pass"
            badge_text = "Pass"
        elif score >= 60:
            badge_class = "badge-poor"
            badge_text = "Poor"
        else:
            badge_class = "badge-fail"
            badge_text = "Fail"

        status_class = "card-pass" if passed_val else "card-fail"
        status_icon = "✓" if passed_val else "✗"
        status_label = "PASSED" if passed_val else "FAILED"

        # Keyword pills
        all_keywords = r.get("expected_keywords", matched)
        keyword_pills = ""
        for kw in all_keywords:
            hit = kw in matched
            pill_class = "pill-hit" if hit else "pill-miss"
            keyword_pills += f'<span class="pill {pill_class}">{kw}</span>'

        # Score bar widths
        kw_w = min(kw_score, 100)
        emb_w = min(emb_score, 100)
        final_w = min(score, 100)

        cards_html += f"""
        <div class="card {status_class}">
            <div class="card-header">
                <div class="card-left">
                    <span class="q-number">Q{i:02d}</span>
                    <p class="question-text">{question}</p>
                </div>
                <div class="card-right">
                    <span class="badge {badge_class}">{badge_text}</span>
                    <div class="status-circle {'circle-pass' if passed_val else 'circle-fail'}">
                        {status_icon}
                    </div>
                </div>
            </div>

            <div class="score-bars">
                <div class="bar-row">
                    <span class="bar-label">Keyword</span>
                    <div class="bar-track">
                        <div class="bar-fill bar-keyword" style="width:{kw_w}%"></div>
                    </div>
                    <span class="bar-value">{kw_score:.1f}%</span>
                </div>
                <div class="bar-row">
                    <span class="bar-label">Semantic</span>
                    <div class="bar-track">
                        <div class="bar-fill bar-semantic" style="width:{emb_w}%"></div>
                    </div>
                    <span class="bar-value">{emb_score:.1f}%</span>
                </div>
                <div class="bar-row">
                    <span class="bar-label">Final</span>
                    <div class="bar-track">
                        <div class="bar-fill bar-final" style="width:{final_w}%"></div>
                    </div>
                    <span class="bar-value final-score-val">{score:.1f}%</span>
                </div>
            </div>

            <div class="keywords-row">
                <span class="kw-label">Keywords:</span>
                {keyword_pills}
            </div>

            <div class="answers-grid">
                <div class="answer-box answer-model">
                    <div class="answer-label">Model Response</div>
                    <div class="answer-text">{response}</div>
                </div>
                <div class="answer-box answer-expected">
                    <div class="answer-label">Expected Answer</div>
                    <div class="answer-text">{expected}</div>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Eval Report</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:        #0f1117;
    --surface:   #181c27;
    --surface2:  #1f2435;
    --border:    #2a3045;
    --pass:      #00c896;
    --fail:      #ff4d6d;
    --warn:      #ffb347;
    --accent:    #4f8ef7;
    --text:      #e8eaf0;
    --muted:     #7a8099;
    --excellent: #00e5b4;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ── HEADER ── */
  .header {{
    background: linear-gradient(135deg, #111827 0%, #1a2035 50%, #0f1520 100%);
    border-bottom: 1px solid var(--border);
    padding: 40px 48px 32px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(79,142,247,0.08) 0%, transparent 70%);
    pointer-events: none;
  }}
  .header-top {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 32px;
  }}
  .header h1 {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.5px;
    color: #fff;
  }}
  .header h1 span {{ color: var(--accent); }}
  .timestamp {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
  }}

  /* ── SUMMARY STATS ── */
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
  }}
  .stat-card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
  }}
  .stat-card::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 10px 10px;
  }}
  .stat-card.s-total::after   {{ background: var(--accent); }}
  .stat-card.s-pass::after    {{ background: var(--pass); }}
  .stat-card.s-fail::after    {{ background: var(--fail); }}
  .stat-card.s-rate::after    {{ background: var(--excellent); }}
  .stat-card.s-avg::after     {{ background: var(--warn); }}

  .stat-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 32px;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 6px;
  }}
  .s-total  .stat-value {{ color: var(--accent); }}
  .s-pass   .stat-value {{ color: var(--pass); }}
  .s-fail   .stat-value {{ color: var(--fail); }}
  .s-rate   .stat-value {{ color: var(--excellent); }}
  .s-avg    .stat-value {{ color: var(--warn); }}
  .stat-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    font-weight: 500;
  }}

  /* ── DISTRIBUTION BAR ── */
  .dist-section {{
    padding: 24px 48px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }}
  .dist-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    margin-bottom: 12px;
  }}
  .dist-bar {{
    display: flex;
    height: 28px;
    border-radius: 6px;
    overflow: hidden;
    gap: 2px;
  }}
  .dist-seg {{
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    transition: opacity 0.2s;
    min-width: 0;
  }}
  .dist-seg:hover {{ opacity: 0.85; }}
  .d-excellent {{ background: var(--excellent); color: #000; }}
  .d-good      {{ background: var(--pass);      color: #000; }}
  .d-poor      {{ background: var(--warn);      color: #000; }}
  .d-bad       {{ background: var(--fail);      color: #fff; }}
  .dist-legend {{
    display: flex;
    gap: 20px;
    margin-top: 10px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--muted);
  }}
  .legend-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
  }}

  /* ── FILTER BAR ── */
  .filter-bar {{
    padding: 16px 48px;
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 10px;
    align-items: center;
  }}
  .filter-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 6px 16px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
    transition: all 0.15s;
  }}
  .filter-btn:hover, .filter-btn.active {{
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(79,142,247,0.08);
  }}

  /* ── CARDS ── */
  .cards-container {{
    padding: 32px 48px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
  }}
  .card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  }}
  .card-pass {{ border-left: 4px solid var(--pass); }}
  .card-fail {{ border-left: 4px solid var(--fail); }}

  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 20px 24px 16px;
    gap: 16px;
  }}
  .card-left {{ flex: 1; }}
  .card-right {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }}

  .q-number {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 1px;
    display: block;
    margin-bottom: 6px;
  }}
  .question-text {{
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.5;
  }}

  .badge {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
  }}
  .badge-excellent {{ background: rgba(0,229,180,0.15); color: var(--excellent); border: 1px solid rgba(0,229,180,0.3); }}
  .badge-pass      {{ background: rgba(0,200,150,0.15); color: var(--pass);      border: 1px solid rgba(0,200,150,0.3); }}
  .badge-poor      {{ background: rgba(255,179,71,0.15); color: var(--warn);     border: 1px solid rgba(255,179,71,0.3); }}
  .badge-fail      {{ background: rgba(255,77,109,0.15); color: var(--fail);     border: 1px solid rgba(255,77,109,0.3); }}

  .status-circle {{
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    flex-shrink: 0;
  }}
  .circle-pass {{ background: rgba(0,200,150,0.15); color: var(--pass); border: 2px solid rgba(0,200,150,0.4); }}
  .circle-fail {{ background: rgba(255,77,109,0.15); color: var(--fail); border: 2px solid rgba(255,77,109,0.4); }}

  /* ── SCORE BARS ── */
  .score-bars {{
    padding: 0 24px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .bar-row {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .bar-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    width: 60px;
    flex-shrink: 0;
  }}
  .bar-track {{
    flex: 1;
    height: 6px;
    background: var(--surface2);
    border-radius: 3px;
    overflow: hidden;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
  }}
  .bar-keyword  {{ background: linear-gradient(90deg, #4f8ef7, #7ab3ff); }}
  .bar-semantic {{ background: linear-gradient(90deg, #a78bfa, #c4b5fd); }}
  .bar-final    {{ background: linear-gradient(90deg, #00c896, #00e5b4); }}
  .card-fail .bar-final {{ background: linear-gradient(90deg, #ff4d6d, #ff8fa3); }}
  .bar-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    width: 42px;
    text-align: right;
    flex-shrink: 0;
  }}
  .final-score-val {{ font-weight: 600; color: var(--text); }}

  /* ── KEYWORDS ── */
  .keywords-row {{
    padding: 0 24px 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }}
  .kw-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-right: 4px;
  }}
  .pill {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
  }}
  .pill-hit  {{ background: rgba(0,200,150,0.12); color: var(--pass);  border: 1px solid rgba(0,200,150,0.25); }}
  .pill-miss {{ background: rgba(255,77,109,0.10); color: var(--fail); border: 1px solid rgba(255,77,109,0.2); text-decoration: line-through; opacity: 0.7; }}

  /* ── ANSWERS ── */
  .answers-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
    border-top: 1px solid var(--border);
  }}
  .answer-box {{
    padding: 16px 24px;
    background: var(--surface);
  }}
  .answer-model    {{ background: rgba(79,142,247,0.04); }}
  .answer-expected {{ background: rgba(0,200,150,0.04); }}
  .answer-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .answer-model    .answer-label {{ color: var(--accent); }}
  .answer-expected .answer-label {{ color: var(--pass); }}
  .answer-text {{
    font-size: 13px;
    color: #b0b8d0;
    line-height: 1.65;
    max-height: 160px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }}

  /* ── FOOTER ── */
  .footer {{
    padding: 24px 48px;
    border-top: 1px solid var(--border);
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: var(--muted);
  }}

  @media (max-width: 768px) {{
    .header, .cards-container, .filter-bar, .dist-section {{ padding-left: 20px; padding-right: 20px; }}
    .answers-grid {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div>
      <h1>LLM <span>Eval</span> Report</h1>
      <div class="timestamp">Generated {timestamp}</div>
    </div>
  </div>
  <div class="stats-grid">
    <div class="stat-card s-total">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Total Questions</div>
    </div>
    <div class="stat-card s-pass">
      <div class="stat-value">{passed}</div>
      <div class="stat-label">Passed</div>
    </div>
    <div class="stat-card s-fail">
      <div class="stat-value">{failed}</div>
      <div class="stat-label">Failed</div>
    </div>
    <div class="stat-card s-rate">
      <div class="stat-value">{pass_rate:.0f}%</div>
      <div class="stat-label">Pass Rate</div>
    </div>
    <div class="stat-card s-avg">
      <div class="stat-value">{avg_score:.1f}</div>
      <div class="stat-label">Avg Score</div>
    </div>
  </div>
</div>

<div class="dist-section">
  <div class="dist-label">Score Distribution</div>
  <div class="dist-bar">
    {"" if excellent == 0 else f'<div class="dist-seg d-excellent" style="flex:{excellent}">{excellent} ≥85%</div>'}
    {"" if good == 0      else f'<div class="dist-seg d-good"      style="flex:{good}">{good} 75–85%</div>'}
    {"" if poor == 0      else f'<div class="dist-seg d-poor"      style="flex:{poor}">{poor} 60–75%</div>'}
    {"" if bad == 0       else f'<div class="dist-seg d-bad"        style="flex:{bad}">{bad} &lt;60%</div>'}
  </div>
  <div class="dist-legend">
    <div class="legend-item"><div class="legend-dot" style="background:var(--excellent)"></div>Excellent ≥85%</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--pass)"></div>Pass 75–85%</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--warn)"></div>Poor 60–75%</div>
    <div class="legend-item"><div class="legend-dot" style="background:var(--fail)"></div>Fail &lt;60%</div>
  </div>
</div>

<div class="filter-bar">
  <span style="font-size:11px;color:var(--muted);font-family:'IBM Plex Mono',monospace;margin-right:4px;">FILTER:</span>
  <button class="filter-btn active" onclick="filterCards('all', this)">All ({total})</button>
  <button class="filter-btn" onclick="filterCards('pass', this)">Passed ({passed})</button>
  <button class="filter-btn" onclick="filterCards('fail', this)">Failed ({failed})</button>
</div>

<div class="cards-container" id="cardsContainer">
{cards_html}
</div>

<div class="footer">
  LLM Response Analyzer · Phase 1 Eval Pipeline · {total} questions evaluated
</div>

<script>
  function filterCards(type, btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.card').forEach(card => {{
      if (type === 'all') {{
        card.style.display = '';
      }} else if (type === 'pass') {{
        card.style.display = card.classList.contains('card-pass') ? '' : 'none';
      }} else {{
        card.style.display = card.classList.contains('card-fail') ? '' : 'none';
      }}
    }});
  }}
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✓ HTML report written to: {output_path}")
    print(f"  Open it in your browser: open {output_path}")