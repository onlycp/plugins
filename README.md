# onlycp/plugins

个人插件集合仓库。插件**不限于网络代理**，也不限于任何特定 App：代理客户端插件、浏览器扩展与油猴脚本、
编辑器/IDE 插件、App 扩展、自托管服务、纯数据（规则集/词库）等等都放这里。

> **三条仓库规则**
> 1. **一个插件 = 一个目录**，插件文件、图标、说明都放进去，做到「一个目录搬走就能用」。
> 2. **发布后的路径不再改动**——很多客户端（Loon、Surge、油猴…）是靠 raw 直链安装和更新的，改路径 = 所有用户失效。新插件只新增目录，不动老目录。
> 3. **只提交成品和源码，不提交过程产物**（抓包原文件、构建中间产物、密钥、编辑器配置…），规则见 [`.gitignore`](.gitignore)。

---

## 🗂 目录结构：按「宿主 / 平台」平铺

```
.
├── README.md                     # 本文件：规则 + 宿主注册表 + 插件索引
├── LICENSE                       # MIT
├── .gitignore                    # 只忽略过程产物，成品插件必须入库
├── .gitattributes                # 统一换行，避免插件文件被改成 CRLF
│
├── loon/                         # ← 宿主目录（Loon）
│   └── banjixiaoguanjia-remove-ads/
│       ├── banjixiaoguanjia-remove-ads.lpx   # 成品：客户端直接下载的文件
│       ├── icon.png                          # 插件图标（#!icon 指向它）
│       └── README.md                         # 原理 / 安装 / 验证 / 风险
│
└── tools/
    ├── serve.py                  # 局域网调试服务器（带一键导入页）
    └── new-plugin.sh             # 新增插件脚手架
```

**为什么按宿主平铺，而不是按「代理 / 浏览器 / 编辑器」这类功能类别分？**

- 每写一个插件，必然知道它跑在哪儿（Loon？Chrome？VS Code？）= **宿主**，但「类别」往往说不清：
  一个油猴脚本算浏览器插件还是自动化插件？一个同时给 Loon 和 Surge 的脚本算哪类？
- 宿主是**稳定且互斥**的维度，类别会重叠、会变。用宿主当前缀，路径永远不用重构。
- 代价只是顶层目录会慢慢变多，这一维增长是可控的，而且一眼能看出「你有哪些平台的插件」。

**新宿主 = 新建同名目录 + 补一行注册表**，不需要动任何已有路径。

### 宿主目录注册表

用到的宿主才建目录（不预建空目录）。下面是已用 / 预留的命名，新增时照抄：

| 目录名 | 宿主 / 平台 | 典型成品文件 | 怎么装 |
| --- | --- | --- | --- |
| `loon` | Loon（iOS 代理客户端） | `*.lpx` | 一键导入链接 / 手动粘直链 |
| `surge` | Surge | `*.sgmodule` / `*.conf` | 模块直链 |
| `quantumultx` | Quantumult X | `*.conf` / `*.js` / `*.list` | 重写 / 脚本 |
| `shadowrocket` | Shadowrocket | `*.module` | 模块直链 |
| `userscript` | Tampermonkey / Violentmonkey / Userscripts | `*.user.js` | 点链接安装 |
| `chrome` | Chrome / Edge / Brave 扩展 | 扩展目录 + 已构建 `*.zip` | 开发者模式「加载已解压的扩展程序」 |
| `vscode` | VS Code / Cursor | 源码 + `*.vsix` | 安装 VSIX |
| `obsidian` | Obsidian | `main.js` / `manifest.json` / zip | 丢进 `.obsidian/plugins/` |
| `shortcuts` | iOS / macOS 快捷指令 | `*.shortcut` | 双击 / 分享链接 |
| `docker` | 自托管服务 | `docker-compose.yml` | `docker compose up -d` |
| `data` | 纯数据：规则集、词库、图标包、配置片段 | `*.list` / `*.json` / `*.plist` | 被其它插件或工具引用 |
| `misc` | 实在归不了类的 | 看各自 README | 看各自 README |

---

## 🧩 插件目录约定（所有宿主通用）

```
<宿主>/<插件id>/
├── README.md        # 必须：干什么 → 怎么装 → 怎么验证 → 原理/抓包结论 → 边界与风险
├── <成品文件>        # 必须：客户端/用户直接用的那个文件（可以有多个，如 .lpx + 图标 + 数据）
├── icon.png         # 可选：需要联网拉图标的宿主（Loon / Surge）建议带上
└── src/             # 可选：成品是构建产物时，源码放这里（**成品也要一起提交**）
```

- `<插件id>` 用 kebab-case：`<app或场景>-<动作>`，例如 `banjixiaoguanjia-remove-ads`、`weibo-clean-feed`、`jira-quick-copy`、`vsnote`。
- 成品文件名尽量与 `<插件id>` 一致（`<插件id>.lpx` / `<插件id>.sgmodule` / `<插件id>.user.js`），方便用户和搜索。
- **同一个插件要出多个宿主版本**：在各宿主目录下用**同一个 `<插件id>`**，两个 README 互相链接。同源的逻辑可复制（各客户端语法不同），也可以把共用部分放进 `data/` 由两边引用。
- 每个插件目录里的 README 用同一套小标题（干什么 / 安装 / 验证 / 原理 / 风险），以后好维护、也好批量生成索引。

---

## 📦 插件索引

| 宿主 | 插件 | 作用 | 一键导入 |
| --- | --- | --- | --- |
| Loon | [班级小管家去广告](loon/banjixiaoguanjia-remove-ads/) | 去掉「班级小管家」App 的开屏/插屏/自建广告位，需配合可莉「广告平台拦截器」 | [导入到 Loon](https://www.nsloon.com/openloon/import?plugin=https%3A%2F%2Fraw.githubusercontent.com%2Fonlycp%2Fplugins%2Fmain%2Floon%2Fbanjixiaoguanjia-remove-ads%2Fbanjixiaoguanjia-remove-ads.lpx) |

> 新增插件后请顺手往这张表加一行。

---

## 🔗 直链与安装

raw 直链（推荐，也是各客户端更新时拉取的地址）：

```
https://raw.githubusercontent.com/onlycp/plugins/main/<宿主>/<插件id>/<成品文件>
```

`raw.githubusercontent.com` 国内偶尔不稳时可换 jsDelivr 镜像（同路径、缓存约 12 小时）：

```
https://cdn.jsdelivr.net/gh/onlycp/plugins@main/<宿主>/<插件id>/<成品文件>
```

**Loon 一键导入**：把直链 URL-encode 后拼到 `https://www.nsloon.com/openloon/import?plugin=` 后面，例如班级小管家：

```
https://www.nsloon.com/openloon/import?plugin=https%3A%2F%2Fraw.githubusercontent.com%2Fonlycp%2Fplugins%2Fmain%2Floon%2Fbanjixiaoguanjia-remove-ads%2Fbanjixiaoguanjia-remove-ads.lpx
```

其它宿主的安装方式见各自插件目录的 README。

**更新插件**：改完推 GitHub → 在客户端里对该插件点「更新」（Loon：`配置 → 插件`，点插件右侧更新）。再次强调：**改了路径就不会自动更新**，等于换了一个新插件。

---

## 🧪 本地调试

```bash
cd /Users/chenpeng/Cloud/onlycp-plugins
python3 tools/serve.py            # 默认 8000 端口，可传其它端口
```

`serve.py` 与裸 `python3 -m http.server` 的区别：

- 以仓库根目录为根（在哪个目录下执行都一样）
- `.lpx` / `.sgmodule` / `.js` 等用 `text/plain; charset=utf-8` 返回，客户端解析更稳
- 插件响应 `Cache-Control: no-store`，改完文件手机上重进即生效，不会被缓存坑
- 首页自动扫描仓库里所有插件，生成**手机可点的一键导入按钮**（自动识别本机局域网 IP，排除代理软件的 fake-ip 段）
- 启动时在终端打印手机可直接打开的地址

手机与 Mac 需在同一局域网。调试完 `Ctrl+C` 关掉——服务对整个局域网开放。

---

## ➕ 新增一个插件

```bash
tools/new-plugin.sh <宿主> <插件id>      # 例：tools/new-plugin.sh userscript weibo-clean-feed
```

脚本会建好目录和 README 骨架，然后你只要：

1. 把成品文件放进 `<宿主>/<插件id>/`
2. 按骨架把 README 里的「干什么 / 安装 / 验证 / 风险」补齐
3. 根 `README.md` 的插件索引表加一行（新宿主的话，注册表也加一行）
4. `git add -A && git commit -m "<宿主>: 新增 <插件id>"` → `git push`

自检（确认成品没被 `.gitignore` 误伤）：

```bash
git status --ignored --short        # 看看有没有该进库的 !! 项
git check-ignore -v loon/xxx/xxx.lpx
```

---

## ⚠️ 免责声明

- 本仓库的插件仅用于**个人学习与自用**：屏蔽自己设备上的广告、做自己需要的效率增强；不修改/破解第三方 App 本体，不绕过付费验证。
- **绝不收集、上报任何用户数据**。面向教育/未成年相关 App 的插件尤其不碰用户数据，不解析聊天、图片、语音、视频等隐私内容。
- 插件可能随宿主升级而失效，也可能引起个别功能异常；请先在小范围验证，异常时先停用插件再排查。
- 相关商标、产品名称归各自权利人所有。
