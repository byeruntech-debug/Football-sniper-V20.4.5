#!/usr/bin/env python3
"""Football Sniper Bot V20.4.5"""
import json, math, os, requests, time
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta

def _get_token():
    return os.environ.get("TELEGRAM_TOKEN", "")

def _get_chat():
    return os.environ.get("TELEGRAM_CHAT", "")

MODEL_PATH = "data/model_v20_complete.json"

LIGA_EMOJI = {
    "EPL":"PL","Bundesliga":"BL","Serie_A":"SA","La_Liga":"LL",
    "Ligue_1":"L1","Eredivisie":"ED","Liga_Portugal":"LP","Super_Lig":"SL",
    "Belgium":"BE","Scotland":"SC","Greece":"GR","J1_League":"J1",
    "Brazil":"BR","Venezuela":"VE","Russia":"RU","Denmark":"DK","Ukraine":"UA",
}
LIGA_NAME = {
    "EPL":"Premier League","Bundesliga":"Bundesliga","Serie_A":"Serie A",
    "La_Liga":"La Liga","Ligue_1":"Ligue 1","Eredivisie":"Eredivisie",
    "Liga_Portugal":"Primeira Liga","Super_Lig":"Super Lig","Belgium":"Pro League",
    "Scotland":"Premiership","Greece":"Super League","J1_League":"J1 League",
    "Brazil":"Serie A Brasil","Venezuela":"Liga FUTVE","Russia":"Premier Liga RU",
    "Denmark":"Superliga","Ukraine":"Premier Liga UA",
}
PRED_LABEL = {"home_win":"MENANG KANDANG","draw":"SERI","away_win":"MENANG TANDANG"}
PRED_ICON  = {"home_win":"H","draw":"D","away_win":"A"}

def load_model():
    for p in ["data/model_v20_complete.json", "model_v20_complete.json"]:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None

def send(chat_id, msg, token=None):
    tk = token or _get_token()
    for chunk in [msg[i:i+4000] for i in range(0, len(msg), 4000)]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tk}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"},
                timeout=10
            )
        except Exception as e:
            print(f"Send error: {e}")

def predict_match(v20, home, away, liga):
    DC = v20["dc_params"].get(liga, {})
    if not DC or home not in DC.get("attack", {}) or away not in DC.get("attack", {}):
        return None
    atk, dfn, hfa, rho = DC["attack"], DC["defense"], DC["hfa"], DC["rho"]
    lh = math.exp(atk[home] + dfn[away] + hfa)
    la = math.exp(atk[away] + dfn[home])
    M = np.zeros((9, 9))
    for gh in range(9):
        for ga in range(9):
            if   gh==0 and ga==0: tau = max(1-lh*la*rho, 1e-10)
            elif gh==1 and ga==0: tau = 1+la*rho
            elif gh==0 and ga==1: tau = 1+lh*rho
            elif gh==1 and ga==1: tau = 1-rho
            else: tau = 1.0
            M[gh, ga] = tau * poisson.pmf(gh, lh) * poisson.pmf(ga, la)
    M /= M.sum()
    hw = float(np.sum(np.tril(M, -1)))
    dr = float(np.sum(np.diag(M)))
    aw = float(np.sum(np.triu(M, 1)))
    ELO = v20["elo"].get(liga, {})
    eh = 1/(1+10**((int(ELO.get(away,1500))-int(ELO.get(home,1500))-50)/400))
    ea = 1 - eh
    edr = max(0.18, 0.35-abs(eh-ea)*0.5)
    BOOST = v20["draw_boost"].get(liga, 1.431)
    ph = 0.55*hw + 0.45*eh*(1-edr)
    pd = (0.55*dr + 0.45*edr) * BOOST
    pa = 0.55*aw + 0.45*ea*(1-edr)
    t = ph+pd+pa
    ph /= t; pd /= t; pa /= t
    conf = max(ph, pd, pa)
    pred = ["home_win","draw","away_win"][[ph,pd,pa].index(conf)]
    thr  = v20["sniper_threshold"].get(liga, 0.65)
    flat = np.argsort(M.ravel())[::-1][:3]
    top  = [(int(i//9), int(i%9), float(M.ravel()[i])) for i in flat]
    return {
        "pred":pred, "conf":round(conf,4),
        "tier":"SNIPER" if conf>=thr else "HOLD",
        "ph":round(ph,3), "pd":round(pd,3), "pa":round(pa,3),
        "thr":thr, "lh":round(lh,2), "la":round(la,2),
        "top_scores":top,
        "elo_h":int(ELO.get(home,1500)),
        "elo_a":int(ELO.get(away,1500)),
    }

def cmd_start(chat_id, v20):
    n = len(v20.get("active_leagues",[]))
    t = sum(len(v20["dc_params"].get(l,{}).get("attack",{})) for l in v20.get("active_leagues",[]))
    send(chat_id,
        f"Football Sniper V20.4.5\n"
        f"---\n"
        f"Dixon-Coles V3 + Elo | {n} liga | {t} tim\n"
        f"---\n\n"
        f"PERINTAH:\n"
        f"/picks - SNIPER picks pekan ini\n"
        f"/liga - Daftar liga aktif\n"
        f"/tim EPL - Daftar tim\n"
        f"/top EPL - Top 5 tim terkuat\n"
        f"/prediksi Arsenal vs Chelsea EPL\n"
        f"/help - Menu ini"
    )

def cmd_liga(chat_id, v20):
    lines = ["LIGA AKTIF\n---"]
    for i, liga in enumerate(v20.get("active_leagues",[]), 1):
        name = LIGA_NAME.get(liga, liga)
        thr  = v20["sniper_threshold"].get(liga, "?")
        n_t  = len(v20["dc_params"].get(liga,{}).get("attack",{}))
        lines.append(f"{i:2d}. {name}  [{liga}]")
        lines.append(f"    thr={thr} | {n_t} tim")
    send(chat_id, "\n".join(lines))

def cmd_tim(chat_id, v20, args):
    if not args:
        send(chat_id, "Format: /tim [liga]\nContoh: /tim EPL")
        return
    match = None
    for l in v20.get("active_leagues",[]):
        if args.lower() in l.lower() or l.lower() in args.lower():
            match = l; break
    if not match:
        send(chat_id, f"Liga tidak ditemukan. Ketik /liga")
        return
    DC    = v20["dc_params"].get(match, {})
    ELO   = v20["elo"].get(match, {})
    teams = sorted(DC.get("attack",{}).keys(), key=lambda t: -ELO.get(t,1500))
    name  = LIGA_NAME.get(match, match)
    lines = [f"{name}\n---"]
    for i, t in enumerate(teams, 1):
        elo = int(ELO.get(t, 1500))
        lines.append(f"{i:2d}. {t}  (Elo: {elo})")
    send(chat_id, "\n".join(lines))

def cmd_top(chat_id, v20, args):
    if not args:
        send(chat_id, "Format: /top [liga]\nContoh: /top EPL")
        return
    match = None
    for l in v20.get("active_leagues",[]):
        if args.lower() in l.lower() or l.lower() in args.lower():
            match = l; break
    if not match:
        send(chat_id, "Liga tidak ditemukan. Ketik /liga")
        return
    DC    = v20["dc_params"].get(match, {})
    ELO   = v20["elo"].get(match, {})
    teams = sorted(DC.get("attack",{}).keys(), key=lambda t: -ELO.get(t,1500))[:5]
    name  = LIGA_NAME.get(match, match)
    lines = [f"Top 5 {name}\n---"]
    medals = ["1.","2.","3.","4.","5."]
    for med, t in zip(medals, teams):
        elo = int(ELO.get(t, 1500))
        atk = DC["attack"].get(t, 0)
        lines.append(f"{med} {t}\n   Elo: {elo} | Atk: {atk:+.3f}")
    send(chat_id, "\n".join(lines))

def cmd_prediksi(chat_id, v20, args):
    try:
        if " vs " not in args.lower():
            raise ValueError("no vs")
        idx_vs   = args.lower().index(" vs ")
        home_raw = args[:idx_vs].strip()
        rest     = args[idx_vs+4:].strip().split()
        liga_raw = rest[-1]
        away_raw = " ".join(rest[:-1])
        match = None
        for l in v20.get("active_leagues",[]):
            if liga_raw.lower() in l.lower() or l.lower() in liga_raw.lower():
                match = l; break
        if not match:
            send(chat_id, f"Liga tidak ditemukan. Ketik /liga")
            return
        DC    = v20["dc_params"].get(match, {})
        teams = list(DC.get("attack",{}).keys())
        def find_team(q):
            q = q.lower()
            for t in teams:
                if t.lower() == q: return t
            matches = [t for t in teams if q in t.lower()]
            if matches: return min(matches, key=len)
            return None
        home = find_team(home_raw)
        away = find_team(away_raw)
        if not home:
            send(chat_id, f"Tim tidak ditemukan: {home_raw}\nKetik /tim {match}")
            return
        if not away:
            send(chat_id, f"Tim tidak ditemukan: {away_raw}\nKetik /tim {match}")
            return
        r = predict_match(v20, home, away, match)
        if not r:
            send(chat_id, "Prediksi gagal"); return
        name   = LIGA_NAME.get(match, match)
        top_sc = " | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:2]])
        tier   = "SNIPER" if r["tier"]=="SNIPER" else "HOLD"
        send(chat_id,
            f"{name}\n"
            f"---\n"
            f"H: {home}\n"
            f"A: {away}\n"
            f"---\n"
            f"TIER: {tier}\n"
            f"PREDIKSI: {PRED_LABEL[r['pred']]}\n"
            f"Confidence: {r['conf']*100:.1f}% (min {r['thr']*100:.0f}%)\n\n"
            f"Prob: H={r['ph']*100:.1f}% D={r['pd']*100:.1f}% A={r['pa']*100:.1f}%\n"
            f"Gol: {r['lh']} vs {r['la']}\n"
            f"Skor: {top_sc}\n"
            f"Elo: {r['elo_h']} vs {r['elo_a']} (gap {r['elo_h']-r['elo_a']:+d})"
        )
    except Exception as e:
        send(chat_id,
            f"Format salah\n\n"
            f"Contoh:\n"
            f"/prediksi Arsenal vs Chelsea EPL\n"
            f"/prediksi Real Madrid vs Barcelona La_Liga"
        )

def cmd_picks(chat_id, v20):
    now        = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_end   = week_start + timedelta(days=6)
    send(chat_id,
        f"SNIPER Picks Pekan Ini\n"
        f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b %Y')}\n"
        f"Loading..."
    )
    total = 0
    for liga in v20.get("active_leagues",[]):
        DC    = v20["dc_params"].get(liga, {})
        teams = sorted(DC.get("attack",{}).keys())
        if len(teams) < 2: continue
        ELO   = v20["elo"].get(liga, {})
        top   = sorted(teams, key=lambda t: -ELO.get(t,1500))[:8]
        picks = []
        seen  = set()
        for h in top:
            for a in top:
                if h==a or (h,a) in seen: continue
                seen.add((h,a))
                r = predict_match(v20, h, a, liga)
                if r and r["tier"]=="SNIPER":
                    picks.append((h, a, r))
        if not picks: continue
        name  = LIGA_NAME.get(liga, liga)
        lines = [f"{name}\n---"]
        for idx, (h, a, r) in enumerate(picks[:2], 1):
            day    = week_start + timedelta(days=min(idx, 6))
            top_sc = " | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:2]])
            lines.append(
                f"\nMatch #{idx}\n"
                f"H: {h}\n"
                f"A: {a}\n"
                f"Est: {day.strftime('%a %d %b')}\n"
                f"{PRED_LABEL[r['pred']]} - {r['conf']*100:.1f}%\n"
                f"H={r['ph']*100:.1f}% D={r['pd']*100:.1f}% A={r['pa']*100:.1f}%\n"
                f"Gol: {r['lh']}-{r['la']} | Skor: {top_sc}\n"
                f"Elo: {r['elo_h']} vs {r['elo_a']}"
            )
            total += 1
        send(chat_id, "\n".join(lines))
    send(chat_id, f"---\nTotal SNIPER: {total} picks\nShadow mode only")

def run_bot():
    token = _get_token()
    chat  = _get_chat()
    print(f"Token set: {bool(token)}")
    print(f"Chat set : {bool(chat)}")
    v20 = load_model()
    if not v20:
        print("ERROR: Model not found")
        return
    print(f"Bot aktif | {len(v20.get('active_leagues',[]))} liga")
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg    = upd.get("message", {})
                if not msg: continue
                chat_id = msg["chat"]["id"]
                text    = msg.get("text", "").strip()
                print(f"{datetime.now().strftime('%H:%M')} {text[:30]}")
                if   text.startswith("/start") or text.startswith("/help"):
                    cmd_start(chat_id, v20)
                elif text.startswith("/liga"):
                    cmd_liga(chat_id, v20)
                elif text.startswith("/tim"):
                    cmd_tim(chat_id, v20, text[4:].strip())
                elif text.startswith("/top"):
                    cmd_top(chat_id, v20, text[4:].strip())
                elif text.startswith("/prediksi"):
                    cmd_prediksi(chat_id, v20, text[9:].strip())
                elif text.startswith("/picks"):
                    cmd_picks(chat_id, v20)
                else:
                    send(chat_id, "Perintah tidak dikenal\nKetik /help")
        except KeyboardInterrupt:
            print("Bot stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
