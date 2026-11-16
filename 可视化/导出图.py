# -*- coding: utf-8 -*-
"""
把仓库里的可视化渲染成 PNG，供 PPT / 报告插图使用。

用法： python 作业/可视化/导出图.py
输出： 作业/图集/*.png

依赖： Windows + Edge（headless 截图）；Pillow 仅用于校验非空。
说明： 5 张核心图直接从 可视化.html 抽取内联 SVG，按 viewBox 尺寸 2x 截图；
      关联图 / 领域分块图 / 3D 图 用 headless 浏览器整页截图。
"""
import base64
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

from PIL import Image, ImageChops


def trim_white(p: Path, pad: int = 40) -> None:
    im = Image.open(p).convert('RGB')
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
               min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))
        im.crop(box).save(p)

sys.stdout.reconfigure(encoding='utf-8')

R = Path(__file__).resolve().parent.parent          # 作业/
OUT = R / '图集'
OUT.mkdir(exist_ok=True)

EDGE_CANDIDATES = [
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    shutil.which('msedge') or '',
    shutil.which('chrome') or '',
]
EDGE = next((p for p in EDGE_CANDIDATES if p and Path(p).exists()), None)
if not EDGE:
    sys.exit('找不到 Edge/Chrome，无法截图')

TMP = Path(tempfile.mkdtemp(prefix='figtmp_'))
PROFILE = TMP / 'profile'


def shot(url: str, out: Path, w: int, h: int, scale: int = 2, wait_ms: int = 1500,
         extra: list[str] | None = None) -> None:
    cmd = [EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
           f'--user-data-dir={PROFILE}', f'--force-device-scale-factor={scale}',
           f'--window-size={w},{h}', f'--virtual-time-budget={wait_ms}',
           f'--screenshot={out}']
    if extra:
        cmd += extra
    cmd.append(url)
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=120)
    if not out.exists() or out.stat().st_size < 8_000:
        print(f'  ! 截图失败或过小：{out.name}')
        return
    im = Image.open(out)
    print(f'  ✓ {out.name}  {im.width}x{im.height}  {out.stat().st_size/1024:.0f} KB')


# ── 1. 五张核心图：从 可视化.html 抽 SVG ──
html = (R / '可视化.html').read_text(encoding='utf-8')
svgs = re.findall(r'<svg.*?</svg>', html, flags=re.S)
print(f'找到 {len(svgs)} 个 SVG')
NAMES = ['图1-依赖集中度', '图2-底基扩张稀释', '图3-谁在支撑运行时',
         '图4-底基由谁供养', '图5-公司影响力', '图6-两生态对照']
for i, (svg, name) in enumerate(zip(svgs, NAMES), 1):
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    W, H = float(vb.group(1)), float(vb.group(2))
    svg = svg.replace('width="100%"', f'width="{W:g}" height="{H:g}"')
    page = (f'<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff">'
            f'{svg}</body>')
    f = TMP / f'fig{i}.html'
    f.write_text(page, encoding='utf-8')
    url = 'file:///' + urllib.parse.quote(str(f).replace('\\', '/'))
    print(f'{name} ({W:g}x{H:g})')
    shot(url, OUT / f'{name}.png', int(W), int(H), scale=2)
    trim_white(OUT / f'{name}.png')

# ── 2. 整页截图：关联图 / 领域分块 / 3D ──
def page_shot(path: Path, name: str, w: int, h: int, wait_ms=3000, extra=None):
    if not path.exists():
        print(f'  - 跳过（不存在）：{path}')
        return
    url = 'file:///' + urllib.parse.quote(str(path).replace('\\', '/'))
    print(name)
    shot(url, OUT / f'{name}.png', w, h, scale=1, wait_ms=wait_ms, extra=extra)


page_shot(R / '关联图.html', '图7-数据血缘关联图', 1400, 1150, 2000)
# 图7 用已有的静态渲染（headless 下 3D 画布截图会空白）
src = R.parent / '依赖图/59-领域分块图.png'
if src.exists():
    shutil.copyfile(src, OUT / '图8-领域分块-76块.png')
    print(f'  ✓ 图8-领域分块-76块.png（复制静态渲染）')

# 图8：headless 无 WebGL，3D 图不截图（需要时手动在浏览器里截）
page_shot(R.parent / '依赖图/快照增量动画.html', '图9-快照增量', 1400, 1000, 5000)

print(f'\n输出目录：{OUT}')
