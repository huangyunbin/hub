# Full-Stack -> Static Playbook (GitHub Pages + hub)

本文档记录一套可复用流程：

1. 把一个前后端项目改造成纯静态前端项目
2. 用 JSON 快照替代后端 API
3. 发布到固定通用仓库 `hub` 的子路径（如 `/apify/`）

适用场景：

- 需要快速分享页面
- 不想维护线上后端
- 需要做历史快照对比和归档

---

## 1. 目标架构

从：

- 前端：`React/Vite`
- 后端：`FastAPI/Node/...`
- 数据：数据库 + API 查询

变成：

- 前端：纯静态页面
- 数据：同目录 JSON 文件（如 `projects.snapshot.json`）
- 部署：GitHub Pages
- 入口：`https://<user>.github.io/hub/<app-name>/`

---

## 2. 改造步骤（通用）

## Step 1: 盘点后端依赖

先列出前端目前依赖的 API：

- 列表接口
- 搜索接口
- 同步接口（如果有）
- 管理接口（如果有）

把它们分成两类：

- 必须保留的用户功能（列表、搜索、分页）
- 静态模式下应删除的功能（同步、写操作、后台任务）

## Step 2: 设计快照 JSON 结构

建议结构：

```json
{
  "snapshot": {
    "generated_at": "2026-03-05T05:17:49.709484+00:00",
    "source_db": "store_insights.db",
    "total_projects": 23051
  },
  "items": []
}
```

要点：

- `snapshot.generated_at` 用于页面展示“数据时间”
- `items` 只保留前端需要字段，避免文件过大
- 不要写本机绝对路径到 JSON 元数据

## Step 3: 写导出脚本（数据库 -> JSON）

建议在项目内固定一个导出脚本，例如：

- `scripts/export_static_snapshot.py`

职责：

- 连接数据库（SQLite/MySQL/Postgres）
- 按前端显示顺序导出数据（例如热门排序）
- 输出到前端 `public/` 目录

示例命令：

```bash
python3 scripts/export_static_snapshot.py
```

## Step 4: 前端 API 层改为本地读取

把原来的 `fetch("/api/...")` 改成读取静态文件：

```js
const SNAPSHOT_PATH = `${import.meta.env.BASE_URL}projects.snapshot.json`;
```

建议在前端做这些处理：

- 首次加载时缓存快照（避免重复网络请求）
- 预构建搜索索引（例如合并标题、描述、分类字段）
- 在前端完成分页和关键词匹配

## Step 5: 删除静态模式无效功能

通常需要删掉：

- “同步数据”按钮
- 触发后端任务的操作
- 任何 POST/PUT/DELETE 入口

保留：

- 列表
- 搜索
- 分页（上一页/下一页/跳页）

## Step 6: 调整构建配置为静态托管友好

Vite 推荐：

```js
export default defineConfig({
  base: "./",
});
```

原因：

- 子路径部署时资源引用稳定
- 复制目录后可以独立访问

## Step 7: 构建并验证

```bash
cd frontend
npm run build
```

检查产物必须同时存在：

- `dist/index.html`
- `dist/projects.snapshot.json`

---

## 3. 发布到通用仓库 `hub`（固定方案）

## 3.1 目录约定

`hub` 仓库建议长期固定如下：

```text
/
  index.html                # 总入口页
  .nojekyll
  /apify/                   # 子页面 A
  /<next-app>/              # 子页面 B
  /docs/                    # 规范文档
```

## 3.2 发布单个子页面

以 `apify` 为例：

1. 在业务项目里构建静态产物
2. 将产物同步到 `hub/apify/`
3. 推送 `hub/main`

示例：

```bash
# 1) 构建业务项目
cd /path/to/apify-store-insights/frontend
npm run build

# 2) 同步到 hub 子目录
rsync -a --delete /path/to/apify-store-insights/frontend/dist/ /path/to/hub/apify/

# 3) 提交并推送
cd /path/to/hub
git add .
git commit -m "Publish apify static page"
git push
```

## 3.3 GitHub Pages 配置

Pages 配置固定为：

- Source Branch: `main`
- Folder: `/` (root)

CLI（可选）：

```bash
gh api -X PUT repos/<user>/hub/pages -f 'source[branch]=main' -f 'source[path]=/'
```

页面地址：

- Hub 首页：`https://<user>.github.io/hub/`
- 子页面：`https://<user>.github.io/hub/apify/`

---

## 4. 新增另一个静态子页面（未来复用）

假设新功能名是 `seo`：

1. 把该项目改造为静态版并能输出 `dist/`
2. 同步到 `hub/seo/`
3. 更新 `hub/index.html` 加一个入口链接
4. `git push`

最终访问：

- `https://<user>.github.io/hub/seo/`

---

## 5. 数据更新与归档建议

## 最新版覆盖发布（推荐默认）

- 每次更新直接覆盖 `hub/apify/`
- URL 稳定，不用改分享链接

## 历史归档（需要对比时）

可以额外保留日期目录：

```text
/archives/apify/2026-03-05/
/archives/apify/2026-03-12/
```

再做一个对比页或索引页即可。

---

## 6. 常见坑

1. 构建后缺少 JSON 文件
   - 检查快照文件是否放在前端 `public/` 下
2. 子路径访问白屏
   - 检查 Vite `base` 是否正确，静态资源是否用相对路径
3. API 404
   - 说明前端还残留 `/api` 请求，没有完全静态化
4. 首次发布 404
   - GitHub Pages 构建中，等待 1-2 分钟再测
5. 文件过大加载慢
   - 精简字段，必要时分片快照或加压缩

---

## 7. 本次项目落地信息（apify）

- 子页面路径：`/apify/`
- 数据文件：`projects.snapshot.json`
- 已发布地址：`https://huangyunbin.github.io/hub/apify/`
- 发布仓库：`https://github.com/huangyunbin/hub`

这套流程后续可直接复制到其他子页面。
