#!/usr/bin/env python3
"""Football Sniper Bot V20.5.2 — with form/h2h/history/notif — Interactive Telegram Bot"""
import json, math, os, requests, time
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
# ═══════════════════════════════════════
# FITUR BARU: FORM, H2H, HISTORY, NOTIF
# ═══════════════════════════════════════
import json as _json

HISTORY_FILE = "data/prediction_history.json"

def _load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f: return _json.load(f)
    return {"predictions": [], "total": 0}

def _save_history(h):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w") as f: _json.dump(h, f, indent=2)

def _add_pred(home, away, liga, pred, conf):
    h = _load_history()
    pid = len(h["predictions"]) + 1
    h["predictions"].append({
        "id": pid, "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "home": home, "away": away, "liga": liga,
        "pred": pred, "conf": round(conf, 4), "result": None, "correct": None
    })
    h["total"] = len(h["predictions"])
    _save_history(h)
    return pid

def cmd_form(chat_id, v20, token, args):
    parts = args.strip().split()
    if len(parts) < 2:
        send(chat_id, "⚠️ Format: /form [tim] [liga]\nContoh: /form Arsenal EPL", token); return
    liga_raw = parts[-1]
    team_raw = " ".join(parts[:-1])
    match = None
    for l in v20.get("active_leagues", []):
        if liga_raw.lower() in l.lower() or l.lower() in liga_raw.lower():
            match = l; break
    if not match:
        send(chat_id, "❌ Liga tidak ditemukan. Ketik /liga", token); return
    DC = v20["dc_params"].get(match, {})
    teams = list(DC.get("attack", {}).keys())
    q = team_raw.lower()
    team = next((t for t in teams if t.lower() == q), None)
    if not team:
        matches = [t for t in teams if q in t.lower()]
        team = min(matches, key=len) if matches else None
    if not team:
        send(chat_id, f"❌ Tim tidak ditemukan di {match}\nKetik /tim {match}", token); return
    ELO = v20["elo"].get(match, {})
    h2h = v20.get("h2h_stats", {})
    emoji = LIGA_EMOJI.get(match, "🏆")
    name  = LIGA_NAME.get(match, match)
    # Hitung form dari H2H aggregate
    total_m = wins = draws = losses = 0
    for key, val in h2h.items():
        try: t1, t2 = eval(key)
        except: continue
        if team not in (t1, t2): continue
        tot = val.get("total", 0)
        if tot == 0: continue
        if team == t1:
            w = val.get("t1_wins", 0); d = val.get("draws", 0); l = val.get("t2_wins", 0)
        else:
            w = val.get("t2_wins", 0); d = val.get("draws", 0); l = val.get("t1_wins", 0)
        total_m += tot; wins += w; draws += d; losses += l
    if total_m > 0:
        wp = wins/total_m*100; dp = draws/total_m*100; lp = losses/total_m*100
        form_str = f"W:{wp:.0f}% D:{dp:.0f}% L:{lp:.0f}% ({total_m} matches)"
    else:
        form_str = "Data belum tersedia"
    elo = int(ELO.get(team, 1500))
    atk = round(DC["attack"].get(team, 0), 3)
    dfn = round(DC["defense"].get(team, 0), 3)
    send(chat_id,
        f"{emoji} <b>{name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👕 <b>{team}</b>\n\n"
        f"📊 <b>Form (dari H2H):</b>\n"
        f"  {form_str}\n\n"
        f"📈 <b>Rating Model:</b>\n"
        f"  Elo Rating : {elo}\n"
        f"  Atk Rating : {atk:+.3f}\n"
        f"  Def Rating : {dfn:+.3f}", token)

def cmd_h2h(chat_id, v20, token, args):
    if " vs " not in args.lower():
        send(chat_id, "⚠️ Format: /h2h [tim1] vs [tim2]\nContoh: /h2h Arsenal vs Chelsea", token); return
    idx = args.lower().index(" vs ")
    t1_raw = args[:idx].strip(); t2_raw = args[idx+4:].strip()
    h2h = v20.get("h2h_stats", {})
    found = None
    for key, val in h2h.items():
        try: t1, t2 = eval(key)
        except: continue
        if (t1_raw.lower() in t1.lower() or t1.lower() in t1_raw.lower()) and            (t2_raw.lower() in t2.lower() or t2.lower() in t2_raw.lower()):
            found = (t1, t2, val); break
        if (t1_raw.lower() in t2.lower() or t2.lower() in t1_raw.lower()) and            (t2_raw.lower() in t1.lower() or t1.lower() in t2_raw.lower()):
            found = (t2, t1, val); break
    if not found:
        send(chat_id, f"📋 H2H: {t1_raw} vs {t2_raw}\nData belum tersedia", token); return
    t1, t2, v = found
    tot = v["total"]
    hw = v.get("t1_wins", 0); aw = v.get("t2_wins", 0); dr = v.get("draws", 0)
    dom = v.get("dominant_team", "?")
    b1 = "█" * int(hw/tot*10) if tot else ""
    b2 = "█" * int(aw/tot*10) if tot else ""
    bd = "█" * int(dr/tot*10) if tot else ""
    send(chat_id,
        f"📋 <b>Head to Head</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 <b>{t1}</b>\n"
        f"✈️ <b>{t2}</b>\n"
        f"Total: {tot} pertandingan\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏠 {t1[:15]}: {hw} ({hw/tot*100:.0f}%) {b1}\n"
        f"🤝 Seri: {dr} ({dr/tot*100:.0f}%) {bd}\n"
        f"✈️  {t2[:15]}: {aw} ({aw/tot*100:.0f}%) {b2}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 Dominan: <b>{dom}</b>\n"
        f"📊 Draw rate: {v.get('draw_rate',0)*100:.1f}%", token)

def cmd_history(chat_id, token, n=10):
    h = _load_history()
    preds = h.get("predictions", [])
    if not preds:
        send(chat_id, "📜 Belum ada history\nGunakan /prediksi untuk mulai", token); return
    recent = preds[-n:][::-1]
    PRED_L = {"home_win": "KANDANG", "draw": "SERI", "away_win": "TANDANG"}
    lines = ["📜 <b>History Prediksi (10 terakhir)</b>\n━━━━━━━━━━━━━━━━━━━━━━━"]
    for p in recent:
        st = "✅" if p.get("correct") == True else ("❌" if p.get("correct") == False else "⏳")
        lines.append(
            f"\n#{p['id']} {st} [{p['liga']}] {p['date'][:10]}\n"
            f"  {p['home'][:15]} vs {p['away'][:15]}\n"
            f"  → {PRED_L.get(p['pred'], p['pred'])} ({p['conf']*100:.1f}%)"
            + (f"\n  Hasil: {p['result']}" if p.get("result") else "")
        )
    done = [p for p in preds if p.get("correct") is not None]
    if done:
        corr = sum(1 for p in done if p.get("correct"))
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━\n📊 Akurasi: {corr}/{len(done)} ({corr/len(done)*100:.1f}%)")
    lines.append("\nInput hasil: /hasil [id] [skor]")
    send(chat_id, "\n".join(lines), token)

def cmd_akurasi(chat_id, token):
    h = _load_history()
    preds = h.get("predictions", [])
    done = [p for p in preds if p.get("correct") is not None]
    if not done:
        send(chat_id,
            f"📊 <b>Statistik Akurasi</b>\n"
            f"Belum ada prediksi yang diverifikasi\n\n"
            f"Total prediksi: {len(preds)}\n"
            f"Gunakan /hasil [id] [skor] untuk input hasil", token); return
    corr = sum(1 for p in done if p["correct"])
    acc  = corr/len(done)*100
    from collections import defaultdict
    by_liga = defaultdict(lambda: {"t": 0, "c": 0})
    for p in done:
        by_liga[p["liga"]]["t"] += 1
        by_liga[p["liga"]]["c"] += int(p.get("correct", False))
    lines = [
        f"📊 <b>Akurasi Football Sniper</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Benar : {corr}/{len(done)} ({acc:.1f}%)\n"
        f"⏳ Pending: {len(preds)-len(done)} prediksi\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Per liga:</b>"
    ]
    for lg, v in sorted(by_liga.items(), key=lambda x: -x[1]["c"]/max(x[1]["t"],1)):
        a2 = v["c"]/v["t"]*100 if v["t"] else 0
        lines.append(f"  {LIGA_EMOJI.get(lg,'🏆')} {lg}: {v['c']}/{v['t']} ({a2:.0f}%)")
    send(chat_id, "\n".join(lines), token)

def cmd_hasil(chat_id, token, args):
    parts = args.strip().split()
    if len(parts) < 2:
        send(chat_id, "⚠️ Format: /hasil [id] [skor]\nContoh: /hasil 5 2-1", token); return
    try:
        pid = int(parts[0]); skor = parts[1]
        hg, ag = map(int, skor.split("-"))
        h = _load_history()
        target = next((p for p in h["predictions"] if p["id"] == pid), None)
        if not target:
            send(chat_id, f"❌ Prediksi #{pid} tidak ditemukan", token); return
        actual = "home_win" if hg > ag else ("away_win" if hg < ag else "draw")
        is_correct = target["pred"] == actual
        target["result"] = skor; target["correct"] = is_correct
        _save_history(h)
        PRED_L = {"home_win": "MENANG KANDANG", "draw": "SERI", "away_win": "MENANG TANDANG"}
        icon = "✅" if is_correct else "❌"
        done = [p for p in h["predictions"] if p.get("correct") is not None]
        corr = sum(1 for p in done if p.get("correct"))
        msg = (
            f"{icon} <b>Hasil diinput!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"#{pid}: {target['home']} vs {target['away']}\n"
            f"Prediksi: {PRED_L.get(target['pred'],'?')}\n"
            f"Hasil: {skor} ({PRED_L.get(actual,'?')})\n"
            f"Status: {'BENAR ✅' if is_correct else 'SALAH ❌'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Total akurasi: {corr}/{len(done)} ({corr/len(done)*100:.1f}%)" if done else ""
        )
        send(chat_id, msg, token)
    except Exception as e:
        send(chat_id, f"❌ Error: {str(e)}\nFormat: /hasil [id] [skor]", token)

def cmd_notif_set(chat_id, token, args, notif_store):
    """Set jadwal notifikasi harian, format: /notif 07:00"""
    parts = args.strip().split()
    if not parts:
        current = notif_store.get(str(chat_id), "off")
        send(chat_id,
            f"⏰ <b>Notifikasi Harian</b>\n"
            f"Status: {current}\n\n"
            f"Set jam: /notif 07:00\n"
            f"Matikan: /notif off", token); return
    jam = parts[0]
    if jam.lower() == "off":
        notif_store.pop(str(chat_id), None)
        send(chat_id, "🔕 Notifikasi dimatikan", token)
    else:
        notif_store[str(chat_id)] = jam
        send(chat_id, f"✅ Notifikasi harian diset: <b>{jam} WIB</b>\nBot akan kirim SNIPER picks setiap hari jam {jam}", token)

LIGA_ESPN = {
    "EPL":"eng.1","Bundesliga":"ger.1","Serie_A":"ita.1",
    "La_Liga":"esp.1","Ligue_1":"fra.1","Eredivisie":"ned.1",
    "Liga_Portugal":"por.1","Super_Lig":"tur.1","Belgium":"bel.1",
    "Scotland":"sco.1","Greece":"gre.1","J1_League":"jpn.1",
    "Brazil":"bra.1","Venezuela":"ven.1","Russia":"rus.1",
    "Denmark":"den.1",
    "UCL":"uefa.champions",
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
    date_to   = (today + _dt.timedelta(days=60)).strftime("%Y%m%d")
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
                # Simpan jam dan tanggal dalam WIB (UTC+7)
                import datetime as _dt2
                raw_date = e["date"]  # format: 2026-03-18T13:00Z
                try:
                    utc_dt = _dt2.datetime.strptime(raw_date[:16], "%Y-%m-%dT%H:%M")
                    wib_dt = utc_dt + _dt2.timedelta(hours=7)
                    fix_time = wib_dt.strftime("%H:%M")
                    fix_date = wib_dt.strftime("%Y-%m-%d")  # pakai WIB date
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
    "J2_League":"🇯🇵2️",
    "UCL":"🏆",
}
LIGA_NAME = {
    "EPL":"Premier League","Bundesliga":"Bundesliga","Serie_A":"Serie A",
    "La_Liga":"La Liga","Ligue_1":"Ligue 1","Eredivisie":"Eredivisie",
    "Liga_Portugal":"Primeira Liga","Super_Lig":"Süper Lig","Belgium":"Pro League",
    "Scotland":"Premiership","Greece":"Super League","J1_League":"J1 League",
    "Brazil":"Série A","Venezuela":"Liga FUTVE","Russia":"Premier Liga",
    "Denmark":"Superliga","Ukraine":"Premier Liga",
    "J2_League":"J2 League",
    "UCL":"Champions League",
}
PRED_LABEL = {"home_win":"MENANG KANDANG","draw":"SERI","away_win":"MENANG TANDANG"}
PRED_ICON  = {"home_win":"🏠","draw":"🤝","away_win":"✈️"}

def load_model():
    for p in [MODEL_PATH, "data/model_v20_complete.json"]:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    return None


def load_j2_fixtures():
    """Load J2 fixtures dari cache lokal (tidak pakai ESPN)"""
    cache_path = "data/fixtures_cache.json"
    if not os.path.exists(cache_path):
        return []
    try:
        with open(cache_path) as f:
            cache = json.load(f)
        return cache.get("J2_League", [])
    except:
        return []


def _load_notif_store():
    """Load notif store dari file — survive Railway restart"""
    path = "data/notif_store.json"
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except:
        pass
    return {}

def _save_notif_store(store):
    """Simpan notif store ke file"""
    path = "data/notif_store.json"
    try:
        os.makedirs("data", exist_ok=True)
        with open(path, "w") as f:
            json.dump(store, f)
    except:
        pass

def send(chat_id, msg, token=None):
    tk = token or TELEGRAM_TOKEN
    for chunk in [msg[i:i+4000] for i in range(0,len(msg),4000)]:
        requests.post(
            f"https://api.telegram.org/bot{tk}/sendMessage",
            json={"chat_id":chat_id,"text":chunk,"parse_mode":"HTML"}
        )

def predict_match(v20, home, away, liga):
    # Guard 1: tim sama → tidak valid
    if home == away:
        return None

    DC = v20["dc_params"].get(liga,{})
    if not DC:
        return None
    atk,dfn,hfa,rho = DC["attack"],DC["defense"],DC["hfa"],DC["rho"]

    # Guard 2: untuk liga NON-UCL, kedua tim harus ada di model
    # UCL punya fallback khusus, liga domestik tidak
    if liga != "UCL":
        if home not in atk or away not in atk:
            return None

    # Fallback untuk tim yang tidak ada di model (UCL only)
    meta      = v20.get("liga_meta",{}).get(liga,{})
    att_fb    = meta.get("att_fallback", 0.0)   # log-scale fallback
    def_fb    = meta.get("def_fallback", 0.0)   # log-scale fallback

    att_home  = atk.get(home, att_fb)
    def_home  = dfn.get(home, def_fb)
    att_away  = atk.get(away, att_fb)
    def_away  = dfn.get(away, def_fb)

    # Jika keduanya tidak dikenal → skip (UCL fallback not reliable)
    if home not in atk and away not in atk:
        return None

    lh=math.exp(att_home+def_away+hfa); la=math.exp(att_away+def_home)
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
    # ── H2H UCL adjustment ───────────────────────────
    if liga == "UCL":
        h2h_ucl = v20.get("h2h_ucl", {})
        _k1 = f"({min(home,away)}, {max(home,away)})"
        _h2h = h2h_ucl.get(_k1)
        # Syarat ketat: min 4 meetings DAN dominance jelas (>0.60) DAN bukan seimbang
        if (_h2h and
            _h2h.get("meetings", 0) >= 4 and
            _h2h.get("dominant_team") is not None and
            _h2h.get("dominance", 0) >= 0.60):
            dom      = _h2h["dominant_team"]
            dom_rate = _h2h["dominance"]
            dr_h2h   = _h2h.get("draw_rate", 0.25)
            n_meet   = _h2h["meetings"]
            # Weight: proporsional meetings (cap 10) dan dominance di atas 0.60
            meet_factor = min(n_meet, 10) / 10  # 0.2→1.0
            dom_factor  = (dom_rate - 0.60) / 0.40  # 0→1.0
            h2h_w = 0.08 * meet_factor * dom_factor  # max 0.08
            if h2h_w > 0.005:
                if dom == home:
                    ph = ph * (1 + h2h_w)
                    pa = pa * (1 - h2h_w * 0.5)
                elif dom == away:
                    pa = pa * (1 + h2h_w)
                    ph = ph * (1 - h2h_w * 0.5)
                pd = pd * (1 + (dr_h2h - 0.25) * 0.2)
                _t = ph + pd + pa
                ph /= _t; pd /= _t; pa /= _t

    conf=max(ph,pd,pa)
    pred=["home_win","draw","away_win"][[ph,pd,pa].index(conf)]
    thr=v20["sniper_threshold"].get(liga,0.65)

    # ── Platt scaling — DISABLED PERMANEN ───────────
    # Root cause: platt_scalers di model di-fit dengan fitur berbeda
    # (bukan [ph,pd,pa] output) sehingga tidak compatible dengan
    # predict_match pipeline sekarang. Perlu re-fit ulang dengan
    # features yang benar sebelum bisa diaktifkan kembali.
    # TODO: re-fit platt_scalers dengan input=[ph,pd,pa] dari predict_match

    # ── Giant killer adjustment ──────────────────────
    gk_data = v20.get("giant_killers", {})
    if gk_data:
        elo_diff = rh_ - ra_  # positif = home lebih kuat
        # Home sebagai giant killer vs tim lebih kuat
        if home in gk_data and elo_diff < -50:
            gk_mult = gk_data[home] / 100.0
            ph = ph * (1 + gk_mult)
            _t = ph + pd + pa; ph /= _t; pd /= _t; pa /= _t
        # Away sebagai giant killer vs tim lebih kuat
        elif away in gk_data and elo_diff > 50:
            gk_mult = gk_data[away] / 100.0
            pa = pa * (1 + gk_mult)
            _t = ph + pd + pa; ph /= _t; pd /= _t; pa /= _t

    # Recalculate conf dan pred setelah giant killer
    conf = max(ph, pd, pa)
    pred = ["home_win","draw","away_win"][[ph,pd,pa].index(conf)]

    # ── Draw warning flag ─────────────────────────────
    dw_thr = v20.get("draw_warning", {}).get(liga, 0.25)
    draw_warn = pd >= dw_thr and pred != "draw"

    # ── Adaptive threshold untuk UCL ─────────────────
    if liga == "UCL":
        thr_base = thr  # 0.68
        thr_high = thr_base + 0.02  # 0.70 — default ketat
        thr_low  = thr_base         # 0.68 — kalau ada justifikasi

        # Faktor 1: Elo gap (tim jelas lebih kuat)
        elo_gap = abs(rh_ - ra_)
        elo_justified = elo_gap >= 100

        # Faktor 2: H2H aktif (sudah di-adjust sebelumnya)
        h2h_ucl  = v20.get("h2h_ucl", {})
        _hkey    = f"({min(home,away)}, {max(home,away)})"
        _hx      = h2h_ucl.get(_hkey, {})
        h2h_active = (
            _hx.get("meetings", 0) >= 4 and
            _hx.get("dominant_team") is not None and
            _hx.get("dominance", 0) >= 0.60
        )

        # Faktor 3: Kekuatan DC jauh berbeda
        _dc    = v20["dc_params"]["UCL"]
        _meta  = v20.get("liga_meta", {}).get("UCL", {})
        _afb   = _meta.get("att_fallback", 0.0)
        _dfb   = _meta.get("def_fallback", 0.0)
        str_h  = math.exp(_dc["attack"].get(home,_afb) - _dc["defense"].get(home,_dfb))
        str_a  = math.exp(_dc["attack"].get(away,_afb) - _dc["defense"].get(away,_dfb))
        str_gap = abs(str_h - str_a)
        dc_justified = str_gap >= 1.5  # gap kekuatan DC signifikan

        # Tentukan threshold adaptif
        n_factors = sum([elo_justified, h2h_active, dc_justified])
        if n_factors >= 2:
            thr = thr_low   # 0.68 — 2+ faktor → lebih longgar
        elif n_factors == 1:
            thr = thr_base + 0.01  # 0.69 — 1 faktor → tengah
        else:
            thr = thr_high  # 0.70 — tidak ada faktor → ketat

    flat=np.argsort(M.ravel())[::-1][:3]
    top=[(int(i//9),int(i%9),float(M.ravel()[i])) for i in flat]
    return {
        "pred":pred,"conf":round(conf,4),"tier":"SNIPER" if conf>=thr else "HOLD",
        "ph":round(ph,3),"pd":round(pd,3),"pa":round(pa,3),
        "thr":round(thr,2),"lh":round(lh,2),"la":round(la,2),
        "top_scores":top,"elo_h":rh_,"elo_a":ra_,
        "draw_warn":draw_warn,"draw_warn_thr":round(dw_thr,3),
    }

def cmd_start(chat_id, v20, token):
    n_liga = len(v20.get("active_leagues",[]))
    n_teams= sum(len(v20["dc_params"].get(l,{}).get("attack",{})) for l in v20.get("active_leagues",[]))
    send(chat_id,
        f"🎯 <b>Football Sniper V20.5.2</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dixon-Coles V3 + Elo Walk-Forward\n"
        f"Akurasi WF: 87.4% | {n_liga} liga | {n_teams} tim\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>PERINTAH TERSEDIA:</b>\n\n"
        f"/today — SNIPER picks hari ini & besok\n"
        f"/picks — SNIPER picks pekan ini\n"
        f"/form [tim] [liga] — form tim\n"
        f"/h2h [tim1] vs [tim2] — head to head\n"
        f"/history — riwayat prediksi\n"
        f"/akurasi — statistik akurasi\n"
        f"/hasil [id] [skor] — input hasil\n"
        f"/notif [jam] — notifikasi harian\n"
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
            + (f"⚠️ <i>Draw warning — peluang seri {r['pd']*100:.0f}% "
               f"(threshold {r['draw_warn_thr']*100:.0f}%)</i>\n" if r.get('draw_warn') else "")
            + "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Shadow mode — bukan saran finansial</i>",
            token
        )
        pid = _add_pred(home, away, liga, r["pred"], r["conf"])
        send(chat_id, f"📝 Tersimpan sebagai <b>#{pid}</b>\nInput hasil: /hasil {pid} skor", token)
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
    now_dt    = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None) + _dt.timedelta(hours=7)
    today     = now_dt.date()
    date_from = today.strftime("%Y%m%d")
    date_to   = (today + _dt.timedelta(days=60)).strftime("%Y%m%d")

    send(chat_id,
        f"\U0001f3af <b>SNIPER Picks — 30 Hari ke Depan</b>\n"
        f"\U0001f4c5 {today.strftime('%d %b %Y')} s/d {(today+_dt.timedelta(days=60)).strftime('%d %b %Y')}\n"
        f"\u23f3 Generating...", token
    )

    LIGA_ESPN_LOCAL = {
        "EPL":"eng.1","Bundesliga":"ger.1","Serie_A":"ita.1",
        "La_Liga":"esp.1","Ligue_1":"fra.1","Eredivisie":"ned.1",
        "Liga_Portugal":"por.1","Super_Lig":"tur.1","Belgium":"bel.1",
        "Scotland":"sco.1","Greece":"gre.1","J1_League":"jpn.1",
        "Brazil":"bra.1","Venezuela":"ven.1","Russia":"rus.1",
        "Denmark":"den.1",
        "UCL":"uefa.champions",
    }

    # Kata yang TIDAK boleh dicocokkan secara ambigu
    BLACKLIST_PAIRS = [
        ("paris fc", "paris sg"), ("paris fc", "paris saint"),
        ("estudiantes de merida", "estudiantes caracas"),
        ("atletico", "athletic"),
        ("sporting cp", "sporting clube de braga"),
        ("sporting cp", "braga"),
    ]

    # Mapping eksplisit ESPN name -> Model name
    ESPN_TO_MODEL = {
        # ── UCL ─────────────────────────────────────
        "fc barcelona": "Barcelona",
        "barcelona": "Barcelona",
        "atlético madrid": "Atletico Madrid",
        "atletico madrid": "Atletico Madrid",
        "atletico de madrid": "Atletico Madrid",
        "atlético de madrid": "Atletico Madrid",
        "galatasaray": "Galatasaray",
        "galatasaray sk": "Galatasaray",
        "atalanta": "Atalanta",
        "atalanta bc": "Atalanta",
        "rb salzburg": "RB Salzburg",
        "red bull salzburg": "RB Salzburg",
        "monaco": "Monaco",
        "as monaco": "Monaco",
        "benfica": "Sport Lisboa e Benfica",
        "sl benfica": "Sport Lisboa e Benfica",
        "girona": "Girona",
        "girona fc": "Girona",
        "brest": "Brest",
        "stade brestois 29": "Brest",
        "bologna": "Bologna",
        "bologna fc": "Bologna",
        "lille": "LOSC Lille",
        "losc lille": "LOSC Lille",
        "villarreal": "Villarreal",
        "villarreal cf": "Villarreal",
        "sturm graz": "Sturm Graz",
        "slovan bratislava": "Slovan Bratislava",
        "young boys": "Young Boys",
        "bsc young boys": "Young Boys",
        "dinamo zagreb": "Dinamo Zagreb",
        "gnk dinamo": "GNK Dinamo",
        "shakhtar donetsk": "Shakhtar Donetsk",
        "red star belgrade": "Red Star Belgrade",
        "crvena zvezda": "Red Star Belgrade",
        "real madrid": "Real Madrid",
        "real madrid cf": "Real Madrid",
        "fc bayern münchen": "Bayern Munich",
        "fc bayern munich": "Bayern Munich",
        "paris saint-germain": "Paris SG",
        "paris sg": "Paris SG",
        "psg": "Paris SG",
        "borussia dortmund": "Dortmund",
        "internazionale": "Inter",
        "inter milan": "Inter",
        "manchester city": "Man City",
        "manchester united": "Man United",
        "juventus": "Juventus",
        "liverpool": "Liverpool",
        "arsenal": "Arsenal",
        "chelsea": "Chelsea",
        "tottenham hotspur": "Tottenham",
        "bayer leverkusen": "Leverkusen",
        "rb leipzig": "RB Leipzig",
        "sevilla fc": "Sevilla",
        "fc porto": "Futebol Clube do Porto",
        "sporting cp": "Sporting Clube de Portugal",
        "ajax": "Ajax",
        "psv eindhoven": "PSV Eindhoven",
        "feyenoord": "Feyenoord",
        "newcastle united": "Newcastle",
        "aston villa": "Aston Villa",
        "club brugge": "Club Brugge",
        "celtic": "Celtic",
        # ── EPL ─────────────────────────────────────
        "afc bournemouth": "Bournemouth",
        "brighton & hove albion": "Brighton",
        "nottingham forest": "Nott'm Forest",
        "west ham united": "West Ham",
        "wolverhampton wanderers": "Wolves",
        "leeds united": "Leeds",
        # ── Bundesliga ──────────────────────────────
        "borussia monchengladbach": "M'gladbach",
        "borussia mönchengladbach": "M'gladbach",
        "eintracht frankfurt": "Ein Frankfurt",
        "fc augsburg": "Augsburg",
        "fc cologne": "FC Koln",
        "hamburg sv": "Hamburg",
        "1. fc heidenheim 1846": "Heidenheim",
        "1. fc union berlin": "Union Berlin",
        "sc freiburg": "Freiburg",
        "st. pauli": "St Pauli",
        "tsg hoffenheim": "Hoffenheim",
        "vfb stuttgart": "Stuttgart",
        "vfl wolfsburg": "Wolfsburg",
        # ── Serie A ─────────────────────────────────
        "ac milan": "Milan",
        "as roma": "Roma",
        "hellas verona": "Verona",
        # ── La Liga ─────────────────────────────────
        "athletic club": "Ath Bilbao",
        "alavés": "Alaves",
        "alaves": "Alaves",
        "celta vigo": "Celta",
        "espanyol": "Espanol",
        "rayo vallecano": "Vallecano",
        "real betis": "Betis",
        "real oviedo": "Oviedo",
        "real sociedad": "Sociedad",
        # ── Ligue 1 ─────────────────────────────────
        "stade rennais": "Rennes",
        "aj auxerre": "Auxerre",
        "le havre ac": "Le Havre",
        "paris fc": "Paris FC",
        # ── Eredivisie ──────────────────────────────
        "ajax amsterdam": "Ajax",
        "fc groningen": "Groningen",
        "fc twente": "Twente",
        "fc utrecht": "Utrecht",
        "fc volendam": "Volendam",
        "feyenoord rotterdam": "Feyenoord",
        "fortuna sittard": "For Sittard",
        "heracles almelo": "Heracles",
        "nec nijmegen": "Nijmegen",
        "pec zwolle": "Zwolle",
        # ── Liga Portugal ───────────────────────────
        "braga": "Sporting Clube de Braga",
        "fc famalicao": "Futebol Clube de Famalicão",
        "vitória de guimaraes": "Vitória Sport Clube",
        "estoril": "Grupo Desportivo Estoril Praia",
        "estrela": "Club Football Estrela da Amadora",
        "arouca": "Futebol Clube de Arouca",
        "casa pia": "Casa Pia Atlético Clube",
        "alverca": "Futebol Clube de Alverca",
        "rio ave": "Rio Ave Futebol Clube",
        "santa clara": "Clube Desportivo Santa Clara",
        "moreirense": "Moreirense Futebol Clube",
        "avs": "AVS Futebol SAD",
        "gil vicente": "Gil Vicente Futebol Clube",
        "tondela": "Clube Desportivo de Tondela",
        "c.d. nacional": "Clube Desportivo Nacional",
        # ── Super Lig ───────────────────────────────
        "goztepe": "Goztep",
        "istanbul basaksehir": "Buyuksehyr",
        "fatih karagümrük": "Karagumruk",
        "fatih karagumruk": "Karagumruk",
        "caykur rizespor": "Rizespor",
        "gaziantep fk": "Gaziantep",
        "kocaelispor": "Kocaelispor Kulübü",
        "genclerbirligi": "Gençlerbirliği Spor Kulübü",
        # ── Belgium ─────────────────────────────────
        "anderlecht": "Royal Sporting Club Anderlecht",
        "antwerp": "Royal Antwerp Football Club",
        "cercle brugge ksv": "Cercle Brugge Koninklijke Sportvereniging",
        "club brugge kv": "Club Brugge Koninklijke Voetbalvereniging",
        "dender": "FC Verbroedering Denderhoutem Denderleeuw Eendracht Hekelgem",
        "kaa gent": "Koninklijke Atletiek Associatie Gent",
        "kv mechelen": "Yellow-Red Koninklijke Voetbalclub Mechelen",
        "kvc westerlo": "Koninklijke Voetbal Club Westerlo",
        "oh leuven": "Oud-Heverlee Leuven",
        "racing genk": "Koninklijke Racing Club Genk",
        "royal charleroi sc": "Royal Charleroi Sporting Club",
        "sint-truidense": "Koninklijke Sint-Truidense Voetbalvereniging",
        "standard liege": "Royal Standard Club de Liège",
        "union st.-gilloise": "Royale Union Saint-Gilloise",
        "zulte-waregem": "Sportvereniging Zulte Waregem",
        # ── Scotland ────────────────────────────────
        "aberdeen": "Aberdeen Football Club",
        "celtic fc": "The Celtic Football Club",
        "rangers": "Rangers Football Club",
        "heart of midlothian": "Heart of Midlothian Football Club",
        "hibernian": "Hibernian Football Club",
        "kilmarnock": "Kilmarnock Football Club",
        "livingston": "Livingston Football Club",
        "motherwell": "Motherwell Football Club",
        "dundee": "Dundee Football Club",
        "dundee united": "Dundee United Football Club",
        "falkirk": "Falkirk Football & Athletic Club",
        "st mirren": "Saint Mirren Football Club",
        # ── Greece ──────────────────────────────────
        "olympiacos": "Olympiakos Syndesmos Filathlon Peiraios",
        "aek athens": "Athlitiki Enosi Konstantinoupoleos",
        "paok salonika": "Panthessalonikios Athlitikos Omilos Konstantinoupoliton",
        "panathinaikos": "Panathinaikos Athlitikos Omilos",
        "aris": "Aris Thessalonikis",
        "atromitos": "APS Atromitos Athinon",
        "levadiakos": "APO Levadiakos Football Club",
        "ofi crete": "Omilos Filathlon Irakliou FC",
        "volos nfc": "Volou Neos Podosferikos Syllogos",
        "kifisia": "Athlitiki Enosi Kifisias",
        "asteras tripoli": "A.G.S Asteras Tripolis",
        "panserraikos fc": "Panserraikos Serres",
        "larissa fc": "Athlitiki Enosi Larisas",
        "panetolikos": "Panetolikos Agrinio",
        # ── J1 League ───────────────────────────────
        "tokyo verdy 1969": "Verdy",
        "kyoto sanga": "Kyoto",
        "urawa red diamonds": "Urawa Reds",
        "jef united ichihara-chiba": "JEF United",
        "mito hollyhock": "Mito HollyHock",
        "hokkaido consadole sapporo": "Sapporo",
        # ── J2 League ───────────────────────────────
        "machida zelvia": "Machida Zelvia",
        "fagiano okayama": "Fagiano Okayama",
        "jef united": "JEF United",
        "jef united ichihara chiba": "JEF United",
        "ventforet kofu": "Ventforet Kofu",
        "albirex niigata": "Albirex Niigata",
        "roasso kumamoto": "Roasso Kumamoto",
        "blaublitz akita": "Blaublitz Akita",
        "grulla morioka": "Grulla Morioka",
        "renofa yamaguchi": "Renofa Yamaguchi",
        "tochigi sc": "Tochigi SC",
        "thespakusatsu gunma": "Thespakusatsu Gunma",
        "giravanz kitakyushu": "Giravanz Kitakyushu",
        "fc ryukyu": "FC Ryukyu",
        "ehime fc": "Ehime FC",
        "jubilo iwata": "Jubilo Iwata",
        "kataller toyama": "Kataller Toyama",
        "iwaki fc": "Iwaki FC",
        "fc imabari": "FC Imabari",
        "fujieda myfc": "Fujieda MYFC",
        "kagoshima united": "Kagoshima United",
        "sc sagamihara": "SC Sagamihara",
        "toolbox kanazawa": "Toolbox Kanazawa",
        "montedio yamagata": "Montedio Yamagata",
        "omiya ardija": "Omiya Ardija",
        # ── Brazil ──────────────────────────────────
        "red bull bragantino": "RB Bragantino",
        "vasco da gama": "Vasco",
        "remo": "Clube do Remo",
        "clube do remo": "Clube do Remo",
        # ── Venezuela ───────────────────────────────
        "academia anzoátegui": "Dep. Anzoátegui",
        "academia puerto cabello": "Puerto Cabello",
        "caracas fc": "Caracas",
        "deportivo la guaira": "La Guaira",
        "deportivo rayo zuliano": "Rayo Zuliano",
        "deportivo táchira": "Dep. Táchira",
        "estudiantes de mérida": "Estudiantes M.",
        "metropolitanos fc": "Metropolitanos",
        "monagas sc": "Monagas",
        # ── Russia ──────────────────────────────────
        "akhmat grozny": "RFK Akhmat Grozny",
        "akron tolyatti": "Akron Togliatti",
        "cska moscow": "PFK CSKA Moskva",
        "dinamo moscow": "FK Dinamo Moskva",
        "dynamo makhachkala": "Dinamo Makhachkala",
        "fc baltika kaliningrad": "FK Baltika",
        "gazovik orenburg": "FC Orenburg",
        "krasnodar": "FK Krasnodar",
        "krylia sovetov": "PFK Krylya Sovetov Samara",
        "lokomotiv moscow": "Футбольный клуб \"Локомотив\" Москва",
        "nizhny novgorod": "FK Nizhny Novgorod",
        "rostov": "FK Rostov",
        "rubin kazan": "FC Rubin Kazan",
        "sochi": "FK Sochi",
        "spartak moscow": "FK Spartak Moskva",
        "zenit st petersburg": "AO FK Zenit Sankt-Peterburg",
        # ── Denmark ─────────────────────────────────
        "agf": "Aarhus Gymnastik Forening",
        "brøndby if": "Brøndby Idrætsforening",
        "f.c. københavn": "Football Club København",
        "fc fredericia": "Fodbold Club Fredericia",
        "fc midtjylland": "Fodbold Club Midtjylland",
        "fc nordsjælland": "Fodbold Club Nordsjælland",
        "randers fc": "Randers Fodbold Club",
        "silkeborg if": "Silkeborg Idrætsforening",
        "viborg ff": "Viborg Fodsports Forening",
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
                    fix_date = wib_dt.strftime("%Y-%m-%d")
                    fix_time = wib_dt.strftime("%H:%M")
                    # Skip jika sudah lewat
                    if wib_dt < now_dt:
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


    # ── J2 League dari cache lokal ────────────────────────────
    j2_fixtures = load_j2_fixtures()
    if j2_fixtures:
        liga   = "J2_League"
        DC     = v20["dc_params"].get(liga, {})
        model_teams = list(DC.get("attack", {}).keys())
        for fix in j2_fixtures:
            try:
                fix_date = fix["date"]
                fix_time = fix.get("time", "12:00")
                home_model = fix["home"]
                away_model = fix["away"]
                if home_model not in model_teams or away_model not in model_teams:
                    continue
                # Skip jika sudah lewat
                try:
                    fix_dt = _dt.datetime.strptime(
                        f"{fix_date} {fix_time}", "%Y-%m-%d %H:%M")
                    if fix_dt < now_dt:
                        continue
                except:
                    pass
                result = predict_match(v20, home_model, away_model, liga)
                if result and result["tier"] == "SNIPER":
                    sniper_picks.append({
                        "date"  : fix_date,
                        "time"  : fix_time,
                        "liga"  : liga,
                        "home"  : home_model,
                        "away"  : away_model,
                        "result": result,
                    })
            except Exception as ex:
                print(f"[Bot] J2 cache error: {ex}")

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
        f"\U0001f916 Model V20.5.2 | Dixon-Coles + Elo\n"
        f"<i>Shadow mode — bukan saran finansial</i>", token
    )


def run_bot():
    """Long polling — jalankan di Colab"""
    v20 = load_model()
    if not v20:
        print("❌ Model tidak ditemukan"); return
    _notif_store     = _load_notif_store()  # persistent — chat_id -> jam WIB
    _last_notif_date = {}                   # chat_id -> date terakhir kirim
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
                chat_id  = msg["chat"]["id"]
                text     = msg.get("text","").strip()
                username = msg.get("from",{}).get("username","?")
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
                elif text.startswith("/form"):
                    cmd_form(chat_id, v20, TELEGRAM_TOKEN, text[5:].strip())
                elif text.startswith("/h2h"):
                    cmd_h2h(chat_id, v20, TELEGRAM_TOKEN, text[4:].strip())
                elif text.startswith("/history"):
                    cmd_history(chat_id, TELEGRAM_TOKEN)
                elif text.startswith("/akurasi"):
                    cmd_akurasi(chat_id, TELEGRAM_TOKEN)
                elif text.startswith("/hasil"):
                    cmd_hasil(chat_id, TELEGRAM_TOKEN, text[6:].strip())
                elif text.startswith("/today"):
                    cmd_today(chat_id, v20, TELEGRAM_TOKEN)
                elif text.startswith("/notif"):
                    cmd_notif_set(chat_id, TELEGRAM_TOKEN, text[6:].strip(), _notif_store)
                    _save_notif_store(_notif_store)
                else:
                    send(chat_id,
                        "❓ Perintah tidak dikenal\n\n"
                        "Ketik /help untuk daftar perintah", TELEGRAM_TOKEN
                    )

            # ── Notifikasi harian — cek setiap selesai polling ──────
            try:
                now_wib  = datetime.utcnow() + timedelta(hours=7)
                now_time = now_wib.strftime("%H:%M")
                now_date = now_wib.date()
                for cid_str, jam in list(_notif_store.items()):
                    cid = int(cid_str)
                    # Kirim jika: jam cocok (toleransi 1 menit) DAN belum kirim hari ini
                    if (now_time == jam or
                        (abs(int(now_time.replace(":","")) -
                             int(jam.replace(":",""))
                        ) <= 1)):
                        last = _last_notif_date.get(cid_str)
                        if last != str(now_date):
                            print(f"[Notif] Kirim picks ke {cid_str} jam {jam}")
                            send(cid,
                                f"⏰ <b>Notifikasi Harian — {now_wib.strftime('%d %b %Y')}</b>\n"
                                f"Berikut SNIPER picks untuk hari ini:",
                                TELEGRAM_TOKEN
                            )
                            cmd_picks(cid, v20, TELEGRAM_TOKEN)
                            _last_notif_date[cid_str] = str(now_date)
            except Exception as ne:
                print(f"[Notif] Error: {ne}")

        except KeyboardInterrupt:
            print("\n⏹ Bot dihentikan")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

# Weekly picks (dipanggil GitHub Actions)
def cmd_today(chat_id, v20, token):
    """SNIPER picks hari ini (sekarang WIB) hingga besok 23:59 WIB"""
    import datetime as _dt
    now_wib  = _dt.datetime.utcnow() + _dt.timedelta(hours=7)
    end_wib  = (now_wib + _dt.timedelta(days=1)).replace(
                    hour=23, minute=59, second=59, microsecond=0)
    today    = now_wib.date()

    send(chat_id,
        f"\U0001f3af <b>SNIPER Picks — Hari Ini &amp; Besok</b>\n"
        f"\U0001f4c5 {now_wib.strftime('%d %b %Y %H:%M')} s/d "
        f"{end_wib.strftime('%d %b %Y %H:%M')} WIB\n"
        f"\u23f3 Generating...", token
    )

    LIGA_ESPN_LOCAL = {
        "EPL":"eng.1","Bundesliga":"ger.1","Serie_A":"ita.1",
        "La_Liga":"esp.1","Ligue_1":"fra.1","Eredivisie":"ned.1",
        "Liga_Portugal":"por.1","Super_Lig":"tur.1","Belgium":"bel.1",
        "Scotland":"sco.1","Greece":"gre.1","J1_League":"jpn.1",
        "Brazil":"bra.1","Venezuela":"ven.1","Russia":"rus.1",
        "Denmark":"den.1",
        "UCL":"uefa.champions",
    }

    BLACKLIST_PAIRS = [
        ("paris fc", "paris sg"), ("paris fc", "paris saint"),
        ("estudiantes de merida", "estudiantes caracas"),
        ("atletico", "athletic"),
        ("sporting cp", "sporting clube de braga"),
        ("sporting cp", "braga"),
    ]

    ESPN_TO_MODEL = {
        "fc barcelona":"Barcelona","barcelona":"Barcelona",
        "atlético madrid":"Atletico Madrid","atletico madrid":"Atletico Madrid",
        "atletico de madrid":"Atletico Madrid","atlético de madrid":"Atletico Madrid",
        "galatasaray":"Galatasaray","galatasaray sk":"Galatasaray",
        "atalanta":"Atalanta","atalanta bc":"Atalanta",
        "rb salzburg":"RB Salzburg","red bull salzburg":"RB Salzburg",
        "monaco":"Monaco","as monaco":"Monaco",
        "benfica":"Sport Lisboa e Benfica","sl benfica":"Sport Lisboa e Benfica",
        "girona":"Girona","girona fc":"Girona",
        "brest":"Brest","stade brestois 29":"Brest",
        "bologna":"Bologna","bologna fc":"Bologna",
        "lille":"LOSC Lille","losc lille":"LOSC Lille",
        "villarreal":"Villarreal","villarreal cf":"Villarreal",
        "sturm graz":"Sturm Graz","slovan bratislava":"Slovan Bratislava",
        "young boys":"Young Boys","bsc young boys":"Young Boys",
        "dinamo zagreb":"Dinamo Zagreb","gnk dinamo":"GNK Dinamo",
        "shakhtar donetsk":"Shakhtar Donetsk",
        "red star belgrade":"Red Star Belgrade","crvena zvezda":"Red Star Belgrade",
        "real madrid":"Real Madrid","real madrid cf":"Real Madrid",
        "fc bayern münchen":"Bayern Munich","fc bayern munich":"Bayern Munich",
        "paris saint-germain":"Paris SG","paris sg":"Paris SG","psg":"Paris SG",
        "borussia dortmund":"Dortmund","internazionale":"Inter","inter milan":"Inter",
        "manchester city":"Man City","manchester united":"Man United",
        "juventus":"Juventus","liverpool":"Liverpool","arsenal":"Arsenal",
        "chelsea":"Chelsea","tottenham hotspur":"Tottenham",
        "bayer leverkusen":"Leverkusen","rb leipzig":"RB Leipzig",
        "sevilla fc":"Sevilla","fc porto":"Futebol Clube do Porto",
        "sporting cp":"Sporting Clube de Portugal","ajax":"Ajax",
        "psv eindhoven":"PSV Eindhoven","feyenoord":"Feyenoord",
        "newcastle united":"Newcastle","aston villa":"Aston Villa",
        "club brugge":"Club Brugge","celtic":"Celtic",
        "afc bournemouth":"Bournemouth","brighton & hove albion":"Brighton",
        "nottingham forest":"Nott'm Forest","west ham united":"West Ham",
        "wolverhampton wanderers":"Wolves","leeds united":"Leeds",
        "borussia monchengladbach":"M'gladbach","borussia mönchengladbach":"M'gladbach",
        "eintracht frankfurt":"Ein Frankfurt","fc augsburg":"Augsburg",
        "fc cologne":"FC Koln","hamburg sv":"Hamburg",
        "1. fc heidenheim 1846":"Heidenheim","1. fc union berlin":"Union Berlin",
        "sc freiburg":"Freiburg","st. pauli":"St Pauli",
        "tsg hoffenheim":"Hoffenheim","vfb stuttgart":"Stuttgart","vfl wolfsburg":"Wolfsburg",
        "ac milan":"Milan","as roma":"Roma","hellas verona":"Verona",
        "athletic club":"Ath Bilbao","alavés":"Alaves","alaves":"Alaves",
        "celta vigo":"Celta","espanyol":"Espanol","rayo vallecano":"Vallecano",
        "real betis":"Betis","real oviedo":"Oviedo","real sociedad":"Sociedad",
        "stade rennais":"Rennes","aj auxerre":"Auxerre","le havre ac":"Le Havre",
        "paris fc":"Paris FC",
        "ajax amsterdam":"Ajax","fc groningen":"Groningen","fc twente":"Twente",
        "fc utrecht":"Utrecht","fc volendam":"Volendam",
        "feyenoord rotterdam":"Feyenoord","fortuna sittard":"For Sittard",
        "heracles almelo":"Heracles","nec nijmegen":"Nijmegen","pec zwolle":"Zwolle",
        "braga":"Sporting Clube de Braga",
        "fc famalicao":"Futebol Clube de Famalicão",
        "vitória de guimaraes":"Vitória Sport Clube",
        "estoril":"Grupo Desportivo Estoril Praia",
        "estrela":"Club Football Estrela da Amadora",
        "arouca":"Futebol Clube de Arouca",
        "casa pia":"Casa Pia Atlético Clube","alverca":"Futebol Clube de Alverca",
        "rio ave":"Rio Ave Futebol Clube","santa clara":"Clube Desportivo Santa Clara",
        "moreirense":"Moreirense Futebol Clube","avs":"AVS Futebol SAD",
        "gil vicente":"Gil Vicente Futebol Clube","tondela":"Clube Desportivo de Tondela",
        "c.d. nacional":"Clube Desportivo Nacional",
        "goztepe":"Goztep","istanbul basaksehir":"Buyuksehyr",
        "fatih karagümrük":"Karagumruk","fatih karagumruk":"Karagumruk",
        "caykur rizespor":"Rizespor","gaziantep fk":"Gaziantep",
        "kocaelispor":"Kocaelispor Kulübü","genclerbirligi":"Gençlerbirliği Spor Kulübü",
        "anderlecht":"Royal Sporting Club Anderlecht",
        "antwerp":"Royal Antwerp Football Club",
        "cercle brugge ksv":"Cercle Brugge Koninklijke Sportvereniging",
        "club brugge kv":"Club Brugge Koninklijke Voetbalvereniging",
        "dender":"FC Verbroedering Denderhoutem Denderleeuw Eendracht Hekelgem",
        "kaa gent":"Koninklijke Atletiek Associatie Gent",
        "kv mechelen":"Yellow-Red Koninklijke Voetbalclub Mechelen",
        "kvc westerlo":"Koninklijke Voetbal Club Westerlo",
        "oh leuven":"Oud-Heverlee Leuven","racing genk":"Koninklijke Racing Club Genk",
        "royal charleroi sc":"Royal Charleroi Sporting Club",
        "sint-truidense":"Koninklijke Sint-Truidense Voetbalvereniging",
        "standard liege":"Royal Standard Club de Liège",
        "union st.-gilloise":"Royale Union Saint-Gilloise",
        "zulte-waregem":"Sportvereniging Zulte Waregem",
        "aberdeen":"Aberdeen Football Club","celtic fc":"The Celtic Football Club",
        "rangers":"Rangers Football Club",
        "heart of midlothian":"Heart of Midlothian Football Club",
        "hibernian":"Hibernian Football Club","kilmarnock":"Kilmarnock Football Club",
        "livingston":"Livingston Football Club","motherwell":"Motherwell Football Club",
        "dundee":"Dundee Football Club","dundee united":"Dundee United Football Club",
        "falkirk":"Falkirk Football & Athletic Club",
        "st mirren":"Saint Mirren Football Club",
        "olympiacos":"Olympiakos Syndesmos Filathlon Peiraios",
        "aek athens":"Athlitiki Enosi Konstantinoupoleos",
        "paok salonika":"Panthessalonikios Athlitikos Omilos Konstantinoupoliton",
        "panathinaikos":"Panathinaikos Athlitikos Omilos",
        "aris":"Aris Thessalonikis","atromitos":"APS Atromitos Athinon",
        "levadiakos":"APO Levadiakos Football Club",
        "ofi crete":"Omilos Filathlon Irakliou FC",
        "volos nfc":"Volou Neos Podosferikos Syllogos",
        "kifisia":"Athlitiki Enosi Kifisias","asteras tripoli":"A.G.S Asteras Tripolis",
        "panserraikos fc":"Panserraikos Serres","larissa fc":"Athlitiki Enosi Larisas",
        "panetolikos":"Panetolikos Agrinio",
        "tokyo verdy 1969":"Verdy","kyoto sanga":"Kyoto",
        "urawa red diamonds":"Urawa Reds",
        "jef united ichihara-chiba":"JEF United","mito hollyhock":"Mito HollyHock",
        "hokkaido consadole sapporo":"Sapporo",
        "machida zelvia":"Machida Zelvia","fagiano okayama":"Fagiano Okayama",
        "jef united":"JEF United","jef united ichihara chiba":"JEF United",
        "ventforet kofu":"Ventforet Kofu","albirex niigata":"Albirex Niigata",
        "roasso kumamoto":"Roasso Kumamoto","blaublitz akita":"Blaublitz Akita",
        "grulla morioka":"Grulla Morioka","renofa yamaguchi":"Renofa Yamaguchi",
        "tochigi sc":"Tochigi SC","thespakusatsu gunma":"Thespakusatsu Gunma",
        "giravanz kitakyushu":"Giravanz Kitakyushu","fc ryukyu":"FC Ryukyu",
        "ehime fc":"Ehime FC","jubilo iwata":"Jubilo Iwata",
        "kataller toyama":"Kataller Toyama","iwaki fc":"Iwaki FC",
        "fc imabari":"FC Imabari","fujieda myfc":"Fujieda MYFC",
        "kagoshima united":"Kagoshima United","sc sagamihara":"SC Sagamihara",
        "toolbox kanazawa":"Toolbox Kanazawa","montedio yamagata":"Montedio Yamagata",
        "omiya ardija":"Omiya Ardija",
        "red bull bragantino":"RB Bragantino","vasco da gama":"Vasco",
        "remo":"Clube do Remo","clube do remo":"Clube do Remo",
        "academia anzoátegui":"Dep. Anzoátegui",
        "academia puerto cabello":"Puerto Cabello","caracas fc":"Caracas",
        "deportivo la guaira":"La Guaira","deportivo rayo zuliano":"Rayo Zuliano",
        "deportivo táchira":"Dep. Táchira","estudiantes de mérida":"Estudiantes M.",
        "metropolitanos fc":"Metropolitanos","monagas sc":"Monagas",
        "akhmat grozny":"RFK Akhmat Grozny","akron tolyatti":"Akron Togliatti",
        "cska moscow":"PFK CSKA Moskva","dinamo moscow":"FK Dinamo Moskva",
        "dynamo makhachkala":"Dinamo Makhachkala",
        "fc baltika kaliningrad":"FK Baltika","gazovik orenburg":"FC Orenburg",
        "krasnodar":"FK Krasnodar","krylia sovetov":"PFK Krylya Sovetov Samara",
        "lokomotiv moscow":"Футбольный клуб \"Локомотив\" Москва",
        "nizhny novgorod":"FK Nizhny Novgorod","rostov":"FK Rostov",
        "rubin kazan":"FC Rubin Kazan","sochi":"FK Sochi",
        "spartak moscow":"FK Spartak Moskva",
        "zenit st petersburg":"AO FK Zenit Sankt-Peterburg",
        "agf":"Aarhus Gymnastik Forening","brøndby if":"Brøndby Idrætsforening",
        "f.c. københavn":"Football Club København",
        "fc fredericia":"Fodbold Club Fredericia",
        "fc midtjylland":"Fodbold Club Midtjylland",
        "fc nordsjælland":"Fodbold Club Nordsjælland",
        "randers fc":"Randers Fodbold Club","silkeborg if":"Silkeborg Idrætsforening",
        "viborg ff":"Viborg Fodsports Forening",
    }

    def find_model_team(espn_name, model_teams):
        en = espn_name.lower().strip()
        if en in ESPN_TO_MODEL:
            mapped = ESPN_TO_MODEL[en]
            if mapped in model_teams:
                return mapped
        for t in model_teams:
            if t.lower() == en:
                return t
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
        en = espn_name.lower(); mn = model_name.lower()
        for bl1, bl2 in BLACKLIST_PAIRS:
            if bl1 in en and bl2 in mn: return True
            if bl2 in en and bl1 in mn: return True
        return False

    # ── Window: date_from=hari ini, date_to=besok ─────────────
    date_from = now_wib.strftime("%Y%m%d")
    date_to   = (now_wib + _dt.timedelta(days=1)).strftime("%Y%m%d")

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
                try:
                    utc_dt   = _dt.datetime.strptime(raw_date[:16], "%Y-%m-%dT%H:%M")
                    wib_dt   = utc_dt + _dt.timedelta(hours=7)
                    fix_date = wib_dt.strftime("%Y-%m-%d")
                    fix_time = wib_dt.strftime("%H:%M")
                    # ── Filter window ketat WIB ──────────────
                    if wib_dt < now_wib:
                        continue   # sudah lewat atau kurang dari sekarang
                    if wib_dt > end_wib:
                        continue   # lewat batas besok 23:59
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
                        "date": fix_date, "time": fix_time,
                        "liga": liga, "home": espn_home, "away": espn_away,
                        "result": result,
                    })
        except Exception as ex:
            print(f"[Today] Error {liga}: {ex}")

    # ── J2 dari cache lokal ───────────────────────────────────
    j2_fixtures = load_j2_fixtures()
    if j2_fixtures:
        liga = "J2_League"
        DC   = v20["dc_params"].get(liga, {})
        model_teams = list(DC.get("attack", {}).keys())
        for fix in j2_fixtures:
            try:
                fix_date  = fix["date"]
                fix_time  = fix.get("time", "12:00")
                home_model = fix["home"]
                away_model = fix["away"]
                if home_model not in model_teams or away_model not in model_teams:
                    continue
                try:
                    fix_dt = _dt.datetime.strptime(f"{fix_date} {fix_time}", "%Y-%m-%d %H:%M")
                    if fix_dt < now_wib or fix_dt > end_wib:
                        continue
                except:
                    pass
                result = predict_match(v20, home_model, away_model, liga)
                if result and result["tier"] == "SNIPER":
                    sniper_picks.append({
                        "date": fix_date, "time": fix_time,
                        "liga": liga, "home": home_model, "away": away_model,
                        "result": result,
                    })
            except Exception as ex:
                print(f"[Today] J2 error: {ex}")

    sniper_picks.sort(key=lambda x: (x["date"], x["time"] or "99:99"))

    if not sniper_picks:
        send(chat_id,
            f"\U0001f4ed Tidak ada SNIPER picks\n"
            f"{now_wib.strftime('%d %b %Y %H:%M')} s/d "
            f"{end_wib.strftime('%d %b %Y %H:%M')} WIB", token)
        return

    PRED_LABEL_LOCAL = {"home_win":"MENANG KANDANG","draw":"SERI","away_win":"MENANG TANDANG"}
    PRED_ICON_LOCAL  = {"home_win":"\U0001f3e0","draw":"\U0001f91d","away_win":"\u2708\ufe0f"}

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
        f"\U0001f4c5 Window: {now_wib.strftime('%d %b %H:%M')} \u2192 "
        f"{end_wib.strftime('%d %b %H:%M')} WIB\n"
        f"\U0001f916 Model V20.5.2 | Dixon-Coles + Elo\n"
        f"<i>Shadow mode — bukan saran finansial</i>", token
    )


def weekly_report():
    v20=load_model()
    if not v20: return
    now=datetime.now()
    ws=now-timedelta(days=now.weekday()); we=ws+timedelta(days=6)
    send(TELEGRAM_CHAT,
        f"🎯 <b>FOOTBALL SNIPER</b> — Weekly Picks\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 {ws.strftime('%d %b')} – {we.strftime('%d %b %Y')}\n"
        f"🤖 V20.5.2 | 87.4% Backtest Accuracy"
    )
    cmd_picks(TELEGRAM_CHAT, v20, TELEGRAM_TOKEN)

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="weekly":
        weekly_report()
    else:
        run_bot()
