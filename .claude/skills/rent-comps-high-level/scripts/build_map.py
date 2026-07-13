#!/usr/bin/env python3
"""Build a self-contained interactive Leaflet rent-comp map (satellite basemap)
from a deal config + HelloData CSV.

Usage:
    python build_map.py config.json [out.html]

Each comp needs lat/lng in the config (see geocode.py). Subject = gold star;
comps = numbered pins colored by submarket cluster; popups show year, units,
avg SF, CoStar occ / HD leased, T-day gross & effective rent, concession, and a
per-bedroom table (# / SF / rent). Leaflet JS+CSS are inlined from ./lib so the
file is self-contained; only the satellite tiles need internet at open time.
"""
import sys, json, os
import pandas as pd

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
DEFAULT_COLORS = {"SUBJECT":"#B49955","_cycle":["#074070","#189AB4","#70AD47","#8E5BA6","#C0392B"]}

def hd_metrics(df, key, t90, asof):
    s=df[df["Property Name"]==key]; exe=s[(s["off"]>=t90)&(s["off"]<=asof)]; o={}
    for b in [0,1,2,3]:
        e=exe[exe["Bedrooms"]==b]
        if len(e): o[b]=dict(ask=round(e["Last Asking Rent"].mean()),eff=round(e["Last Effective Rent"].mean()))
    idx=s.sort_values("on").groupby("Unit").tail(1); tot=s["Unit"].nunique()
    o["leased"]=round((1-idx["off"].isna().sum()/tot)*100) if tot else None
    return o

def blended(counts,hd,f):
    n=d=0.0
    for i,b in enumerate([0,1,2,3]):
        if b in hd and counts[i]>0: n+=hd[b][f]*counts[i]; d+=counts[i]
    return round(n/d) if d else None

def beds(counts,hd,bedsf):
    lbl=["Studio","1 BR","2 BR","3 BR"]; rows=[]
    for i,b in enumerate([0,1,2,3]):
        if counts[i]>0:
            rows.append(dict(t=lbl[i],n=counts[i],sf=(bedsf[i] if i<len(bedsf) else None),
                             rent=(hd[b]["ask"] if b in hd else None)))
    return rows

def main(cfg_path, out_path=None):
    cfg=json.load(open(cfg_path)); out_path=out_path or "Rent_Comps_Map.html"
    df=pd.read_csv(cfg["hellodata_csv"])
    df["off"]=pd.to_datetime(df["Off Market Date"],errors="coerce")
    df["on"]=pd.to_datetime(df["On Market Date"],errors="coerce")
    asof=pd.Timestamp(cfg.get("as_of","today")); t90=asof-pd.Timedelta(days=cfg.get("t_days",90))

    # assign a color per cluster
    colors=dict(cfg.get("cluster_colors",{})); cyc=DEFAULT_COLORS["_cycle"]; k=0
    for rec in cfg["comps"]:
        cl=rec.get("cluster","")
        if cl not in colors: colors[cl]=cyc[k%len(cyc)]; k+=1
    colors["SUBJECT"]=cfg.get("subject_color",DEFAULT_COLORS["SUBJECT"])

    def mk(rec, n, subject=False):
        hd=hd_metrics(df,rec["hd_key"],t90,asof); counts=rec["counts"]
        g=blended(counts,hd,"ask"); e=blended(counts,hd,"eff")
        return dict(n=("S" if subject else n), name=rec["name"],
                    grp=("SUBJECT" if subject else rec.get("cluster","")),
                    lat=rec["lat"], lng=rec["lng"], yr=rec.get("year"), units=rec.get("units",sum(counts)),
                    sf=rec["avg_sf"], occ=round(rec.get("occ_costar",0)*100) if rec.get("occ_costar") else None,
                    leased=hd.get("leased"), dist=rec.get("dist",0.0), gross=g, eff=e,
                    conc=(round((1-e/g)*100) if (g and e) else None),
                    beds=beds(counts,hd,rec.get("bed_sf",[None]*4)))
    pins=[mk(cfg["subject"],"S",subject=True)]+[mk(r,i+1) for i,r in enumerate(cfg["comps"])]

    lcss=open(os.path.join(LIB,"leaflet.css")).read(); ljs=open(os.path.join(LIB,"leaflet.js")).read()
    HTML=TEMPLATE.replace("__LEAFLET_CSS__",lcss).replace("__LEAFLET_JS__",ljs)\
        .replace("__DATA__",json.dumps(pins)).replace("__COLORS__",json.dumps(colors))\
        .replace("__TITLE__",cfg.get("title","Rent Comps")).replace("__SUB__",cfg.get("submarket",""))\
        .replace("__SRC__",cfg.get("sources",""))\
        .replace("__LEGEND__",legend_html(cfg["comps"],colors))
    open(out_path,"w").write(HTML)
    print(f"wrote {out_path}  ({len(pins)} pins)")

def legend_html(comps,colors):
    seen=[];
    for r in comps:
        cl=r.get("cluster","")
        if cl not in seen: seen.append(cl)
    rows=['<div class="row"><span class="star">&#9733;</span> Subject</div>']
    for cl in seen:
        rows.append(f'<div class="row"><span class="dot" style="background:{colors[cl]}"></span> {cl}</div>')
    return "".join(rows)

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>__TITLE__ — Rent Comps</title>
<style>__LEAFLET_CSS__</style>
<script>__LEAFLET_JS__</script>
<style>
 :root{--navy:#074070;--gold:#B49955;--gray:#6F6F70;--ink:#1A2B3C;}
 html,body{margin:0;height:100%;font-family:Calibri,'Segoe UI',Arial,sans-serif;color:#404040;}
 #wrap{display:flex;flex-direction:column;height:100%;}
 header{background:var(--navy);color:#fff;padding:10px 18px;}
 header .kick{font-size:11px;letter-spacing:3px;color:#B6D6EF;text-transform:uppercase;font-weight:bold;}
 header h1{margin:2px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:600;font-size:22px;}
 header .sub{font-size:12px;color:#cfe0ef;margin-top:2px;}
 #map{flex:1;} footer{background:#f3f4f6;color:var(--gray);font-size:11px;padding:6px 18px;border-top:1px solid #e5e7eb;}
 .legend{background:#fff;padding:9px 11px;border-radius:5px;box-shadow:0 1px 5px rgba(0,0,0,.3);font-size:12px;line-height:1.6;}
 .legend b{font-family:Georgia,serif;color:var(--navy);}
 .legend .row{display:flex;align-items:center;gap:7px;}
 .legend .dot{width:13px;height:13px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #999;}
 .legend .star{color:var(--gold);font-size:16px;line-height:1;}
 .pin{border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.5);color:#fff;font-weight:bold;
      text-align:center;font-family:Calibri,Arial,sans-serif;display:flex;align-items:center;justify-content:center;}
 .pin.sub{background:transparent;border:none;box-shadow:none;font-size:34px;color:var(--gold);
          text-shadow:0 0 3px #fff,0 0 3px #fff,1px 1px 2px rgba(0,0,0,.6);}
 .lp{font-family:Calibri,Arial,sans-serif;} .lp h3{margin:0 0 1px;font-family:Georgia,serif;color:var(--navy);font-size:15px;}
 .lp .grp{font-size:11px;letter-spacing:.5px;text-transform:uppercase;font-weight:bold;margin-bottom:6px;}
 .lp .kv{display:grid;grid-template-columns:auto auto;gap:1px 14px;font-size:12px;margin-bottom:6px;}
 .lp .kv span:nth-child(odd){color:var(--gray);} .lp .kv b{color:var(--ink);}
 .lp table{border-collapse:collapse;font-size:11.5px;width:100%;}
 .lp th{background:#DCE6F1;color:var(--navy);padding:2px 6px;text-align:right;font-size:10.5px;}
 .lp th:first-child{text-align:left;} .lp td{padding:2px 6px;border-bottom:1px solid #eee;text-align:right;}
 .lp td:first-child{text-align:left;color:var(--gray);} .lp .big{font-size:13px;}
</style></head>
<body><div id="wrap">
<header><div class="kick">__TITLE__ &nbsp;—&nbsp; Rent Comps</div>
 <h1>Comp Map &nbsp;·&nbsp; __SUB__</h1>
 <div class="sub">HelloData executed rents &amp; CoStar identity · click any pin for detail · grouped by submarket cluster</div></header>
<div id="map"></div>
<footer>__SRC__ The Milestone Group · Confidential &amp; Proprietary.</footer></div>
<script>
const PINS=__DATA__, GRPCOL=__COLORS__;
const map=L.map('map',{scrollWheelZoom:true});
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:19, attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics'}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,opacity:0.9}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,opacity:0.9}).addTo(map);
const usd=v=>v==null?'—':'$'+v.toLocaleString();
function popup(p){
 let b=p.beds.map(x=>`<tr><td>${x.t}</td><td>${x.n}</td><td>${x.sf?x.sf.toLocaleString():'—'}</td><td>${usd(x.rent)}</td></tr>`).join('');
 return `<div class="lp"><h3>${p.n==='S'?'&#9733; ':''}${p.name}</h3>
  <div class="grp" style="color:${GRPCOL[p.grp]||'#074070'}">${p.grp==='SUBJECT'?'SUBJECT':'Comp '+p.n+' · '+p.grp}</div>
  <div class="kv"><span>Built</span><b>${p.yr||'—'}</b><span>Units</span><b>${p.units||'—'}</b>
   <span>Avg SF</span><b>${p.sf?p.sf.toLocaleString():'—'}</b><span>Distance</span><b>${p.dist} mi</b>
   <span>Occ % (CoStar)</span><b>${p.occ==null?'—':p.occ+'%'}</b><span>Leased % (HD)</span><b>${p.leased==null?'—':p.leased+'%'}</b>
   <span>Gross</span><b class="big">${usd(p.gross)}</b><span>Effective</span><b class="big">${usd(p.eff)}</b>
   <span>Concession</span><b>${p.conc==null?'—':p.conc+'%'}</b><span></span><span></span></div>
  <table><tr><th>Plan</th><th>#</th><th>SF</th><th>Rent</th></tr>${b}</table></div>`;
}
const bounds=[];
PINS.forEach(p=>{bounds.push([p.lat,p.lng]);
 let icon;
 if(p.n==='S'){icon=L.divIcon({className:'',html:`<div class="pin sub">&#9733;</div>`,iconSize:[34,34],iconAnchor:[17,30]});}
 else{const c=GRPCOL[p.grp]||'#074070';icon=L.divIcon({className:'',html:`<div class="pin" style="background:${c};width:26px;height:26px;font-size:13px;">${p.n}</div>`,iconSize:[26,26],iconAnchor:[13,13]});}
 L.marker([p.lat,p.lng],{icon,zIndexOffset:p.n==='S'?1000:0}).addTo(map).bindPopup(popup(p),{maxWidth:300});});
map.fitBounds(bounds,{padding:[55,55]});
const lg=L.control({position:'bottomright'});
lg.onAdd=function(){const d=L.DomUtil.create('div','legend');d.innerHTML=`<b>Legend</b>__LEGEND__`;return d;};
lg.addTo(map);
</script></body></html>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
