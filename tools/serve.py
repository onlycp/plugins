#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网调试服务器（给手机装插件用）。

    cd /Users/chenpeng/Cloud/onlycp-plugins
    python3 tools/serve.py [端口]

比裸 `python3 -m http.server` 多做几件事：
  * 以**仓库根目录**为根，而不是当前目录
  * 按仓库约定 <宿主>/<插件id>/ 扫描插件，首页自动生成手机可点的一键导入页
  * .lpx / .sgmodule / .user.js 等用 text/plain; charset=utf-8 返回（客户端解析更稳）
  * 插件文件禁止缓存（no-store），改完文件手机上重进即生效
  * 链接主机名取自客户端实际访问的 Host，不用改代码适配 IP

安全提示：服务监听 0.0.0.0，对**整个局域网**开放，调试完请 Ctrl+C 关掉。
"""

import socket
import subprocess
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 后缀 -> MIME（客户端是拿文本去解析的，别用 octet-stream）
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
    ".json": "text/plain; charset=utf-8",
}

# 宿主目录名 -> 展示名（认不出来就直接显示目录名）
TARGET_LABEL = {
    "loon": "Loon",
    "surge": "Surge",
    "quantumultx": "Quantumult X",
    "shadowrocket": "Shadowrocket",
    "userscript": "油猴脚本",
    "chrome": "浏览器扩展",
    "vscode": "编辑器扩展",
    "obsidian": "Obsidian",
    "shortcuts": "快捷指令",
    "docker": "自托管服务",
    "data": "数据",
    "misc": "其它",
}

# 这些宿主目录里的成品可以直接一键导入（目前只有 Loon 有通用 scheme）
IMPORT_SCHEME = {"loon": "https://www.nsloon.com/openloon/import?plugin="}

NOT_DELIVERABLE = {"README.md", "LICENSE", "CHANGELOG.md", "icon.png"}


def _bad_ip(ip: str) -> bool:
    """排除 loopback / 链路本地 / 代理软件 fake-ip 段（198.18.0.0/15 等）。"""
    if ip.startswith(("127.", "169.254.", "198.18.", "198.19.", "0.")):
        return True
    try:
        socket.inet_aton(ip)
    except OSError:
        return True
    return False


def lan_ip() -> str:
    """猜一个本机局域网 IP。

    优先读物理网卡（en0 有线 / en1 Wi-Fi）：本机若装了代理客户端，
    UDP connect 探到的可能是 fake-ip 段（198.18.x.x）而不是真实地址。
    """
    for iface in ("en0", "en1", "en2"):
        try:
            ip = subprocess.run(
                ["ipconfig", "getifaddr", iface],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
        if ip and not _bad_ip(ip):
            return ip

    for probe in ("223.5.5.5", "8.8.8.8"):
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sk.connect((probe, 80))
                ip = sk.getsockname()[0]
            finally:
                sk.close()
        except OSError:
            continue
        if ip and not _bad_ip(ip):
            return ip

    return "127.0.0.1"


def find_plugins():
    """按约定找插件目录：<宿主>/<插件id>/，即仓库根下第二层目录。"""
    found = []
    for target in sorted(REPO_ROOT.iterdir()):
        if not target.is_dir() or target.name.startswith(".") or target.name == "tools":
            continue
        for plugin in sorted(target.iterdir()):
            if not plugin.is_dir() or plugin.name.startswith("."):
                continue
            found.append(plugin.relative_to(REPO_ROOT))
    return found


def deliverables(plugin_dir: Path):
    """插件目录里除 README 之外的成品文件（跳过源码子目录之外的隐藏文件）。"""
    files = []
    for f in sorted(plugin_dir.rglob("*")):
        if not f.is_file() or f.name in NOT_DELIVERABLE or f.name.startswith("."):
            continue
        files.append(f)
    return files


def read_meta(path: Path):
    """从插件文件头部注释里抓 #!name= / #!desc= 或 @name / @description。"""
    name = desc = ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(40):
                line = fh.readline()
                if not line:
                    break
                raw = line.strip()
                low = raw.lower()
                if low.startswith("#!name="):
                    name = raw[7:].strip()
                elif low.startswith("#!desc="):
                    desc = raw[7:].strip()
                elif low.startswith(("// @name", "// @description", "# @name", "# @description")):
                    key, _, val = raw.partition(" ")
                    _, _, val = val.partition(" ")
                    if not name and "name" in key.lower():
                        name = val.strip()
                    elif not desc and "desc" in key.lower():
                        desc = val.strip()
    except OSError:
        pass
    return name, desc


def plugin_name(plugin_dir: Path, files):
    """插件显示名：优先插件文件里的 #!name，其次目录里其它文件，最后目录名。"""
    for f in files:
        if f.suffix.lower() in PLUGIN_MIME:
            name, desc = read_meta(f)
            if name or desc:
                return name or plugin_dir.name, desc
    for f in files:
        name, desc = read_meta(f)
        if name or desc:
            return name or plugin_dir.name, desc
    # 退路：README 的一级标题
    readme = plugin_dir / "README.md"
    if readme.exists():
        try:
            for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("# "):
                    return line[2:].strip(), ""
        except OSError:
            pass
    return plugin_dir.name, ""


def render_index(host: str) -> str:
    base = f"http://{host}"
    cards = []

    for rel in find_plugins():
        plugin_dir = REPO_ROOT / rel
        target = rel.parts[0]
        label = TARGET_LABEL.get(target, target)
        files = deliverables(plugin_dir)

        primary = next(
            (f for f in files if f.suffix.lower() in PLUGIN_MIME), files[0] if files else None
        )
        name, desc = plugin_name(plugin_dir, files)

        icon = plugin_dir / "icon.png"
        icon_html = (
            f'<img class="ico" src="/{urllib.parse.quote(str(rel))}/icon.png" alt="">'
            if icon.exists() else '<div class="ico ico-ph"></div>'
        )

        file_rows = []
        for f in files:
            frepo = f.relative_to(REPO_ROOT)
            furl = f"{base}/{urllib.parse.quote(str(frepo))}"
            file_rows.append(
                f'<a class="file" href="/{urllib.parse.quote(str(frepo))}">{f.name}</a>'
                f'<code class="url">{furl}</code>'
            )
        if not file_rows:
            file_rows.append('<span class="hint">还没放成品文件</span>')

        actions = []
        if primary is not None and target in IMPORT_SCHEME:
            purl = f"{base}/{urllib.parse.quote(str(primary.relative_to(REPO_ROOT)))}"
            actions.append(
                f'<a class="btn" href="{IMPORT_SCHEME[target]}{urllib.parse.quote(purl, safe="")}">'
                f'一键导入到 {label}</a>'
            )
        elif primary is not None:
            actions.append('<span class="hint">在客户端里粘贴下面的直链安装</span>')

        cards.append(f'''
    <div class="card">
      {icon_html}
      <div class="meta">
        <div class="name">{name} <span class="plat">{label}</span></div>
        <div class="desc">{desc or "（文件头没有 #!desc / @description）"}</div>
        <div class="files">{''.join(file_rows)}</div>
        <div class="actions">{''.join(actions)}</div>
      </div>
    </div>''')

    if not cards:
        cards.append('<p class="empty">还没找到插件目录。约定是 <code>&lt;宿主&gt;/&lt;插件id&gt;/</code>，'
                     '可以用 <code>tools/new-plugin.sh</code> 生成。</p>')

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
.files{{display:flex;flex-direction:column;gap:6px;margin-bottom:4px}}
a.file{{font-size:13px;font-weight:600}}
code.url{{display:block;font-size:12px;background:rgba(127,127,127,.18);
  padding:6px 8px;border-radius:7px;word-break:break-all;user-select:all}}
.actions{{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.btn{{flex:1 1 150px;text-align:center;padding:10px 12px;border-radius:10px;
  background:#0a84ff;color:#fff;text-decoration:none;font-weight:600;font-size:14px}}
.hint{{font-size:13px;color:#888}}
.note{{margin-top:26px;padding-top:14px;border-top:1px solid rgba(127,127,127,.25);
  font-size:12px;color:#888}}
</style></head><body>
<h1>onlycp/plugins · 本地调试</h1>
<div class="sub">手机用这个地址打开即可安装；改完文件重进插件即生效（已禁用缓存）。</div>
{''.join(cards)}
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
        # 解析畸形请求时 self.path 可能还没建立（局域网里常有设备乱扫端口），兜一下
        path = urllib.parse.urlparse(getattr(self, "path", "") or "/").path.lower()
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
        files = deliverables(REPO_ROOT / rel)
        name, _ = plugin_name(REPO_ROOT / rel, files)
        primary = next((f for f in files if f.suffix.lower() in PLUGIN_MIME), None)
        url = f"http://{ip}:{port}/{urllib.parse.quote(str(rel))}/"
        if primary is not None:
            url = f"http://{ip}:{port}/{urllib.parse.quote(str(primary.relative_to(REPO_ROOT)))}"
        print(f"  - {name} ({rel}): {url}")
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
