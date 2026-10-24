"""오늘(한국 시간) 날짜 폴더의 게시물을 인스타그램에 발행한다. GitHub Actions에서 실행.
필요한 Secrets: IG_USER_ID, IG_ACCESS_TOKEN
선택 Variables: GRAPH_HOST (기본 graph.facebook.com), GRAPH_VERSION (기본 v23.0)
"""
import os,sys,json,time,glob,datetime,urllib.request,urllib.parse

KST=datetime.timezone(datetime.timedelta(hours=9))
date=os.environ.get('POST_DATE') or datetime.datetime.now(KST).date().isoformat()
dry=os.environ.get('DRY_RUN','false').lower()=='true'
folder=f'posts/{date}'
if not os.path.isdir(folder): print(f'{folder} 없음: 오늘 발행할 게시물이 없습니다'); sys.exit(0)
if os.path.exists(f'{folder}/published.json'): print(f'{folder} 이미 발행됨'); sys.exit(0)

imgs=sorted(glob.glob(f'{folder}/[0-9][0-9].jpg'))
caption=open(f'{folder}/caption.txt',encoding='utf-8').read().strip()
assert 1<=len(imgs)<=10, f'이미지 수 오류: {len(imgs)}'
assert len(caption)<=2200, '캡션이 2200자를 넘습니다'
repo=os.environ['GITHUB_REPOSITORY']; sha=os.environ.get('GITHUB_SHA','main')
urls=[f'https://raw.githubusercontent.com/{repo}/{sha}/{p}' for p in imgs]
print(f'{date}: 이미지 {len(urls)}장'); [print(' ',u) for u in urls]
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

if dry:
    if not (IG and TOKEN): print('DRY_RUN: IG_USER_ID 또는 IG_ACCESS_TOKEN 시크릿이 없습니다'); sys.exit(1)
    me=call('GET',IG,fields='username')
    print(f"DRY_RUN: 토큰 정상, 연결된 계정 @{me.get('username')}")
    # 게시 권한 확인: 업로드 준비(컨테이너)만 만들고 발행은 하지 않는다. 미발행 컨테이너는 24시간 뒤 자동 만료된다
    test=call('POST',f'{IG}/media',image_url=urls[0],is_carousel_item='true')['id']
    wait(test)
    print('DRY_RUN: 게시 권한 정상 (업로드 준비까지만 확인, 실제 발행은 하지 않음)'); sys.exit(0)

if len(urls)==1:
    cid=call('POST',f'{IG}/media',image_url=urls[0],caption=caption)['id']
else:
    kids=[]
    for u in urls:
        k=call('POST',f'{IG}/media',image_url=u,is_carousel_item='true')['id']; kids.append(k)
    for k in kids: wait(k)
    cid=call('POST',f'{IG}/media',media_type='CAROUSEL',children=','.join(kids),caption=caption)['id']
wait(cid)
mid=call('POST',f'{IG}/media_publish',creation_id=cid)['id']
link=call('GET',mid,fields='permalink').get('permalink')
json.dump({'media_id':mid,'permalink':link,'published_at':datetime.datetime.now(KST).isoformat()},open(f'{folder}/published.json','w'),ensure_ascii=False,indent=1)
print('발행 완료:',link)
