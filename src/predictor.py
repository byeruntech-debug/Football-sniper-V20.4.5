#!/usr/bin/env python3
"""
Football Sniper Prediction System
Version : V20.5.2-V3Extended
Engine  : Dixon-Coles V3 + Elo Walk-Forward
Accuracy: 81.4% (warm walk-forward, no data leakage)
Yield   : +1.6% vs B365 closing odds (194 picks)

QUICK START:
    from predictor import load_model, predict_v20
    load_model('/content/drive/MyDrive/Football_Project')
    predict_v20('Inter', 'Juventus', 'Serie_A')

VALID LEAGUES:
    EPL | La_Liga | Bundesliga | Serie_A |
    Eredivisie | Liga_Portugal | Super_Lig
"""

import json, math, os
import numpy as np
from scipy.stats import poisson

# ── Global state (diisi oleh load_model) ─────────────
DC = ELO = H2H = THRESH = DRAW_B = GK = INJ_SYS = DRAW_W = META = None
_MODEL_LOADED = False


def load_model(base_path: str) -> dict:
    """
    Load model V20.3 dari model_v20_complete.json.

    Args:
        base_path: path ke folder Football_Project
                   e.g. '/content/drive/MyDrive/Football_Project'
    Returns:
        dict meta info model
    """
    global DC, ELO, H2H, THRESH, DRAW_B, GK, INJ_SYS, DRAW_W, META, _MODEL_LOADED

    path = os.path.join(base_path, 'outputs', 'model_v20_complete.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model tidak ditemukan: {path}")

    with open(path, 'r') as f:
        v20 = json.load(f)

    DC       = v20['dc_params']
    ELO      = v20['elo']
    H2H      = v20['h2h_stats']
    THRESH   = v20['sniper_threshold']
    DRAW_B   = v20['draw_boost']
    GK       = v20['giant_killers']
    INJ_SYS  = v20['injury_system']
    DRAW_W   = v20.get('draw_warning', {})
    META     = v20['meta']
    _MODEL_LOADED = True

    print(f"✅ Model loaded: {META['version']}")
    print(f"   Leagues : {v20['active_leagues']}")
    print(f"   Teams   : {META['total_teams']}")
    return META


def _check_loaded():
    if not _MODEL_LOADED:
        raise RuntimeError("Model belum diload. Panggil load_model() dulu.")


# ════════════════════════════════════════════════════════
#  DIXON-COLES ENGINE
# ════════════════════════════════════════════════════════

def _tau(lh: float, la: float, gh: int, ga: int, rho: float) -> float:
    """Low-score correction (Dixon & Coles 1997)."""
    if   gh == 0 and ga == 0: return 1 - lh * la * rho
    elif gh == 1 and ga == 0: return 1 + la * rho
    elif gh == 0 and ga == 1: return 1 + lh * rho
    elif gh == 1 and ga == 1: return 1 - rho
    return 1.0


def dc_predict(home: str, away: str, liga: str, max_goals: int = 8,
               home_formation: str = None, away_formation: str = None,
               home_rest_days: float = None, away_rest_days: float = None) -> dict | None:
    """
    Hitung probabilitas H/D/A dengan Dixon-Coles Poisson model.

    Returns:
        dict: home_win, draw, away_win, lambda_home, lambda_away, top_scores
        None: jika liga tidak dikenali
    """
    _check_loaded()
    p = DC.get(liga)
    if not p:
        return None

    atk, dfn, hfa, rho = p['attack'], p['defense'], p['hfa'], p['rho']

    if home not in atk or away not in atk:
        lam_h, lam_a = math.exp(hfa), 1.0
    else:
        lam_h = math.exp(atk[home] + dfn[away] + hfa)
        lam_a = math.exp(atk[away] + dfn[home])

    M = np.zeros((max_goals + 1, max_goals + 1))
    for gh in range(max_goals + 1):
        for ga in range(max_goals + 1):
            M[gh, ga] = (
                _tau(lam_h, lam_a, gh, ga, rho)
                * poisson.pmf(gh, lam_h)
                * poisson.pmf(ga, lam_a)
            )
    M /= M.sum()

    hw = float(np.sum(np.tril(M, -1)))
    dr = float(np.sum(np.diag(M)))
    aw = float(np.sum(np.triu(M,  1)))

    flat      = np.argsort(M.ravel())[::-1][:5]
    top_scores = [
        ((int(i // (max_goals + 1)), int(i % (max_goals + 1))),
         float(M.ravel()[i]))
        for i in flat
    ]

    return {
        'home_win'    : round(hw, 4),
        'draw'        : round(dr, 4),
        'away_win'    : round(aw, 4),
        'lambda_home' : round(lam_h, 3),
        'lambda_away' : round(lam_a, 3),
        'top_scores'  : top_scores,
    }


# ════════════════════════════════════════════════════════
#  ELO ENGINE
# ════════════════════════════════════════════════════════

def elo_predict(home: str, away: str, liga: str, hfa: int = 50) -> dict:
    """
    Hitung probabilitas dari Elo rating.
    Home advantage default +50 Elo points.
    """
    _check_loaded()
    tbl = ELO.get(liga, {})
    rh  = tbl.get(home, 1500) + hfa
    ra  = tbl.get(away, 1500)

    eh   = 1 / (1 + 10 ** ((ra - rh) / 400))
    ea   = 1 - eh
    diff = abs(eh - ea)
    dr   = max(0.18, 0.35 - diff * 0.5)
    hw   = eh * (1 - dr)
    aw   = ea * (1 - dr)
    t    = hw + dr + aw

    return {
        'home_win' : round(hw / t, 4),
        'draw'     : round(dr / t, 4),
        'away_win' : round(aw / t, 4),
        'elo_home' : tbl.get(home, 1500),
        'elo_away' : tbl.get(away, 1500),
        'elo_diff' : int(tbl.get(home, 1500) - tbl.get(away, 1500)),
    }


# ════════════════════════════════════════════════════════
#  FILTERS
# ════════════════════════════════════════════════════════

def check_giant_killer(home: str, away: str, liga: str) -> tuple[bool, str | None]:
    """
    Deteksi potensi giant killer.
    Trigger: away jauh lebih kuat (Elo diff > 100) + home ada di daftar GK.
    """
    _check_loaded()
    tbl  = ELO.get(liga, {})
    diff = tbl.get(away, 1500) - tbl.get(home, 1500)
    if diff < 100:
        return False, None
    score = GK.get(home, 0)
    if score >= 2.0:
        return True, f"⚠️  GIANT KILLER: {home} (score={score})"
    return False, None


def injury_warning(
    home_team: str,
    away_team: str,
    absent_h: list | None = None,
    absent_a: list | None = None,
) -> dict:
    """
    V20.6 Injury Warning System — WARNING FLAG ONLY.
    Upgrade: tambah injury_type severity lookup dari 143K records Transfermarkt.

    absent_h / absent_a format:
        [{'name': 'Salah', 'position': 'Winger', 'injury_type': 'Muscle injury',
          'days_out': 14}]

    Valid positions:
        Goalkeeper | Centre-Back | Full-Back | Defensive Midfielder |
        Midfielder | Attacking Midfielder | Winger | Forward |
        Striker | Defender

    Severity levels (dari data empiris):
        CRITICAL  : >= 30 days (ACL, fracture, dll)
        MAJOR     : 15-29 days (muscle tear, dll)
        MODERATE  : 7-14 days (sprain, dll)
        MINOR     : < 7 days
    """
    _check_loaded()
    pos_w      = INJ_SYS['position_weights']
    inj_lookup = INJ_SYS.get('injury_lookup', {})
    warnings   = []

    for team, absents in [(home_team, absent_h or []), (away_team, absent_a or [])]:
        for player in absents:
            pos      = player.get('position', 'Midfielder')
            inj_type = player.get('injury_type', '')
            wa  = pos_w.get(pos, {}).get('attack',  0.05)
            wd  = pos_w.get(pos, {}).get('defense', 0.05)

            # Lookup severity dari database
            inj_info = inj_lookup.get(inj_type, {})
            severity = inj_info.get('severity', None)
            avg_days = inj_info.get('avg_days', player.get('days_out', 0))

            # Severity override berdasarkan days_out
            days_out = player.get('days_out', avg_days)
            try: days_out = float(str(days_out).replace(' days','').strip())
            except: days_out = avg_days

            if severity is None:
                if   days_out >= 30: severity = 'CRITICAL'
                elif days_out >= 15: severity = 'MAJOR'
                elif days_out >= 7:  severity = 'MODERATE'
                else:                severity = 'MINOR'

            if max(wa, wd) >= 0.08 or severity in ('CRITICAL','MAJOR'):
                impact = severity if severity else (
                    'HIGH'   if max(wa,wd)>=0.12 else 'MEDIUM')
                warnings.append({
                    'team'      : team,
                    'name'      : player.get('name', '?'),
                    'position'  : pos,
                    'injury_type': inj_type or '?',
                    'impact'    : impact,
                    'avg_days'  : avg_days,
                    'days_out'  : days_out,
                    'severity'  : severity,
                })

    return {
        'has_warning': len(warnings) > 0,
        'home': [w for w in warnings if w['team'] == home_team],
        'away': [w for w in warnings if w['team'] == away_team],
        'critical_count': sum(1 for w in warnings if w['severity']=='CRITICAL'),
        'major_count'   : sum(1 for w in warnings if w['severity']=='MAJOR'),
    }


def get_h2h(home: str, away: str) -> dict | None:
    """Lookup data H2H dari database 1,749 pasang."""
    _check_loaded()
    return (
        H2H.get(f"(\'{home}\', \'{away}\')")
        or H2H.get(f"(\'{away}\', \'{home}\')")
    )


# ════════════════════════════════════════════════════════
#  MAIN PREDICTION FUNCTION
# ════════════════════════════════════════════════════════

def predict_v20(
    home_team   : str,
    away_team   : str,
    liga        : str,
    match_date  : str | None  = None,
    absent_h    : list | None = None,
    absent_a    : list | None = None,
    verbose     : bool        = True,
) -> dict | None:
    """
    Prediksi pertandingan V20.3.

    Pipeline:
        1. Dixon-Coles (55%) — Poisson MLE + tau correction
        2. Elo Rating   (45%) — K=32, HFA +50 points
        3. Draw Boost         — per-liga multiplier
        4. Sniper Filter      — confidence >= threshold
        5. Giant Killer check — home underdog trap detection
        6. Draw Warning       — liga-specific draw threshold
        7. Injury Warning     — V20.5 flag only (no lambda change)

    Args:
        home_team  : nama tim kandang (sesuai nama di JSON)
        away_team  : nama tim tamu
        liga       : EPL | La_Liga | Bundesliga | Serie_A |
                     Eredivisie | Liga_Portugal | Super_Lig
        match_date : string "YYYY-MM-DD" (opsional)
        absent_h   : list cedera tim kandang
        absent_a   : list cedera tim tamu
        verbose    : print output ke konsol

    Returns:
        dict hasil prediksi, atau None jika liga tidak valid
    """
    _check_loaded()

    # ── Step 1: Dixon-Coles ──────────────────────────
    dc = dc_predict(home_team, away_team, liga)
    if not dc:
        print(f"❌ Liga '{liga}' tidak dikenali.")
        print(f"   Valid: EPL | La_Liga | Bundesliga | Serie_A | "
              f"Eredivisie | Liga_Portugal | Super_Lig")
        return None

    # ── Step 2: Elo ──────────────────────────────────
    el = elo_predict(home_team, away_team, liga)

    # ── Step 3: Ensemble DC 55% + Elo 45% ───────────
    h = 0.55 * dc['home_win'] + 0.45 * el['home_win']
    d = 0.55 * dc['draw']     + 0.45 * el['draw']
    a = 0.55 * dc['away_win'] + 0.45 * el['away_win']

    # ── Step 4: Draw Boost ───────────────────────────
    boost = DRAW_B.get(liga, 1.431)
    d    *= boost
    t     = h + d + a
    h /= t; d /= t; a /= t

    # ── Step 5: Sniper Filter ────────────────────────
    conf  = max(h, d, a)
    pred  = max({'home_win': h, 'draw': d, 'away_win': a}, key=lambda k: {'home_win': h, 'draw': d, 'away_win': a}[k])
    thr   = THRESH.get(liga, 0.65)
    tier  = 'SNIPER' if conf >= thr else 'HOLD'

    # ── Step 6: Draw Warning ─────────────────────────
    dw_thr = DRAW_W.get(liga, 0)
    dw_msg = (f"Draw danger: {d:.3f} > threshold {dw_thr}"
              if dw_thr and d > dw_thr else None)
    if dw_msg:
        tier = 'HOLD'

    # ── Step 7: Giant Killer ─────────────────────────
    gk_flag, gk_msg = check_giant_killer(home_team, away_team, liga)
    if gk_flag and tier == 'SNIPER':
        tier = 'HOLD'

    # ── Step 8: Injury Warning ───────────────────────
    inj = injury_warning(home_team, away_team, absent_h, absent_a)

    # ── Step 9: H2H ──────────────────────────────────
    h2h = get_h2h(home_team, away_team)

    # ── Output ───────────────────────────────────────
    if verbose:
        t_emoji = {'SNIPER': '🎯', 'HOLD': '⏸️ '}
        print(f"\n{'═'*56}")
        print(f"  ⚽  {home_team}  vs  {away_team}")
        print(f"  📅  {match_date or 'TBD'}  │  🏆  {liga}")
        print(f"{'─'*56}")
        print(f"  [DC]   H={dc['home_win']*100:.1f}%  D={dc['draw']*100:.1f}%  "
              f"A={dc['away_win']*100:.1f}%   λ={dc['lambda_home']}/{dc['lambda_away']}")
        print(f"  [Elo]  H={el['home_win']*100:.1f}%  D={el['draw']*100:.1f}%  "
              f"A={el['away_win']*100:.1f}%   diff={el['elo_diff']:+d}")
        print(f"{'─'*56}")
        print(f"  FINAL  🏠 {h*100:.1f}%  🤝 {d*100:.1f}%  ✈️   {a*100:.1f}%")
        print(f"  Pred   : {pred.upper().replace('_',' ')}  │  "
              f"Conf: {conf*100:.1f}%  (thr: {thr*100:.0f}%)")
        print(f"  {t_emoji.get(tier, '?' )} {tier}")
        print(f"  🏆 Top : " + "  ".join(
            [f"{s[0][0]}-{s[0][1]}({s[1]*100:.1f}%)" for s in dc['top_scores'][:3]]))
        if h2h:
            print(f"  📋 H2H ({h2h['total']} laga): "
                  f"🏠{h2h['t1_wins']}W 🤝{h2h['draws']}D ✈️{h2h['t2_wins']}W")
        if dw_msg:  print(f"  ⚠️   {dw_msg}")
        if gk_msg:  print(f"  {gk_msg}")
        if inj['has_warning']:
            for w in inj['home'] + inj['away']:
                print(f"  ⚕️   {w['team']}: {w['name']} ({w['position']}) — {w['impact']}")
        print(f"{'═'*56}")

    return {
        'prediction'     : pred,
        'home_prob'      : round(h,    4),
        'draw_prob'      : round(d,    4),
        'away_prob'      : round(a,    4),
        'confidence'     : round(conf, 4),
        'tier'           : tier,
        'threshold'      : thr,
        'liga'           : liga,
        'match_date'     : match_date,
        'lambda_home'    : dc['lambda_home'],
        'lambda_away'    : dc['lambda_away'],
        'elo_diff'       : el['elo_diff'],
        'top_scores'     : dc['top_scores'],
        'giant_killer'   : gk_flag,
        'draw_warning'   : dw_msg,
        'injury_warning' : inj,
        'h2h'            : h2h,
    }


# ════════════════════════════════════════════════════════
#  UTILITY
# ════════════════════════════════════════════════════════

def show_teams(liga: str) -> None:
    """Tampilkan semua tim + Elo rating untuk satu liga."""
    _check_loaded()
    p = DC.get(liga)
    if not p:
        print(f"Liga '{liga}' tidak ada.")
        return
    teams = sorted(p['attack'].keys())
    print(f"\n📋 {liga} — {len(teams)} tim:")
    for i, t in enumerate(teams, 1):
        elo = ELO.get(liga, {}).get(t, 1500)
        print(f"  {i:2d}. {t:<28} Elo: {elo:.0f}")


def show_thresholds() -> None:
    """Tampilkan threshold Sniper per liga."""
    _check_loaded()
    print("\n📊 Sniper Thresholds V20.3:")
    active = META.get('final_spec', {}).get('active_leagues', [])
    for liga, thr in THRESH.items():
        tag = '✅ ACTIVE' if liga in active else '   watch'
        print(f"  {liga:<22}: {thr:.2f}  {tag}")



def calculate_kelly(confidence: float, odds,
                    min_ev: float = 0.05,
                    min_conf: float = 0.60,
                    max_stake: float = 0.10) -> dict:
    """
    Passive Kelly Calculator — shadow mode, dynamic fraction.

    Fraction otomatis berdasarkan confidence:
      conf >= 0.70  → Quarter-Kelly  (0.25)
      conf >= 0.65  → Fifth-Kelly    (0.20)
      conf >= 0.60  → Eighth-Kelly   (0.125)
      conf <  0.60  → SKIP

    Safety rules:
      1. EV minimum +0.05
      2. Confidence minimum 0.60
      3. Hard cap 10% bankroll
    """
    SKIP = {"stake":0.0,"ev":0.0,"f_full":0.0,"fraction":0,"active":False}

    if odds is None or odds <= 1.0:
        return {**SKIP, "status":"NO_ODDS"}

    ev = round((confidence * odds) - 1, 4)

    if ev < min_ev:
        return {**SKIP, "ev":ev, "status":f"EV {ev:+.3f} < min {min_ev}"}

    if confidence < min_conf:
        return {**SKIP, "ev":ev, "status":f"Conf {confidence:.2f} < min {min_conf}"}

    # Dynamic fraction — semakin yakin, semakin berani
    if confidence >= 0.70:
        fraction = 0.25
        tier     = "Quarter-Kelly"
    elif confidence >= 0.65:
        fraction = 0.20
        tier     = "Fifth-Kelly"
    else:
        fraction = 0.125
        tier     = "Eighth-Kelly"

    b      = odds - 1.0
    f_full = round((confidence * (b + 1) - 1) / b, 4)

    if f_full <= 0:
        return {**SKIP, "ev":ev, "status":f"Kelly negatif f*={f_full:.4f}"}

    stake = round(min(f_full * fraction, max_stake), 4)

    return {
        "stake"      : stake,
        "f_full"     : f_full,
        "ev"         : ev,
        "fraction"   : fraction,
        "tier"       : tier,
        "active"     : True,
        "status"     : "ACTIVE",
        "recommendation": f"Bet {stake*100:.1f}% bankroll ({tier}, cap {max_stake*100:.0f}%)",
    }
