#!/usr/bin/env python3
"""Weekly Picks Bot - Football Sniper V20.4.5"""
import json, math, os, requests
import numpy as np
from scipy.stats import poisson
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN","")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT","")

def load_model():
    for p in ["data/model_v20_complete.json","model_v20_complete.json"]:
        if os.path.exists(p):
            with open(p) as f: return json.load(f)
    raise FileNotFoundError("Model not found")

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("Telegram not configured"); return
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id":TELEGRAM_CHAT,"text":msg,"parse_mode":"HTML"}
    )
    print(f"Telegram status: {r.status_code}")

def predict(v20, home, away, liga):
    DC = v20["dc_params"].get(liga,{})
    if not DC or home not in DC.get("attack",{}) or away not in DC.get("attack",{}):
        return None
    atk,dfn,hfa,rho = DC["attack"],DC["defense"],DC["hfa"],DC["rho"]
    lh = math.exp(atk[home]+dfn[away]+hfa)
    la = math.exp(atk[away]+dfn[home])
    M  = np.zeros((9,9))
    for gh in range(9):
        for ga in range(9):
            if   gh==0 and ga==0: tau=max(1-lh*la*rho,1e-10)
            elif gh==1 and ga==0: tau=1+la*rho
            elif gh==0 and ga==1: tau=1+lh*rho
            elif gh==1 and ga==1: tau=1-rho
            else: tau=1.0
            M[gh,ga]=tau*poisson.pmf(gh,lh)*poisson.pmf(ga,la)
    M /= M.sum()
    hw=float(np.sum(np.tril(M,-1))); dr=float(np.sum(np.diag(M))); aw=float(np.sum(np.triu(M,1)))
    ELO=v20["elo"].get(liga,{})
    rh_=ELO.get(home,1500)+50; ra_=ELO.get(away,1500)
    eh=1/(1+10**((ra_-rh_)/400)); ea=1-eh
    edr=max(0.18,0.35-abs(eh-ea)*0.5)
    BOOST=v20["draw_boost"].get(liga,1.431)
    ph=0.55*hw+0.45*eh*(1-edr)
    pd=(0.55*dr+0.45*edr)*BOOST
    pa=0.55*aw+0.45*ea*(1-edr)
    t=ph+pd+pa; ph/=t; pd/=t; pa/=t
    conf=max(ph,pd,pa)
    pred=["home_win","draw","away_win"][[ph,pd,pa].index(conf)]
    thr=v20["sniper_threshold"].get(liga,0.65)
    return {"pred":pred,"conf":round(conf,4),
            "tier":"SNIPER" if conf>=thr else "HOLD",
            "ph":round(ph,3),"pd":round(pd,3),"pa":round(pa,3)}

def weekly_report(v20):
    lines=[]
    lines.append(f"<b>Football Sniper Weekly Picks</b>")
    lines.append(f"<b>{datetime.now().strftime('%d %B %Y')}</b>")
    lines.append("=" * 28)
    total=0
    for liga in v20.get("active_leagues",[]):
        DC=v20["dc_params"].get(liga,{})
        teams=sorted(DC.get("attack",{}).keys())
        if len(teams)<2: continue
        ELO=v20["elo"].get(liga,{})
        top=sorted(teams,key=lambda t:-ELO.get(t,1500))[:6]
        picks=[]
        seen=set()
        for h in top:
            for a in top:
                if h==a or (h,a) in seen: continue
                seen.add((h,a))
                r=predict(v20,h,a,liga)
                if r and r["tier"]=="SNIPER":
                    picks.append((h,a,r))
        if picks:
            lines.append(f"\n<b>{liga}</b>")
            for h,a,r in picks[:2]:
                pm={"home_win":f"H {h[:14]}","draw":"Draw","away_win":f"A {a[:14]}"}
                lines.append(f"  {h[:12]} vs {a[:12]}")
                lines.append(f"  -> {pm[r['pred']]} ({r['conf']*100:.1f}%)")
                total+=1
    lines.append(f"\n{'='*28}")
    lines.append(f"SNIPER picks: {total}")
    lines.append("Shadow mode only - not financial advice")
    return "\n".join(lines)

if __name__=="__main__":
    print(f"Weekly picks - {datetime.now()}")
    v20=load_model()
    msg=weekly_report(v20)
    print(msg)
    send_telegram(msg)
