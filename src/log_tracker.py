#!/usr/bin/env python3
"""
Log Tracker V20.3
Mencatat, memantau, dan menganalisis performa prediksi live.

Fitur:
    - Catat prediksi sebelum pertandingan
    - Update hasil aktual + odds penutup
    - Hitung Brier Score, Yield vs odds
    - Handle postponed (tidak merusak statistik)
    - Export CSV untuk analisis lanjutan
    - Grafik kalibrasi confidence vs actual win rate

CARA PAKAI:
    from log_tracker import log_pick, update_result, show_stats, export_csv

    # Sebelum pertandingan
    log_pick("Bayern Munich", "Dortmund", "Bundesliga",
             "2026-03-22", odds=1.55)

    # Setelah pertandingan
    update_result("Bayern Munich", "Dortmund", "H",
                  "2026-03-22", score="2-1", closing_odds=1.52)

    # Pantau performa
    show_stats()
    export_csv()
"""

import json, os
import pandas as pd
import numpy as np
from datetime import datetime


# ── Storage ───────────────────────────────────────────
_BASE    = None
_LOG_PATH = None


def init_tracker(base_path: str) -> None:
    """Inisialisasi path storage log tracker."""
    global _BASE, _LOG_PATH
    _BASE     = base_path
    _LOG_PATH = os.path.join(base_path, "outputs", "live_predictions_log.json")


def _load() -> dict:
    if _LOG_PATH and os.path.exists(_LOG_PATH):
        with open(_LOG_PATH, "r") as f:
            return json.load(f)
    return {"picks": [], "meta": {"created": str(datetime.now()), "version": "V20.3"}}


def _save(data: dict) -> None:
    if not _LOG_PATH:
        raise RuntimeError("Panggil init_tracker(base_path) dulu.")
    with open(_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ════════════════════════════════════════════════════════
#  BRIER SCORE
# ════════════════════════════════════════════════════════

def _brier_score(home_prob: float, draw_prob: float, away_prob: float,
                 actual: str) -> float:
    """
    Hitung Brier Score untuk satu prediksi.
    Brier Score = mean((prob_i - actual_i)^2) untuk i in {H, D, A}
    Range: 0.0 (sempurna) → 1.0 (terburuk) → 0.667 (random)
    """
    outcome = {"home_win": [1,0,0], "draw": [0,1,0], "away_win": [0,0,1]}
    probs   = [home_prob, draw_prob, away_prob]
    actual_vec = outcome.get(actual, [0,0,0])
    return round(sum((p - a)**2 for p, a in zip(probs, actual_vec)) / 3, 4)


# ════════════════════════════════════════════════════════
#  LOG PICK
# ════════════════════════════════════════════════════════

def log_pick(
    home       : str,
    away       : str,
    liga       : str,
    match_date : str,
    odds       : float = None,
    notes      : str   = "",
    absent_h   : list  = None,
    absent_a   : list  = None,
) -> dict | None:
    """
    Catat prediksi SEBELUM pertandingan dimainkan.

    Args:
        home       : nama tim kandang
        away       : nama tim tamu
        liga       : nama liga
        match_date : "YYYY-MM-DD"
        odds       : odds yang tersedia saat pick (opsional, untuk yield)
        notes      : catatan konteks (cedera, motivasi, dll)

    Returns:
        dict entry yang disimpan
    """
    from predictor import predict_v20
    from sniper_filter import sniper_filter

    res = predict_v20(home, away, liga, match_date,
                      absent_h=absent_h, absent_a=absent_a, verbose=False)
    if not res:
        return None

    res["home_team"] = home
    res["away_team"] = away
    sf = sniper_filter(res, verbose=False)

    entry_id = f"{match_date}_{home}_{away}".replace(" ", "_")
    data     = _load()

    # Cek duplikat
    if entry_id in [p["id"] for p in data["picks"]]:
        print(f"⚠️  Pick {entry_id} sudah ada di log.")
        return None

    entry = {
        # Identitas
        "id"          : entry_id,
        "date"        : match_date,
        "liga"        : liga,
        "home"        : home,
        "away"        : away,

        # Prediksi
        "prediction"  : res["prediction"],
        "home_prob"   : res["home_prob"],
        "draw_prob"   : res["draw_prob"],
        "away_prob"   : res["away_prob"],
        "confidence"  : res["confidence"],
        "tier"        : sf["tier"],
        "filter_reason": sf["reason"],

        # Model detail
        "lambda_home" : res["lambda_home"],
        "lambda_away" : res["lambda_away"],
        "elo_diff"    : res["elo_diff"],
        "top_score"   : f"{res['top_scores'][0][0][0]}-{res['top_scores'][0][0][1]}",

        # Odds & yield (diisi saat log + update)
        "odds_open"   : odds,
        "odds_close"  : None,

        # Hasil aktual (diisi setelah pertandingan)
        "actual"      : None,
        "score"       : None,
        "correct"     : None,
        "brier_score" : None,
        "yield_unit"  : None,
        "status"      : "pending",   # pending | correct | wrong | postponed

        # Meta
        "notes"       : notes,
        "logged_at"   : str(datetime.now()),
        "updated_at"  : None,
    }

    data["picks"].append(entry)
    _save(data)

    # Print summary
    t_emoji = {"SNIPER": "🎯", "HOLD": "⏸️ "}
    print(f"\n{'='*54}")
    print(f"  📝 PICK DICATAT")
    print(f"  ⚽ {home} vs {away} | {match_date}")
    print(f"  🏆 {liga}")
    print(f"  🏠 {res['home_prob']*100:.1f}%  "
          f"🤝 {res['draw_prob']*100:.1f}%  "
          f"✈️  {res['away_prob']*100:.1f}%")
    print(f"  Pred: {res['prediction'].upper().replace('_',' ')} | "
          f"Conf: {res['confidence']*100:.1f}%")
    print(f"  {t_emoji[sf['tier']]} Tier: {sf['tier']}")
    if odds:
        print(f"  💰 Odds: {odds}")
    print(f"  🆔 ID: {entry_id}")
    print(f"{'='*54}")
    return entry


# ════════════════════════════════════════════════════════
#  UPDATE RESULT
# ════════════════════════════════════════════════════════

def update_result(
    home         : str,
    away         : str,
    result_ftr   : str,
    match_date   : str,
    score        : str   = "?-?",
    closing_odds : float = None,
) -> None:
    """
    Update hasil aktual setelah pertandingan selesai.

    Args:
        result_ftr   : "H" (home), "D" (draw), "A" (away), "P" (postponed)
        closing_odds : odds penutup (lebih akurat untuk yield)
    """
    assert result_ftr in ["H","D","A","P"],         "result_ftr harus H, D, A, atau P (postponed)"

    actual_map = {"H":"home_win","D":"draw","A":"away_win"}
    data       = _load()

    for p in data["picks"]:
        if (p["home"] == home and p["away"] == away
                and p["date"] == match_date and p["actual"] is None):

            if result_ftr == "P":
                # Postponed — tidak dihitung dalam statistik
                p["status"]     = "postponed"
                p["actual"]     = "postponed"
                p["updated_at"] = str(datetime.now())
                _save(data)
                print(f"⏸️  POSTPONED: {home} vs {away} — tidak dihitung dalam statistik")
                return

            actual       = actual_map[result_ftr]
            correct      = (p["prediction"] == actual)
            brier        = _brier_score(p["home_prob"], p["draw_prob"],
                                        p["away_prob"], actual)

            # Yield: (odds * stake - stake) if correct, else -stake
            # Stake = 1 unit flat betting
            odds_used = closing_odds or p["odds_open"]
            if odds_used:
                y = round((odds_used - 1) if correct else -1.0, 4)
            else:
                y = None

            p["actual"]       = actual
            p["score"]        = score
            p["correct"]      = correct
            p["brier_score"]  = brier
            p["yield_unit"]   = y
            p["odds_close"]   = closing_odds
            p["status"]       = "correct" if correct else "wrong"
            p["updated_at"]   = str(datetime.now())

            _save(data)

            icon = "✅" if correct else "❌"
            print(f"\n{icon} UPDATE: {home} vs {away}")
            print(f"   Pred    : {p['prediction'].upper()} | "
                  f"Aktual: {actual.upper()} | Skor: {score}")
            print(f"   Brier   : {brier:.4f} "
                  f"(< 0.25 = baik | < 0.20 = sangat baik)")
            if y is not None:
                print(f"   Yield   : {y:+.2f} unit")
            return

    print(f"⚠️  Pick tidak ditemukan: {home} vs {away} ({match_date})")


# ════════════════════════════════════════════════════════
#  SHOW STATS
# ════════════════════════════════════════════════════════

def show_stats(liga: str = None) -> pd.DataFrame | None:
    """
    Tampilkan statistik performa lengkap.

    Args:
        liga: filter per liga (None = semua liga)
    """
    data  = _load()
    picks = [p for p in data["picks"]
             if p["status"] in ("correct","wrong")]

    if liga:
        picks = [p for p in picks if p["liga"] == liga]

    pending = sum(1 for p in data["picks"] if p["status"] == "pending")
    postponed = sum(1 for p in data["picks"] if p["status"] == "postponed")

    if not picks:
        print(f"⏳ Belum ada hasil aktual.")
        print(f"   Pending    : {pending} picks")
        print(f"   Postponed  : {postponed} picks")
        return None

    df      = pd.DataFrame(picks)
    sniper  = df[df["tier"] == "SNIPER"]
    hold    = df[df["tier"] == "HOLD"]

    acc_all = df["correct"].mean() * 100
    acc_snp = sniper["correct"].mean() * 100 if len(sniper) else 0

    # Brier Score
    brier_all = df["brier_score"].mean() if "brier_score" in df else None
    brier_snp = sniper["brier_score"].mean() if len(sniper) and "brier_score" in sniper else None

    # Yield
    has_odds   = df["yield_unit"].notna().any()
    yield_all  = df["yield_unit"].sum() if has_odds else None
    yield_snp  = sniper["yield_unit"].sum() if has_odds and len(sniper) else None
    yield_pct  = (yield_snp / len(sniper) * 100) if yield_snp is not None and len(sniper) else None

    print(f"\n{'═'*52}")
    print(f"  📊 LIVE TRACKER STATS"
          + (f" — {liga}" if liga else ""))
    print(f"{'─'*52}")
    print(f"  Selesai    : {len(df)} picks")
    print(f"  Pending    : {pending} picks")
    print(f"  Postponed  : {postponed} picks (tidak dihitung)")
    print(f"{'─'*52}")
    print(f"  AKURASI")
    print(f"  Semua      : {acc_all:.1f}%  ({df['correct'].sum()}/{len(df)})")
    print(f"  🎯 Sniper  : {acc_snp:.1f}%  ({int(sniper['correct'].sum()) if len(sniper) else 0}/{len(sniper)})")
    if len(hold):
        acc_h = hold["correct"].mean() * 100
        print(f"  ⏸️  Hold    : {acc_h:.1f}%  ({int(hold['correct'].sum())}/{len(hold)})")

    if brier_all is not None:
        print(f"{'─'*52}")
        print(f"  BRIER SCORE (lebih rendah = lebih baik)")
        print(f"  Semua      : {brier_all:.4f}")
        if brier_snp is not None:
            print(f"  🎯 Sniper  : {brier_snp:.4f}  "
                  f"({'✅ baik' if brier_snp < 0.25 else '⚠️ perlu perbaikan'})")
        print(f"  Referensi  : random=0.667 | baik<0.25 | sangat baik<0.20")

    if yield_all is not None:
        print(f"{'─'*52}")
        print(f"  YIELD (flat betting 1 unit)")
        print(f"  Semua      : {yield_all:+.2f} unit")
        if yield_snp is not None:
            print(f"  🎯 Sniper  : {yield_snp:+.2f} unit "
                  f"({yield_pct:+.1f}% per pick)")

    # Recent form
    if len(sniper) >= 5:
        recent = sniper.tail(10)
        form   = "".join(["✅" if r else "❌" for r in recent["correct"].values])
        recent_acc = recent["correct"].mean() * 100
        print(f"{'─'*52}")
        print(f"  RECENT FORM (last {len(recent)} Sniper picks)")
        print(f"  {form}")
        print(f"  Akurasi: {recent_acc:.1f}%")

    # Breakdown per liga
    if not liga and len(df) > 0:
        print(f"{'─'*52}")
        print(f"  PER LIGA:")
        for lg in df["liga"].unique():
            sub = df[df["liga"] == lg]
            snp = sub[sub["tier"] == "SNIPER"]
            acc = sub["correct"].mean() * 100
            print(f"  {lg:<18}: {acc:.1f}%  ({len(sub)} picks"
                  + (f", {len(snp)} sniper" if len(snp) else "") + ")")

    print(f"{'─'*52}")
    print(f"  Benchmark: 55% industry | 81.4% V20.3 WF target")
    status = "✅ DI ATAS TARGET" if acc_snp >= 75 else (
             "📈 PROGRESSING"    if acc_snp >= 60 else "⚠️  DI BAWAH TARGET")
    print(f"  Status   : {status}")
    print(f"{'═'*52}")
    return df


# ════════════════════════════════════════════════════════
#  EXPORT & UTILITY
# ════════════════════════════════════════════════════════

def export_csv(filename: str = "live_picks_export.csv") -> str:
    """Export semua picks ke CSV untuk analisis lanjutan."""
    data  = _load()
    picks = [p for p in data["picks"] if p["status"] != "postponed"]
    if not picks:
        print("⚠️  Belum ada data untuk diekspor.")
        return ""
    out_path = os.path.join(_BASE, "outputs", filename)
    pd.DataFrame(picks).to_csv(out_path, index=False)
    print(f"✅ Exported {len(picks)} picks → {out_path}")
    return out_path


def show_log(n: int = 20, tier: str = None) -> None:
    """Tampilkan n pick terakhir dari log."""
    data  = _load()
    picks = data["picks"]
    if tier:
        picks = [p for p in picks if p.get("tier") == tier]
    picks = picks[-n:]

    print(f"\n{'═'*70}")
    print(f"  📋 LOG PICKS (last {len(picks)})")
    print(f"{'─'*70}")
    for p in picks:
        s_map  = {"correct":"✅","wrong":"❌","pending":"⏳","postponed":"⏸️ "}
        t_map  = {"SNIPER":"🎯","HOLD":"⏸️ "}
        status = s_map.get(p.get("status","pending"), "❓")
        tier_e = t_map.get(p.get("tier","HOLD"), "")
        actual = p.get("actual") or "pending"
        brier  = f"B={p['brier_score']:.3f}" if p.get("brier_score") else ""
        print(f"  {status} {p['date']} | {p['home'][:14]:<14} vs "
              f"{p['away'][:14]:<14} | "
              f"Pred:{p['prediction'][:9]:<9} Act:{actual[:9]:<9} | "
              f"{tier_e}{p.get('tier','?')} {brier}")
    print(f"{'═'*70}")


def mark_postponed(home: str, away: str, match_date: str) -> None:
    """Tandai laga sebagai postponed — tidak dihitung dalam statistik."""
    update_result(home, away, "P", match_date)


def show_shadow_bankroll(start_balance: float = 100.0) -> None:
    """
    Bandingkan pertumbuhan Flat Betting vs Quarter-Kelly secara shadow.
    Hanya picks dengan odds tercatat yang dihitung.
    """
    data  = _load()
    picks = [p for p in data["picks"]
             if p["status"] in ("correct","wrong")
             and p.get("odds_open") or p.get("odds_close")]

    if not picks:
        print("Belum ada picks dengan odds tercatat.")
        return

    flat_bal   = start_balance
    kelly_bal  = start_balance
    flat_hist  = [start_balance]
    kelly_hist = [start_balance]

    print(f"\n{'═'*52}")
    print(f"  💰 SHADOW BANKROLL TRACKER")
    print(f"  Start balance: {start_balance} unit")
    print(f"{'─'*52}")
    print(f"  {'Date':<12} {'Match':<24} {'Flat':>8} {'Kelly':>8}")
    print(f"{'─'*52}")

    for p in picks:
        odds    = p.get("odds_close") or p.get("odds_open")
        correct = p["correct"]
        conf    = p["confidence"]

        # Flat: 1 unit per pick
        flat_pnl  = (odds - 1) if correct else -1.0
        flat_bal  = round(flat_bal + flat_pnl, 4)
        flat_hist.append(flat_bal)

        # Kelly shadow
        from predictor import calculate_kelly
        k = calculate_kelly(conf, odds)
        if k["active"]:
            kelly_units = round(kelly_bal * k["stake"], 4)
            kelly_pnl   = round(kelly_units * (odds-1) if correct
                                else -kelly_units, 4)
        else:
            kelly_pnl = 0.0
        kelly_bal  = round(kelly_bal + kelly_pnl, 4)
        kelly_hist.append(kelly_bal)

        match = f"{p['home'][:10]} v {p['away'][:10]}"
        fp    = f"{flat_pnl:+.2f}" if flat_pnl != 0 else "—"
        kp    = f"{kelly_pnl:+.2f}" if kelly_pnl != 0 else "—"
        print(f"  {p['date']:<12} {match:<24} {fp:>8} {kp:>8}")

    print(f"{'─'*52}")
    flat_ret  = round((flat_bal  - start_balance) / start_balance * 100, 2)
    kelly_ret = round((kelly_bal - start_balance) / start_balance * 100, 2)
    print(f"  {'FINAL':<36} {flat_bal:>8.2f} {kelly_bal:>8.2f}")
    print(f"  {'Return':<36} {flat_ret:>+7.1f}% {kelly_ret:>+7.1f}%")
    print(f"{'─'*52}")

    # Drawdown calculation
    def max_dd(hist):
        peak = hist[0]
        dd   = 0.0
        for v in hist:
            peak = max(peak, v)
            dd   = min(dd, v - peak)
        return round(dd, 4)

    flat_dd  = max_dd(flat_hist)
    kelly_dd = max_dd(kelly_hist)
    print(f"  Max Drawdown (Flat) : {flat_dd:+.2f} unit")
    print(f"  Max Drawdown (Kelly): {kelly_dd:+.2f} unit")
    print(f"{'═'*52}")
    print(f"\n  ⚠️  Kelly masih SHADOW MODE — data {len(picks)} picks")
    print(f"  Aktifkan Kelly setelah N > 100 picks + kalibrasi odds")
