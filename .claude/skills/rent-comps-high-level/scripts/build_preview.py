#!/usr/bin/env python3
"""Render a one-page PNG preview of the rent-comp table (per-bedroom SF + rent,
rent heat, submarket-cluster bands) — mirrors the Excel for quick eyeballing.

Usage:
    python build_preview.py config.json [out.png]

Self-contained: needs matplotlib + pandas; uses Liberation Serif / DejaVu Sans
(falls back to matplotlib defaults). Brand palette is inlined.
"""
import sys, json
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

NAVY="#074070"; BLUE="#589BD5"; INK="#1A2B3C"; GRAY="#6F6F70"; LGRAY="#A6A6A6"; BODY="#404040"
SERIF="Liberation Serif"; SANS="DejaVu Sans"
CL_TINTS=["#EAF1F8","#EEEFF2","#ECF3EE","#F3EEF5","#FBF4E6","#EAF3F3"]

def hd(df,key,t90,asof):
    s=df[df["Property Name"]==key]; exe=s[(s["off"]>=t90)&(s["off"]<=asof)]; o={}
    for b in [0,1,2,3]:
        e=exe[exe["Bedrooms"]==b]
        if len(e): o[b]=dict(ask=round(e["Last Asking Rent"].mean()),eff=round(e["Last Effective Rent"].mean()))
    idx=s.sort_values("on").groupby("Unit").tail(1); tot=s["Unit"].nunique()
    o["leased"]=(1-idx["off"].isna().sum()/tot) if tot else None
    return o
def bl(counts,h,f):
    n=d=0.0
    for i,b in enumerate([0,1,2,3]):
        if b in h and counts[i]>0: n+=h[b][f]*counts[i]; d+=counts[i]
    return round(n/d) if d else None

def main(cfg_path, out_path=None):
    cfg=json.load(open(cfg_path)); out_path=out_path or "Rent_Comps_Preview.png"
    df=pd.read_csv(cfg["hellodata_csv"])
    df["off"]=pd.to_datetime(df["Off Market Date"],errors="coerce"); df["on"]=pd.to_datetime(df["On Market Date"],errors="coerce")
    asof=pd.Timestamp(cfg.get("as_of","today")); t90=asof-pd.Timedelta(days=cfg.get("t_days",90))
    def rec2row(rec,subject=False):
        h=hd(df,rec["hd_key"],t90,asof); cnt=rec["counts"]; bsf=rec.get("bed_sf",[None]*4)
        r=dict(nm=rec["name"],yr=rec.get("year"),occ=rec.get("occ_costar"),lsd=h["leased"],
               dist=rec.get("dist",0.0),subj=subject,gsf=rec["avg_sf"],cl=rec.get("cluster",""))
        for i,b in enumerate([0,1,2,3]):
            r[f"sf{b}"]=bsf[i] if cnt[i]>0 else None
            r[f"b{b}"]=h[b]["ask"] if (b in h and cnt[i]>0) else None
        r["gross"]=bl(cnt,h,"ask"); r["eff"]=bl(cnt,h,"eff")
        r["conc"]=(1-r["eff"]/r["gross"]) if (r["gross"] and r["eff"]) else None
        return r
    recs=[rec2row(cfg["subject"],True)]+[rec2row(c) for c in cfg["comps"]]
    comps=[r for r in recs if not r["subj"]]
    clusters=[]
    for r in comps:
        if r["cl"] not in clusters: clusters.append(r["cl"])
    cltint={cl:CL_TINTS[i%len(CL_TINTS)] for i,cl in enumerate(clusters)}
    def scale(key):
        v=[r[key] for r in comps if r[key] is not None]; lo,hi=(min(v),max(v)) if v else (0,1)
        def col(x):
            if x is None: return "#FFFFFF"
            t=(x-lo)/(hi-lo) if hi>lo else .5
            if t<.5: k=t/.5;c0=(0xF6,0xC9,0xBE);c1=(255,255,255)
            else: k=(t-.5)/.5;c0=(255,255,255);c1=(0xC7,0xDC,0xEF)
            return "#%02X%02X%02X"%tuple(round(c0[m]+(c1[m]-c0[m])*k) for m in range(3))
        return col
    hf={c:scale(c) for c in ["b0","b1","b2","b3","gross"]}

    fig=plt.figure(figsize=(13.333,7.5),dpi=170); fig.patch.set_facecolor("white")
    sc=lambda s:"  ".join(ch for ch in s.upper())
    fig.text(0.04,0.965,sc(cfg.get("title","Rent Comps")+" — Rent Comps"),fontfamily=SANS,fontsize=7.4,fontweight="bold",color=BLUE,va="top")
    fig.text(0.04,0.94,"High-Level Breakdown · SF by unit type + HelloData executed rent (heat = rent level)",fontfamily=SERIF,fontsize=17,color=INK,va="top")
    fig.add_artist(Rectangle((0.04,0.90),0.06,0.005,color=NAVY,transform=fig.transFigure))
    C=[("#",0.020,"num",0),("Property",0.135,"nm",0),("Yr",0.028,"yr",0),("Occ",0.035,"occ",0),("Lsd",0.033,"lsd",0)]
    for g,sfk,rk in [("Studio","sf0","b0"),("1 BR","sf1","b1"),("2 BR","sf2","b2"),("3 BR","sf3","b3"),("Gross","gsf","gross")]:
        C.append((g+"|SF",0.046,sfk,1)); C.append((g+"|$",0.052,rk,0))
    C+=[("Eff",0.05,"eff",0),("Conc",0.034,"conc",0),("Dist",0.03,"dist",0)]
    x0=0.04; W=0.93; xs=[x0]
    for _,w,_,_ in C: xs.append(xs[-1]+w*W)
    top=0.84; rh=0.0515
    def fmt(k,v):
        if v is None: return "—"
        if k in("occ","lsd","conc"): return f"{v*100:.0f}%"
        if k in("b0","b1","b2","b3","gross","eff"): return f"${v:,.0f}"
        if k in("sf0","sf1","sf2","sf3","gsf"): return f"{v:,.0f}"
        if k=="dist": return f"{v:.1f}"
        if k=="yr": return f"{int(v)}"
        return str(v)
    yh=top
    for j,(lab,w,k,issf) in enumerate(C):
        fig.add_artist(Rectangle((xs[j],yh-rh*0.92),xs[j+1]-xs[j],rh*0.92,color="#DCE6F1",transform=fig.transFigure))
        parts=lab.split("|"); ha="left" if k=="nm" else "center"; tx=xs[j]+0.003 if k=="nm" else (xs[j]+xs[j+1])/2
        if len(parts)==2:
            fig.text(tx,yh-rh*0.30,parts[0],fontfamily=SANS,fontsize=6.2,fontweight="bold",color=NAVY,va="center",ha="center")
            fig.text(tx,yh-rh*0.66,parts[1],fontfamily=SANS,fontsize=6.8,fontweight="bold",color=NAVY,va="center",ha="center")
        else:
            fig.text(tx,yh-rh*0.46,lab,fontfamily=SANS,fontsize=7.2,fontweight="bold",color=NAVY,va="center",ha=ha)
    def clof(ri):
        if ri==0: return None
        return clusters.index(comps[ri-1]["cl"])
    for ri,r in enumerate(recs):
        y=top-rh*0.92-(ri+1)*rh; cl=clof(ri)
        for j,(lab,w,k,issf) in enumerate(C):
            cx=xs[j]; cw=xs[j+1]-xs[j]
            if r["subj"]: bg="#FFF6E6"
            elif k in hf: bg=hf[k](r[k])
            elif k in("num","nm","yr","occ","lsd") and cl is not None: bg=cltint[clusters[cl]]
            else: bg="#FFFFFF"
            fig.add_artist(Rectangle((cx,y),cw,rh,facecolor=bg,edgecolor="#E5E7EB",lw=0.4,transform=fig.transFigure))
            val=str(ri) if k=="num" and not r["subj"] else ("S" if k=="num" else (r["nm"] if k=="nm" else fmt(k,r.get(k))))
            ha="left" if k=="nm" else "center"; tx=cx+0.003 if k=="nm" else cx+cw/2
            bold=(k=="num" or r["subj"]); fs=7.4 if k=="nm" else (6.6 if issf else 7.2)
            col=LGRAY if (issf and not r["subj"]) else (INK if k in("num","nm") else BODY)
            fig.text(tx,y+rh/2,val[:28],fontfamily=SANS,fontsize=fs,color=col,va="center",ha=ha,fontweight="bold" if bold else "normal")
    # cluster dividers
    boundary=1
    for ci in range(len(clusters)-1):
        boundary+=sum(1 for r in comps if r["cl"]==clusters[ci])
        yb=top-rh*0.92-boundary*rh
        fig.add_artist(Rectangle((x0,yb-0.0006),xs[-1]-x0,0.0013,color="#9AA7B4",transform=fig.transFigure,zorder=6))
    # bedroom section boxes (col indices 5..12)
    ybot=top-rh*0.92-len(recs)*rh
    for gi in range(4):
        a=5+gi*2; b=a+1
        fig.add_artist(Rectangle((xs[a],ybot),xs[b+1]-xs[a],top-ybot,fill=False,edgecolor="#7F7F7F",lw=1.1,transform=fig.transFigure,zorder=5))
    ly=ybot-0.022
    fig.text(0.04,ly,"Lower rent",fontfamily=SANS,fontsize=7.5,color=GRAY,va="center")
    for i in range(18):
        t=i/17
        if t<.5:k=t/.5;c0=(0xF6,0xC9,0xBE);c1=(255,255,255)
        else:k=(t-.5)/.5;c0=(255,255,255);c1=(0xC7,0xDC,0xEF)
        fig.add_artist(Rectangle((0.105+i*0.006,ly-0.011),0.006,0.022,facecolor="#%02X%02X%02X"%tuple(round(c0[m]+(c1[m]-c0[m])*k) for m in range(3)),edgecolor="none",transform=fig.transFigure))
    fig.text(0.105+18*0.006+0.006,ly,"Higher rent   ·   SF = CoStar avg SF by unit type   ·   subject = cream",fontfamily=SANS,fontsize=7.5,color=GRAY,va="center")
    fig.text(0.04,0.05,"Sources: "+cfg.get("sources","HelloData executed rents; CoStar."),fontfamily=SANS,fontstyle="italic",fontsize=7.3,color=GRAY)
    fig.add_artist(Rectangle((0.04,0.04),0.92,0.0014,color="#E5E7EB",transform=fig.transFigure))
    fig.text(0.04,0.026,"The Milestone Group   ·   CONFIDENTIAL & PROPRIETARY",fontfamily=SANS,fontsize=8,color=LGRAY)
    fig.savefig(out_path,dpi=170,facecolor="white"); print("wrote",out_path)

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
