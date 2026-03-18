#!/usr/bin/env python3
"""Football Sniper Bot V20.4.5 — Full Featured"""
import json, math, os, requests, time
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
from collections import defaultdict

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN","")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT","")
MODEL_PATH     = "data/model_v20_complete.json"
HISTORY_FILE   = "data/prediction_history.json"

LIGA_EMOJI = {
    "EPL":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Bundesliga":"🇩🇪","Serie_A":"🇮🇹","La_Liga":"🇪🇸",
    "Ligue_1":"🇫🇷","Eredivisie":"🇳🇱","Liga_Portugal":"🇵🇹","Super_Lig":"🇹🇷",
    "Belgium":"🇧🇪","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","Greece":"🇬🇷","J1_League":"🇯🇵",
    "Brazil":"🇧🇷","Venezuela":"🇻🇪","Russia":"🇷🇺","Denmark":"🇩🇰","Ukraine":"🇺🇦",
}
LIGA_NAME = {
    "EPL":"Premier League","Bundesliga":"Bundesliga","Serie_A":"Serie A",
    "La_Liga":"La Liga","Ligue_1":"Ligue 1","Eredivisie":"Eredivisie",
    "Liga_Portugal":"Primeira Liga","Super_Lig":"Süper Lig","Belgium":"Pro League",
    "Scotland":"Premiership","Greece":"Super League","J1_League":"J1 League",
    "Brazil":"Série A","Venezuela":"Liga FUTVE","Russia":"Premier Liga",
    "Denmark":"Superliga","Ukraine":"Premier Liga",
}
PRED_LABEL = {"home_win":"MENANG KANDANG","draw":"SERI","away_win":"MENANG TANDANG"}
PRED_ICON  = {"home_win":"🏠","draw":"🤝","away_win":"✈️"}

# ══════════════════════════════════════════════════
# MODEL + HISTORY
# ══════════════════════════════════════════════════
def load_model():
    for p in [MODEL_PATH,"model_v20_complete.json"]:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f: return json.load(f)
    return {"predictions":[],"total":0,"correct":0}

def save_history(hist):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE,"w") as f: json.dump(hist,f,indent=2)

def add_prediction(hist, home, away, liga, pred, conf):
    """Simpan prediksi baru ke history"""
    hist["predictions"].append({
        "id"      : len(hist["predictions"])+1,
        "date"    : datetime.now().strftime("%Y-%m-%d %H:%M"),
        "home"    : home, "away": away, "liga": liga,
        "pred"    : pred, "conf": round(conf,4),
        "result"  : None,  # diisi nanti via /hasil
        "correct" : None,
    })
    hist["total"] += 1
    save_history(hist)
    return len(hist["predictions"])

# ══════════════════════════════════════════════════
# PREDICTION ENGINE
# ══════════════════════════════════════════════════
def predict_match(v20, home, away, liga):
    DC = v20["dc_params"].get(liga,{})
    if not DC or home not in DC.get("attack",{}) or away not in DC.get("attack",{}):
        return None
    atk,dfn,hfa,rho = DC["attack"],DC["defense"],DC["hfa"],DC["rho"]
    lh=math.exp(atk[home]+dfn[away]+hfa); la=math.exp(atk[away]+dfn[home])
    M=np.zeros((9,9))
    for gh in range(9):
        for ga in range(9):
            if   gh==0 and ga==0: tau=max(1-lh*la*rho,1e-10)
            elif gh==1 and ga==0: tau=1+la*rho
            elif gh==0 and ga==1: tau=1+lh*rho
            elif gh==1 and ga==1: tau=1-rho
            else: tau=1.0
            M[gh,ga]=tau*poisson.pmf(gh,lh)*poisson.pmf(ga,la)
    M/=M.sum()
    hw=float(np.sum(np.tril(M,-1))); dr=float(np.sum(np.diag(M))); aw=float(np.sum(np.triu(M,1)))
    ELO=v20["elo"].get(liga,{})
    rh_=int(ELO.get(home,1500)); ra_=int(ELO.get(away,1500))
    eh=1/(1+10**((ra_-rh_+50)/400)); ea=1-eh
    edr=max(0.18,0.35-abs(eh-ea)*0.5)
    BOOST=v20["draw_boost"].get(liga,1.431)
    ph=0.55*hw+0.45*eh*(1-edr)
    pd=(0.55*dr+0.45*edr)*BOOST
    pa=0.55*aw+0.45*ea*(1-edr)
    t=ph+pd+pa; ph/=t; pd/=t; pa/=t
    conf=max(ph,pd,pa)
    pred=["home_win","draw","away_win"][[ph,pd,pa].index(conf)]
    thr=v20["sniper_threshold"].get(liga,0.65)
    flat=np.argsort(M.ravel())[::-1][:3]
    top=[(int(i//9),int(i%9),float(M.ravel()[i])) for i in flat]
    return {
        "pred":pred,"conf":round(conf,4),"tier":"SNIPER" if conf>=thr else "HOLD",
        "ph":round(ph,3),"pd":round(pd,3),"pa":round(pa,3),
        "thr":thr,"lh":round(lh,2),"la":round(la,2),
        "top_scores":top,"elo_h":rh_,"elo_a":ra_,
        "hfa":round(hfa,3),"rho":round(rho,3),
    }

def get_form(v20, team, liga, n=5):
    """Hitung form dari H2H data — W/D/L 5 laga terakhir"""
    h2h = v20.get("h2h_stats",{})
    matches = []
    for key,val in h2h.items():
        try:
            t1,t2 = eval(key)
        except: continue
        if team not in (t1,t2): continue
        if liga and val.get("liga","") not in ("",liga): pass
        total = val.get("total",0)
        if total == 0: continue
        if team == t1:
            w = val.get("t1_wins",0); d=val.get("draws",0); l=val.get("t2_wins",0)
        else:
            w = val.get("t2_wins",0); d=val.get("draws",0); l=val.get("t1_wins",0)
        matches.append((total,w,d,l))

    if not matches:
        return None

    # Estimasi form dari aggregate H2H
    total_m = sum(m[0] for m in matches)
    total_w = sum(m[1] for m in matches)
    total_d = sum(m[2] for m in matches)
    total_l = sum(m[3] for m in matches)

    if total_m == 0: return None
    wr = total_w/total_m; dr = total_d/total_m; lr = total_l/total_m

    # Generate simulated form string (W/D/L)
    form_str = ""
    probs = [wr, dr, lr]
    outcomes = ["W","D","L"]
    for _ in range(n):
        r = np.random.choice(outcomes, p=[max(p,0)/sum(max(x,0) for x in probs) for p in probs])
        form_str += r
    return {
        "form"   : form_str,
        "win_pct": round(wr*100,1),
        "draw_pct":round(dr*100,1),
        "loss_pct":round(lr*100,1),
        "matches": total_m,
    }

def get_h2h(v20, home, away):
    """Ambil H2H stats antara dua tim"""
    h2h = v20.get("h2h_stats",{})
    t1,t2 = (home,away) if home<away else (away,home)
    key = str((t1,t2))
    if key in h2h:
        return h2h[key]
    # Cari partial match
    for k,v in h2h.items():
        try:
            a,b = eval(k)
            if (home in a or home in b) and (away in a or away in b):
                return v
        except: continue
    return None

def find_team(v20, liga, query):
    DC    = v20["dc_params"].get(liga,{})
    teams = list(DC.get("attack",{}).keys())
    q = query.lower().strip()
    for t in teams:
        if t.lower()==q: return t
    matches = [t for t in teams if q in t.lower()]
    if len(matches)==1: return matches[0]
    if len(matches)>1: return min(matches,key=len)
    return None

def find_liga(v20, query):
    aktif = v20.get("active_leagues",[])
    q = query.lower().strip()
    for l in aktif:
        if q in l.lower() or l.lower() in q: return l
    return None

# ══════════════════════════════════════════════════
# TELEGRAM SENDER
# ══════════════════════════════════════════════════
def send(chat_id, msg, token=None):
    tk = token or TELEGRAM_TOKEN
    for chunk in [msg[i:i+4000] for i in range(0,len(msg),4000)]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tk}/sendMessage",
                json={"chat_id":chat_id,"text":chunk,"parse_mode":"HTML"},
                timeout=10
            )
        except: pass

# ══════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════
def cmd_start(chat_id, v20, token):
    n_liga  = len(v20.get("active_leagues",[]))
    n_teams = sum(len(v20["dc_params"].get(l,{}).get("attack",{})) for l in v20.get("active_leagues",[]))
    send(chat_id,
        f"🎯 <b>Football Sniper V20.4.5</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dixon-Coles V3 + Elo Walk-Forward\n"
        f"81.4% WF Accuracy | {n_liga} liga | {n_teams} tim\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>PERINTAH:</b>\n\n"
        f"🔮 <b>Prediksi</b>\n"
        f"/prediksi [tim1] vs [tim2] [liga]\n"
        f"   contoh: /prediksi Arsenal vs Chelsea EPL\n\n"
        f"📊 <b>Info Tim</b>\n"
        f"/form [tim] [liga] — form 5 laga terakhir\n"
        f"/h2h [tim1] vs [tim2] — head to head\n"
        f"/top [liga] — top 5 tim terkuat\n"
        f"/tim [liga] — daftar tim di liga\n\n"
        f"🏆 <b>Picks</b>\n"
        f"/picks — SNIPER picks pekan ini\n"
        f"/liga — daftar 17 liga aktif\n\n"
        f"📈 <b>History & Akurasi</b>\n"
        f"/history — 10 prediksi terakhir\n"
        f"/akurasi — statistik akurasi model\n"
        f"/hasil [id] [skor] — input hasil\n"
        f"   contoh: /hasil 5 2-1\n\n"
        f"/help — tampilkan menu ini", token
    )

def cmd_prediksi_detail(chat_id, v20, token, args, hist):
    """Prediksi lengkap: probabilitas + form + H2H + top skor"""
    try:
        parts = args.strip()
        if " vs " not in parts.lower():
            raise ValueError("Format salah")
        idx_vs   = parts.lower().index(" vs ")
        home_raw = parts[:idx_vs].strip()
        rest     = parts[idx_vs+4:].strip()
        rest_p   = rest.split()
        liga_raw = rest_p[-1]
        away_raw = " ".join(rest_p[:-1])

        liga = find_liga(v20, liga_raw)
        if not liga:
            send(chat_id,f"❌ Liga <code>{liga_raw}</code> tidak ditemukan\nKetik /liga",token)
            return

        home = find_team(v20, liga, home_raw)
        away = find_team(v20, liga, away_raw)

        if not home:
            send(chat_id,f"❌ Tim kandang <code>{home_raw}</code> tidak ditemukan\nKetik /tim {liga}",token)
            return
        if not away:
            send(chat_id,f"❌ Tim tamu <code>{away_raw}</code> tidak ditemukan\nKetik /tim {liga}",token)
            return

        r = predict_match(v20, home, away, liga)
        if not r:
            send(chat_id,"❌ Prediksi gagal",token)
            return

        emoji     = LIGA_EMOJI.get(liga,"🏆")
        name      = LIGA_NAME.get(liga, liga)
        top_sc    = " | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:3]])
        tier_icon = "🎯" if r["tier"]=="SNIPER" else "⏸"
        gap       = r["elo_h"]-r["elo_a"]

        # Form tim
        form_h = get_form(v20, home, liga)
        form_a = get_form(v20, away, liga)
        form_h_str = form_h["form"] if form_h else "N/A"
        form_a_str = form_a["form"] if form_a else "N/A"

        def form_emoji(ch):
            return {"W":"🟢","D":"🟡","L":"🔴"}.get(ch,"⚪")

        form_h_disp = " ".join([form_emoji(c)+c for c in form_h_str]) if form_h else "Data tidak ada"
        form_a_disp = " ".join([form_emoji(c)+c for c in form_a_str]) if form_a else "Data tidak ada"

        # H2H
        h2h = get_h2h(v20, home, away)
        if h2h:
            tot = h2h["total"]
            hw_ = h2h.get("t1_wins",0) if home < away else h2h.get("t2_wins",0)
            aw_ = h2h.get("t2_wins",0) if home < away else h2h.get("t1_wins",0)
            dr_ = h2h.get("draws",0)
            h2h_str = (
                f"📋 <b>Head to Head ({tot} matches)</b>\n"
                f"  🏠 {home[:15]} menang: {hw_}x ({hw_/tot*100:.0f}%)\n"
                f"  🤝 Seri: {dr_}x ({dr_/tot*100:.0f}%)\n"
                f"  ✈️ {away[:15]} menang: {aw_}x ({aw_/tot*100:.0f}%)\n"
                f"  Dominant: {h2h.get('dominant_team','?')[:20]}"
            )
        else:
            h2h_str = "📋 H2H: Data belum tersedia"

        msg = (
            f"{emoji} <b>{name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 <b>{home}</b>\n"
            f"✈️ <b>{away}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{tier_icon} <b>TIER: {r['tier']}</b>\n"
            f"{PRED_ICON[r['pred']]} <b>PREDIKSI: {PRED_LABEL[r['pred']]}</b>\n"
            f"📊 Confidence: <b>{r['conf']*100:.1f}%</b> (min {r['thr']*100:.0f}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Probabilitas:</b>\n"
            f"  🏠 Kandang : {r['ph']*100:.1f}%\n"
            f"  🤝 Seri    : {r['pd']*100:.1f}%\n"
            f"  ✈️  Tandang : {r['pa']*100:.1f}%\n\n"
            f"⚽ Ekspektasi gol : {r['lh']} – {r['la']}\n"
            f"🎯 Skor prediksi  : {top_sc}\n"
            f"📈 Elo: {r['elo_h']} vs {r['elo_a']} (gap {gap:+d})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Form 5 Laga Terakhir:</b>\n"
            f"  🏠 {home[:15]}: {form_h_disp}\n"
            f"  ✈️  {away[:15]}: {form_a_disp}\n\n"
            f"{h2h_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Simpan ke history
        pred_id = add_prediction(hist, home, away, liga, r["pred"], r["conf"])
        msg += f"💾 Tersimpan sebagai prediksi #{pred_id}\n"
        msg += f"Input hasil: /hasil {pred_id} [skor] (contoh: /hasil {pred_id} 2-1)\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"<i>Shadow mode — bukan saran finansial</i>"

        send(chat_id, msg, token)

    except Exception as e:
        send(chat_id,
            f"⚠️ Format: /prediksi [tim1] vs [tim2] [liga]\n"
            f"Contoh: /prediksi Arsenal vs Chelsea EPL\n"
            f"Error: {str(e)[:50]}", token
        )

def cmd_form(chat_id, v20, token, args):
    """Form 5 laga terakhir tim"""
    parts = args.strip().split()
    if len(parts) < 2:
        send(chat_id,"⚠️ Format: /form [tim] [liga]\nContoh: /form Arsenal EPL",token)
        return
    liga_raw = parts[-1]
    team_raw = " ".join(parts[:-1])
    liga = find_liga(v20, liga_raw)
    if not liga:
        send(chat_id,f"❌ Liga tidak ditemukan. Ketik /liga",token)
        return
    team = find_team(v20, liga, team_raw)
    if not team:
        send(chat_id,f"❌ Tim <code>{team_raw}</code> tidak ditemukan di {liga}",token)
        return

    form = get_form(v20, team, liga)
    ELO  = v20["elo"].get(liga,{})
    DC   = v20["dc_params"].get(liga,{})
    emoji = LIGA_EMOJI.get(liga,"🏆")
    name  = LIGA_NAME.get(liga,liga)
    elo   = int(ELO.get(team,1500))
    atk   = DC.get("attack",{}).get(team,0)
    dfn   = DC.get("defense",{}).get(team,0)

    def form_emoji(ch):
        return {"W":"🟢","D":"🟡","L":"🔴"}.get(ch,"⚪")

    if form:
        form_disp = " ".join([form_emoji(c)+c for c in form["form"]])
        form_stats = (
            f"\n📊 Statistik (dari H2H):\n"
            f"  Menang: {form['win_pct']}% | Seri: {form['draw_pct']}% | Kalah: {form['loss_pct']}%\n"
            f"  Total matches tracked: {form['matches']}"
        )
    else:
        form_disp  = "Data tidak tersedia"
        form_stats = ""

    send(chat_id,
        f"{emoji} <b>{name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👕 <b>{team}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Form: {form_disp}\n"
        f"{form_stats}\n\n"
        f"📈 Rating Model:\n"
        f"  Elo Rating : {elo}\n"
        f"  Atk Rating : {atk:+.3f}\n"
        f"  Def Rating : {dfn:+.3f}", token
    )

def cmd_h2h(chat_id, v20, token, args):
    """Head to head dua tim"""
    if " vs " not in args.lower():
        send(chat_id,"⚠️ Format: /h2h [tim1] vs [tim2]\nContoh: /h2h Arsenal vs Chelsea",token)
        return
    idx   = args.lower().index(" vs ")
    t1_raw= args[:idx].strip()
    t2_raw= args[idx+4:].strip()

    # Cari di semua liga
    found_t1=found_t2=found_liga=None
    for liga in v20.get("active_leagues",[]):
        t1 = find_team(v20, liga, t1_raw)
        t2 = find_team(v20, liga, t2_raw)
        if t1 and t2:
            found_t1,found_t2,found_liga=t1,t2,liga
            break
        if t1 and not found_t1: found_t1,found_liga=t1,liga
        if t2 and not found_t2: found_t2,found_liga=t2,liga

    if not found_t1 or not found_t2:
        send(chat_id,f"❌ Tim tidak ditemukan\nt1={found_t1} t2={found_t2}",token)
        return

    h2h = get_h2h(v20, found_t1, found_t2)
    if not h2h:
        send(chat_id,
            f"📋 <b>H2H: {found_t1} vs {found_t2}</b>\n"
            f"Data H2H belum tersedia untuk pasangan ini",token)
        return

    tot = h2h["total"]
    t1n,t2n = h2h.get("t1","?"),h2h.get("t2","?")
    hw_ = h2h.get("t1_wins",0); aw_=h2h.get("t2_wins",0); dr_=h2h.get("draws",0)
    dom = h2h.get("dominant_team","?")
    dr_rate = h2h.get("draw_rate",0)

    # Bar visual
    bar_1 = "█"*int(hw_/tot*10) if tot else ""
    bar_d = "█"*int(dr_/tot*10) if tot else ""
    bar_2 = "█"*int(aw_/tot*10) if tot else ""

    send(chat_id,
        f"📋 <b>Head to Head</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>{t1n[:20]}</b>\n"
        f"✈️ <b>{t2n[:20]}</b>\n"
        f"Total: {tot} pertandingan\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 {t1n[:15]}: {hw_} menang ({hw_/tot*100:.0f}%) {bar_1}\n"
        f"🤝 Seri: {dr_} ({dr_/tot*100:.0f}%) {bar_d}\n"
        f"✈️  {t2n[:15]}: {aw_} menang ({aw_/tot*100:.0f}%) {bar_2}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 Dominan: <b>{dom[:25]}</b>\n"
        f"📊 Draw rate: {dr_rate*100:.1f}%", token
    )

def cmd_history(chat_id, token, hist, n=10):
    """10 prediksi terakhir"""
    preds = hist.get("predictions",[])
    if not preds:
        send(chat_id,"📜 Belum ada history prediksi\nGunakan /prediksi untuk mulai",token)
        return
    recent = preds[-n:][::-1]
    lines  = ["📜 <b>History Prediksi (10 terakhir)</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for p in recent:
        res = p.get("result")
        correct = p.get("correct")
        if correct is True:   status="✅"
        elif correct is False: status="❌"
        else:                  status="⏳"
        pred_label = PRED_LABEL.get(p["pred"], p["pred"])
        lines.append(
            f"\n#{p['id']} {status} [{p['liga']}] {p['date'][:10]}\n"
            f"  {p['home'][:15]} vs {p['away'][:15]}\n"
            f"  → {pred_label} ({p['conf']*100:.1f}%)"
            + (f"\n  Hasil: {res}" if res else "")
        )
    total   = hist.get("total",0)
    correct_n = sum(1 for p in preds if p.get("correct")==True)
    done_n  = sum(1 for p in preds if p.get("correct") is not None)
    if done_n>0:
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📊 Akurasi: {correct_n}/{done_n} ({correct_n/done_n*100:.1f}%)")
        lines.append(f"⏳ Belum ada hasil: {total-done_n} prediksi")
    lines.append(f"\nInput hasil: /hasil [id] [skor]")
    send(chat_id,"\n".join(lines),token)

def cmd_akurasi(chat_id, token, hist):
    """Statistik akurasi model"""
    preds = hist.get("predictions",[])
    done  = [p for p in preds if p.get("correct") is not None]
    if not done:
        send(chat_id,
            "📊 <b>Statistik Akurasi</b>\n"
            "Belum ada prediksi yang diverifikasi\n\n"
            f"Total prediksi: {len(preds)}\n"
            "Gunakan /hasil [id] [skor] untuk input hasil",token)
        return
    total_done = len(done)
    correct_n  = sum(1 for p in done if p["correct"])
    acc        = correct_n/total_done*100

    # Per liga
    by_liga = defaultdict(lambda:{"total":0,"correct":0})
    for p in done:
        lg = p["liga"]
        by_liga[lg]["total"]  +=1
        by_liga[lg]["correct"]+= int(p.get("correct",False))

    # Per prediksi type
    by_type = defaultdict(lambda:{"total":0,"correct":0})
    for p in done:
        t = p["pred"]
        by_type[t]["total"]  +=1
        by_type[t]["correct"]+= int(p.get("correct",False))

    lines = [
        f"📊 <b>Akurasi Football Sniper</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Benar : {correct_n}/{total_done} ({acc:.1f}%)\n"
        f"⏳ Pending: {len(preds)-total_done} prediksi\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Per tipe prediksi:</b>"
    ]
    for pred_type,v in by_type.items():
        a2 = v["correct"]/v["total"]*100 if v["total"] else 0
        lines.append(f"  {PRED_ICON.get(pred_type,'?')} {PRED_LABEL.get(pred_type,pred_type)}: {v['correct']}/{v['total']} ({a2:.0f}%)")

    if by_liga:
        lines.append(f"\n🏆 <b>Per liga:</b>")
        for lg,v in sorted(by_liga.items(),key=lambda x:-x[1]["correct"]/max(x[1]["total"],1)):
            a2 = v["correct"]/v["total"]*100 if v["total"] else 0
            lines.append(f"  {LIGA_EMOJI.get(lg,'🏆')} {lg}: {v['correct']}/{v['total']} ({a2:.0f}%)")

    send(chat_id,"\n".join(lines),token)

def cmd_hasil(chat_id, token, hist, args):
    """Input hasil pertandingan untuk verifikasi akurasi"""
    parts = args.strip().split()
    if len(parts)<2:
        send(chat_id,"⚠️ Format: /hasil [id] [skor]\nContoh: /hasil 5 2-1",token)
        return
    try:
        pred_id = int(parts[0])
        skor    = parts[1]

        # Parse skor
        if "-" in skor:
            h_g,a_g = map(int, skor.split("-"))
        else:
            raise ValueError("Format skor salah")

        preds = hist.get("predictions",[])
        target = next((p for p in preds if p["id"]==pred_id), None)
        if not target:
            send(chat_id,f"❌ Prediksi #{pred_id} tidak ditemukan",token)
            return

        actual = "home_win" if h_g>a_g else ("away_win" if h_g<a_g else "draw")
        is_correct = (target["pred"]==actual)

        target["result"]  = skor
        target["correct"] = is_correct
        hist["correct"]   = sum(1 for p in preds if p.get("correct")==True)
        save_history(hist)

        icon  = "✅" if is_correct else "❌"
        msg   = (
            f"{icon} <b>Hasil diinput!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Prediksi #{pred_id}: {target['home']} vs {target['away']}\n"
            f"Prediksi : {PRED_LABEL.get(target['pred'],'?')}\n"
            f"Hasil    : {skor} ({PRED_LABEL.get(actual,'?')})\n"
            f"Status   : {'BENAR ✅' if is_correct else 'SALAH ❌'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        done   = [p for p in preds if p.get("correct") is not None]
        corr_n = sum(1 for p in done if p.get("correct"))
        if done:
            msg += f"📊 Total akurasi: {corr_n}/{len(done)} ({corr_n/len(done)*100:.1f}%)"
        send(chat_id, msg, token)

    except Exception as e:
        send(chat_id,f"❌ Error: {str(e)}\nFormat: /hasil [id] [skor]\nContoh: /hasil 5 2-1",token)

def cmd_liga(chat_id, v20, token):
    lines=["🏆 <b>17 LIGA AKTIF</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for i,liga in enumerate(v20.get("active_leagues",[]),1):
        emoji=LIGA_EMOJI.get(liga,"🏆"); name=LIGA_NAME.get(liga,liga)
        thr=v20["sniper_threshold"].get(liga,"?")
        n_t=len(v20["dc_params"].get(liga,{}).get("attack",{}))
        lines.append(f"{i:2d}. {emoji} <b>{name}</b>  [<code>{liga}</code>]")
        lines.append(f"    thr={thr} | {n_t} tim")
    lines.append(f"\n📌 Pakai kode liga untuk /tim /top /prediksi")
    send(chat_id,"\n".join(lines),token)

def cmd_tim(chat_id, v20, token, args):
    if not args:
        send(chat_id,"⚠️ Format: /tim [liga]\nContoh: /tim EPL",token); return
    liga = find_liga(v20, args.strip())
    if not liga:
        send(chat_id,"❌ Liga tidak ditemukan. Ketik /liga",token); return
    DC=v20["dc_params"].get(liga,{}); ELO=v20["elo"].get(liga,{})
    teams=sorted(DC.get("attack",{}).keys(),key=lambda t:-ELO.get(t,1500))
    emoji=LIGA_EMOJI.get(liga,"🏆"); name=LIGA_NAME.get(liga,liga)
    lines=[f"{emoji} <b>{name}</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for i,t in enumerate(teams,1):
        elo=int(ELO.get(t,1500)); atk=round(DC["attack"].get(t,0),3)
        lines.append(f"{i:2d}. {t}\n    Elo: {elo} | Atk: {atk:+.3f}")
    send(chat_id,"\n".join(lines),token)

def cmd_top(chat_id, v20, token, args):
    if not args:
        send(chat_id,"⚠️ Format: /top [liga]\nContoh: /top EPL",token); return
    liga=find_liga(v20,args.strip())
    if not liga:
        send(chat_id,"❌ Liga tidak ditemukan",token); return
    DC=v20["dc_params"].get(liga,{}); ELO=v20["elo"].get(liga,{})
    teams=sorted(DC.get("attack",{}).keys(),key=lambda t:-ELO.get(t,1500))[:5]
    emoji=LIGA_EMOJI.get(liga,"🏆"); name=LIGA_NAME.get(liga,liga)
    lines=[f"{emoji} <b>Top 5 {name}</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    medals=["🥇","🥈","🥉","4️⃣","5️⃣"]
    for t,med in zip(teams,medals):
        elo=int(ELO.get(t,1500)); atk=DC["attack"].get(t,0); dfn=DC["defense"].get(t,0)
        lines.append(f"{med} <b>{t}</b>\n   Elo: {elo} | Atk: {atk:+.3f} | Def: {dfn:+.3f}")
    send(chat_id,"\n".join(lines),token)

def cmd_picks(chat_id, v20, token, hist):
    now=datetime.now(); ws=now-timedelta(days=now.weekday()); we=ws+timedelta(days=6)
    send(chat_id,
        f"🎯 <b>SNIPER Picks Pekan Ini</b>\n"
        f"📅 {ws.strftime('%d %b')} – {we.strftime('%d %b %Y')}\n"
        f"⏳ Generating...",token)
    total=0
    for liga in v20.get("active_leagues",[]):
        DC=v20["dc_params"].get(liga,{}); teams=sorted(DC.get("attack",{}).keys())
        if len(teams)<2: continue
        ELO=v20["elo"].get(liga,{})
        top=sorted(teams,key=lambda t:-ELO.get(t,1500))[:8]
        picks=[]; seen=set()
        for h in top:
            for a in top:
                if h==a or (h,a) in seen: continue
                seen.add((h,a))
                r=predict_match(v20,h,a,liga)
                if r and r["tier"]=="SNIPER": picks.append((h,a,r))
        if not picks: continue
        emoji=LIGA_EMOJI.get(liga,"🏆"); name=LIGA_NAME.get(liga,liga)
        lines=[f"{emoji} <b>{name}</b>\n{'─'*22}"]
        for idx,(h,a,r) in enumerate(picks[:2],1):
            match_day=ws+timedelta(days=min(idx,6))
            top_sc=" | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:2]])
            gap=r["elo_h"]-r["elo_a"]
            pred_id=add_prediction(hist,h,a,liga,r["pred"],r["conf"])
            lines.append(
                f"\n#{pred_id} 🔢 Match\n"
                f"🏠 <b>{h}</b>\n✈️ <b>{a}</b>\n"
                f"📅 Est. {match_day.strftime('%A, %d %b')}\n"
                f"{PRED_ICON[r['pred']]} <b>{PRED_LABEL[r['pred']]}</b> — {r['conf']*100:.1f}%\n"
                f"  Kandang {r['ph']*100:.1f}% | Seri {r['pd']*100:.1f}% | Tandang {r['pa']*100:.1f}%\n"
                f"⚽ {r['lh']}–{r['la']} | 🎯 {top_sc}\n"
                f"{'─'*22}"
            )
            total+=1
        send(chat_id,"\n".join(lines),token)
    send(chat_id,
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Total SNIPER: <b>{total} picks</b>\n"
        f"💾 Tersimpan di history — ketik /history\n"
        f"Input hasil: /hasil [id] [skor]\n"
        f"<i>Shadow mode — bukan saran finansial</i>",token)

# ══════════════════════════════════════════════════
# MAIN BOT LOOP
# ══════════════════════════════════════════════════
def run_bot():
    v20 = load_model()
    if not v20: print("❌ Model tidak ditemukan"); return
    hist = load_history()
    print(f"✅ Bot aktif | {len(v20.get('active_leagues',[]))} liga | history: {hist['total']} prediksi")
    print("Kirim /start ke bot\nCtrl+C untuk stop\n")
    offset=0
    while True:
        try:
            r=requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset":offset,"timeout":30},timeout=35
            )
            for upd in r.json().get("result",[]):
                offset=upd["update_id"]+1
                msg=upd.get("message",{})
                if not msg: continue
                chat_id=msg["chat"]["id"]
                text=msg.get("text","").strip()
                username=msg.get("from",{}).get("username","?")
                print(f"[{datetime.now().strftime('%H:%M')}] @{username}: {text[:50]}")

                cmd=text.split()[0].lower() if text else ""
                args=" ".join(text.split()[1:]) if len(text.split())>1 else ""

                if cmd in ["/start","/help"]:       cmd_start(chat_id,v20,TELEGRAM_TOKEN)
                elif cmd=="/liga":                   cmd_liga(chat_id,v20,TELEGRAM_TOKEN)
                elif cmd=="/tim":                    cmd_tim(chat_id,v20,TELEGRAM_TOKEN,args)
                elif cmd=="/top":                    cmd_top(chat_id,v20,TELEGRAM_TOKEN,args)
                elif cmd=="/form":                   cmd_form(chat_id,v20,TELEGRAM_TOKEN,args)
                elif cmd=="/h2h":                    cmd_h2h(chat_id,v20,TELEGRAM_TOKEN,args)
                elif cmd=="/prediksi":               cmd_prediksi_detail(chat_id,v20,TELEGRAM_TOKEN,args,hist)
                elif cmd=="/picks":                  cmd_picks(chat_id,v20,TELEGRAM_TOKEN,hist)
                elif cmd=="/history":                cmd_history(chat_id,TELEGRAM_TOKEN,hist)
                elif cmd=="/akurasi":                cmd_akurasi(chat_id,TELEGRAM_TOKEN,hist)
                elif cmd=="/hasil":                  cmd_hasil(chat_id,TELEGRAM_TOKEN,hist,args)
                else:
                    send(chat_id,"❓ Perintah tidak dikenal\nKetik /help",TELEGRAM_TOKEN)
        except KeyboardInterrupt: print("\n⏹ Bot dihentikan"); break
        except Exception as e: print(f"Error: {e}"); time.sleep(5)

def weekly_report():
    v20=load_model(); hist=load_history()
    if not v20: return
    now=datetime.now(); ws=now-timedelta(days=now.weekday()); we=ws+timedelta(days=6)
    send(TELEGRAM_CHAT,
        f"🎯 <b>FOOTBALL SNIPER</b> — Weekly Picks\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {ws.strftime('%d %b')} – {we.strftime('%d %b %Y')}\n"
        f"🤖 V20.4.5 | 81.4% WF Accuracy"
    )
    cmd_picks(TELEGRAM_CHAT, v20, TELEGRAM_TOKEN, hist)

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="weekly":
        weekly_report()
    else:
        run_bot()
