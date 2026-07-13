#!/usr/bin/env python3
"""Geocode comp addresses for the map and compute straight-line distance from the
subject. Census (best for US street addresses) first, then Nominatim fallback.

Usage:
    python geocode.py config.json        # prints lat/lng/dist; writes config back with coords

Reads cfg['subject']['lat'/'lng'] as the distance anchor (set it first — for a
brand-new building CoStar/Census may miss it; anchor off a known adjacent point).
Each comp must have an 'address'. Writes lat/lng/dist into each comp and re-saves
the config. ALWAYS eyeball the printed distances against your submarket clustering —
TIGER/Nominatim can mis-hit; hand-fix obvious outliers in the config.
"""
import sys, json, math, time, urllib.request, urllib.parse

def census(a):
    base='https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'
    q=urllib.parse.urlencode({'address':a,'benchmark':'Public_AR_Current','format':'json'})
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(base+'?'+q,headers={'User-Agent':'tmg/1.0'}),timeout=25))
        m=r['result']['addressMatches']
        if m: return (m[0]['coordinates']['y'],m[0]['coordinates']['x'])
    except Exception: pass
    return None

def nomi(a):
    url='https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=us&q='+urllib.parse.quote(a)
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'tmg-map/1.0'}),timeout=20))
        if r: return (float(r[0]['lat']),float(r[0]['lon']))
    except Exception: pass
    return None

def hav(a,b):
    R=3958.8; la1,lo1,la2,lo2=map(math.radians,[a[0],a[1],b[0],b[1]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*R*math.asin(math.sqrt(h))

def main(cfg_path):
    cfg=json.load(open(cfg_path)); sub=(cfg["subject"]["lat"],cfg["subject"]["lng"])
    for rec in cfg["comps"]:
        if rec.get("lat") and rec.get("lng"):
            src="config"; c=(rec["lat"],rec["lng"])
        else:
            a=rec.get("address","")
            c=census(a); src="census"
            if not c: c=nomi(a); src="nomi"; time.sleep(1.1)
        if c:
            rec["lat"],rec["lng"]=round(c[0],6),round(c[1],6)
            rec["dist"]=round(hav(sub,c),1)
        print(f'{rec["name"][:36]:37} {src:7} ({rec.get("lat")},{rec.get("lng")})  dist={rec.get("dist")}mi')
    json.dump(cfg,open(cfg_path,"w"),indent=1)
    print("updated",cfg_path)

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    main(sys.argv[1])
