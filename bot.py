#!/usr/bin/env python3
"""Football Sniper Bot V20.4.5 — Interactive Telegram Bot"""
import json, math, os, requests, time
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
LIGA_ESPN = {
    "EPL":"eng.1","Bundesliga":"ger.1","Serie_A":"ita.1",
    "La_Liga":"esp.1","Ligue_1":"fra.1","Eredivisie":"ned.1",
    "Liga_Portugal":"por.1","Super_Lig":"tur.1","Belgium":"bel.1",
    "Scotland":"sco.1","Greece":"gre.1","J1_League":"jpn.1",
    "Brazil":"bra.1","Venezuela":"ven.1","Russia":"rus.1",
    "Denmark":"den.1","Ukraine":"ukr.1",
}

ESPN_KEYWORDS = {
    # EPL
    "man city":       ["manchester city"],
    "man united":     ["manchester united"],
    "nott'm forest":  ["nottingham forest"],
    "newcastle":      ["newcastle united"],
    "wolves":         ["wolverhampton"],
    "west ham":       ["west ham united"],
    "bournemouth":    ["afc bournemouth"],
    "spurs":          ["tottenham hotspur"],
    "brighton":       ["brighton & hove"],
    # Bundesliga
    "bayern munich":  ["bayern munich"],
    "leverkusen":     ["bayer leverkusen"],
    "dortmund":       ["borussia dortmund"],
    "m'gladbach":     ["monchengladbach","mönchengladbach"],
    "ein frankfurt":  ["eintracht frankfurt"],
    "rb leipzig":     ["rb leipzig"],
    "hoffenheim":     ["tsg hoffenheim"],
    "heidenheim":     ["heidenheim"],
    "union berlin":   ["union berlin"],
    "fc koln":        ["fc cologne","cologne"],
    "st pauli":       ["st. pauli"],
    "wolfsburg":      ["vfl wolfsburg"],
    "freiburg":       ["sc freiburg"],
    "augsburg":       ["fc augsburg"],
    "stuttgart":      ["vfb stuttgart"],
    "hamburg":        ["hamburg sv"],
    "werder bremen":  ["werder bremen"],
    # Serie A
    "inter":          ["internazionale"],
    "milan":          ["ac milan"],
    "roma":           ["as roma"],
    "verona":         ["hellas verona"],
    # La Liga
    "ath bilbao":     ["athletic club"],
    "ath madrid":     ["atletico madrid","atlético madrid"],
    "sociedad":       ["real sociedad"],
    "betis":          ["real betis"],
    "espanol":        ["espanyol"],
    "celta":          ["celta vigo"],
    "vallecano":      ["rayo vallecano"],
    "alaves":         ["alavés","alaves"],
    "oviedo":         ["real oviedo"],
    # Ligue 1
    "paris sg":       ["paris saint-germain"],
    "rennes":         ["stade rennais"],
    "auxerre":        ["aj auxerre"],
    "monaco":         ["as monaco"],
    "le havre":       ["le havre ac"],
    # Eredivisie
    "ajax":           ["ajax amsterdam"],
    "feyenoord":      ["feyenoord rotterdam"],
    "nijmegen":       ["nec nijmegen"],
    "for sittard":    ["fortuna sittard"],
    "zwolle":         ["pec zwolle"],
    "heracles":       ["heracles almelo"],
    "twente":         ["fc twente"],
    "utrecht":        ["fc utrecht"],
    "groningen":      ["fc groningen"],
    "volendam":       ["fc volendam"],
    # Liga Portugal
    "sporting clube de portugal": ["sporting cp"],
    "sport lisboa e benfica":     ["benfica"],
    "futebol clube do porto":     ["fc porto"],
    "sporting clube de braga":    ["braga"],
    "futebol clube de famalicao": ["fc famalicao"],
    "vitoria sport clube":        ["vitória de guimaraes","vitoria"],
    "grupo desportivo estoril praia": ["estoril"],
    "club football estrela da amadora": ["estrela"],
    "futebol clube de arouca":    ["arouca"],
    "casa pia atletico clube":    ["casa pia"],
    "futebol clube de alverca":   ["alverca"],
    "rio ave futebol clube":      ["rio ave"],
    "clube desportivo santa clara":["santa clara"],
    "moreirense futebol clube":   ["moreirense"],
    "avs futebol sad":            ["avs"],
    "boavista fc":                ["boavista"],
    "gil vicente futebol clube":  ["gil vicente"],
    "clube desportivo de tondela":["tondela"],
    "clube desportivo nacional":  ["c.d. nacional","nacional"],
    # Super Lig
    "goztep":         ["goztepe"],
    "buyuksehyr":     ["istanbul basaksehir","basaksehir"],
    "gaziantep":      ["gaziantep fk"],
    "rizespor":       ["caykur rizespor"],
    "karagumruk":     ["fatih karagümrük","karagumruk"],
    "ad. demirspor":  ["adana demirspor"],
    "ankaragucu":     ["ankaragucu","ankaragücü"],
    # Belgium
    "royale union saint-gilloise": ["union st.-gilloise"],
    "club brugge koninklijke voetbalvereniging": ["club brugge"],
    "koninklijke sint-truidense voetbalvereniging": ["sint-truidense"],
    "koninklijke racing club genk": ["racing genk"],
    "royal sporting club anderlecht": ["anderlecht"],
    "koninklijke atletiek associatie gent": ["kaa gent"],
    "koninklijke voetbal club westerlo": ["kvc westerlo"],
    "yellow-red koninklijke voetbalclub mechelen": ["kv mechelen"],
    "royal standard club de liege": ["standard liege"],
    "royal antwerp football club": ["antwerp"],
    "royal charleroi sporting club": ["royal charleroi sc"],
    "cercle brugge koninklijke sportvereniging": ["cercle brugge"],
    "oud-heverlee leuven": ["oh leuven"],
    "fc verbroedering denderhoutem denderleeuw eendracht hekelgem": ["dender"],
    "sportvereniging zulte waregem": ["zulte-waregem"],
    # Scotland
    "the celtic football club": ["celtic"],
    "rangers football club":    ["rangers"],
    "heart of midlothian football club": ["heart of midlothian"],
    "hibernian football club":  ["hibernian"],
    "motherwell football club": ["motherwell"],
    "falkirk football & athletic club": ["falkirk"],
    "dundee united football club": ["dundee united"],
    "dundee football club":     ["dundee"],
    "aberdeen football club":   ["aberdeen"],
    "st. johnstone fc":         ["st johnstone"],
    "kilmarnock football club": ["kilmarnock"],
    "saint mirren football club":["st mirren"],
    "livingston football club": ["livingston"],
    # Greece
    "olympiakos syndesmos filathlon peiraios": ["olympiacos"],
    "athlitiki enosi konstantinoupoleos":      ["aek athens"],
    "panthessalonikios athlitikos omilos konstantinoupoliton": ["paok"],
    "panathinaikos athlitikos omilos":         ["panathinaikos"],
    "aris thessalonikis":                      ["aris"],
    "aps atromitos athinon":                   ["atromitos"],
    "apo levadiakos football club":            ["levadiakos"],
    "omilos filathlon irakliou fc":            ["ofi crete"],
    "volou neos podosferikos syllogos":        ["volos nfc"],
    "athlitiki enosi kifisias":                ["kifisia"],
    "a.g.s asteras tripolis":                  ["asteras tripoli"],
    "panserraikos serres":                     ["panserraikos fc"],
    "athlitiki enosi larisas":                 ["larissa fc"],
    # J1 League
    "verdy":          ["tokyo verdy"],
    "kyoto":          ["kyoto sanga"],
    "hokkaido consadole sapporo": ["sapporo","consadole"],
    # Brazil
    "rb bragantino":  ["red bull bragantino"],
    "vasco":          ["vasco da gama"],
    "athletico-pr":   ["athletico-pr"],
    # Venezuela
    "la guaira":      ["deportivo la guaira"],
    "dep. táchira":   ["deportivo táchira"],
    "anzoategui fc":  ["academia anzoátegui"],
    "dep. anzoátegui":["academia anzoátegui"],
    "rayo zuliano":   ["deportivo rayo zuliano"],
    "caracas":        ["caracas fc"],
    "metropolitanos": ["metropolitanos fc"],
    "monagas":        ["monagas sc"],
    "puerto cabello": ["academia puerto cabello"],
    "estudiantes m.": ["estudiantes de mérida"],
    # Russia
    "ao fk zenit sankt-peterburg": ["zenit st petersburg"],
    "fk spartak moskva": ["spartak moscow"],
    "pfk cska moskva":   ["cska moscow"],
    "fk dinamo moskva":  ["dinamo moscow"],
    "fk baltika":        ["fc baltika"],
    "rfk akhmat grozny": ["akhmat grozny"],
    "fc rubin kazan":    ["rubin kazan"],
    "fk rostov":         ["rostov"],
    "akron togliatti":   ["akron tolyatti"],
    "fc orenburg":       ["gazovik orenburg"],
    "pfk krylya sovetov samara": ["krylia sovetov"],
    "dinamo makhachkala":["dynamo makhachkala"],
    "fk nizhny novgorod":["nizhny novgorod"],
    "fk sochi":          ["sochi"],
    # Denmark
    "aarhus gymnastik forening":  ["agf"],
    "fodbold club midtjylland":   ["fc midtjylland"],
    "brondby idraetsforening":    ["brøndby if"],
    "fodbold club nordsjaelland": ["fc nordsjælland"],
    "viborg fodsports forening":  ["viborg ff"],
    "football club kobenhavn":    ["f.c. københavn"],
    "sonderjyske fodbold":        ["sønderjyske"],
    "randers fodbold club":       ["randers fc"],
    "fodbold club fredericia":    ["fc fredericia"],
    "silkeborg idraetsforening":  ["silkeborg if"],
}


_fixtures_cache = {}
_fixtures_date  = None

def _get_kw(name):
    n = name.lower().strip()
    if n in ESPN_KEYWORDS:
        return ESPN_KEYWORDS[n]
    return [w for w in n.split() if len(w) > 3]

def _is_match(model_name, espn_name):
    en = espn_name.lower()
    return any(kw in en for kw in _get_kw(model_name))

def _refresh_fixtures():
    global _fixtures_cache, _fixtures_date
    import datetime as _dt
    today = _dt.date.today()
    if _fixtures_date == today and _fixtures_cache:
        return
    date_from = today.strftime("%Y%m%d")
    date_to   = (today + _dt.timedelta(days=30)).strftime("%Y%m%d")
    for liga, slug in LIGA_ESPN.items():
        try:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard",
                headers={"User-Agent":"Mozilla/5.0"}, timeout=8,
                params={"dates": f"{date_from}-{date_to}"}
            )
            if r.status_code != 200:
                continue
            fixes = []
            for e in r.json().get("events",[]):
                comps = e["competitions"][0]["competitors"]
                home  = next(c for c in comps if c["homeAway"]=="home")["team"]["displayName"]
                away  = next(c for c in comps if c["homeAway"]=="away")["team"]["displayName"]
                # Simpan jam dalam WIB (UTC+7) - tanggal tetap pakai UTC date
                import datetime as _dt2
                raw_date = e["date"]  # format: 2026-03-18T13:00Z
                try:
                    utc_dt = _dt2.datetime.strptime(raw_date[:16], "%Y-%m-%dT%H:%M")
                    wib_dt = utc_dt + _dt2.timedelta(hours=7)
                    fix_time = wib_dt.strftime("%H:%M")
                    fix_date = raw_date[:10]  # pakai tanggal asli UTC
                except:
                    fix_time = None
                    fix_date = raw_date[:10]
                fixes.append({"date": fix_date, "time": fix_time, "home": home, "away": away})
            _fixtures_cache[liga] = fixes
        except:
            pass
    _fixtures_date = today
    print(f"[Bot] Fixtures: {sum(len(v) for v in _fixtures_cache.values())} total")

def _get_fixture_time(liga, home_model, away_model):
    """Ambil jam pertandingan dari ESPN cache"""
    for fix in _fixtures_cache.get(liga, []):
        fh, fa = fix["home"], fix["away"]
        if (_is_match(home_model, fh) and _is_match(away_model, fa)) or            (_is_match(home_model, fa) and _is_match(away_model, fh)):
            if "time" in fix:
                import datetime as _dt
                try:
                    return _dt.time.fromisoformat(fix["time"])
                except:
                    return None
    return None

def find_fixture_date(liga, home_model, away_model):
    _refresh_fixtures()
    for fix in _fixtures_cache.get(liga, []):
        fh, fa = fix["home"], fix["away"]
        if _is_match(home_model, fh) and _is_match(away_model, fa):
            return fix["date"]
        if _is_match(home_model, fa) and _is_match(away_model, fh):
            return fix["date"]
    return "TBD"


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN","")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT","")
MODEL_PATH     = "data/model_v20_complete.json"

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

def load_model():
    for p in [MODEL_PATH, "model_v20_complete.json"]:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    return None

def send(chat_id, msg, token=None):
    tk = token or TELEGRAM_TOKEN
    for chunk in [msg[i:i+4000] for i in range(0,len(msg),4000)]:
        requests.post(
            f"https://api.telegram.org/bot{tk}/sendMessage",
            json={"chat_id":chat_id,"text":chunk,"parse_mode":"HTML"}
        )

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
    }

def cmd_start(chat_id, v20, token):
    n_liga = len(v20.get("active_leagues",[]))
    n_teams= sum(len(v20["dc_params"].get(l,{}).get("attack",{})) for l in v20.get("active_leagues",[]))
    send(chat_id,
        f"🎯 <b>Football Sniper V20.4.5</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dixon-Coles V3 + Elo Walk-Forward\n"
        f"Akurasi WF: 81.4% | {n_liga} liga | {n_teams} tim\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>PERINTAH TERSEDIA:</b>\n\n"
        f"/picks — SNIPER picks pekan ini\n"
        f"/liga — Daftar semua liga aktif\n"
        f"/tim [liga] — Daftar tim di liga\n"
        f"  contoh: /tim EPL\n"
        f"/prediksi [tim1] vs [tim2] [liga] — Prediksi 1 match\n"
        f"  contoh: /prediksi Arsenal vs Chelsea EPL\n"
        f"/top [liga] — Top 5 tim terkuat di liga\n"
        f"  contoh: /top Bundesliga\n"
        f"/help — Tampilkan menu ini", token
    )

def cmd_liga(chat_id, v20, token):
    lines = ["🏆 <b>LIGA AKTIF</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for i,liga in enumerate(v20.get("active_leagues",[]),1):
        emoji = LIGA_EMOJI.get(liga,"🏆")
        name  = LIGA_NAME.get(liga,liga)
        thr   = v20["sniper_threshold"].get(liga,"?")
        n_t   = len(v20["dc_params"].get(liga,{}).get("attack",{}))
        lines.append(f"{i:2d}. {emoji} <b>{name}</b>  [<code>{liga}</code>]")
        lines.append(f"    thr={thr} | {n_t} tim")
    lines.append(f"\n📌 Gunakan kode liga untuk perintah /tim dan /top")
    send(chat_id, "\n".join(lines), token)

def cmd_tim(chat_id, v20, token, args):
    if not args:
        send(chat_id, "⚠️ Format: /tim [kode_liga]\nContoh: /tim EPL\n\nKode liga: EPL, Bundesliga, Serie_A, La_Liga, dll\nKetik /liga untuk daftar lengkap", token)
        return
    liga = args.strip()
    # Fuzzy match
    aktif = v20.get("active_leagues",[])
    match = None
    for l in aktif:
        if liga.lower() in l.lower() or l.lower() in liga.lower():
            match = l; break
    if not match:
        send(chat_id, f"❌ Liga <code>{liga}</code> tidak ditemukan\nKetik /liga untuk daftar kode liga", token)
        return
    DC    = v20["dc_params"].get(match,{})
    ELO   = v20["elo"].get(match,{})
    teams = sorted(DC.get("attack",{}).keys(), key=lambda t:-ELO.get(t,1500))
    emoji = LIGA_EMOJI.get(match,"🏆")
    name  = LIGA_NAME.get(match,match)
    lines = [f"{emoji} <b>{name}</b> — Daftar Tim\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for i,t in enumerate(teams,1):
        elo = int(ELO.get(t,1500))
        atk = round(DC["attack"].get(t,0),3)
        lines.append(f"{i:2d}. {t}\n    Elo: {elo} | Atk: {atk:+.3f}")
    lines.append(f"\n📊 Total: {len(teams)} tim | Diurutkan by Elo")
    send(chat_id, "\n".join(lines), token)

def cmd_top(chat_id, v20, token, args):
    if not args:
        send(chat_id, "⚠️ Format: /top [liga]\nContoh: /top EPL", token)
        return
    liga = args.strip()
    aktif = v20.get("active_leagues",[])
    match = None
    for l in aktif:
        if liga.lower() in l.lower() or l.lower() in liga.lower():
            match = l; break
    if not match:
        send(chat_id, f"❌ Liga tidak ditemukan. Ketik /liga", token)
        return
    DC    = v20["dc_params"].get(match,{})
    ELO   = v20["elo"].get(match,{})
    teams = sorted(DC.get("attack",{}).keys(), key=lambda t:-ELO.get(t,1500))[:5]
    emoji = LIGA_EMOJI.get(match,"🏆")
    name  = LIGA_NAME.get(match,match)
    lines = [f"{emoji} <b>Top 5 {name}</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    for i,(t,med) in enumerate(zip(teams,medals),1):
        elo = int(ELO.get(t,1500))
        atk = DC["attack"].get(t,0)
        dfn = DC["defense"].get(t,0)
        lines.append(
            f"{med} <b>{t}</b>\n"
            f"   Elo: {elo} | Atk: {atk:+.3f} | Def: {dfn:+.3f}"
        )
    send(chat_id, "\n".join(lines), token)

def cmd_prediksi(chat_id, v20, token, args):
    # Format: Arsenal vs Chelsea EPL
    try:
        parts = args.strip()
        # Cari "vs" sebagai pemisah
        if " vs " not in parts.lower():
            raise ValueError("Format salah")
        # Split: "Arsenal vs Chelsea EPL" -> ["Arsenal", "Chelsea EPL"]
        idx_vs = parts.lower().index(" vs ")
        home_raw = parts[:idx_vs].strip()
        rest     = parts[idx_vs+4:].strip()
        # Liga adalah kata terakhir
        rest_parts = rest.split()
        liga_raw   = rest_parts[-1]
        away_raw   = " ".join(rest_parts[:-1])
        # Match liga
        aktif = v20.get("active_leagues",[])
        liga  = None
        for l in aktif:
            if liga_raw.lower() in l.lower() or l.lower() in liga_raw.lower():
                liga = l; break
        if not liga:
            send(chat_id, f"❌ Liga <code>{liga_raw}</code> tidak ditemukan\nKetik /liga", token)
            return
        # Match tim
        DC    = v20["dc_params"].get(liga,{})
        teams = list(DC.get("attack",{}).keys())
        def find_team(query):
            q = query.lower()
            # Exact
            for t in teams:
                if t.lower()==q: return t
            # Partial
            matches = [t for t in teams if q in t.lower()]
            if len(matches)==1: return matches[0]
            if len(matches)>1:
                return min(matches, key=len)
            return None
        home = find_team(home_raw)
        away = find_team(away_raw)
        if not home:
            send(chat_id, f"❌ Tim kandang <code>{home_raw}</code> tidak ditemukan di {liga}\nKetik /tim {liga}", token)
            return
        if not away:
            send(chat_id, f"❌ Tim tamu <code>{away_raw}</code> tidak ditemukan di {liga}\nKetik /tim {liga}", token)
            return
        r = predict_match(v20, home, away, liga)
        if not r:
            send(chat_id, "❌ Prediksi gagal", token)
            return
        emoji     = LIGA_EMOJI.get(liga,"🏆")
        name      = LIGA_NAME.get(liga,liga)
        top_sc    = " | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:2]])
        tier_icon = "🎯" if r["tier"]=="SNIPER" else "⏸"
        tier_clr  = "✅" if r["tier"]=="SNIPER" else "⚠️"
        gap       = r["elo_h"]-r["elo_a"]
        send(chat_id,
            f"{emoji} <b>{name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 <b>{home}</b>\n"
            f"✈️ <b>{away}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{tier_clr} <b>TIER: {tier_icon} {r['tier']}</b>\n"
            f"{PRED_ICON[r['pred']]} <b>PREDIKSI: {PRED_LABEL[r['pred']]}</b>\n"
            f"📊 Confidence: <b>{r['conf']*100:.1f}%</b> (min {r['thr']*100:.0f}%)\n\n"
            f"Probabilitas:\n"
            f"  🏠 Kandang : {r['ph']*100:.1f}%\n"
            f"  🤝 Seri    : {r['pd']*100:.1f}%\n"
            f"  ✈️  Tandang : {r['pa']*100:.1f}%\n\n"
            f"⚽ Ekspektasi gol : {r['lh']} – {r['la']}\n"
            f"🎯 Skor prediksi  : {top_sc}\n"
            f"📈 Elo: {r['elo_h']} vs {r['elo_a']} (gap {gap:+d})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Shadow mode — bukan saran finansial</i>",
            token
        )
    except Exception as e:
        send(chat_id,
            f"⚠️ Format salah\n\n"
            f"Contoh benar:\n"
            f"/prediksi Arsenal vs Chelsea EPL\n"
            f"/prediksi Real Madrid vs Barcelona La_Liga\n"
            f"/prediksi PSV vs Ajax Eredivisie\n\n"
            f"Ketik /tim [liga] untuk daftar nama tim lengkap",
            token
        )

def cmd_picks(chat_id, v20, token):
    import datetime as _dt
    now_dt    = _dt.datetime.utcnow() + _dt.timedelta(hours=7)
    today     = now_dt.date()
    date_from = today.strftime("%Y%m%d")
    date_to   = (today + _dt.timedelta(days=30)).strftime("%Y%m%d")

    send(chat_id,
        f"\U0001f3af <b>SNIPER Picks — 30 Hari ke Depan</b>\n"
        f"\U0001f4c5 {today.strftime('%d %b %Y')} s/d {(today+_dt.timedelta(days=30)).strftime('%d %b %Y')}\n"
        f"\u23f3 Generating...", token
    )

    LIGA_ESPN_LOCAL = {
        "EPL":"eng.1","Bundesliga":"ger.1","Serie_A":"ita.1",
        "La_Liga":"esp.1","Ligue_1":"fra.1","Eredivisie":"ned.1",
        "Liga_Portugal":"por.1","Super_Lig":"tur.1","Belgium":"bel.1",
        "Scotland":"sco.1","Greece":"gre.1","J1_League":"jpn.1",
        "Brazil":"bra.1","Venezuela":"ven.1","Russia":"rus.1",
        "Denmark":"den.1",
    }

    # Kata yang TIDAK boleh dicocokkan secara ambigu
    BLACKLIST_PAIRS = [
        ("paris fc", "paris sg"), ("paris fc", "paris saint"),
        ("estudiantes de merida", "estudiantes caracas"),
        ("atletico", "athletic"),
    ]

    # Mapping eksplisit ESPN name -> Model name
    ESPN_TO_MODEL = {
        # EPL
        "afc bournemouth":          "Bournemouth",
        "brighton & hove albion":   "Brighton",
        "manchester city":          "Man City",
        "manchester united":        "Man United",
        "newcastle united":         "Newcastle",
        "nottingham forest":        "Nott'm Forest",
        "tottenham hotspur":        "Tottenham",
        "west ham united":          "West Ham",
        "wolverhampton wanderers":  "Wolves",
        "leeds united":             "Leeds",
        # Bundesliga
        "bayer leverkusen":         "Leverkusen",
        "borussia dortmund":        "Dortmund",
        "borussia monchengladbach": "M'gladbach",
        "borussia mönchengladbach": "M'gladbach",
        "eintracht frankfurt":      "Ein Frankfurt",
        "fc augsburg":              "Augsburg",
        "fc cologne":               "FC Koln",
        "hamburg sv":               "Hamburg",
        "1. fc heidenheim 1846":    "Heidenheim",
        "1. fc union berlin":       "Union Berlin",
        "sc freiburg":              "Freiburg",
        "st. pauli":                "St Pauli",
        "tsg hoffenheim":           "Hoffenheim",
        "vfb stuttgart":            "Stuttgart",
        "vfl wolfsburg":            "Wolfsburg",
        # Serie A
        "ac milan":                 "Milan",
        "as roma":                  "Roma",
        "hellas verona":            "Verona",
        "internazionale":           "Inter",
        # La Liga
        "athletic club":            "Ath Bilbao",
        "atletico madrid":          "Ath Madrid",
        "atlético madrid":          "Ath Madrid",
        "alavés":                   "Alaves",
        "alaves":                   "Alaves",
        "celta vigo":               "Celta",
        "espanyol":                 "Espanol",
        "rayo vallecano":           "Vallecano",
        "real betis":               "Betis",
        "real oviedo":              "Oviedo",
        "real sociedad":            "Sociedad",
        # Ligue 1
        "paris saint-germain":      "Paris SG",
        "stade rennais":            "Rennes",
        "aj auxerre":               "Auxerre",
        "as monaco":                "Monaco",
        "le havre ac":              "Le Havre",
        # Eredivisie
        "ajax amsterdam":           "Ajax",
        "fc groningen":             "Groningen",
        "fc twente":                "Twente",
        "fc utrecht":               "Utrecht",
        "fc volendam":              "Volendam",
        "feyenoord rotterdam":      "Feyenoord",
        "fortuna sittard":          "For Sittard",
        "heracles almelo":          "Heracles",
        "nec nijmegen":             "Nijmegen",
        "pec zwolle":               "Zwolle",
        # Liga Portugal
        "sporting cp":              "Sporting Clube de Portugal",
        "benfica":                  "Sport Lisboa e Benfica",
        "fc porto":                 "Futebol Clube do Porto",
        "braga":                    "Sporting Clube de Braga",
        "fc famalicao":             "Futebol Clube de Famalicão",
        "vitória de guimaraes":     "Vitória Sport Clube",
        "estoril":                  "Grupo Desportivo Estoril Praia",
        "estrela":                  "Club Football Estrela da Amadora",
        "arouca":                   "Futebol Clube de Arouca",
        "casa pia":                 "Casa Pia Atlético Clube",
        "alverca":                  "Futebol Clube de Alverca",
        "rio ave":                  "Rio Ave Futebol Clube",
        "santa clara":              "Clube Desportivo Santa Clara",
        "moreirense":               "Moreirense Futebol Clube",
        "avs":                      "AVS Futebol SAD",
        "gil vicente":              "Gil Vicente Futebol Clube",
        "tondela":                  "Clube Desportivo de Tondela",
        "c.d. nacional":            "Clube Desportivo Nacional",
        # Super Lig
        "goztepe":                  "Goztep",
        "istanbul basaksehir":      "Buyuksehyr",
        "fatih karagümrük":         "Karagumruk",
        "fatih karagumruk":         "Karagumruk",
        "caykur rizespor":          "Rizespor",
        "gaziantep fk":             "Gaziantep",
        # Belgium
        "anderlecht":               "Royal Sporting Club Anderlecht",
        "antwerp":                  "Royal Antwerp Football Club",
        "cercle brugge ksv":        "Cercle Brugge Koninklijke Sportvereniging",
        "club brugge":              "Club Brugge Koninklijke Voetbalvereniging",
        "dender":                   "FC Verbroedering Denderhoutem Denderleeuw Eendracht Hekelgem",
        "kaa gent":                 "Koninklijke Atletiek Associatie Gent",
        "kv mechelen":              "Yellow-Red Koninklijke Voetbalclub Mechelen",
        "kvc westerlo":             "Koninklijke Voetbal Club Westerlo",
        "oh leuven":                "Oud-Heverlee Leuven",
        "racing genk":              "Koninklijke Racing Club Genk",
        "royal charleroi sc":       "Royal Charleroi Sporting Club",
        "sint-truidense":           "Koninklijke Sint-Truidense Voetbalvereniging",
        "standard liege":           "Royal Standard Club de Liège",
        "union st.-gilloise":       "Royale Union Saint-Gilloise",
        "zulte-waregem":            "Sportvereniging Zulte Waregem",
        # Scotland
        "aberdeen":                 "Aberdeen Football Club",
        "celtic":                   "The Celtic Football Club",
        "dundee":                   "Dundee Football Club",
        "dundee united":            "Dundee United Football Club",
        "falkirk":                  "Falkirk Football & Athletic Club",
        "heart of midlothian":      "Heart of Midlothian Football Club",
        "hibernian":                "Hibernian Football Club",
        "kilmarnock":               "Kilmarnock Football Club",
        "livingston":               "Livingston Football Club",
        "motherwell":               "Motherwell Football Club",
        "rangers":                  "Rangers Football Club",
        "st mirren":                "Saint Mirren Football Club",
        # Greece
        "olympiacos":               "Olympiakos Syndesmos Filathlon Peiraios",
        "aek athens":               "Athlitiki Enosi Konstantinoupoleos",
        "paok salonika":            "Panthessalonikios Athlitikos Omilos Konstantinoupoliton",
        "panathinaikos":            "Panathinaikos Athlitikos Omilos",
        "aris":                     "Aris Thessalonikis",
        "atromitos":                "APS Atromitos Athinon",
        "levadiakos":               "APO Levadiakos Football Club",
        "ofi crete":                "Omilos Filathlon Irakliou FC",
        "volos nfc":                "Volou Neos Podosferikos Syllogos",
        "kifisia":                  "Athlitiki Enosi Kifisias",
        "asteras tripoli":          "A.G.S Asteras Tripolis",
        "panserraikos fc":          "Panserraikos Serres",
        "larissa fc":               "Athlitiki Enosi Larisas",
        "panetolikos":              "Panetolikos Agrinio",
        # J1 League
        "tokyo verdy 1969":         "Verdy",
        "kyoto sanga":              "Kyoto",
        "urawa red diamonds":       "Urawa Reds",
        # Brazil
        "red bull bragantino":      "RB Bragantino",
        "vasco da gama":            "Vasco",
        # Venezuela
        "academia anzoátegui":      "Dep. Anzoátegui",
        "academia puerto cabello":  "Puerto Cabello",
        "caracas fc":               "Caracas",
        "deportivo la guaira":      "La Guaira",
        "deportivo rayo zuliano":   "Rayo Zuliano",
        "deportivo táchira":        "Dep. Táchira",
        "estudiantes de mérida":    "Estudiantes M.",
        "metropolitanos fc":        "Metropolitanos",
        "monagas sc":               "Monagas",
        # Russia
        "akhmat grozny":            "RFK Akhmat Grozny",
        "akron tolyatti":           "Akron Togliatti",
        "cska moscow":              "PFK CSKA Moskva",
        "dinamo moscow":            "FK Dinamo Moskva",
        "dynamo makhachkala":       "Dinamo Makhachkala",
        "fc baltika kaliningrad":   "FK Baltika",
        "gazovik orenburg":         "FC Orenburg",
        "krasnodar":                "FK Krasnodar",
        "krylia sovetov":           "PFK Krylya Sovetov Samara",
        "lokomotiv moscow":         "Футбольный клуб \"Локомотив\" Москва",
        "nizhny novgorod":          "FK Nizhny Novgorod",
        "rostov":                   "FK Rostov",
        "rubin kazan":              "FC Rubin Kazan",
        "sochi":                    "FK Sochi",
        "spartak moscow":           "FK Spartak Moskva",
        "zenit st petersburg":      "AO FK Zenit Sankt-Peterburg",
        # Denmark
        "agf":                      "Aarhus Gymnastik Forening",
        "brøndby if":               "Brøndby Idrætsforening",
        "f.c. københavn":           "Football Club København",
        "fc fredericia":            "Fodbold Club Fredericia",
        "fc midtjylland":           "Fodbold Club Midtjylland",
        "fc nordsjælland":          "Fodbold Club Nordsjælland",
        "randers fc":               "Randers Fodbold Club",
        "silkeborg if":             "Silkeborg Idrætsforening",
        "viborg ff":                "Viborg Fodsports Forening",
    }

    def find_model_team(espn_name, model_teams):
        en = espn_name.lower().strip()
        # Cek explicit mapping dulu
        if en in ESPN_TO_MODEL:
            mapped = ESPN_TO_MODEL[en]
            if mapped in model_teams:
                return mapped
        # Exact match
        for t in model_teams:
            if t.lower() == en:
                return t
        # Partial match - min 2 kata cocok
        best, best_score = None, 0
        for t in model_teams:
            tn = t.lower()
            score = sum(1 for w in tn.split() if len(w)>3 and w in en)
            score += sum(1 for w in en.split() if len(w)>3 and w in tn)
            if score > best_score:
                best_score = score
                best = t
        return best if best_score >= 2 else None

    def is_blacklisted(espn_name, model_name):
        en = espn_name.lower()
        mn = model_name.lower()
        for bl1, bl2 in BLACKLIST_PAIRS:
            if bl1 in en and bl2 in mn:
                return True
            if bl2 in en and bl1 in mn:
                return True
        return False

    # Ambil fixtures dan jalankan prediksi
    sniper_picks = []
    for liga, slug in LIGA_ESPN_LOCAL.items():
        try:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard",
                headers={"User-Agent":"Mozilla/5.0"}, timeout=8,
                params={"dates": f"{date_from}-{date_to}"}
            )
            if r.status_code != 200:
                continue
            DC = v20["dc_params"].get(liga, {})
            model_teams = list(DC.get("attack", {}).keys())
            if not model_teams:
                continue
            for e in r.json().get("events", []):
                comps     = e["competitions"][0]["competitors"]
                espn_home = next(c for c in comps if c["homeAway"]=="home")["team"]["displayName"]
                espn_away = next(c for c in comps if c["homeAway"]=="away")["team"]["displayName"]
                raw_date  = e["date"]
                # Konversi ke WIB
                try:
                    utc_dt  = _dt.datetime.strptime(raw_date[:16], "%Y-%m-%dT%H:%M")
                    wib_dt  = utc_dt + _dt.timedelta(hours=7)
                    fix_date = raw_date[:10]
                    fix_time = wib_dt.strftime("%H:%M")
                    # Skip jika sudah lewat
                    if _dt.datetime.combine(_dt.date.fromisoformat(fix_date),
                        _dt.time.fromisoformat(fix_time)) < now_dt:
                        continue
                except:
                    fix_date = raw_date[:10]
                    fix_time = None

                home_model = find_model_team(espn_home, model_teams)
                away_model = find_model_team(espn_away, model_teams)

                if not home_model or not away_model or home_model == away_model:
                    continue
                if is_blacklisted(espn_home, home_model) or is_blacklisted(espn_away, away_model):
                    continue

                result = predict_match(v20, home_model, away_model, liga)
                if result and result["tier"] == "SNIPER":
                    sniper_picks.append({
                        "date": fix_date,
                        "time": fix_time,
                        "liga": liga,
                        "home": espn_home,
                        "away": espn_away,
                        "result": result,
                    })
        except Exception as ex:
            print(f"[Bot] Error {liga}: {ex}")

    # Urutkan berdasarkan tanggal
    sniper_picks.sort(key=lambda x: (x["date"], x["time"] or "99:99"))

    if not sniper_picks:
        send(chat_id, "Tidak ada SNIPER picks dalam 30 hari ke depan", token)
        return

    PRED_LABEL_LOCAL = {"home_win":"MENANG KANDANG","draw":"SERI","away_win":"MENANG TANDANG"}
    PRED_ICON_LOCAL  = {"home_win":"\U0001f3e0","draw":"\U0001f91d","away_win":"\u2708\ufe0f"}

    # Kirim per tanggal
    current_date = None
    lines = []
    total = 0
    for p in sniper_picks:
        r     = p["result"]
        emoji = LIGA_EMOJI.get(p["liga"], "\U0001f3c6")
        name  = LIGA_NAME.get(p["liga"], p["liga"])
        top_sc = " | ".join([f"{s[0]}-{s[1]}({s[2]*100:.0f}%)" for s in r["top_scores"][:2]])
        date_label = (p["date"] + " " + p["time"] + " WIB") if p["time"] else p["date"]

        if p["date"] != current_date:
            if lines:
                send(chat_id, "\n".join(lines), token)
            current_date = p["date"]
            lines = [f"\n\U0001f4c5 <b>{current_date}</b>\n{'\u2501'*22}"]

        lines.append(
            f"\n{emoji} <b>{name}</b>\n"
            "\U0001f3e0 <b>" + p["home"] + "</b>\n"
            "\u2708\ufe0f <b>" + p["away"] + "</b>\n"
            "\u23f0 " + date_label + "\n"
            + PRED_ICON_LOCAL[r["pred"]] + " <b>" + PRED_LABEL_LOCAL[r["pred"]] + "</b> \u2014 " + f'{r["conf"]*100:.1f}' + "%\n"
            + "  H:" + f'{r["ph"]*100:.1f}' + "% D:" + f'{r["pd"]*100:.1f}' + "% A:" + f'{r["pa"]*100:.1f}' + "%\n"
            + "\u26bd " + str(r["lh"]) + "\u2013" + str(r["la"]) + " | \U0001f3af " + top_sc + "\n"
            f"{'\u2501'*22}"
        )
        total += 1

    if lines:
        send(chat_id, "\n".join(lines), token)

    send(chat_id,
        f"{'\u2501'*22}\n"
        f"\u2705 Total SNIPER: <b>{total} picks</b>\n"
        f"\U0001f916 Model V20.4.5 | Dixon-Coles + Elo\n"
        f"<i>Shadow mode — bukan saran finansial</i>", token
    )


def run_bot():
    """Long polling — jalankan di Colab"""
    v20 = load_model()
    if not v20:
        print("❌ Model tidak ditemukan"); return
    print(f"✅ Bot aktif | {len(v20.get('active_leagues',[]))} liga")
    print("Kirim /start ke bot untuk mulai\nCtrl+C untuk stop\n")
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset":offset,"timeout":30},
                timeout=35
            )
            updates = r.json().get("result",[])
            for upd in updates:
                offset = upd["update_id"]+1
                msg    = upd.get("message",{})
                if not msg: continue
                chat_id = msg["chat"]["id"]
                text    = msg.get("text","").strip()
                username= msg.get("from",{}).get("username","?")
                print(f"[{datetime.now().strftime('%H:%M')}] @{username}: {text}")
                if   text.startswith("/start") or text.startswith("/help"):
                    cmd_start(chat_id, v20, TELEGRAM_TOKEN)
                elif text.startswith("/liga"):
                    cmd_liga(chat_id, v20, TELEGRAM_TOKEN)
                elif text.startswith("/tim"):
                    cmd_tim(chat_id, v20, TELEGRAM_TOKEN, text[4:].strip())
                elif text.startswith("/top"):
                    cmd_top(chat_id, v20, TELEGRAM_TOKEN, text[4:].strip())
                elif text.startswith("/prediksi"):
                    cmd_prediksi(chat_id, v20, TELEGRAM_TOKEN, text[9:].strip())
                elif text.startswith("/picks"):
                    cmd_picks(chat_id, v20, TELEGRAM_TOKEN)
                else:
                    send(chat_id,
                        "❓ Perintah tidak dikenal\n\n"
                        "Ketik /help untuk daftar perintah", TELEGRAM_TOKEN
                    )
        except KeyboardInterrupt:
            print("\n⏹ Bot dihentikan")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

# Weekly picks (dipanggil GitHub Actions)
def weekly_report():
    v20=load_model()
    if not v20: return
    now=datetime.now()
    ws=now-timedelta(days=now.weekday()); we=ws+timedelta(days=6)
    send(TELEGRAM_CHAT,
        f"🎯 <b>FOOTBALL SNIPER</b> — Weekly Picks\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {ws.strftime('%d %b')} – {we.strftime('%d %b %Y')}\n"
        f"🤖 V20.4.5 | 81.4% WF Accuracy"
    )
    cmd_picks(TELEGRAM_CHAT, v20, TELEGRAM_TOKEN)

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="weekly":
        weekly_report()
    else:
        run_bot()
