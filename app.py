"""
Football Sniper V20.4.5 — Streamlit Web UI
Run: streamlit run app.py
"""

import streamlit as st
import json, math, os
import numpy as np
from scipy.stats import poisson
from datetime import date, datetime

# ── Page config ───────────────────────────────────────
st.set_page_config(
    page_title="Football Sniper",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #0a0a0a;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem; max-width: 1100px; }

/* Header */
.sniper-header {
    text-align: center;
    padding: 3rem 0 2rem;
    position: relative;
}
.sniper-logo {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .25em;
    text-transform: uppercase;
    color: #4ade80;
    margin-bottom: 12px;
}
.sniper-title {
    font-family: 'Syne', sans-serif;
    font-size: 52px;
    font-weight: 800;
    color: #f5f4f0;
    line-height: 1;
    margin-bottom: 10px;
}
.sniper-title span { color: #4ade80; }
.sniper-sub {
    font-size: 14px;
    color: #666;
    letter-spacing: .03em;
}

/* Stats bar */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 32px;
    padding: 16px 0;
    margin: 1.5rem 0;
    border-top: 1px solid #1a1a1a;
    border-bottom: 1px solid #1a1a1a;
}
.stat-item { text-align: center; }
.stat-val {
    font-family: 'DM Mono', monospace;
    font-size: 20px;
    font-weight: 500;
    color: #4ade80;
    display: block;
}
.stat-lbl {
    font-size: 10px;
    color: #555;
    text-transform: uppercase;
    letter-spacing: .08em;
}

/* Form section */
.form-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}
.form-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #555;
    margin-bottom: 8px;
    display: block;
}

/* Override streamlit inputs */
.stSelectbox > div > div {
    background: #0f0f0f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #f5f4f0 !important;
}
.stTextInput > div > div > input {
    background: #0f0f0f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #f5f4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stNumberInput > div > div > input {
    background: #0f0f0f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #f5f4f0 !important;
}

/* Result cards */
.result-wrapper {
    animation: fadeIn .4s ease;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }

.tier-banner {
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.tier-banner.sniper {
    background: #0d2a1a;
    border: 1px solid #1a5c2e;
}
.tier-banner.hold {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
}
.tier-icon {
    font-size: 42px;
    display: block;
    margin-bottom: 8px;
}
.tier-label {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 800;
    display: block;
    margin-bottom: 4px;
}
.tier-label.sniper { color: #4ade80; }
.tier-label.hold { color: #666; }
.tier-reason {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #555;
}

/* Metric grid */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 16px 18px;
}
.metric-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #444;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #f5f4f0;
}
.metric-sub {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #555;
    margin-top: 2px;
}
.metric-value.green { color: #4ade80; }
.metric-value.amber { color: #fbbf24; }
.metric-value.red   { color: #f87171; }

/* Probability bars */
.prob-section {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 1.5rem;
}
.prob-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 12px;
}
.prob-row:last-child { margin-bottom: 0; }
.prob-name {
    font-size: 12px;
    color: #888;
    min-width: 90px;
}
.prob-bar-bg {
    flex: 1;
    height: 8px;
    background: #1a1a1a;
    border-radius: 4px;
    overflow: hidden;
}
.prob-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width .6s ease;
}
.prob-pct {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: #f5f4f0;
    min-width: 44px;
    text-align: right;
}

/* Filter badges */
.filter-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 1.5rem;
}
.filter-badge {
    background: #111;
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
}
.filter-badge.pass { border: 1px solid #1a3d26; }
.filter-badge.fail { border: 1px solid #2a1a1a; }
.filter-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.filter-dot.pass { background: #4ade80; }
.filter-dot.fail { background: #f87171; }
.filter-name { color: #888; font-size: 11px; }
.filter-msg  { color: #444; font-size: 10px; font-family: 'DM Mono', monospace; margin-top: 1px; }

/* Top scores */
.scores-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.score-pill {
    background: #161616;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #888;
}
.score-pill span { color: #f5f4f0; }

/* Kelly card */
.kelly-card {
    background: #0d1f13;
    border: 1px solid #1a3d26;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 1.5rem;
}
.kelly-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #4ade80;
    margin-bottom: 12px;
    font-weight: 500;
}
.kelly-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}
.kelly-item { text-align: center; }
.kelly-val {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #4ade80;
    display: block;
}
.kelly-lbl {
    font-size: 10px;
    color: #444;
    margin-top: 2px;
}

/* Warning cards */
.warning-card {
    background: #1a1200;
    border: 1px solid #3d2f00;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 12px;
    color: #fbbf24;
}

/* H2H */
.h2h-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 1.5rem;
}
.h2h-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #555;
    margin-bottom: 12px;
}
.h2h-bars {
    display: flex;
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
    gap: 2px;
    margin-bottom: 8px;
}
.h2h-label-row {
    display: flex;
    justify-content: space-between;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
}

/* Divider */
.divider {
    height: 1px;
    background: #1a1a1a;
    margin: 1.5rem 0;
}

/* Footer */
.sniper-footer {
    text-align: center;
    padding: 2rem 0 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #333;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  MODEL LOADER
# ══════════════════════════════════════════════════════

@st.cache_resource
def load_model_data(model_path: str):
    with open(model_path, "r") as f:
        return json.load(f)

def get_model_path():
    candidates = [
        "data/model_v20_complete.json",
        "model_v20_complete.json",
        "outputs/model_v20_complete.json",
        "/content/drive/MyDrive/Football_Project/outputs/model_v20_complete.json",
        "/content/drive/MyDrive/Football_Project/v20_3_1/outputs/model_v20_complete_v2031.json",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

model_path = get_model_path()
MODEL_LOADED = False
v20 = {}

if model_path:
    try:
        v20 = load_model_data(model_path)
        MODEL_LOADED = True
    except Exception as e:
        st.error(f"Error loading model: {e}")


# ══════════════════════════════════════════════════════
#  ENGINE FUNCTIONS
# ══════════════════════════════════════════════════════

def _tau(lh, la, gh, ga, rho):
    if   gh==0 and ga==0: return 1 - lh*la*rho
    elif gh==1 and ga==0: return 1 + la*rho
    elif gh==0 and ga==1: return 1 + lh*rho
    elif gh==1 and ga==1: return 1 - rho
    return 1.0

def dc_predict(home, away, liga, max_goals=8):
    DC = v20.get("dc_params", {})
    p  = DC.get(liga)
    if not p: return None
    atk, dfn, hfa, rho = p["attack"], p["defense"], p["hfa"], p["rho"]
    if home not in atk or away not in atk:
        lam_h, lam_a = math.exp(hfa), 1.0
    else:
        lam_h = math.exp(atk[home] + dfn[away] + hfa)
        lam_a = math.exp(atk[away] + dfn[home])
    M = np.zeros((max_goals+1, max_goals+1))
    for gh in range(max_goals+1):
        for ga in range(max_goals+1):
            M[gh,ga] = _tau(lam_h,lam_a,gh,ga,rho)*poisson.pmf(gh,lam_h)*poisson.pmf(ga,lam_a)
    M /= M.sum()
    hw = float(np.sum(np.tril(M,-1)))
    dr = float(np.sum(np.diag(M)))
    aw = float(np.sum(np.triu(M,1)))
    flat = np.argsort(M.ravel())[::-1][:5]
    top  = [((int(i//(max_goals+1)), int(i%(max_goals+1))), float(M.ravel()[i])) for i in flat]
    return {"home_win":round(hw,4),"draw":round(dr,4),"away_win":round(aw,4),
            "lambda_home":round(lam_h,3),"lambda_away":round(lam_a,3),"top_scores":top}

def elo_predict(home, away, liga):
    ELO = v20.get("elo", {})
    tbl = ELO.get(liga, {})
    rh  = tbl.get(home, 1500) + 50
    ra  = tbl.get(away, 1500)
    eh  = 1/(1+10**((ra-rh)/400))
    ea  = 1-eh
    diff = abs(eh-ea)
    dr  = max(0.18, 0.35-diff*0.5)
    hw  = eh*(1-dr); aw = ea*(1-dr)
    t   = hw+dr+aw
    return {"home_win":round(hw/t,4),"draw":round(dr/t,4),"away_win":round(aw/t,4),
            "elo_home":tbl.get(home,1500),"elo_away":tbl.get(away,1500),
            "elo_diff":int(tbl.get(home,1500)-tbl.get(away,1500))}

def predict_full(home, away, liga, odds=None):
    THRESH  = v20.get("sniper_threshold", {})
    DRAW_B  = v20.get("draw_boost", {})
    GK      = v20.get("giant_killers", {})
    DRAW_W  = v20.get("draw_warning", {})
    ELO     = v20.get("elo", {})
    H2H     = v20.get("h2h_stats", {})

    dc = dc_predict(home, away, liga)
    if not dc: return None
    el = elo_predict(home, away, liga)

    h = 0.55*dc["home_win"] + 0.45*el["home_win"]
    d = 0.55*dc["draw"]     + 0.45*el["draw"]
    a = 0.55*dc["away_win"] + 0.45*el["away_win"]

    boost = DRAW_B.get(liga, 1.431)
    d *= boost
    t  = h+d+a; h/=t; d/=t; a/=t

    conf  = max(h,d,a)
    probs = {"home_win":h,"draw":d,"away_win":a}
    pred  = max(probs, key=probs.get)
    thr   = THRESH.get(liga, 0.65)

    # Filters
    filters = []
    tier    = "SNIPER"

    # 1. Threshold
    f1_pass = conf >= thr
    filters.append(("Threshold", f1_pass,
                    f"Conf {conf:.3f} {'≥' if f1_pass else '<'} thr {thr:.2f}"))
    if not f1_pass: tier = "HOLD"

    # 2. Draw Warning
    dw_thr = DRAW_W.get(liga, 0)
    f2_pass = not (dw_thr and d > dw_thr)
    dw_msg  = f"Draw {d:.3f} {'≤' if f2_pass else '>'} limit {dw_thr:.3f}"
    filters.append(("Draw warning", f2_pass, dw_msg))
    if not f2_pass: tier = "HOLD"

    # 3. Giant Killer
    tbl = ELO.get(liga, {})
    gap = tbl.get(away,1500) - tbl.get(home,1500)
    gk_score = GK.get(home, 0)
    f3_pass  = not (gap >= 100 and gk_score >= 2.0)
    filters.append(("Giant killer", f3_pass,
                    f"GK score {gk_score} | gap {int(gap):+d}"))
    if not f3_pass: tier = "HOLD"

    # 4. Lambda
    lam_total = dc["lambda_home"] + dc["lambda_away"]
    f4_pass   = 1.2 <= lam_total <= 6.5
    filters.append(("Lambda", f4_pass,
                    f"λ total {lam_total:.2f} [1.2–6.5]"))
    if not f4_pass: tier = "HOLD"

    # 5. Elo Gap
    elo_diff  = el["elo_diff"]
    f5_pass   = abs(elo_diff) >= 30
    filters.append(("Elo gap", f5_pass,
                    f"Gap {abs(elo_diff)} {'≥' if f5_pass else '<'} 30"))
    if not f5_pass: tier = "HOLD"

    # 6. EV Check
    strict = {"EPL","La_Liga"}
    if odds and odds > 1.0:
        ev = round((conf*odds)-1, 4)
        f6_pass = ev >= 0.05
        filters.append(("EV check",f6_pass,f"EV {ev:+.3f} vs min +0.05"))
        if not f6_pass: tier = "HOLD"
    elif liga in strict and not odds:
        filters.append(("EV check", False, "EPL/La_Liga wajib input odds"))
        tier = "HOLD"
    else:
        filters.append(("EV check", True, "Odds tidak diinput (opsional)"))

    # Kelly
    kelly = None
    if odds and odds > 1.0:
        ev_k = (conf*odds)-1
        if ev_k >= 0.05 and conf >= 0.60:
            b = odds-1
            f_full = (conf*(b+1)-1)/b
            frac = 0.25 if conf>=0.70 else (0.20 if conf>=0.65 else 0.125)
            tier_k = "Quarter-K" if frac==0.25 else ("Fifth-K" if frac==0.20 else "Eighth-K")
            stake = round(min(f_full*frac, 0.10), 4)
            kelly = {"ev":round(ev_k,4),"f_full":round(f_full,4),
                     "stake":stake,"tier":tier_k,"active":True}

    # H2H
    h2h = (H2H.get(f"('{home}', '{away}')") or
           H2H.get(f"('{away}', '{home}')"))

    # fail reason
    failed = [f for f in filters if not f[1]]
    reason = failed[0][2] if failed else "All filters passed"

    return {
        "prediction":pred,"home_prob":round(h,4),
        "draw_prob":round(d,4),"away_prob":round(a,4),
        "confidence":round(conf,4),"tier":tier,
        "threshold":thr,"filters":filters,"reason":reason,
        "dc":dc,"elo":el,"kelly":kelly,"h2h":h2h,
        "liga":liga,"home":home,"away":away,
        "elo_diff":el["elo_diff"],
    }

def get_teams(liga):
    DC = v20.get("dc_params", {})
    p  = DC.get(liga)
    if not p: return []
    return sorted(p["attack"].keys())


# ══════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="sniper-header">
    <div class="sniper-logo">⬡ Football Sniper System</div>
    <div class="sniper-title">The <span>Sniper</span></div>
    <div class="sniper-sub">Dixon-Coles V3 · Elo Walk-Forward · 6-Layer Filter · V20.3.1</div>
</div>
<div class="stats-bar">
    <div class="stat-item"><span class="stat-val">81.4%</span><span class="stat-lbl">WF Accuracy</span></div>
    <div class="stat-item"><span class="stat-val">+1.6%</span><span class="stat-lbl">Yield vs B365</span></div>
    <div class="stat-item"><span class="stat-val">4.3e-19</span><span class="stat-lbl">p-value</span></div>
    <div class="stat-item"><span class="stat-val">17</span><span class="stat-lbl">Active Leagues</span></div>
    <div class="stat-item"><span class="stat-val">405</span><span class="stat-lbl">Teams</span></div>
</div>
""", unsafe_allow_html=True)

if not MODEL_LOADED:
    st.error("Model tidak ditemukan. Pastikan `model_v20_complete.json` ada di folder yang sama dengan `app.py`, atau edit variabel `candidates` di `get_model_path()`.")
    st.stop()

# Load dari JSON — otomatis include semua liga aktif
ACTIVE_LEAGUES = v20.get("active_leagues", [
    "Bundesliga","EPL","Serie_A","Eredivisie",
    "La_Liga","Liga_Portugal","Super_Lig",
    "Ligue_1","Belgium","Scotland","J1_League"
])

# Display names yang lebih rapi
LIGA_DISPLAY = {
    "EPL"          : "Premier League (England)",
    "Bundesliga"   : "Bundesliga (Germany)",
    "Serie_A"      : "Serie A (Italy)",
    "La_Liga"      : "La Liga (Spain)",
    "Ligue_1"      : "Ligue 1 (France)",
    "Eredivisie"   : "Eredivisie (Netherlands)",
    "Liga_Portugal": "Primeira Liga (Portugal)",
    "Super_Lig"    : "Super Lig (Turkey)",
    "Belgium"      : "Pro League (Belgium)",
    "Scotland"     : "Premiership (Scotland)",
    "Brazil"       : "Serie A (Brazil)",
    "J1_League"    : "J1 League (Japan)",
    "Venezuela"    : "Liga FUTVE (Venezuela)",
    "Russia"       : "Premier Liga (Russia)",
    "Denmark"      : "Superliga (Denmark)",
    "Ukraine"      : "Premier Liga (Ukraine)",
}

# ── Input form ────────────────────────────────────────
st.markdown('<div class="form-card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.2, 1.2, 1])

with col1:
    st.markdown('<span class="form-label">Liga</span>', unsafe_allow_html=True)
    liga_options = {LIGA_DISPLAY.get(l, l): l for l in ACTIVE_LEAGUES}
    liga_display = st.selectbox("Liga", list(liga_options.keys()),
                                label_visibility="collapsed")
    liga = liga_options[liga_display]

teams = get_teams(liga)

with col2:
    st.markdown('<span class="form-label">Tim Kandang</span>', unsafe_allow_html=True)
    home_team = st.selectbox("Tim Kandang", teams, label_visibility="collapsed")

with col3:
    away_options = [t for t in teams if t != home_team]
    st.markdown('<span class="form-label">Tim Tamu</span>', unsafe_allow_html=True)
    away_team = st.selectbox("Tim Tamu", away_options, label_visibility="collapsed")

col4, col5, col6 = st.columns([1, 1, 2])

with col4:
    st.markdown('<span class="form-label">Tanggal Pertandingan</span>', unsafe_allow_html=True)
    match_date = st.date_input("Tanggal", value=date.today(), label_visibility="collapsed")

with col5:
    st.markdown('<span class="form-label">Odds Pasar (opsional)</span>', unsafe_allow_html=True)
    odds_input = st.number_input("Odds", min_value=1.01, max_value=20.0,
                                  value=1.80, step=0.01, label_visibility="collapsed")
    use_odds = st.checkbox("Gunakan odds untuk EV check", value=True)

with col6:
    st.markdown('<span class="form-label">&nbsp;</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🎯  ANALISA SEKARANG", use_container_width=True, type="primary")

st.markdown('</div>', unsafe_allow_html=True)

# ── Result ────────────────────────────────────────────
if analyze_btn:
    odds_val = odds_input if use_odds else None

    with st.spinner("Menghitung prediksi..."):
        res = predict_full(home_team, away_team, liga, odds_val)

    if not res:
        st.error(f"Tidak bisa menghitung prediksi untuk liga {liga}.")
        st.stop()

    # Tier banner
    is_sniper = res["tier"] == "SNIPER"
    tier_class = "sniper" if is_sniper else "hold"
    tier_icon  = "🎯" if is_sniper else "⏸"
    tier_text  = "SNIPER" if is_sniper else "HOLD"

    st.markdown(f"""
    <div class="result-wrapper">
    <div class="tier-banner {tier_class}">
        <span class="tier-icon">{tier_icon}</span>
        <span class="tier-label {tier_class}">{tier_text}</span>
        <span class="tier-reason">{res['reason']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Match title
    pred_label = {"home_win": f"{home_team} menang",
                  "draw": "Imbang",
                  "away_win": f"{away_team} menang"}.get(res["prediction"], "—")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        # Metric cards
        conf_color = "green" if res["confidence"] >= res["threshold"] else "red"
        elo_diff   = res["elo_diff"]
        lam_total  = round(res["dc"]["lambda_home"] + res["dc"]["lambda_away"], 2)

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Prediksi</div>
                <div class="metric-value" style="font-size:18px">{pred_label}</div>
                <div class="metric-sub">Hasil paling mungkin</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Confidence</div>
                <div class="metric-value {conf_color}">{res['confidence']*100:.1f}%</div>
                <div class="metric-sub">threshold {res['threshold']*100:.0f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Elo Difference</div>
                <div class="metric-value {'green' if elo_diff > 0 else 'red'}">{elo_diff:+d}</div>
                <div class="metric-sub">{home_team[:12]} vs {away_team[:12]}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Lambda Home</div>
                <div class="metric-value amber">{res['dc']['lambda_home']}</div>
                <div class="metric-sub">xG kandang</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Lambda Away</div>
                <div class="metric-value amber">{res['dc']['lambda_away']}</div>
                <div class="metric-sub">xG tamu</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Lambda Total</div>
                <div class="metric-value {'green' if 1.2<=lam_total<=6.5 else 'red'}">{lam_total}</div>
                <div class="metric-sub">valid [1.2–6.5]</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Probability bars
        h_pct = round(res["home_prob"]*100, 1)
        d_pct = round(res["draw_prob"]*100, 1)
        a_pct = round(res["away_prob"]*100, 1)

        st.markdown(f"""
        <div class="prob-section">
            <div class="metric-label" style="margin-bottom:14px">Distribusi Probabilitas</div>
            <div class="prob-row">
                <div class="prob-name">{home_team[:16]}</div>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width:{h_pct}%;background:#4ade80"></div>
                </div>
                <div class="prob-pct">{h_pct}%</div>
            </div>
            <div class="prob-row">
                <div class="prob-name">Imbang</div>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width:{d_pct}%;background:#fbbf24"></div>
                </div>
                <div class="prob-pct">{d_pct}%</div>
            </div>
            <div class="prob-row">
                <div class="prob-name">{away_team[:16]}</div>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width:{a_pct}%;background:#f87171"></div>
                </div>
                <div class="prob-pct">{a_pct}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top predicted scores
        top_scores = res["dc"]["top_scores"][:5]
        pills = "".join([
            f'<div class="score-pill"><span>{s[0][0]}-{s[0][1]}</span> {s[1]*100:.1f}%</div>'
            for s in top_scores
        ])
        st.markdown(f"""
        <div class="h2h-card">
            <div class="h2h-title">Skor Paling Mungkin</div>
            <div class="scores-row">{pills}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        # DC vs Elo breakdown
        dc_h = round(res["dc"]["home_win"]*100, 1)
        dc_d = round(res["dc"]["draw"]*100, 1)
        dc_a = round(res["dc"]["away_win"]*100, 1)
        el_h = round(res["elo"]["home_win"]*100, 1)
        el_d = round(res["elo"]["draw"]*100, 1)
        el_a = round(res["elo"]["away_win"]*100, 1)

        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:12px">
            <div class="metric-label">Dixon-Coles (55%)</div>
            <div style="font-family:'DM Mono',monospace;font-size:13px;color:#888;line-height:2">
                🏠 {dc_h}%&nbsp;&nbsp;🤝 {dc_d}%&nbsp;&nbsp;✈️ {dc_a}%
            </div>
        </div>
        <div class="metric-card" style="margin-bottom:12px">
            <div class="metric-label">Elo Rating (45%)</div>
            <div style="font-family:'DM Mono',monospace;font-size:13px;color:#888;line-height:2">
                🏠 {el_h}%&nbsp;&nbsp;🤝 {el_d}%&nbsp;&nbsp;✈️ {el_a}%
            </div>
            <div class="metric-sub" style="margin-top:6px">
                {home_team[:10]}: {res['elo']['elo_home']} &nbsp;|&nbsp; {away_team[:10]}: {res['elo']['elo_away']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # H2H
        h2h = res.get("h2h")
        if h2h:
            total  = h2h.get("total", 1)
            h_wins = h2h.get("t1_wins", 0)
            draws  = h2h.get("draws", 0)
            a_wins = h2h.get("t2_wins", 0)
            h_w = round(h_wins/total*100)
            d_w = round(draws/total*100)
            a_w = round(a_wins/total*100)
            st.markdown(f"""
            <div class="h2h-card">
                <div class="h2h-title">H2H ({total} laga)</div>
                <div class="h2h-bars">
                    <div style="width:{h_w}%;background:#4ade80"></div>
                    <div style="width:{d_w}%;background:#555"></div>
                    <div style="width:{a_w}%;background:#f87171"></div>
                </div>
                <div class="h2h-label-row">
                    <span style="color:#4ade80">{h_wins}W</span>
                    <span style="color:#666">{draws}D</span>
                    <span style="color:#f87171">{a_wins}W</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="h2h-card">
                <div class="h2h-title">H2H</div>
                <div style="font-size:12px;color:#444">Data H2H tidak tersedia</div>
            </div>
            """, unsafe_allow_html=True)

        # Match date & liga info
        thr_val = res["threshold"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Info Laga</div>
            <div style="font-size:12px;color:#666;line-height:2">
                📅 {match_date.strftime('%d %b %Y')}<br>
                🏆 {liga}<br>
                🎯 Threshold: {thr_val*100:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Kelly
    if res.get("kelly") and res["kelly"]["active"]:
        k = res["kelly"]
        st.markdown(f"""
        <div class="kelly-card">
            <div class="kelly-title">Passive Kelly Calculator (Shadow Mode)</div>
            <div class="kelly-grid">
                <div class="kelly-item">
                    <span class="kelly-val">{k['tier']}</span>
                    <div class="kelly-lbl">Fraction tier</div>
                </div>
                <div class="kelly-item">
                    <span class="kelly-val">{k['ev']:+.3f}</span>
                    <div class="kelly-lbl">Expected Value</div>
                </div>
                <div class="kelly-item">
                    <span class="kelly-val">{k['f_full']*100:.1f}%</span>
                    <div class="kelly-lbl">Full Kelly f*</div>
                </div>
                <div class="kelly-item">
                    <span class="kelly-val">{k['stake']*100:.1f}%</span>
                    <div class="kelly-lbl">Rekomendasi stake</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Filters
    st.markdown('<div style="margin-bottom:8px"><span class="form-label">Filter Pipeline</span></div>', unsafe_allow_html=True)
    filter_html = '<div class="filter-grid">'
    for fname, fpass, fmsg in res["filters"]:
        cls  = "pass" if fpass else "fail"
        icon = "pass" if fpass else "fail"
        filter_html += f"""
        <div class="filter-badge {cls}">
            <div class="filter-dot {icon}"></div>
            <div>
                <div class="filter-name">{fname}</div>
                <div class="filter-msg">{fmsg[:38]}</div>
            </div>
        </div>"""
    filter_html += '</div>'
    st.markdown(filter_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close result-wrapper

# ── Footer ─────────────────────────────────────────────
st.markdown("""
<div class="divider"></div>
<div class="sniper-footer">
    Football Sniper V20.3.6 &nbsp;·&nbsp;
    Dixon-Coles + Elo Walk-Forward &nbsp;·&nbsp;
    81.4% WF Accuracy &nbsp;·&nbsp;
    95% CI [75.3%, 86.1%] &nbsp;·&nbsp;
    p = 4.27×10⁻¹⁹
</div>
""", unsafe_allow_html=True)
