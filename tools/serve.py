#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网调试服务器（给手机装插件用）。

    cd /Users/chenpeng/Cloud/onlycp-plugins
    python3 tools/serve.py [端口]

比裸 `python3 -m http.server` 多做了几件事：
  * 以仓库根目录为根，而不是当前目录
  * .lpx / .sgmodule / .js 等用 text/plain; charset=utf-8 返回（客户端解析更稳）
  * 插件响应禁止缓存（no-store），改完文件手机上重进即生效
  * 首页自动列出仓库里所有插件，并生成手机可点的一键导入按钮
  * 链接里的主机名取自浏览器/客户端实际访问的 Host，不用改代码适配 IP

安全提示：服务监听 0.0.0.0，对**整个局域网**开放，调试完请 Ctrl+C 关掉。
"""

import socket
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 插件成品后缀 -> MIME
PLUGIN_MIME = {
    ".lpx": "text/plain; charset=utf-8",
    ".sgmodule": "text/plain; charset=utf-8",
    ".module": "text/plain; charset=utf-8",
    ".snippet": "text/plain; charset=utf-8",
    ".stoverride": "text/plain; charset=utf-8",
    ".plugin": "text/plain; charset=utf-8",
    ".conf": "text/plain; charset=utf-8",
    ".list": "text/plain; charset=utf-8",
    ".ini": "text/plain; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

# 哪些后缀算「插件成品」，会被列到首页
PLUGIN_SUFFIXES = (".lpx", ".sgmodule", ".module", ".snippet", ".stoverride", ".plugin")
SKIP_DIRS = {".git", "tools", "node_modules", "dist", "build"}

PLATFORM_LABEL = {
    "loon": "Loon",
    "surge": "Surge",
    "quantumultx": "Quantumult X",
    "shadowrocket": "Shadowrocket",
    "scripts": "脚本",
}


def lan_ip() -> str:
    """猜一个本机局域网 IP（不产生真实流量）。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("223.5.5.5", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return "127.0.0.1"


def find_plugins():
    """扫描仓库里的插件成品文件，返回相对路径列表（排序稳定）。"""
    out = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in PLUGIN_SUFFIXES:
            continue
        rel = p.relative_to(REPO_ROOT)
        if any(part.startswith(".") or part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(rel)
    return sorted(out, key=lambda r: (r.parts[0], str(r).lower()))


def read_title(path: Path) -> str:
    """从插件文件头部注释里取 #!name / #!desc，取不到就用文件名。"""
    name, desc = "", ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(12):
                line = fh.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("#!name="):
                    name = line[len("#!name="):].strip()
                elif line.startswith("#!desc="):
                    desc = line[len("#!desc="):].strip()
        # 部分平台用 // @name 之类的注释
        if not name:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for _ in range(20):
                    line = fh.readline()
                    if not line:
                        break
                    line = line.strip().lstrip("/#* ").strip()
                    if line.lower().startswith(("@name", "name=")):
                        name = line.split("=", 1)[-1].strip()
                        break
    except OSError:
        pass
    return name or path.stem, desc


def render_index(host: str) -> str:
    base = f"http://{host}"
    rows = []
    for rel in find_plugins():
        target = REPO_ROOT / rel
        name, desc = read_title(target)
        platform = PLATFORM_LABEL.get(rel.parts[0], rel.parts[0])
        url = f"{base}/{urllib.parse.quote(str(rel))}"
        icon = target.parent / "icon.png"
        icon_html = (
            f'<img class="ico" src="/{urllib.parse.quote(str(rel.parent))}/icon.png" alt="">'
            if icon.exists() else '<div class="ico ico-ph"></div>'
        )
        if rel.suffix.lower() == ".lpx":
            action = (
                f'<a class="btn" href="https://www.nsloon.com/openloon/import?plugin='
                f'{urllib.parse.quote(url, safe="")}">导入到 Loon</a>'
            )
        else:
            action = '<span class="hint">在客户端里粘贴下面的直链</span>'
        rows.append(f'''
    <div class="card">
      {icon_html}
      <div class="meta">
        <div class="name">{name} <span class="plat">{platform}</span></div>
        <div class="desc">{desc or "（插件文件里没有 #!desc）"}</div>
        <code class="url">{url}</code>
        <div class="actions">{action}<a class="btn ghost" href="/{urllib.parse.quote(str(rel))}">查看源文件</a></div>
      </div>
    </div>''')

    if not rows:
        rows.append('<p class="empty">仓库里还没找到插件成品文件（.lpx / .sgmodule / .module）。</p>')

    return f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>onlycp/plugins · 本地调试</title>
<style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
body{{margin:0 auto;padding:22px 16px 60px;max-width:720px;
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif}}
h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:#888;font-size:13px;margin-bottom:20px}}
.card{{display:flex;gap:14px;padding:14px;margin:12px 0;border-radius:14px;
  background:rgba(127,127,127,.10)}}
.ico{{width:64px;height:64px;border-radius:16px;object-fit:cover;flex:0 0 auto}}
.ico-ph{{background:rgba(127,127,127,.25)}}
.meta{{min-width:0;flex:1}}
.name{{font-weight:600}}
.plat{{font-size:12px;font-weight:400;color:#888;border:1px solid currentColor;
  border-radius:6px;padding:0 5px;margin-left:4px;vertical-align:middle}}
.desc{{font-size:13px;color:#888;margin:4px 0 8px;word-break:break-word}}
code.url{{display:block;font-size:12px;background:rgba(127,127,127,.18);
  padding:6px 8px;border-radius:7px;word-break:break-all;user-select:all}}
.actions{{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.btn{{flex:1 1 130px;text-align:center;padding:10px 12px;border-radius:10px;
  background:#0a84ff;color:#fff;text-decoration:none;font-weight:600;font-size:14px}}
.btn.ghost{{background:transparent;color:#0a84ff;border:1px solid rgba(10,132,255,.6);flex:0 1 auto}}
.hint{{font-size:13px;color:#888}}
.note{{margin-top:26px;padding-top:14px;border-top:1px solid rgba(127,127,127,.25);
  font-size:12px;color:#888}}
button.copy{{all:unset;cursor:pointer}}
</style></head><body>
<h1>onlycp/plugins · 本地调试</h1>
<div class="sub">扫码/输入这个地址即可在手机上安装；改完文件手机上重进插件即生效（已禁用缓存）。</div>
{''.join(rows)}
<div class="note">
  服务根目录：<code>{REPO_ROOT}</code><br>
  本页地址：<code>{base}/</code> · 手机需与 Mac 在同一局域网 · 调试完在终端按 Ctrl+C 关闭。
</div>
</body></html>
'''


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def guess_type(self, path):
        lower = str(path).lower()
        for ext, ctype in PLUGIN_MIME.items():
            if lower.endswith(ext):
                return ctype
        return super().guess_type(path)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            host = self.headers.get("Host") or f"{lan_ip()}:{self.server.server_address[1]}"
            body = render_index(host).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        path = urllib.parse.urlparse(self.path).path.lower()
        if path == "/" or path.endswith(tuple(PLUGIN_MIME)):
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")


def main():
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"端口参数不合法：{sys.argv[1]}", file=sys.stderr)
            return 2

    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    ip = lan_ip()
    plugins = find_plugins()
    print(f"仓库根目录: {REPO_ROOT}")
    print(f"手机打开:   http://{ip}:{port}/")
    print(f"本机打开:   http://127.0.0.1:{port}/")
    print(f"发现插件:   {len(plugins)} 个")
    for rel in plugins:
        name, _ = read_title(REPO_ROOT / rel)
        print(f"  - {name}: http://{ip}:{port}/{urllib.parse.quote(str(rel))}")
    print("（Ctrl+C 停止）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
