# atuo-social

个人自媒体内容工作流：**订阅 → 收件箱 → AI 改写 → 多平台分发**。

## 功能（当前 MVP）

- **收件箱**：RSS / Atom 订阅，Twitter 列表抓取，按订阅源/状态筛选
- **AI 改写**：基于规则（关键词、标签、来源匹配）自动把收件箱条目改写为草稿；也可手动单条改写
- **多 LLM**：Anthropic Claude / OpenAI / DeepSeek / 通义千问，可热切换
- **草稿编辑**：标题、Markdown 正文、封面、图片素材
- **多平台发布**：当前接入 Twitter/X（v2 + 媒体上传）；适配器接口已就绪，后续接入微博、小红书、知乎、公众号等
- **定时排期**：APScheduler 持久化，重启不丢任务
- **数据回流**：Twitter `public_metrics` → `metric_snapshot`

## 目录结构

```
backend/    FastAPI + SQLAlchemy + APScheduler
frontend/   Vue 3 + Element Plus + Vite
docker-compose.yml
.env.example
```

## 本地开发

```bash
# 1. 配置
cp .env.example .env
# 编辑 .env 填 SECRET_KEY

# 2. 后端
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端（另一个终端）
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

## Docker 一键启动

```bash
cp .env.example .env  # 修改 SECRET_KEY
docker compose up -d --build
# 前端 http://localhost:8080  后端 http://localhost:8000
```

## 端到端验证

1. 浏览器打开前端 → "AI 设置" 页面，录入 Claude / OpenAI 等任一 Key 并设为激活
2. "订阅源" 页面 → 新增 RSS（如 `https://hnrss.org/frontpage`）→ 点 "立即抓取"
3. "收件箱" 页面看到条目 → 点 "改写" → "草稿/发布" 中出现新草稿
4. （可选）"账号" 页面绑定 Twitter API Key（需要从 developer.twitter.com 申请）
5. 编辑草稿 → 选目标账号 → 点发布 / 设定时

## 平台适配器

新平台只需在 `backend/app/platforms/` 实现 `PlatformAdapter` 子类（`publish` / `fetch_metrics` / `adapt_content`），并在 `registry.py` 注册即可。

## 开发约定

- **加密**：所有 API Key 与 Cookie 通过 Fernet 加密存库（`SECRET_KEY` 派生）
- **测试**：`cd backend && pytest`
- **数据**：SQLite 落 `backend/data/atuo.db`，Compose 挂卷持久化
