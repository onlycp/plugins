# 班级小管家 去广告（Loon 插件）

面向 **iOS App**（App Store id `1524125516`，bundle `com.banjixiaoguanjia.app`，开发方 北京校萌科技 / 北京班级小管家科技）。
配合可莉（iKeLee）的「广告平台拦截器」使用。

- 所属仓库：<https://github.com/onlycp/plugins>（路径 `loon/banjixiaoguanjia-remove-ads/`，发布后不改路径）
- 插件文件：`banjixiaoguanjia-remove-ads.lpx` · 图标：`icon.png`

---
## 一、App 的广告是怎么来的（逆向结论）

App 是 Flutter 写的，广告分成**两套完全独立的系统**：

### 1. 三方 SDK 广告（开屏、部分插屏）

- 客户端里有 `AppAds` 类，日志字符串可以一一对上：
  - `AppAds showSplash` → `AppAds showSplashPage pop posId:103544143`，`103544143` 是**优量汇开屏广告位 ID**（硬编码在客户端）。
  - 其它写死的位号：`103544338`、`102255258`（首页/完成页弹窗）、`5209496`。
- 展示前会先做三重判断：`checkConfig(posId)` → `checkPlatformConfig(4)` → `isPhonePortrait`。
  **任何一环拿不到配置就不展示** —— 所以「把配置接口弄空」和「把 SDK 域名墙掉」都能让开屏广告消失。
- 位配置由 `https://service.banjixiaoguanjia.com/app/getAdConfV2` 下发，本地缓存 key = `ad_config_v2`。
  （实测该接口要求 App 侧的签名/参数，裸请求返回 `{"code":900,"msg":"此版本过低..."}`，因此**结构未验证**，插件默认不动它。）
- 官方《第三方 SDK 目录》(`/public/website/app_sdk_list.html`) 列出的广告平台：
  优量汇、穿山甲、Funlink、美数聚合、AdScope、亿帆、优推、Octopus、趣盟。

### 2. App 自建广告位（导流到支付宝小程序）

- 配置是一个**公开的静态 JSON**（不需要登录、可直接 curl）：
  `https://allsystemfile.welife001.com/app/ads/app_ads_config.json`
- 真实返回（2026-10 实测）：

  ```json
  {"code":0,"msg":"success","data":[
    {"platform":"zfb","posid":"111101","name":"app_ad_home_banner", ...},
    {"platform":"zfb","posid":"111103","name":"app_ad_home_chapin", ...},
    {"platform":"zfb","posid":"111102","name":"app_ad_post_end_banner", ...}
  ]}
  ```

  对应首页 Banner、首页插屏、作业结束页 Banner，点击后跳支付宝小程序。
- 客户端逻辑：`code==0` 时解析 `data` 列表 → 按 `name`/`posid` 查表 → 查到才展示。
  **把 `data` 换成 `[]`，这些广告位全部消失**，且不会影响任何业务逻辑。
- 另一个静态配置 `app_config.json` 里有 `data.ads.submit_card_list` 和 `data.ads.app_ad_home_icon`
  两个广告开关（当前是空数组，但服务端随时能塞内容），插件一并兜底清空。

---
## 二、图标

用的是**官方 App Store 图标**（512×512 PNG），已随插件放进本仓库，`#!icon` 指向仓库内的 raw 直链：

```
#!icon=https://raw.githubusercontent.com/onlycp/plugins/main/loon/banjixiaoguanjia-remove-ads/icon.png
```

- **想换图标：直接替换同目录的 `icon.png`**（正方形 PNG，建议 256×256 或 512×512），插件正文一行都不用改。
- Loon 是**联网拉取**图标 URL 的，所以必须是公网可达地址；`raw.githubusercontent.com` 偶尔抽风时，可以把 `#!icon` 换成同路径的 jsDelivr 镜像：
  `https://cdn.jsdelivr.net/gh/onlycp/plugins@main/loon/banjixiaoguanjia-remove-ads/icon.png`
- 本地调试期间也可以临时指向 `http://<Mac IP>:8000/loon/banjixiaoguanjia-remove-ads/icon.png`（服务用 `tools/serve.py` 起）。

## 三、插件做了什么

| 手段 | 内容 | 是否需要 MitM |
| --- | --- | --- |
| `[Rule]` 补漏 | 可莉「广告平台拦截器」未覆盖的 6 个广告 SDK 域名 REJECT | 否 |
| `[Rewrite]` | 把自建广告位配置 `app_ads_config.json` 的 `data` 改写为 `[]`；兜底清空 `app_config.json` 的两个广告开关数组 | 是（仅 `allsystemfile.welife001.com`） |
| 进阶（默认注释） | `/app/getAdConfV2` 的响应改写 / Mock，等抓到真实结构再启用 | 是 |

补漏的 6 个域名（都已用 `dig @223.5.5.5` 验证有解析）：

- `atdplus.cn`（美数聚合，CNAME 到 `adx-svr.1rtb.com`）、`admate.cn`
- `ad-scope.com.cn`（AdScope）
- `yfanads.cn`（亿帆，主域无解析但 `www.yfanads.cn` 有）
- `gameley.com`（优推，`youtui.gameley.com` 有）
- `qttunion.com`（趣盟）

已由可莉覆盖、此处不重复：`gdt.qq.com` / `pgdt.qq.com` / `ugdtimg.com`（优量汇）、`*.pangolin*` / `*.snssdk.com`（穿山甲）、`adfunlink.com`（Funlink）、`sdk.zhangyuyidong.cn`（Octopus）。

**MitM 故意只加 `allsystemfile.welife001.com`**，不碰业务网关 `service.banjixiaoguanjia.com`，避免解密登录/作业流量，也避免万一 App 做证书校验时整个 App 不可用。

---
## 四、安装

### 1. 从 GitHub 安装（推荐）

raw 直链：

```
https://raw.githubusercontent.com/onlycp/plugins/main/loon/banjixiaoguanjia-remove-ads/banjixiaoguanjia-remove-ads.lpx
```

一键导入（Loon 会自己打开并询问是否添加插件）：

```
https://www.nsloon.com/openloon/import?plugin=https%3A%2F%2Fraw.githubusercontent.com%2Fonlycp%2Fplugins%2Fmain%2Floon%2Fbanjixiaoguanjia-remove-ads%2Fbanjixiaoguanjia-remove-ads.lpx
```

也可以手动加：Loon → `配置 → 插件 → 添加`，粘贴上面的 raw 直链。

**更新插件**：改动推到 GitHub 后，在 Loon 的插件列表里对该插件点「更新」即可。
本仓库约定**插件路径发布后不再改动**——改路径等于换了个新插件，老用户不会自动更新。

### 2. 本地调试（改插件时用这个）

```bash
cd /Users/chenpeng/Cloud/onlycp-plugins
python3 tools/serve.py            # 默认 8000 端口，可传其它端口号
```

手机与 Mac 同一局域网，浏览器打开终端里打印的 `http://<Mac IP>:8000/`：
首页会自动列出仓库里所有插件，并生成**手机可点的一键导入按钮**。改完 `.lpx` 重新导入就生效（服务已对插件文件禁用缓存）。

### 3. 主配置里的顺序（重要）

```ini
[Plugin]
https://kelee.one/Tool/Loon/Lpx/BlockAdvertisers.lpx, enabled = true
https://raw.githubusercontent.com/onlycp/plugins/main/loon/banjixiaoguanjia-remove-ads/banjixiaoguanjia-remove-ads.lpx, enabled = true
```

**列表顺序 = 生效顺序**，可莉的 BlockAdvertisers 必须在上面。

---

## 五、怎么确认插件真的生效

1. Loon → `请求记录`，筛选 `allsystemfile.welife001.com`，冷启动 App。
2. 找到 `/app/ads/app_ads_config.json` 这条响应，展开 Body，应该看到 `"data":[]`。
   - 还是原始三条记录 → 改写没生效：检查 MitM 是否包含 `allsystemfile.welife001.com`、证书是否已安装并信任。
   - 请求记录里**根本看不到该域名** → 说明 App 用了缓存（客户端会把上次结果存本地），清一次 App 缓存或重装后再看。
3. 找 `service.banjixiaoguanjia.com` 下的 `getAdConfV2`，把它的响应 JSON 复制出来（这就是进阶改写需要的结构）。
## 六、验证清单

打开插件后依次确认（任何一项异常就先把 `[Rewrite]` 两行注释掉回滚）：

- [ ] 开屏广告消失，且启动没有多出几秒白屏
- [ ] 首页顶部/信息流没多出「支付宝」样式的 Banner
- [ ] 作业结束页没有横幅广告
- [ ] 交作业、上传照片、语音、录音回放正常
- [ ] 打卡 / 成绩单 / 通知消息正常
- [ ] 加载图片、视频、语音（`img|video|record|file.welife001.com` 等 CDN）正常

---
## 七、边界与风险

- **只对 App 生效**。微信小程序里的广告走微信通道，域名拦截无效。
- 教育类 App 涉及未成年人数据，本插件**不含任何统计/上报逻辑**，也**不解密图片、语音、视频 CDN**：
  `img|video|record|file|cosimg|disk|album.welife001.com`、`campusfile.welife001.com`、`tos*.banjixiaoguanjia.com` 一律不进 MitM。
- 建议按 App 精细控制（只给班级小管家开这个插件），银行/支付类 App 不要开。
- 本地调试用的 HTTP 服务（`tools/serve.py`）对**整个局域网**开放（日志里已经看到 `192.168.3.168` 这类无关设备来敲门），调试完请 `Ctrl+C` 关掉。
- 插件 `[Rule]` 只能用 `DIRECT` / `REJECT` 系列 / `PROXY` 三种策略。

---
## 八、下一步（可选）

1. 用 Loon 的「请求记录」只筛 `service.banjixiaoguanjia.com`，冷启动复现开屏广告，抓 `/app/getAdConfV2` 的**真实响应结构**。
2. 拿到结构后启用 `[Rewrite]` 里注释掉的进阶两行（注释里已写好两种写法），比单纯墙域名更干净：客户端连 `/launch_page` 都不会跳，也不会有白屏风险。
3. 要做同款其它客户端的版本，直接在仓库里新建 `surge/<插件id>/`（`.sgmodule`）、`quantumultx/<插件id>/`（rewrite 片段）即可，域名清单和改写逻辑可以直接复用。

### 插件 `[Rewrite]` 语法备忘（Loon 旧版语法）

```ini
^https://example\.com/api response-body-json-replace data []      # 把 data 换成空数组
^https://example\.com/api response-body-json-del data.ad          # 删掉某个 key
^https://example\.com/api response-body-json-jq 'del(.data.ad)'   # 用 jq 表达式
```

单行按空格分参数，值里不能有空格（要写空格用 `\x20`）。另外 `reject-dict` 返回的是 `{}`，
对本 App 的 `{"code":..,"msg":..,"data":..}` 信封格式会解析失败，所以本插件不用它。
