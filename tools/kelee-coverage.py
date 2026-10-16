#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核对「本仓库的去广告插件」与「可莉 广告平台拦截器」的规则覆盖关系。

    python3 tools/kelee-coverage.py                     # 用默认的本地副本核对仓库里所有 Loon 插件
    python3 tools/kelee-coverage.py -k 可莉.lpx          # 指定可莉插件（本地文件）
    python3 tools/kelee-coverage.py -k https://xxx.lpx   # 指定可莉插件（URL，会下载到 .cache/）

为什么需要这个脚本（血泪教训）：
  1. 可莉的规则写法是 `DOMAIN-SUFFIX, gdt.qq.com, REJECT`——**逗号后面带空格**。
     直接拿字符串 `"DOMAIN-SUFFIX,gdt.qq.com"` 去匹配会漏，把"已覆盖"误判成"没覆盖"，
     于是写出多余规则、还在 README 里写了错误的"补漏"结论。（真的发生过。）
  2. 第三方备份仓库（GitHub 上那些 KeleeOne/kele/Tool 之类）经常是几个月前的旧快照，
     拿它当"可莉现状"会得出完全错误的结论。所以本脚本一定会打印可莉副本的 `#!date`，
     请确认它是新的再用。

判定逻辑：
  我们的一条 `DOMAIN-SUFFIX,a.b.com,REJECT` 只要被可莉的
  `DOMAIN-SUFFIX,<a.b.com 或任一父域>` / `DOMAIN,<同域>` / `DOMAIN-KEYWORD,<子串>` 命中，
  就算"已被覆盖=我们多余"。
"""

import argparse
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE = REPO_ROOT / ".cache"

# 可莉插件的常见地址（按可靠性排序，默认先用本地缓存）
DEFAULT_URLS = [
    "https://kelee.one/Tool/Loon/Lpx/BlockAdvertisers.lpx",  # 官方，但对脚本访问有 Cloudflare 403
]


def load_kelee(src: str | None) -> tuple[str, str]:
    """返回 (文本, 来源说明)。src 为 None 时用缓存/内置 URL 尝试。"""
    if src and src.startswith(("http://", "https://")):
        CACHE.mkdir(exist_ok=True)
        dst = CACHE / "BlockAdvertisers.lpx"
        req = urllib.request.Request(src, headers={
            "User-Agent": "Loon/3.5.1 (iPhone; iOS 18.0)",
            "Accept": "*/*",
        })
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                dst.write_bytes(r.read())
            return dst.read_text(encoding="utf-8", errors="replace"), f"下载自 {src}"
        except Exception as e:  # noqa: BLE001
            sys.exit(f"下载失败：{e}\n提示：kelee.one 对脚本访问有 Cloudflare 拦截，"
                     f"用手机/Loon 抓一份存到本地，再用 -k 传路径。")

    if src:
        return Path(src).read_text(encoding="utf-8", errors="replace"), src

    cached = CACHE / "BlockAdvertisers.lpx"
    if cached.exists():
        return cached.read_text(encoding="utf-8", errors="replace"), f"缓存 {cached}"
    sys.exit("没有可莉插件副本。用法：python3 tools/kelee-coverage.py -k <可莉BlockAdvertisers.lpx|URL>")


def parse_rules(text: str) -> set[tuple[str, str]]:
    """抽出所有规则行，统一成 (大写类型, 小写值)，并去掉逗号前后空格。"""
    out = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ";", "//")):
            continue
        parts = [x.strip() for x in s.split(",")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            out.add((parts[0].upper(), parts[1].lower()))
    return out


def covered(domain: str, kelee: set[tuple[str, str]]) -> str | None:
    d = domain.lower()
    parts = d.split(".")
    for i in range(len(parts) - 1):
        parent = ".".join(parts[i:])
        if ("DOMAIN-SUFFIX", parent) in kelee:
            return f"DOMAIN-SUFFIX,{parent}"
    if ("DOMAIN", d) in kelee:
        return f"DOMAIN,{d}"
    if ("DOMAIN-KEYWORD", d) in kelee:
        return f"DOMAIN-KEYWORD,{d}"
    for t, v in kelee:
        if t == "DOMAIN-KEYWORD" and v and v in d:
            return f"DOMAIN-KEYWORD,{v}（关键字命中）"
    return None


def our_domains(text: str) -> list[tuple[str, str]]:
    """取我们插件里指向 REJECT 的域名规则（只理解标准的 DOMAIN 系列行）。"""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ";")):
            continue
        parts = [x.strip() for x in s.split(",")]
        if len(parts) >= 3 and parts[0].upper().startswith("DOMAIN") and "REJECT" in parts[-1].upper():
            out.append((parts[0].upper(), parts[1].lower()))
    return out


def date_of(text: str) -> str:
    m = re.search(r"^#!date\s*=\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else "（无 #!date 字段）"


def main() -> int:
    ap = argparse.ArgumentParser(description="核对本仓库插件与可莉插件的规则覆盖关系")
    ap.add_argument("-k", "--kelee", help="可莉 BlockAdvertisers 的本地路径或 URL")
    ap.add_argument("plugins", nargs="*", help="要核对的插件文件（默认扫描 loon/*/*.lpx）")
    a = ap.parse_args()

    ktext, kfrom = load_kelee(a.kelee)
    krules = parse_rules(ktext)
    print(f"可莉插件：{kfrom}")
    print(f"  #!date = {date_of(ktext)}  规则行 = {len(krules)} 条")
    print("  ⚠️ 请确认这个 date 是新的；第三方备份仓库常常落后好几个月。\n")

    targets = [Path(x) for x in a.plugins] if a.plugins else sorted(REPO_ROOT.glob("loon/*/*.lpx"))
    if not targets:
        print("没找到要核对的插件。")
        return 1

    redundant_total = 0
    for f in targets:
        if not f.exists():
            print(f"跳过（不存在）：{f}")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if "[Rule]" not in text:
            continue
        rules = our_domains(text)
        try:
            label = f.relative_to(REPO_ROOT)
        except ValueError:      # 传了仓库外的路径
            label = f
        print(f"== {label} ==  {len(rules)} 条域名规则")
        for t, d in rules:
            hit = covered(d, krules)
            if hit:
                redundant_total += 1
                print(f"  ⚠️ 多余  {t},{d}  → 可莉已用 {hit}")
            else:
                print(f"  ✅ 保留  {t},{d}  → 可莉没有")
        print()
    if redundant_total:
        print(f"合计 {redundant_total} 条与可莉重复：建议删掉，插件越短越好维护。")
    else:
        print("没有与可莉重复的规则。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
