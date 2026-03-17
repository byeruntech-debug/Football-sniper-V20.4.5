#!/usr/bin/env python3
"""Sniper Filter V20.3 — Dynamic Binding Fix"""

import predictor as _p

LAMBDA_MAX = 6.5
LAMBDA_MIN = 1.2
ELO_GAP_MIN = 30


def filter_threshold(confidence, liga):
    thr = _p.THRESH.get(liga, 0.65)
    if confidence >= thr:
        return True, f"Conf {confidence:.3f} >= thr {thr:.2f}"
    return False, f"Conf {confidence:.3f} < thr {thr:.2f} HOLD"


def filter_draw_warning(draw_prob, liga):
    dw = _p.DRAW_W.get(liga, 0)
    if dw and draw_prob > dw:
        return False, f"Draw danger {draw_prob:.3f} > {dw} HOLD"
    return True, f"Draw OK {draw_prob:.3f}"


def filter_giant_killer(home, away, liga):
    tbl = _p.ELO.get(liga, {})
    gap = tbl.get(away, 1500) - tbl.get(home, 1500)
    if gap < 100:
        return True, f"No GK risk gap={gap}"
    score = _p.GK.get(home, 0)
    if score >= 2.0:
        return False, f"GIANT KILLER {home} score={score} HOLD"
    return True, f"GK score low {score}"


def filter_lambda(lam_h, lam_a):
    total = lam_h + lam_a
    if total > LAMBDA_MAX:
        return False, f"Lambda too high {total:.2f} HOLD"
    if total < LAMBDA_MIN:
        return False, f"Lambda too low {total:.2f} HOLD"
    return True, f"Lambda OK {total:.2f}"


def filter_elo_gap(elo_diff):
    gap = abs(elo_diff)
    if gap < ELO_GAP_MIN:
        return False, f"Elo gap too small {gap} HOLD"
    return True, f"Elo gap OK {gap}"



def filter_ev(confidence, odds, liga, min_ev=0.05):
    strict      = {"EPL", "La_Liga"}
    if odds is None:
        if liga in strict:
            return False, "EPL/La_Liga wajib input odds untuk EV check"
        return True, "No odds, EV skipped"
    ev = round((confidence * odds) - 1, 4)
    if ev >= min_ev:
        return True,  f"EV +{ev:.3f} >= {min_ev}"
    return False, f"EV {ev:+.3f} < {min_ev} HOLD"

def sniper_filter(result, verbose=True):
    liga   = result["liga"]
    conf   = result["confidence"]
    draw_p = result["draw_prob"]
    lam_h  = result["lambda_home"]
    lam_a  = result["lambda_away"]
    elo_d  = result["elo_diff"]
    home   = result.get("home_team", "")
    away   = result.get("away_team", "")

    odds = result.get("odds_open")
    checks = [
        ("Threshold",    filter_threshold(conf, liga)),
        ("Draw Warning", filter_draw_warning(draw_p, liga)),
        ("Giant Killer", filter_giant_killer(home, away, liga)),
        ("Lambda",       filter_lambda(lam_h, lam_a)),
        ("Elo Gap",      filter_elo_gap(elo_d)),
        ("EV Check",     filter_ev(conf, odds, liga)),
    ]

    passed = [{"filter":n,"msg":m} for n,(ok,m) in checks if ok]
    failed = [{"filter":n,"msg":m} for n,(ok,m) in checks if not ok]
    tier   = "SNIPER" if not failed else "HOLD"
    reason = failed[0]["msg"] if failed else "All passed"

    if verbose:
        e = {"SNIPER":"🎯","HOLD":"⏸️ "}
        print(f"\n  {chr(8212)*48}")
        print(f"  SNIPER FILTER — {liga}")
        for n,(ok,m) in checks:
            print(f"  {chr(9989) if ok else chr(10060)} [{n:<14}] {m}")
        print(f"  {chr(8212)*48}")
        print(f"  {e[tier]} Final tier: {tier}")
        if failed:
            print(f"  Alasan: {reason}")
        print(f"  {chr(8212)*48}")

    return {"tier":tier,"passed":passed,"failed":failed,"reason":reason}


def predict_and_filter(home, away, liga,
                       match_date=None, absent_h=None, absent_a=None,
                       verbose=True):
    res = _p.predict_v20(home, away, liga,
                         match_date=match_date,
                         absent_h=absent_h,
                         absent_a=absent_a,
                         verbose=verbose)
    if not res:
        return None
    res["home_team"] = home
    res["away_team"] = away
    sf = sniper_filter(res, verbose=True)
    res.update(sf)
    return res
