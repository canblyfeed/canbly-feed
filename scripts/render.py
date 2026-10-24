"""posts/<날짜>/post.json -> posts/<날짜>/01.jpg ... 렌더링
usage: python3 scripts/render.py posts/2026-11-02
"""
import sys,os,subprocess,glob,tempfile
from PIL import Image
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder=os.path.abspath(sys.argv[1])
for f in glob.glob(os.path.join(folder,'[0-9][0-9].jpg')): os.remove(f)
with tempfile.TemporaryDirectory() as t:
    html=os.path.join(t,'slides.html')
    subprocess.run([sys.executable,os.path.join(R,'template/build.py'),os.path.join(folder,'post.json'),html],check=True)
    subprocess.run(['node',os.path.join(R,'template/shot.js'),html,t],check=True,cwd=R)
    pngs=sorted(glob.glob(os.path.join(t,'[0-9][0-9].png')))
    for p in pngs: Image.open(p).convert('RGB').save(os.path.join(folder,os.path.basename(p)[:-4]+'.jpg'),quality=92,optimize=True)
print(f'{folder}: {len(pngs)} slides')
