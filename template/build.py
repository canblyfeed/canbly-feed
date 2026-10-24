import json,sys,os,html
T=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(T)
d=json.load(open(sys.argv[1])); OUT=sys.argv[2]; F=os.path.join(R,'node_modules/pretendard/dist/web/static/woff2'); I=os.path.join(T,'icon.svg')
e=html.escape; br=lambda L:'<br>'.join(e(x) for x in L)
N=2+len(d['items'])
css=f"""@font-face{{font-family:P;src:url(file://{F}/Pretendard-Medium.woff2);font-weight:500}}
@font-face{{font-family:P;src:url(file://{F}/Pretendard-Bold.woff2);font-weight:700}}
@font-face{{font-family:P;src:url(file://{F}/Pretendard-ExtraBold.woff2);font-weight:800}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:P;letter-spacing:-0.025em;background:#000}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;color:#fff;margin-bottom:10px;
background:radial-gradient(900px 700px at 70% 18%,#1d4a3c 0%,rgba(29,74,60,0) 60%),linear-gradient(180deg,#16211c 0%,#0f1512 100%)}}
.tag{{display:inline-block;border:3px solid #1FC28B;color:#1FC28B;font-weight:800;font-size:28px;letter-spacing:.06em;padding:10px 24px;border-radius:40px}}
.ttl{{font-size:96px;font-weight:800;line-height:1.2;margin-top:34px}}
.bottom{{position:absolute;left:84px;right:84px;bottom:110px}}
.card{{background:#fff;color:#1B2430;border-radius:30px;box-shadow:0 30px 60px rgba(0,0,0,.45)}}
.stk{{position:absolute;font-weight:800;border-radius:16px;padding:14px 26px;font-size:40px;box-shadow:0 14px 30px rgba(0,0,0,.35)}}
.foot{{position:absolute;left:84px;right:84px;bottom:52px;display:flex;justify-content:space-between;font-size:26px;font-weight:700;opacity:.55}}
.tile{{position:absolute;width:118px;height:118px;border-radius:30px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 14px 30px rgba(0,0,0,.4)}}
.tile img{{width:100px}}
.row{{display:flex;gap:20px;align-items:flex-start;font-size:40px;font-weight:700;line-height:1.4;padding:20px 0;border-bottom:2px solid #EEF0F3}}
.row:last-child{{border-bottom:0}}
.mk{{flex:0 0 52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:800;color:#fff;margin-top:2px}}
.x{{background:#E5484D}}.v{{background:#1FC28B}}
.lab{{font-size:28px;font-weight:800;margin-bottom:8px}}"""
def foot(i): return f'<div class="foot"><span>캔블리 · @can_bly_official</span><span>{i}/{N}</span></div>'
c=d['cover']
cover=f"""<section class="s">
<div class="card" style="position:absolute;left:150px;top:150px;width:720px;height:560px;transform:rotate(-4deg);overflow:hidden">
 <div style="height:58px;background:#F1F3F6;display:flex;align-items:center;gap:12px;padding:0 26px"><i style="width:18px;height:18px;border-radius:50%;background:#FF5F57"></i><i style="width:18px;height:18px;border-radius:50%;background:#FEBC2E"></i><i style="width:18px;height:18px;border-radius:50%;background:#28C840"></i><span style="margin-left:20px;flex:1;height:28px;border-radius:14px;background:#fff"></span></div>
 <div style="margin:30px;height:200px;border-radius:18px;background:linear-gradient(135deg,#cfd6df,#9aa6b4)"></div>
 <div style="margin:0 30px;height:26px;width:60%;border-radius:8px;background:#E3E7EC"></div>
 <div style="margin:16px 30px;height:26px;width:42%;border-radius:8px;background:#E3E7EC"></div>
 <div style="margin:30px;height:70px;width:240px;border-radius:14px;background:#E3E7EC"></div>
</div>
<div class="card" style="position:absolute;right:110px;top:420px;width:400px;padding:34px 38px;transform:rotate(3deg)">
 <div style="font-size:30px;font-weight:700;color:#6B7480">{e(c['stat_label'])}</div>
 <div style="font-size:120px;font-weight:800;color:#E5484D;line-height:1.1">{e(c['stat_value'])}</div>
 <div style="height:16px;border-radius:8px;background:#EEF0F3;margin-top:14px"></div>
</div>
<div class="tile" style="left:96px;top:96px;transform:rotate(-8deg)"><img src="file://{I}"></div>
<div class="stk" style="left:110px;top:640px;background:#1FC28B;color:#0f1512;transform:rotate(-6deg)">{e(c['sticker2'])}</div>
<div class="stk" style="right:120px;top:300px;background:#fff;color:#E5484D;border:4px solid #E5484D;transform:rotate(5deg)">{e(c['sticker'])}</div>
<div class="bottom"><span class="tag">{e(d['tag'])}</span><div class="ttl">{br(d['title'])}</div></div>{foot(1)}</section>"""
inner=''
for k,it in enumerate(d['items']):
    rows=lambda L,cl,m:''.join(f'<div class="row"><span class="mk {cl}">{m}</span><span>{e(x)}</span></div>' for x in L)
    inner+=f"""<section class="s"><div style="position:absolute;left:84px;right:84px;top:110px">
<span class="tag">{e(d.get("item_label","이유"))} {k+1:02d}</span><div class="ttl" style="font-size:78px">{br(it['title'])}</div>
<div class="card" style="margin-top:56px;padding:30px 40px"><div class="lab" style="color:#E5484D">{e(d.get("bad_label","이런 상태라면"))}</div>{rows(it['bad'],'x','✕')}</div>
<div class="card" style="margin-top:26px;padding:30px 40px;border:5px solid #1FC28B"><div class="lab" style="color:#13A374">{e(d.get("good_label","이렇게 바꾸세요"))}</div>{rows(it['good'],'v','✓')}</div>
</div>{foot(k+2)}</section>"""
t=d['cta']
checks=''.join(f'<div class="row"><span class="mk" style="background:#fff;border:4px solid #1FC28B"></span><span>{e(x)}</span></div>' for x in t['checks'])
cta=f"""<section class="s"><div style="position:absolute;left:84px;right:84px;top:110px">
<span class="tag">{e(t.get("tag","CHECK"))}</span><div class="ttl" style="font-size:78px">{br(t['title'])}</div>
<div class="card" style="margin-top:50px;padding:24px 40px">{checks}</div>
<div style="margin-top:44px;background:#1FC28B;color:#0f1512;font-size:46px;font-weight:800;padding:34px 0;border-radius:24px;text-align:center">{e(t['button'])}</div>
</div>{foot(N)}</section>"""
open(OUT,'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{cover}{inner}{cta}</body></html>')
