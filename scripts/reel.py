"""reels/<날짜>/reel.json -> reels/<날짜>/reel.mp4 (+ check.jpg 확인용 프레임 모음)
usage: python3 scripts/reel.py reels/2026-11-17

장면(beat)은 기본 1.5초. 각 장면은 아래 키를 조합한다 (reel.json 형식은 CLAUDE.md 참고)
  title / title_color("white"|"green")  : 위쪽 큰 제목 (2줄까지)
  x / v                                   : 위쪽 큰 ✕ / ✓ 항목 (제목 대신)
  compare {bad, good}                     : 위쪽 ✕ 취소선 문구 → ✓ 좋은 문구
  sub                                     : 제목 아래 초록 보조 문구
  screen {site, view, zoom, to_zoom, label, fake, highlight, wipe_from}
                                          : 가운데 PC 브라우저 화면 (assets/sites/<site>/desktop.jpg)
  phone {site, pages, label, fake}        : 가운데 휴대폰 화면 (assets/sites/<site>/m01.jpg ...), pages 여러 장이면 스크롤
  chips [..]                              : 아래쪽 칩 "A + B + C"
  caption                                 : 아래쪽 작은 설명
  next                                    : 다음 편 예고 (마지막 장면)
"""
import sys,os,json,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD=os.path.join(R,'node_modules/pretendard/dist/public/static/')
W,H,FPS=1080,1920,30
G=(31,194,139);RED=(229,72,77);WHITE=(255,255,255);DARK=(15,21,18);SUBC=(217,225,220)
_fc={}
def font(w,s):
    k=(w,s)
    if k not in _fc:_fc[k]=ImageFont.truetype(FD+f'Pretendard-{w}.otf',s)
    return _fc[k]
def ease(t):t=max(0.,min(1.,t));return t*t*(3-2*t)
def A(c,a):return tuple(c)+(int(255*max(0,min(1,a))),)

def background():
    y=np.linspace(0,1,H)[:,None];x=np.linspace(0,1,W)[None,:]
    top=np.array([22,33,28]);bot=np.array([15,21,18]);gl=np.array([29,74,60])
    base=np.stack([top[i]*(1-y)+bot[i]*y+0*x for i in range(3)],-1)
    d=np.sqrt(((x-0.85)*W)**2+((y-0.12)*H)**2);g=(np.clip(1-d/1000,0,1)*0.6)[...,None]
    return Image.fromarray((base*(1-g)+gl*g).astype(np.uint8)).convert('RGBA')

def load_site(site,name):
    return Image.open(os.path.join(R,'assets/sites',site,name)).convert('RGB')
def fake_version(img,fake):
    """fake={"box":[x0,y0,x1,y1],"lines":["Welcome to","Clean Life"],"size":54}: 그 영역을 흐리게 지우고 가짜 문구를 얹는다 (나쁜 예시용)"""
    im=img.copy();b=fake['box'];patch=im.crop(b).filter(ImageFilter.GaussianBlur(28));im.paste(patch,b[:2])
    d=ImageDraw.Draw(im);y=b[1]+20;s=fake.get('size',54)
    for ln in fake['lines']:
        d.text((b[0]+15,y),ln,font=font('Bold',s),fill=WHITE);y+=int(s*1.25)
    return im

# ---------- PC 브라우저 화면 ----------
MX,MY,MW,BAR=70,840,940,46
def screen_card(img,src,rect,url,label=None,wipe=None):
    sw,sh=src.size;zx,zy,zw=rect;zh=zw*sh/sw
    zx=max(0,min(sw-zw,zx));zy=max(0,min(sh-zh,zy))
    CH=int(MW*sh/sw)
    content=src.crop((int(zx),int(zy),int(zx+zw),int(zy+zh))).resize((MW,CH),Image.LANCZOS)
    if wipe:  # (other_src_content, progress)
        o,p=wipe;wx=int(MW*p);c=o.copy();c.paste(content.crop((0,0,wx,CH)),(0,0));content=c
    card=Image.new('RGB',(MW,BAR+CH),(238,241,245));dc=ImageDraw.Draw(card)
    for i,col in enumerate([(255,95,87),(254,188,46),(40,200,64)]):dc.ellipse((22+i*26,16,36+i*26,30),fill=col)
    dc.rounded_rectangle((110,10,MW-24,36),13,fill=WHITE);dc.text((126,13),url,font=font('Medium',18),fill=(138,148,163))
    card.paste(content,(0,BAR))
    if label:dc.rounded_rectangle((MW-110,BAR+16,MW-20,BAR+56),20,fill=(0,0,0));dc.text((MW-65,BAR+36),label,font=font('Bold',24),fill=WHITE,anchor='mm')
    mask=Image.new('L',card.size,0);ImageDraw.Draw(mask).rounded_rectangle((0,0,MW-1,BAR+CH-1),24,fill=255)
    sh_=Image.new('RGBA',(MW+80,BAR+CH+80),(0,0,0,0));ImageDraw.Draw(sh_).rounded_rectangle((40,50,MW+40,BAR+CH+50),24,fill=(0,0,0,120))
    img.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(18)),(MX-40,MY-40))
    cc=card.convert('RGBA');cc.putalpha(mask);img.alpha_composite(cc,(MX,MY))
    if wipe and 0<wipe[1]<1:ImageDraw.Draw(img).rectangle((MX+int(MW*wipe[1])-4,MY+BAR,MX+int(MW*wipe[1])+4,MY+BAR+CH),fill=G)
    return (zx,zy,zw,CH)

# ---------- 휴대폰 화면 ----------
PW=520;PX=(W-PW)//2;PY=760;PS=PW/486;PH=int(715*PS)
def phone_card(img,pages,offset,label=None):
    """pages: 세로로 이어 붙일 이미지들(486 폭). offset: 위에서부터 스크롤한 px(원본 기준)"""
    strip_h=sum(p.size[1] for p in pages);strip=Image.new('RGB',(486,strip_h),WHITE);y=0
    for p in pages:strip.paste(p,(0,y));y+=p.size[1]
    off=max(0,min(strip_h-715,offset))
    view=strip.crop((0,int(off),486,int(off)+715)).resize((PW,PH),Image.LANCZOS)
    bez=18;fw,fh=PW+bez*2,PH+bez*2+40
    frame=Image.new('RGBA',(fw,fh),(0,0,0,0));d=ImageDraw.Draw(frame)
    d.rounded_rectangle((0,0,fw-1,fh-1),56,fill=(20,24,22,255),outline=(70,80,75,255),width=3)
    d.rounded_rectangle((fw//2-60,14,fw//2+60,30),8,fill=(40,46,43,255))
    m=Image.new('L',(PW,PH),0);ImageDraw.Draw(m).rounded_rectangle((0,0,PW-1,PH-1),34,fill=255)
    vv=view.convert('RGBA');vv.putalpha(m);frame.alpha_composite(vv,(bez,bez+40))
    if label:d.rounded_rectangle((fw-130,bez+56,fw-34,bez+96),20,fill=(0,0,0,255));d.text((fw-82,bez+76),label,font=font('Bold',24),fill=WHITE,anchor='mm')
    sh=Image.new('RGBA',(fw+80,fh+80),(0,0,0,0));ImageDraw.Draw(sh).rounded_rectangle((40,50,fw+40,fh+50),56,fill=(0,0,0,130))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)),(PX-bez-40,PY-bez-40-40+40))
    img.alpha_composite(frame,(PX-bez,PY-bez))

# ---------- 위쪽 글자 ----------
def mark(d,x,y,kind,a,sz=88):
    if kind=='x':
        d.ellipse((x,y,x+sz,y+sz),fill=A(RED,a));c=A(WHITE,a);p=sz*0.3
        d.line((x+p,y+p,x+sz-p,y+sz-p),fill=c,width=9);d.line((x+sz-p,y+p,x+p,y+sz-p),fill=c,width=9)
    else:
        d.ellipse((x,y,x+sz,y+sz),fill=A(G,a));c=A(DARK,a)
        d.line((x+sz*.26,y+sz*.52,x+sz*.44,y+sz*.70),fill=c,width=9);d.line((x+sz*.44,y+sz*.70,x+sz*.76,y+sz*.32),fill=c,width=9)
def chip(d,x,y,s,a):
    f=font('ExtraBold',52);w=d.textlength(s,font=f)+64
    d.rounded_rectangle((x,y,x+w,y+92),22,fill=A(WHITE,a));d.text((x+32,y+16),s,font=f,fill=A(DARK,a));return x+w

def render(folder):
    spec=json.load(open(os.path.join(folder,'reel.json'),encoding='utf-8'))
    beats=spec['beats'];series=spec.get('series','');ep=spec.get('episode')
    durs=[b.get('dur',1.5) for b in beats];T=sum(durs);N=int(round(T*FPS))
    starts=np.cumsum([0]+durs[:-1])
    BG=background()
    cache={}
    def img_of(site,name,fake=None):
        k=(site,name,json.dumps(fake,sort_keys=True) if fake else '')
        if k not in cache:
            im=load_site(site,name);cache[k]=fake_version(im,fake) if fake else im
        return cache[k]
    sites=json.load(open(os.path.join(R,'assets/sites/sites.json'),encoding='utf-8'))
    out=os.path.join(folder,'reel.mp4');tmp=os.path.join(folder,'reel.tmp.mp4')
    p=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-f','lavfi','-i','anullsrc=channel_layout=stereo:sample_rate=44100','-shortest',
        '-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',
        '-c:a','aac','-b:a','128k',tmp],stdin=subprocess.PIPE)
    checks=[]
    tag=f"{series} {ep}편" if ep else series
    for n in range(N):
        t=n/FPS;k=int(np.searchsorted(starts,t,side='right')-1);b=beats[k];lt=t-starts[k];D=durs[k]
        img=BG.copy();d=ImageDraw.Draw(img)
        # 머리: 진행 막대 + 시리즈 + 계정
        d.rectangle((80,212,1000,220),fill=(60,72,66));d.rectangle((80,212,80+int(920*(n+1)/N),220),fill=G)
        if tag:
            tw=d.textlength(tag,font=font('ExtraBold',36))
            d.rounded_rectangle((80,250,80+tw+48,312),14,fill=G);d.text((104,258),tag,font=font('ExtraBold',36),fill=DARK)
        d.text((W-80,262),'@can_bly_official',font=font('Bold',30),fill=(143,165,154),anchor='ra')
        a=ease(lt/0.15);dy=int(30*(1-a));pop=1+0.03*(1-ease(lt/0.2))
        # 가운데: 화면
        if 'screen' in b:
            s=b['screen'];site=s['site'];src=img_of(site,s.get('view','desktop.jpg'),s.get('fake'))
            sw,sh=src.size;z0=s.get('zoom',[0,0,sw]);z1=s.get('to_zoom',z0);z=ease(lt/max(0.3,D*0.8))
            rect=[z0[i]+(z1[i]-z0[i])*z for i in range(3)];rect[2]/=pop
            wipe=None
            if 'wipe_from' in s:
                wf=s['wipe_from'];o=img_of(wf['site'],wf.get('view','desktop.jpg'),wf.get('fake'))
                ow,oh=o.size;oz=wf.get('zoom',[0,0,ow]);ozh=oz[2]*oh/ow
                oc=o.crop((int(oz[0]),int(oz[1]),int(oz[0]+oz[2]),int(oz[1]+ozh))).resize((MW,int(MW*sh/sw)),Image.LANCZOS)
                wipe=(oc,ease((lt-0.1)/0.6))
            zx,zy,zw,CH=screen_card(img,src,rect,sites[site]['url'],s.get('label'),wipe)
            if s.get('highlight') and lt>s.get('highlight_at',0.6):
                hb=s['highlight'];bb=ease((lt-s.get('highlight_at',0.6))/0.25);sc=MW/zw
                x0=MX+(hb[0]-zx)*sc;y0=MY+BAR+(hb[1]-zy)*sc;x1=MX+(hb[2]-zx)*sc;y1=MY+BAR+(hb[3]-zy)*sc
                for q in range(7):d.rounded_rectangle((x0-12-q,y0-12-q,x1+12+q,y1+12+q),16,outline=A(G,bb))
        if 'phone' in b:
            ph=b['phone'];site=ph['site'];names=ph.get('pages',['m01.jpg'])
            pages=[img_of(site,nm,ph.get('fake') if i==0 else None) for i,nm in enumerate(names)]
            pages=[pages[0]]+[pg.crop((0,48,486,715)) for pg in pages[1:]]  # 이어 붙일 때 반복되는 상단 메뉴 제거
            total=sum(pg.size[1] for pg in pages)-715;off=total*ease((lt-0.15)/max(0.3,D-0.3)) if len(pages)>1 else 0
            phone_card(img,pages,off,ph.get('label'))
        # 위쪽 글자 (화면·폰이 없는 장면은 글자를 가운데로 내린다)
        oy=0 if ('screen' in b or 'phone' in b) else 320
        if 'title' in b:
            col=G if b.get('title_color')=='green' else WHITE
            d.multiline_text((80,oy+400+dy),b['title'],font=font('ExtraBold',b.get('title_size',100)),fill=A(col,a),spacing=16)
            if 'sub' in b:d.multiline_text((80,oy+400+(b['title'].count(chr(10))+1)*int(b.get('title_size',100)*1.16)+50+dy),b['sub'],font=font('Bold',52),fill=A(G,ease((lt-0.2)/0.2)),spacing=16)
        for kind in ('x','v'):
            if kind in b:
                mark(d,80,oy+400+dy,kind,a,96);d.multiline_text((80,oy+540+dy),b[kind],font=font('ExtraBold',92),fill=A(WHITE,a),spacing=14)
        if 'compare' in b:
            c=b['compare'];f=font('Bold',52);mark(d,80,oy+420,'x',a,80);d.text((190,oy+428),c['bad'],font=f,fill=A((154,166,160),a))
            d.line((190,oy+462,190+d.textlength(c['bad'],font=f),oy+462),fill=A((154,166,160),a),width=4)
            if lt>0.35:
                bb=ease((lt-0.35)/0.15);mark(d,80,oy+560,'v',bb,80);d.multiline_text((190,oy+556),c['good'],font=font('ExtraBold',84),fill=A(WHITE,bb),spacing=16)
        if 'next' in b:
            d.text((80,oy+420),'다음 편',font=font('Bold',50),fill=A((159,176,168),a))
            d.multiline_text((80,oy+500+dy),b['next'],font=font('ExtraBold',100),fill=A(WHITE,a),spacing=16)
            d.text((80,oy+780),b.get('next_cta','팔로우하고 다음 편 보기 →'),font=font('Bold',50),fill=A(G,a))
        # 아래쪽
        if 'chips' in b:
            x=80;yy=1440 if 'screen' in b else oy+900
            for q,s_ in enumerate(b['chips']):
                st=0.1+0.3*q
                if lt>=st:
                    bb=ease((lt-st)/0.15)
                    if q:d.text((x+10,yy+14),'+',font=font('ExtraBold',56),fill=A(G,bb));x+=60
                    x=chip(d,x,yy,s_,bb)+10
        if 'caption' in b and lt>0.25:
            yy=1440 if 'screen' in b else oy+900
            if 'chips' in b:yy+=130
            d.multiline_text((80,yy),b['caption'],font=font('Bold',46),fill=A(SUBC,ease((lt-0.25)/0.2)),spacing=14)
        frame=img.convert('RGB');p.stdin.write(frame.tobytes())
        if abs(lt-min(D*0.8,1.2))<0.5/FPS:checks.append(frame.resize((270,480)))
    p.stdin.close();p.wait()
    if p.returncode!=0:sys.exit('ffmpeg 실패')
    os.replace(tmp,out)
    sheet=Image.new('RGB',(len(checks)*280,480),WHITE)
    for i,c in enumerate(checks):sheet.paste(c,(i*280,0))
    sheet.save(os.path.join(folder,'check.jpg'),quality=85)
    print(f'{out}: {T:.1f}s, 장면 {len(beats)}개')

if __name__=='__main__':render(os.path.abspath(sys.argv[1]))
