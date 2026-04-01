# 影视资源合集页 - 操作指引

## 项目简介

将金山文档中维护的影视资源合集，自动转换为美观的 HTML 页面，托管在 GitHub Pages 上。

- **在线页面**：https://huangyunbin.github.io/hub/ju/
- **数据源**：https://www.kdocs.cn/l/ceY4XreMYOc8 （金山文档）
- **用途**：微博等平台推广时，分享此链接作为资源合集入口

## 文件说明

```
ju/
├── index.html    # 最终展示的网页（由 sync.py 自动生成，不要手动编辑）
├── sync.py       # 核心脚本：抓取金山文档 → 解析内容 → 生成 HTML → 推送 GitHub
├── sync.sh       # 一键执行的 shell 快捷方式
└── README.md     # 本文件，操作指引
```

### sync.py 各模块功能

| 函数 | 功能 |
|------|------|
| `fetch_content()` | 用 Playwright 无头浏览器打开金山文档，提取文档纯文本内容 |
| `parse_entries()` | 解析文本，识别每部剧的标题、标签（画质/语言/类型/季数）、网盘链接 |
| `generate_html()` | 将解析结果填入 HTML 模板，生成带搜索、卡片布局、响应式的页面 |
| `git_push()` | 自动 git add + commit + push 到 GitHub |
| `main()` | 串联以上步骤，依次执行 |

### index.html 页面功能

- 紫色渐变头部 + 标题
- 搜索框：按片名实时过滤
- 卡片式布局：每部剧一张卡片，含标题、标签、网盘按钮
- 标签分类：绿色=画质，蓝色=语言，红色=类型
- 网盘按钮：紫色=夸克，蓝色=百度，橙色=阿里
- 手机端自适应

## 日常操作

### 更新资源（最常用）

1. 在金山文档中编辑（增删剧目、修改链接等）
2. 执行同步命令：

```bash
cd /tmp/hub-repo/ju && python3 sync.py
```

或：

```bash
cd /tmp/hub-repo/ju && bash sync.sh
```

3. 等待约 10 秒，页面自动更新

### 金山文档的编辑格式

sync.py 会自动识别以下格式：

```
剧名  【季数信息】 【画质】【语言】【类型】
夸克网盘：https://pan.quark.cn/s/xxxxx
百度网盘：https://pan.baidu.com/s/xxxxx
```

**支持的标签识别规则：**
- 画质标签：含 `4K`、`1080`、`高清`、`HDR` → 绿色
- 语言标签：含 `中英`、`双语`、`双字`、`字幕` → 蓝色
- 类型标签：含 `美剧`、`英剧`、`韩剧`、`电影`、`动漫`、`纪录片` → 红色
- 季数标签：含 `季`、`全集`、`特别篇` → 显示在标题后面
- 标题前加 🔥 emoji → 卡片标题前显示火焰图标
- 支持【方括号】和（圆括号）两种标签写法

**示例：**
```
🔥老友记  【1-10 季全集】 【1080p 高清】【中英双语】【美剧】
夸克网盘：https://pan.quark.cn/s/a95ceef1e76f
百度网盘：https://pan.baidu.com/s/12puC-mYHmifFz-sfdiIRMQ?pwd=68jd
```

### 修改页面配置

编辑 `sync.py` 顶部的配置区：

```python
KDOCS_URL = "https://www.kdocs.cn/l/ceY4XreMYOc8"  # 金山文档链接
WEIBO_ID = "你的微博ID"   # 页面底部显示的微博昵称
WEIBO_URL = "#"            # 微博主页链接
```

## 环境要求

### 首次安装

```bash
pip install playwright
playwright install chromium
```

### 运行环境
- Python 3.8+
- Git（已配置 push 权限）
- 网络可访问 kdocs.cn

## 注意事项

- `index.html` 是自动生成的，不要手动编辑（下次 sync 会覆盖）
- 所有内容编辑都在金山文档中进行
- 金山文档需要设置为"公开可查看"（当前已是）
- GitHub Pages 部署通常在 push 后 1-2 分钟生效
- 如果金山文档页面结构变化导致抓取失败，需要调整 `fetch_content()` 中的选择器
