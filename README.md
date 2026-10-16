# onlycp/plugins

个人插件集合仓库：代理客户端插件（Loon / Surge / Quantumult X / Shadowrocket）、跨平台脚本，以及后续其它形态的插件。

> **仓库规则**
> 1. **一个插件 = 一个目录**（目录名 kebab-case），插件文件、图标、说明都放进去，做到「一个目录搬走就能用」。
> 2. **发布后的路径不再改动**——客户端是靠 raw 直链安装和更新的，改路径 = 所有用户失效。新插件只新增目录，不动老目录。
> 3. **只提交成品与源码，不提交过程产物**（抓包原文件、构建产物、密钥、编辑器配置等），规则见 [`.gitignore`](.gitignore)。

---

## 📦 插件索引

| 平台 | 插件 | 作用 | 一键导入 |
| --- | --- | --- | --- |
| Loon | [班级小管家去广告](loon/banjixiaoguanjia-remove-ads/) | 去掉「班级小管家」App 的开屏/插屏/自建广告位，需配合可莉「广告平台拦截器」 | [导入到 Loon](https://www.nsloon.com/openloon/import?plugin=https%3A%2F%2Fraw.githubusercontent.com%2Fonlycp%2Fplugins%2Fmain%2Floon%2Fbanjixiaoguanjia-remove-ads%2Fbanjixiaoguanjia-remove-ads.lpx) |

> 新增插件后请顺手在这张表里加一行。

---

## 🗂 目录结构

```
.
├── README.md                     # 本文件：总说明 + 插件索引
├── LICENSE                       # MIT
├── .gitignore                    # 只忽略过程产物，成品插件必须入库
│
├── loon/                         # Loon 插件（.lpx）
│   └── banjixiaoguanjia-remove-ads/
│       ├── banjixiaoguanjia-remove-ads.lpx   # 插件本体
│       ├── icon.png                          # 插件图标（#!icon 指向它）
│       └── README.md                         # 该插件的原理 / 安装 / 验证清单
├── surge/                        # Surge 模块（.sgmodule）
├── quantumultx/                  # Quantumult X 重写、脚本、规则集
├── shadowrocket/                 # Shadowrocket 模块（.module）
├── scripts/                      # 跨客户端共用的脚本
└── tools/
    └── serve.py                  # 局域网调试服务器（带一键导入页，替代裸 http.server）
```

**为什么按「客户端/平台」分一级，而不是按 App 分？**
同一个 App 往往要给不同客户端各写一份（Loon 一份、Surge 一份、QX 一份），它们语法不同、发布节奏也不同；
按平台分一级，路径天然不冲突，用户也只需要记住自己用的那个平台目录。

**插件目录命名**：`<app或场景>-<动作>`，kebab-case，例如
`banjixiaoguanjia-remove-ads`、`weibo-clean-feed`、`jd-remove-ads`。
目录名、文件名、`#!name` 里的中文名三者要保持能对上，方便搜索。

---

## 🔗 直链与安装

raw 直链（推荐）：

```
https://raw.githubusercontent.com/onlycp/plugins/main/<插件相对路径>
```

国内访问 raw 不稳定时可用 jsDelivr 镜像（同一个文件，缓存 12 小时左右）：

```
https://cdn.jsdelivr.net/gh/onlycp/plugins@main/<插件相对路径>
```

**Loon 一键导入**：把直链 URL-encode 后拼到 `https://www.nsloon.com/openloon/import?plugin=` 后面，例如班级小管家：

```
https://www.nsloon.com/openloon/import?plugin=https%3A%2F%2Fraw.githubusercontent.com%2Fonlycp%2Fplugins%2Fmain%2Floon%2Fbanjixiaoguanjia-remove-ads%2Fbanjixiaoguanjia-remove-ads.lpx
```

也可以不走链接：Loon → `配置 → 插件 → 添加`，直接粘贴 raw 直链。

**更新插件**：改完文件推 GitHub 后，在 Loon 插件列表里对该插件点「更新」（或删除后重新导入）。
如果改了路径，等于新插件，老用户不会自动更新——所以老目录只增不改。

---

## 🧪 本地调试

```bash
cd /Users/chenpeng/Cloud/onlycp-plugins
python3 tools/serve.py            # 默认 8000 端口
```

`serve.py` 和裸 `python3 -m http.server` 的区别：

- 按仓库根目录启动，`.lpx` / `.sgmodule` / `.js` 用 `text/plain; charset=utf-8` 返回（Loon 解析更稳）
- 插件响应带 `Cache-Control: no-store`，改完文件手机上重进插件即生效，不会被缓存坑
- 首页自动列出仓库里所有插件，并生成**手机可点的一键导入按钮**（自动填本机局域网 IP）
- 启动时会在终端打印手机可直接打开的地址

手机与 Mac 需在同一局域网。调试完 `Ctrl+C` 关掉——这个服务对整个局域网开放。

---

## ➕ 新增一个插件

1. 在对应平台目录下建插件目录：`<平台>/<插件id>/`
2. 放文件：`<插件id>.lpx`（或 `.sgmodule` / `.module` / `.conf`）、`icon.png`、`README.md`
3. 该插件 README 建议包含：**原理（抓包/逆向结论）→ 插件做了什么 → 安装与顺序要求 → 验证清单 → 边界与风险**
4. 更新根 `README.md` 的插件索引表
5. `git add` → 提交 → 推送；提交信息建议 `loon: 新增 xxx 去广告` 这种前缀
6. 想确认没被误忽略：`git status --ignored`、`git check-ignore -v <文件>`

---

## ⚠️ 免责声明

- 本仓库的插件仅用于**个人学习与自用**，用于屏蔽自己设备上的广告，不修改/破解第三方 App 本体，不绕过付费。
- **绝不收集、上报任何用户数据**；面向教育类 App 的插件尤其不碰未成年人相关数据，不解析图片/语音/视频 CDN。
- 插件对 App 的改动可能随 App 版本失效，也可能导致个别功能异常；使用前请自行确认风险，出现异常先停用插件再排查。
- 相关商标、App 名称归各自权利人所有。
