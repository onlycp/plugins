# Loon 插件

存放 Loon 的 `*.lpx` 插件，一个插件一个子目录。

- 文件名：`<插件id>.lpx`（kebab-case，和目录名保持一致）
- 同目录可放：`icon.png`（插件图标）、`README.md`（该插件的说明与逆向结论）
- Loon 抓的是**公网直链**，所以改动插件后记得同步推 GitHub；本地调试用 `python3 tools/serve.py`
- 主配置 `[Plugin]` 段里**列表顺序 = 生效顺序**，具体见各插件 README
