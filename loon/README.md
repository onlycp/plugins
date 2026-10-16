# Loon（宿主目录）

存放 Loon 的 `*.lpx` 插件，一个插件一个子目录 —— 命名与目录约定见仓库根 [README](../README.md#-插件目录约定所有宿主通用)。

```
loon/<插件id>/
├── <插件id>.lpx     # 成品：Loon 下载并解析的就是这个文件
├── icon.png         # 插件图标，#!icon 指向仓库 raw 直链
└── README.md        # 原理 / 安装 / 验证 / 风险
```

Loon 相关的几条要点：

- Loon 支持用**直链**安装和更新插件，所以插件路径发布后不要改（改路径 = 老用户不会自动更新）。
- 主配置 `[Plugin]` 段里**列表顺序 = 生效顺序**，依赖别的插件的（比如可莉 `BlockAdvertisers.lpx`）要写在它下面，具体见各插件 README。
- `[Rule]` 段只支持 `DIRECT` / `REJECT` 系列 / `PROXY` 三种策略。
- 插件头部建议填全：`#!name` `#!desc` `#!author` `#!tag` `#!icon` `#!homepage` `#!date`，Loon 的插件列表和分享页都读这些字段。
- 本地调试：在仓库根跑 `python3 tools/serve.py`，首页会给出一键导入按钮。
