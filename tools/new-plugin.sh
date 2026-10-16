#!/usr/bin/env bash
# 新增插件脚手架：建目录 + 生成 README 骨架
#
#   tools/new-plugin.sh <宿主> <插件id>
#   tools/new-plugin.sh userscript weibo-clean-feed
#   tools/new-plugin.sh loon jd-remove-ads
#
# 宿主目录约定见仓库根 README 的「宿主目录注册表」。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'USAGE'
用法: tools/new-plugin.sh <宿主> <插件id>

宿主示例: loon surge quantumultx shadowrocket userscript chrome vscode
          obsidian shortcuts docker data misc
插件id:   kebab-case，形如 <app或场景>-<动作>，例: weibo-clean-feed
USAGE
}

[ $# -eq 2 ] || { usage; exit 2; }

target="$1"
pid="$2"

# 宿主 -> 成品后缀 / 中文名（未知宿主也允许，只是不给后缀建议）
case "$target" in
  loon)         ext="lpx";       kind="Loon 插件" ;;
  surge)        ext="sgmodule";  kind="Surge 模块" ;;
  quantumultx)  ext="conf";      kind="Quantumult X 重写/脚本" ;;
  shadowrocket) ext="module";    kind="Shadowrocket 模块" ;;
  userscript)   ext="user.js";   kind="油猴脚本（Tampermonkey / Violentmonkey）" ;;
  chrome)       ext="zip";       kind="浏览器扩展（Chrome / Edge）" ;;
  vscode)       ext="vsix";      kind="编辑器扩展（VS Code / Cursor）" ;;
  obsidian)     ext="zip";       kind="Obsidian 插件" ;;
  shortcuts)    ext="shortcut";  kind="快捷指令" ;;
  docker)       ext="";          kind="自托管服务（Docker）" ;;
  data)         ext="";          kind="纯数据（规则集 / 词库 / 图标包）" ;;
  misc)         ext="";          kind="其它" ;;
  *)            ext="";          kind="$target" ;;
esac

if [[ ! "$target" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "× 宿主目录名要小写 kebab-case：$target" >&2; exit 2
fi
if [[ ! "$pid" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "× 插件id 要小写 kebab-case（例：weibo-clean-feed）：$pid" >&2; exit 2
fi

dir="$REPO_ROOT/$target/$pid"
[ -e "$dir" ] && { echo "× 已存在：$dir" >&2; exit 1; }

mkdir -p "$dir"

if [ -n "$ext" ]; then
  deliverable="\`$pid.$ext\`"
else
  deliverable="（放成品文件，文件名与插件id 保持一致）"
fi

cat > "$dir/README.md" <<EOF
# ${pid}

- 宿主：${kind}
- 成品文件：${deliverable}
- 安装方式：（一键导入链接 / 直链 / 手动步骤）
- 状态：开发中

## 干什么

（一句话说清：解决什么问题、对什么生效、需要什么前置条件。）

## 安装

（从 GitHub raw 直链安装的完整步骤；需要顺序要求的写清楚放在谁上面/下面。）

## 怎么验证生效

（能自查的步骤，越具体越好：看哪个界面的什么变化、到哪里看日志。）

## 原理

（抓包 / 逆向 / 官方文档结论。把「为什么这样写」记下来，半年后还能看懂。）

## 边界与风险

（对什么不生效、可能误伤什么、隐私与数据边界、出问题怎么回滚。）

## 更新记录

| 日期 | 说明 |
| --- | --- |
| $(date +%F) | 首次提交 |
EOF

echo "√ 已创建 $target/$pid/"
echo "  下一步："
[ -n "$ext" ] && echo "   1. 把成品放进去：$target/$pid/$pid.$ext"
[ -z "$ext" ] && echo "   1. 把成品放进去：$target/$pid/"
echo "   2. 补 README（安装 / 验证 / 风险）"
echo "   3. 根 README.md 的「插件索引」加一行（新宿主的话「宿主目录注册表」也加一行）"
echo "   4. git add -A && git commit -m \"$target: 新增 $pid\" && git push"
