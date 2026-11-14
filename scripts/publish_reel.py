"""오늘(한국 시간) reels/<날짜>/reel.mp4 를 인스타 릴스로 발행한다. GitHub Actions에서 실행.
필요한 Secrets: IG_USER_ID, IG_ACCESS_TOKEN / 선택 Variables: GRAPH_HOST, GRAPH_VERSION
"""
import os,sys,json,time,datetime,urllib.request,urllib.parse
KST=datetime.timezone(datetime.timedelta(hours=9))
date=os.environ.get('POST_DATE') or datetime.datetime.now(KST).date().isoformat()
dry=os.environ.get('DRY_RUN','false').lower()=='true'
folder=f'reels/{date}'
if not os.path.exists(f'{folder}/reel.mp4'): print(f'{folder}/reel.mp4 없음: 오늘 발행할 릴스가 없습니다'); sys.exit(0)
if os.path.exists(f'{folder}/published.json') and not dry: print(f'{folder} 이미 발행됨'); sys.exit(0)
caption=open(f'{folder}/caption.txt',encoding='utf-8').read().strip()
assert len(caption)<=2200,'캡션이 2200자를 넘습니다'
repo=os.environ['GITHUB_REPOSITORY']; sha=os.environ.get('GITHUB_SHA','main')
# 영상 주소 후보: GitHub raw(application/octet-stream) → 실패하면 jsDelivr(video/mp4)
urls=[f'https://raw.githubusercontent.com/{repo}/{sha}/{folder}/reel.mp4',f'https://cdn.jsdelivr.net/gh/{repo}@{sha}/{folder}/reel.mp4']
print(f'{date}: {folder}/reel.mp4')
IG=os.environ.get('IG_USER_ID',''); TOKEN=os.environ.get('IG_ACCESS_TOKEN','')
if not (IG and TOKEN): print('IG_USER_ID 또는 IG_ACCESS_TOKEN 시크릿이 없습니다'); sys.exit(1)
BASE=f"https://{os.environ.get('GRAPH_HOST') or 'graph.facebook.com'}/{os.environ.get('GRAPH_VERSION') or 'v23.0'}"
def call(method,path,**params):
    params['access_token']=TOKEN; data=urllib.parse.urlencode(params).encode(); u=f'{BASE}/{path}'
    req=urllib.request.Request(u,data=data,method='POST') if method=='POST' else urllib.request.Request(u+'?'+data.decode())
    try:
        with urllib.request.urlopen(req,timeout=90) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        print('API 오류:',e.read().decode()); raise
def wait(cid):
    for _ in range(60):  # 영상 처리: 최대 10분
        s=call('GET',cid,fields='status_code,status')
        if s.get('status_code')=='FINISHED': return
        if s.get('status_code') in ('ERROR','EXPIRED'): raise RuntimeError(f"{cid} 상태 {s}")
        time.sleep(10)
    raise RuntimeError(f'{cid} 처리 시간 초과')
me=call('GET',IG,fields='username'); print(f"계정 @{me.get('username')}")
cid=None
for i,url in enumerate(urls):
    print('업로드 시도:',url)
    try:
        cid=call('POST',f'{IG}/media',media_type='REELS',video_url=url,caption=caption,share_to_feed='true')['id']; wait(cid); break
    except Exception as e:
        print('실패:',e); cid=None
        if i==len(urls)-1: raise
if dry: print('DRY_RUN: 영상 업로드·처리까지 정상 (실제 발행은 하지 않음)'); sys.exit(0)
mid=call('POST',f'{IG}/media_publish',creation_id=cid)['id']
link=call('GET',mid,fields='permalink').get('permalink')
json.dump({'media_id':mid,'permalink':link,'published_at':datetime.datetime.now(KST).isoformat()},open(f'{folder}/published.json','w'),ensure_ascii=False,indent=1)
print('발행 완료:',link)
