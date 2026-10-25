"""월·수·금, 그날의 게시물 3개를 한국 시간 08:00 / 14:00 / 20:00에 하나씩 인스타그램에 발행한다. GitHub Actions에서 실행.
폴더: posts/<날짜>_1 (08:00 홈페이지), posts/<날짜>_2 (14:00 홈페이지), posts/<날짜>_3 (20:00 블로그)
블로그를 마지막에 올려야 그리드 맨 윗줄이 "블로그 · 홈페이지 · 홈페이지"가 된다.
앞 순서가 발행되지 않았으면(실행 누락·실패) 그것부터 먼저 발행해서 순서가 어긋나지 않게 한다.
필요한 Secrets: IG_USER_ID, IG_ACCESS_TOKEN
선택 Variables: GRAPH_HOST (기본 graph.facebook.com), GRAPH_VERSION (기본 v23.0)
"""
import os,sys,json,time,glob,datetime,urllib.request,urllib.parse

KST=datetime.timezone(datetime.timedelta(hours=9))
# publish.yml의 cron과 똑같이 맞춘다 (UTC 기준)
SLOT_BY_CRON={'0 23 * * 0,2,4':1,'0 5 * * 1,3,5':2,'0 11 * * 1,3,5':3}

now=datetime.datetime.now(KST)
cron=os.environ.get('CRON_SCHEDULE','')
slot=os.environ.get('POST_SLOT') or SLOT_BY_CRON.get(cron)
if not slot: slot=1 if now.hour<14 else 2 if now.hour<20 else 3
slot=int(slot)
date=os.environ.get('POST_DATE') or now.date().isoformat()
dry=os.environ.get('DRY_RUN','false').lower()=='true'

todo=[f'posts/{date}_{n}' for n in range(1,slot+1)]
todo=[d for d in todo if os.path.isdir(d) and not os.path.exists(f'{d}/published.json')]
if not todo: print(f'{date} {slot}번: 발행할 게시물이 없습니다 (없거나 이미 발행됨)'); sys.exit(0)

repo=os.environ['GITHUB_REPOSITORY']; sha=os.environ.get('GITHUB_SHA','main')
IG=os.environ.get('IG_USER_ID',''); TOKEN=os.environ.get('IG_ACCESS_TOKEN','')
BASE=f"https://{os.environ.get('GRAPH_HOST') or 'graph.facebook.com'}/{os.environ.get('GRAPH_VERSION') or 'v23.0'}"

def call(method,path,**params):
    params['access_token']=TOKEN
    data=urllib.parse.urlencode(params).encode()
    url=f'{BASE}/{path}'
    req=urllib.request.Request(url,data=data,method='POST') if method=='POST' else urllib.request.Request(url+'?'+data.decode())
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        print('API 오류:',e.read().decode()); raise

def wait(cid):
    for _ in range(30):
        s=call('GET',cid,fields='status_code').get('status_code')
        if s=='FINISHED': return
        if s in ('ERROR','EXPIRED'): raise RuntimeError(f'{cid} 상태 {s}')
        time.sleep(5)
    raise RuntimeError(f'{cid} 처리 시간 초과')

def load(folder):
    imgs=sorted(glob.glob(f'{folder}/[0-9][0-9].jpg'))
    caption=open(f'{folder}/caption.txt',encoding='utf-8').read().strip()
    assert 1<=len(imgs)<=10, f'{folder} 이미지 수 오류: {len(imgs)}'
    assert len(caption)<=2200, f'{folder} 캡션이 2200자를 넘습니다'
    urls=[f'https://raw.githubusercontent.com/{repo}/{sha}/{p}' for p in imgs]
    print(f'{folder}: 이미지 {len(urls)}장'); [print(' ',u) for u in urls]
    return urls,caption

if dry:
    urls,_=load(todo[-1])
    if not (IG and TOKEN): print('DRY_RUN: IG_USER_ID 또는 IG_ACCESS_TOKEN 시크릿이 없습니다'); sys.exit(1)
    me=call('GET',IG,fields='username')
    print(f"DRY_RUN: 토큰 정상, 연결된 계정 @{me.get('username')}")
    # 게시 권한 확인: 업로드 준비(컨테이너)만 만들고 발행은 하지 않는다. 미발행 컨테이너는 24시간 뒤 자동 만료된다
    test=call('POST',f'{IG}/media',image_url=urls[0],is_carousel_item='true')['id']
    wait(test)
    print(f'DRY_RUN: 게시 권한 정상 (발행 예정 순서: {", ".join(todo)}, 실제 발행은 하지 않음)'); sys.exit(0)

for folder in todo:
    urls,caption=load(folder)
    if len(urls)==1:
        cid=call('POST',f'{IG}/media',image_url=urls[0],caption=caption)['id']
    else:
        kids=[call('POST',f'{IG}/media',image_url=u,is_carousel_item='true')['id'] for u in urls]
        for k in kids: wait(k)
        cid=call('POST',f'{IG}/media',media_type='CAROUSEL',children=','.join(kids),caption=caption)['id']
    wait(cid)
    mid=call('POST',f'{IG}/media_publish',creation_id=cid)['id']
    link=call('GET',mid,fields='permalink').get('permalink')
    json.dump({'media_id':mid,'permalink':link,'published_at':datetime.datetime.now(KST).isoformat()},open(f'{folder}/published.json','w'),ensure_ascii=False,indent=1)
    print('발행 완료:',link)
    if folder!=todo[-1]: time.sleep(60)  # 밀린 게시물을 연달아 올릴 때 순서가 섞이지 않게 잠깐 쉰다
