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
| `[Rule]` 补漏 | 5 个域名 `DOMAIN-SUFFIX` → `REJECT`，都经过 `tools/kelee-coverage.py` 核对、确认可莉确实没盖 | 否 |
| `[Rewrite]` | ① 自建广告位 `app_ads_config.json` 的 `data` → `[]`；② 广告图目录 `/app/ads/imgs/` 整段 `reject` 兜底；③ 精确清空 `app_config.json` 里的两个广告开关数组 | 是（仅 `allsystemfile.welife001.com`） |
| 进阶（默认注释掉） | `/app/getAdConfV2` 的响应改写 / Mock，等抓到真实结构再启用 | 是（要开业务网关，默认坚决不做） |

### 3.1 域名补漏：只补可莉确实没盖的 5 条

规则不是越多越好。可莉的 `BlockAdvertisers` 已经把主流广告 SDK 覆盖得相当全，
本插件**只补它确实漏的**，免得两个插件在同一批域名上重复堆规则、以后互相打架。

**核对基准：可莉 2026-10-02 版，346 条规则。**

| 域名（本插件加的） | 平台 | 可莉 2026-10-02 版的状态 |
| --- | --- | --- |
| `atdplus.cn` | 美数聚合 | ❌ 没有 —— 她只墙了它的上游 RTB `1rtb.com` / `1rtb.net`，落地域名反而没盖 |
| `admate.cn` | 美数聚合 | ❌ 没有 |
| `yfanads.cn` | 亿帆 | ❌ 没有 —— 她写的是 `yfanads.com`，`.cn` 是另一个域名（实测 `www.yfanads.cn` 有解析） |
| `gameley.com` | 优推 | ❌ 没有 —— 她只墙了 `ad.gameley.com`，而 `youtui.` / `www.gameley.com` 也有解析 |
| `qttunion.com` | 趣盟 | ❌ 没有 |

**已由可莉覆盖、这里刻意不重复写的**（均为 2026-10-02 版**实测**，不是猜的）：

| 平台 | 可莉用的规则 |
| --- | --- |
| 优量汇（腾讯广告） | `DOMAIN-SUFFIX,gdt.qq.com` / `gdtimg.com` / `ugdtimg.com` —— **整域**，不是逐子域 |
| 穿山甲 | `DOMAIN-KEYWORD,pangolin` / `pglstatp` / `panplayable-toutiao`，`DOMAIN-SUFFIX,pangle.io` |
| AdScope（轻变聚合） | `DOMAIN-SUFFIX,ad-scope.com.cn` |
| Funlink | `DOMAIN-SUFFIX,adfunlink.com` |
| Octopus | `DOMAIN,sdk.zhangyuyidong.cn` / `sdklog.zhangyuyidong.cn` |
| 美数上游 RTB | `DOMAIN-SUFFIX,1rtb.com` / `1rtb.net` |
| 优量汇 SDK 配置 | `DOMAIN,sdk.e.qq.com` |

#### 怎么复核这一层依赖（踩过的坑，务必看）

```bash
python3 tools/kelee-coverage.py -k <可莉BlockAdvertisers副本.lpx>
```

脚本会打印可莉副本的 `#!date`，并逐条告诉我们「这条她已覆盖/她确实没有」。

> **⚠️ 这个脚本是踩坑之后写的。** 最初复核时我拿到的是 GitHub 上一个备份仓库里的 `.lpx`，
> 它的 `#!date` 是 **2025-09-16**（落后整整一年）；同时可莉的规则写法是
> `DOMAIN-SUFFIX, gdt.qq.com, REJECT`——**逗号后面带空格**。两个因素叠加，
> 我得出「可莉漏了优量汇 `win.` / `v.` / `sdk.gdt.qq.com`」的**错误结论**，
> 往插件里加了 3 条多余规则（`gdt.qq.com`、`ugdtimg.com`、`ad-scope.com.cn`）并推上了 GitHub。
> 换成 **2026-10-02** 的副本重新核对才发现，这些她早就整域盖住了，现已删除。

所以以后核对可莉覆盖，记住两条：

1. **先看副本的 `#!date`** —— 第三方备份仓库（KeleeOne、kele、Tool 之类）经常落后好几个月，很容易把它当成"可莉现状"。
2. **比对前去掉逗号后的空格** —— 她的规则是 `DOMAIN-SUFFIX, xxx, REJECT`，直接拼 `DOMAIN-SUFFIX,xxx` 去匹配会全部漏判。

`tools/kelee-coverage.py` 已经把这两件事都处理了，直接用它就行（它也会在有重复规则时报出来）。

解析结论均用 `dig @223.5.5.5` 实测（本机 DNS 被 fake-ip 接管，只能指定 DNS 查）：

```
www.yfanads.cn      14.103.234.158
youtui.gameley.com  81.70.205.221
gdt.qq.com          113.108.27.43      win.gdt.qq.com  123.151.49.178
v.gdt.qq.com        113.108.81.233     sdk.gdt.qq.com  119.147.12.159
```

（最后两行是优量汇的子域，**由可莉的整域规则拦掉**，写在这里只是存档，本插件没有再重复加。）

> **两个反例（别照抄网上的大杂烩规则集）**
> 1. **不要写 `DOMAIN-SUFFIX,snssdk.com,REJECT`** —— 抖音等字节系 App 的业务接口（`aweme.snssdk.com`）就在同一域名下。可莉自己的做法是用 `AND` 规则把「字节系 API 域名 + `tnc` 关键字」显式 `DIRECT`，要拦就学她那种做法，别整域墙。
> 2. **不要碰用户数据 CDN** —— `img|video|record|file|cosimg|disk|album.welife001.com`、`campusfile.welife001.com`、`tos*.banjixiaoguanjia.com` 放的是孩子的照片、语音、作业附件，一条都不能拦。

### 3.2 广告图兜底

自建广告位的图片（`img_ad_zfb_*.webp`）和那份配置 JSON 在**同一个静态站**的 `/app/ads/imgs/` 下。
配置清空后客户端本来就不该再拉图，但客户端有本地缓存，冷启动的一瞬间仍可能闪出旧图，
所以再加一条 `reject` 把整个目录封死——广告位只会是空的，连闪一下都不会。

### 3.3 `app_config.json` 只清两个键，不整包替换

这个文件里还有 `soe` / `launch` / `record` / `post` / `notification` 等十几项**业务配置**，
所以规则只精确清空 `data.ads.submit_card_list` 与 `data.ads.app_ad_home_icon` 两个键，
其余字段一个字节都不动。**这条是硬约束**：写成整包 `data` 替换会把作业、打卡、通知等配置一起打掉。

### 3.4 MitM 范围：只解密一个静态资源站

**故意只加 `allsystemfile.welife001.com`**，不碰业务网关 `service.banjixiaoguanjia.com`，
避免解密登录 / 作业 / 成绩等请求，也避免万一 App 做证书校验时整个 App 不可用。

- `service.banjixiaoguanjia.com`：承载登录、作业，**故意不加**。想改写 `/app/getAdConfV2` 就必须加它，所以这个进阶方案默认关闭、只留注释。
- `allsystemfile.banjixiaoguanjia.com`：另一个火山 TOS 存储桶，2026-10-16 实测 `/app/ads/app_ads_config.json` 返回 `NoSuchKey`，广告配置只在 `welife001.com` 上，**不用加**。


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

### A. 域名拦截（`[Rule]`，不用 MitM，最容易先看）

1. 冷启动 App，「请求记录」里筛本插件保留的 5 个域名 `atdplus.cn`、`admate.cn`、`yfanads.cn`、`gameley.com`、`qttunion.com`，应该看到请求被拒绝、根本没出网。
   （可莉自己已覆盖的 `gdt.qq.com` / `ugdtimg.com` 等，筛出来会挂在可莉那条规则上，属正常。）
2. 看到广告消失即生效。若这些域名仍正常返回 → 多半是本插件排在了可莉**上面**（插件顺序 = 生效顺序，见第四节），或插件没启用。

### B. 配置改写（依赖 MitM）

1. Loon → `请求记录`，筛选 `allsystemfile.welife001.com`，冷启动 App。
2. 找到 `/app/ads/app_ads_config.json` 这条响应，展开 Body，应该看到 `"data":[]`。
   - 还是原始三条记录 → 改写没生效：检查 MitM 是否包含 `allsystemfile.welife001.com`、证书是否已安装并信任。
   - 请求记录里**根本看不到该域名** → 说明 App 吃了缓存（客户端会把上次结果存本地），清一次 App 缓存或重装再看。
3. 顺手确认 `/app/ads/imgs/` 下的图片请求返回的是空响应（被 `reject` 掉）。

### C. 想拿进阶改写要的数据结构（可选，且是临时动作）

默认方案**不解密业务网关**。如果确实想推进 `/app/getAdConfV2` 那条进阶路线，
就临时在 MitM 里加上 `service.banjixiaoguanjia.com`，冷启动一次把该接口的响应 JSON 抄出来，
**抄完立刻把这行删掉**——不要把业务网关长期留在 MitM 里。

## 六、验证清单

打开插件后依次确认（任何一项异常，先把 `[Rewrite]` 段整段注释掉回滚——现在是 3 条改写）：

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
- MitM 只解密 `allsystemfile.welife001.com` 这一个静态站，且只改写 3 条明确的广告/图片路径；若你还有别的 App 也从这个站取资源，注意 `[Rewrite]` 的路径匹配是否可能误伤（本插件匹配的都是 `/app/ads/` 与 `app_config.json` 的固定路径）。
- 本地调试用的 HTTP 服务（`tools/serve.py`）对**整个局域网**开放（日志里已经看到 `192.168.3.168` 这类无关设备来敲门），调试完请 `Ctrl+C` 关掉。
- 插件 `[Rule]` 只能用 `DIRECT` / `REJECT` 系列 / `PROXY` 三种策略。
- **`[Rule]` 是全设备生效的，不是「只对这个 App」。** 上面 5 个都是纯广告域名（美数 / 亿帆 / 优推 / 趣盟），
  任何 App 都不该访问它们，所以全局 REJECT 是安全的；反过来说，**千万别往里加业务域名**（见 3.1 的两个反例）。
  代价是：它会连带挡住**别的 App 里的优量汇/美数广告**（例如某些游戏的开屏）。对"全局去广告"这是期望行为；
  如果你只想动班级小管家，只能把整域 `SUFFIX` 改回更窄的子域列表，代价是重新出现漏网子域。

---
## 八、下一步（可选）

1. 抓 `/app/getAdConfV2` 的**真实响应结构**（临时开业务网关 MitM 的做法见 5.C，抓完记得删）。
2. 拿到结构后启用第四节里注释掉的进阶写法（`response-body-json-replace` / `mock-response-body` 两种等价写法任选一行）。它比单纯墙域名干净：客户端连 `/launch_page` 都不会跳，也不会有白屏风险。
3. 要做同款其它客户端的版本，直接在仓库里新建 `surge/<插件id>/`（`.sgmodule`）、`quantumultx/<插件id>/`（rewrite 片段）即可，域名清单和改写逻辑可以直接复用。

### 插件 `[Rewrite]` 语法备忘（Loon 旧版语法）

```ini
^https://example\.com/api response-body-json-replace data []      # 把 data 换成空数组
^https://example\.com/api response-body-json-del data.ad          # 删掉某个 key
^https://example\.com/api response-body-json-jq 'del(.data.ad)'   # 用 jq 表达式
```

单行按空格分参数，值里不能有空格（要写空格用 `\x20`）。另外 `reject-dict` 返回的是 `{}`，
对本 App 的 `{"code":..,"msg":..,"data":..}` 信封格式会解析失败，所以本插件不用它。

---

## 九、能不能收录到可莉的插件中心？

**结论：可以，但没有公开投稿入口，只能联系可莉本人手动收录；而且这个插件并不依赖收录。**

| 事实 | 依据（2026-10-16 实测） |
| --- | --- |
| 插件中心 | <https://hub.kelee.one> |
| 列表数据源 | <https://hub.kelee.one/list.json>（275 条插件） |
| 275 条插件的下载地址 | **全部**指向 `https://kelee.one/Tool/Loon/Lpx/<名字>.lpx`——即插件托管在她自己的服务器上，**没有一条指向作者自己的 GitHub 仓库** |
| 投稿说明 | 她的仓库里没有 `CONTRIBUTING` 或投稿章节 |
| 唯一联系入口 | Telegram 频道 [`@ibilibili`](https://t.me/ibilibili)（「֍可莉日常֎」） |
| 她的 GitHub | [`luestr`](https://github.com/luestr)（主仓库 `luestr/ProxyResource`） |

清单里没有一个外部地址，说明插件中心是**她一个人维护的托管列表**，不是自助提交的分发索引——
要收录得她本人点头（她很可能还会自己复核规则、改写成她的写法再放进自己仓库）。

### 想投稿就照这个发

```text
你好，我想投稿一个 Loon 插件：班级小管家去广告
https://raw.githubusercontent.com/onlycp/plugins/main/loon/banjixiaoguanjia-remove-ads/banjixiaoguanjia-remove-ads.lpx

定位：你的 BlockAdvertisers 的补充，不是替代，安装时放在它下方。
[Rule] 只有 5 个域名，都核对过你 2026-10-02 版确实没盖：
atdplus.cn / admate.cn / yfanads.cn / gameley.com / qttunion.com；
你已覆盖的 gdt.qq.com、gdtimg.com、ugdtimg.com、ad-scope.com.cn 我都没有重复写。
主要手段是 [Rewrite]：改的是 App 自建的支付宝广告位静态 JSON（allsystemfile.welife001.com），
MitM 只开这一个静态资源站，不碰业务网关，也不碰照片/语音/视频 CDN。
README 里写明了依赖你的插件并置于其下方。
```

### 两个提醒

- **授权**：她的资源库标注 CC BY-NC-SA 4.0，并要求「非商业、不得在中国境内平台传播」。
  本插件**没有复制她的任何规则文本**，只是刻意避开重合域名（对照表见 3.1），属于独立作品；
  但以后若要直接引用她的规则片段，需按其许可署名、以相同方式共享，也不要用于商业售卖或在中国境内平台传播。
- **收录不是必需**：本插件靠 raw 直链安装与更新（见第四节），收录只是多一个曝光入口；
  而且收录后每次更新要等她同步，而你自己推 GitHub 后，用一键导入的用户立刻就能更新。
