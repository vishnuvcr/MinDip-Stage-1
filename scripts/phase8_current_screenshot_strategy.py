from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

OPTION_URLS = {
    "NIFTY": [
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/8f7739cab3f38abdcbc6332a6d0a83e1341326e3/upstox_intraday/NIFTY/NIFTY_2025.parquet",
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/8f7739cab3f38abdcbc6332a6d0a83e1341326e3/upstox_intraday/NIFTY/NIFTY_2026.parquet",
    ],
    "SENSEX": [
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/8f7739cab3f38abdcbc6332a6d0a83e1341326e3/upstox_intraday/SENSEX/SENSEX_2025.parquet",
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/8f7739cab3f38abdcbc6332a6d0a83e1341326e3/upstox_intraday/SENSEX/SENSEX_2026.parquet",
    ],
}
SPOT_URLS = {
    "NIFTY": "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m/resolve/904fbfbf7d448e7007cd3dd197849ba561b30c06/index/NIFTY.parquet",
    "SENSEX": "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m/resolve/904fbfbf7d448e7007cd3dd197849ba561b30c06/index/SENSEX.parquet",
}
RULES = {"NIFTY": {"weekday": 1, "entry_weekday": 2, "interval": 50.0},
         "SENSEX": {"weekday": 3, "entry_weekday": 4, "interval": 100.0}}
CAPITAL, SLIPPAGE, FIXED_COST = 150_000.0, 0.005, 160.0
HOLIDAYS = {}

def q(x): return "'" + x.replace("'", "''") + "'"
def rel(urls): return "read_parquet([" + ",".join(q(x) for x in urls) + "])"

def load_holidays(path: Path, ticker: str):
    df = pd.read_csv(path)
    return set(pd.to_datetime(df.loc[df.Ticker.astype(str).str.upper().eq(ticker), "Date"],
                              errors="coerce").dropna().dt.normalize())

def is_td(d, holidays):
    d = pd.Timestamp(d).normalize()
    return d.weekday() < 5 and d not in holidays

def prev_td(d, holidays):
    d = pd.Timestamp(d).normalize()
    for _ in range(370):
        if is_td(d, holidays): return d
        d -= pd.Timedelta(days=1)
    raise ValueError("no trading day")

def last_weekday(y, m, wd):
    first_next = (pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthBegin(1)).normalize()
    last = first_next - pd.Timedelta(days=1)
    return (last - pd.Timedelta(days=(last.weekday() - wd) % 7)).normalize()

def next_weekly(entry, wd, holidays):
    d = pd.Timestamp(entry).normalize() + pd.Timedelta(days=1)
    for _ in range(60):
        if d.weekday() == wd:
            x = prev_td(d, holidays)
            if x > entry: return x
        d += pd.Timedelta(days=1)
    raise ValueError("weekly expiry not found")

def next_monthly(entry, wd, holidays):
    cur = pd.Timestamp(entry).normalize()
    for _ in range(24):
        x = prev_td(last_weekday(cur.year, cur.month, wd), holidays)
        if x > entry: return x
        cur = (cur + pd.offsets.MonthBegin(1)).normalize()
    raise ValueError("monthly expiry not found")

def nearest_atm(spot, interval):
    return float(np.floor((spot / interval) + 0.5) * interval)

def lot_size(ticker, expiry):
    expiry = pd.Timestamp(expiry).normalize()
    if ticker == "NIFTY": return 75 if expiry <= pd.Timestamp("2025-12-30") else 65
    if ticker == "SENSEX": return 20
    raise ValueError(ticker)

def spot_query(con, ticker, start, end):
    sql = f"""SELECT timestamp,trading_day,symbol,close
              FROM {rel([SPOT_URLS[ticker]])}
              WHERE symbol={q(ticker)}
              AND CAST(trading_day AS DATE) BETWEEN DATE {q(start)} AND DATE {q(end)}
              ORDER BY timestamp"""
    out = con.execute(sql).df()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    out["trading_day"] = pd.to_datetime(out["trading_day"]).dt.normalize()
    return out

def targets(spot, ticker, start, end):
    rule = RULES[ticker]; rows=[]
    for scheduled in pd.date_range(start, end, freq="D"):
        if scheduled.weekday() != rule["entry_weekday"]: continue
        entry = prev_td(scheduled, HOLIDAYS[ticker])
        if not (pd.Timestamp(start) <= entry <= pd.Timestamp(end)): continue
        day = spot[spot.trading_day.eq(entry)].sort_values("timestamp")
        day = day[day.timestamp.dt.time >= pd.Timestamp("09:30:00").time()]
        if day.empty:
            rows.append({"ticker":ticker,"scheduled_entry_date":scheduled,"entry_date":entry,
                         "spot_available":False,"skip_reason":"missing_spot_0930"})
            continue
        r=day.iloc[0]; spot_px=float(r.close)
        rows.append({"ticker":ticker,"scheduled_entry_date":scheduled,"entry_date":entry,
                     "spot_available":True,"skip_reason":"","spot":spot_px,
                     "spot_timestamp":r.timestamp,"atm":nearest_atm(spot_px,rule["interval"])})
    return pd.DataFrame(rows)

def extract(con, cyc, ticker, leg4_k):
    cyc = cyc[cyc.spot_available.eq(True)].copy()
    if cyc.empty: return pd.DataFrame()
    rule=RULES[ticker]; wanted=[]
    for _,c in cyc.iterrows():
        weekly=next_weekly(c.entry_date,rule["weekday"],HOLIDAYS[ticker])
        monthly=next_monthly(c.entry_date,rule["weekday"],HOLIDAYS[ticker])
        specs=[
            ("L1","SELL","PE",monthly,float(c.atm)),
            ("L2","BUY","CE",monthly,float(c.atm - 2*rule["interval"])),
            ("L3","BUY","PE",weekly,float(c.atm + 2*rule["interval"])),
            ("L4","SELL","CE",weekly,float(c.atm)),
        ]
        for leg,side,opt,exp,strike in specs:
            wanted.append({"ticker":ticker,"leg":leg,"side":side,"option_type":opt,
                           "expiry":pd.Timestamp(exp).normalize(),"strike":strike,
                           "entry_date":pd.Timestamp(c.entry_date).normalize(),
                           "weekly_expiry":pd.Timestamp(weekly).normalize(),
                           "monthly_expiry":pd.Timestamp(monthly).normalize(),
                           "scheduled_entry_date":pd.Timestamp(c.scheduled_entry_date).normalize(),
                           "spot":float(c.spot),"atm":float(c.atm),
                           "leg4_itm_strikes":2,"spot_timestamp":c.spot_timestamp})
    w=pd.DataFrame(wanted)
    dates=sorted(set(w.entry_date.dt.strftime("%Y-%m-%d"))|set(w.weekly_expiry.dt.strftime("%Y-%m-%d")))
    exps=sorted(set(w.expiry.dt.strftime("%Y-%m-%d")))
    date_list=",".join("DATE "+q(x) for x in dates); exp_list=",".join("DATE "+q(x) for x in exps)
    sql=f"""SELECT timestamp,CAST(date AS DATE) AS trading_day,underlying AS symbol,
                   CAST(expiry AS DATE) AS expiry,strike,option_type,close
            FROM {rel(OPTION_URLS[ticker])}
            WHERE underlying={q(ticker)}
            AND CAST(date AS DATE) IN ({date_list})
            AND CAST(expiry AS DATE) IN ({exp_list})
            AND ((EXTRACT(HOUR FROM timestamp)=9 AND EXTRACT(MINUTE FROM timestamp) BETWEEN 30 AND 35)
                 OR (EXTRACT(HOUR FROM timestamp)=15 AND EXTRACT(MINUTE FROM timestamp) BETWEEN 10 AND 15))"""
    obs=con.execute(sql).df()
    if obs.empty: return pd.DataFrame()
    obs["timestamp"]=pd.to_datetime(obs["timestamp"]); obs["trading_day"]=pd.to_datetime(obs["trading_day"]).dt.normalize()
    obs["expiry"]=pd.to_datetime(obs["expiry"]).dt.normalize()
    out=[]
    for _,x in w.iterrows():
        cand=obs[obs.symbol.eq(ticker)&obs.expiry.eq(x.expiry)&np.isclose(obs.strike.astype(float),float(x.strike))
                 &obs.option_type.eq(x.option_type)&obs.trading_day.isin([x.entry_date,x.weekly_expiry])].sort_values("timestamp")
        en=cand[cand.trading_day.eq(x.entry_date)&(cand.timestamp.dt.time>=pd.Timestamp("09:30:00").time())]
        ex=cand[cand.trading_day.eq(x.weekly_expiry)&(cand.timestamp.dt.time<=pd.Timestamp("15:15:00").time())]
        r=dict(x)
        if not en.empty:r.update(entry_timestamp=en.iloc[0].timestamp,entry_close=float(en.iloc[0].close))
        if not ex.empty:r.update(exit_timestamp=ex.iloc[-1].timestamp,exit_close=float(ex.iloc[-1].close))
        r["entry_available"]="entry_close" in r; r["exit_available"]="exit_close" in r; out.append(r)
    return pd.DataFrame(out)

def evaluate(legs):
    if legs.empty:return pd.DataFrame()
    out=[]
    for key,g in legs.groupby(["ticker","entry_date","weekly_expiry","monthly_expiry","leg4_itm_strikes"]):
        if set(g.leg)!={"L1","L2","L3","L4"}: continue
        if not (g.entry_available & g.exit_available).all(): continue
        gross=0.0
        for _,r in g.iterrows():
            lot=lot_size(r.ticker,r.expiry); en=float(r.entry_close); ex=float(r.exit_close)
            if r.side=="BUY": gross+=(ex*(1-SLIPPAGE)-en*(1+SLIPPAGE))*lot
            else: gross+=(en*(1-SLIPPAGE)-ex*(1+SLIPPAGE))*lot
        out.append({"ticker":key[0],"entry_date":key[1],"weekly_expiry":key[2],
                    "monthly_expiry":key[3],"leg4_itm_strikes":key[4],
                    "gross_pnl":gross,"fixed_cost":FIXED_COST,"net_pnl":gross-FIXED_COST})
    return pd.DataFrame(out)

def metrics(c):
    if c.empty:return {"trades":0,"net_pnl":0.0,"roc_pct":0.0,"win_rate_pct":0.0,"expectancy":0.0,
                       "max_drawdown":0.0,"max_drawdown_pct":0.0}
    p=c.net_pnl.astype(float); eq=CAPITAL+p.cumsum(); peak=eq.cummax()
    return {"trades":len(p),"net_pnl":float(p.sum()),"roc_pct":float(p.sum()/CAPITAL*100),
            "win_rate_pct":float((p>0).mean()*100),"expectancy":float(p.mean()),
            "max_drawdown":float((eq-peak).min()),"max_drawdown_pct":float(((eq/peak)-1).min()*100)}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for ch in iter(lambda:f.read(1048576),b""):h.update(ch)
    return h.hexdigest()

def demo():
    spot=23329.0; interval=50.0
    atm=nearest_atm(spot,interval)
    return {"spot":spot,"atm":atm,
            "sell_monthly_pe":atm,
            "buy_monthly_ce":atm-2*interval,
            "buy_weekly_pe":atm+2*interval,
            "sell_weekly_ce":atm}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--start",default="2025-10-01"); ap.add_argument("--end",default="2026-05-27")
    ap.add_argument("--output",default="data/cache/phase7"); a=ap.parse_args()
    global HOLIDAYS
    HOLIDAYS={t:load_holidays(Path("data/calendar/exchange_holidays.csv"),t) for t in ("NIFTY","SENSEX")}
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); con.execute("PRAGMA threads=4")
    allm=[]
    for t in ("NIFTY","SENSEX"):
        s=spot_query(con,t,a.start,a.end)
        cy=targets(s,t,a.start,a.end); cy.to_csv(out/f"{t}_target_cycles.csv",index=False)
        for k in (2,):
            lg=extract(con,cy,t,k); lg.to_csv(out/f"{t}_variant{k}_legs.csv",index=False)
            tr=evaluate(lg); tr.to_csv(out/f"{t}_variant{k}_cycles.csv",index=False)
            m=metrics(tr); m.update(ticker=t,leg4_itm_strikes=k,target_cycles=int(len(cy)),
                                  complete_cycles=int(len(tr)),strategy_id=("screenshot_exact" if k==1 else "screenshot_leg4_alt2"))
            allm.append(m)
    pd.DataFrame(allm).to_csv(out/"cross_index_metrics.csv",index=False)
    (out/"screenshot_strike_demo.json").write_text(json.dumps(demo(),indent=2))
    manifest={"start":a.start,"end":a.end,"strategy":"current_uploaded_screenshot","files":{}}
    for p in sorted(out.glob("*")): manifest["files"][p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    (out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print(pd.DataFrame(allm).to_string(index=False))

if __name__=="__main__": main()
