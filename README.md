# TraceWeaver

> 个人数据痕迹采集与处理平台，当前重点是数据源同步、统一活动模型、向量化和若干管理/调试能力。

## 项目现状

`TraceWeaver` 目前还不是一个完整的“个人知识库产品”，更准确地说，它现在是一个已经跑通部分核心底座的工作台：

- 支持配置和管理多种数据源
- 支持把外部数据同步为统一的 `Activity`
- 支持将活动内容切块并写入 `pgvector`
- 支持管理 LLM 模型配置和 Prompt 模板
- 支持基于 Prompt 的图片分析任务与结果查看
- 提供若干管理员调试页面，用于验证 SiYuan SQL 和向量检索链路

README 以下内容只描述当前仓库里已经存在的能力；还没实现的能力统一放到文末 `TODO`。

## 已实现能力

### 数据源管理

当前前后端都已经实现了数据源配置管理：

- `Git` 数据源
- `Dayflow` 数据源
- `SiYuan` 数据源

支持的操作：

- 创建数据源配置
- 编辑数据源配置
- 删除数据源配置
- 测试连接
- 手动触发同步

说明：

- `Dayflow` 当前实际接入的是本地 SQLite 数据库文件，不是 README 旧版本里写的 API/CSV 方案
- 同步入口已经在后端和前端打通，但首页当前只提供了 `Dayflow` 的便捷同步卡片

### 统一活动模型

不同来源的数据会被标准化为统一的 `Activity` 记录，核心字段包括：

- `user_id`
- `source_config_id`
- `source_type`
- `title`
- `content`
- `extra_data`
- `fingerprint`
- `created_at`
- `updated_at`

这个模型是当前仓库里最明确的核心抽象，数据同步、去重和向量化都围绕它展开。

### 同步与向量化

当前同步链路已经具备：

1. 从已配置的数据源抓取活动
2. 将数据转换为统一 `Activity`
3. 基于 `fingerprint` 做去重和更新
4. 将活动文本切块
5. 生成 embedding
6. 将向量写入 `activity_embedding` 表

当前 embedding 相关实现特点：

- 向量存储使用 `PostgreSQL + pgvector`
- 已接入 `Agno`
- 当前实际可用的 embedder provider 只有 `Ollama`

### LLM 配置与 Prompt 管理

前后端提供了两套管理能力：

- `LLM Models`：管理模型连接配置
- `LLM Prompts`：管理 Prompt 模板

当前这部分能力主要服务于图片分析功能，而不是通用对话或 RAG 问答。

### 图片分析

仓库当前有一条完整的“图片分析”链路：

- 配置 LLM 模型
- 配置 Prompt 模板
- 提交图片分析任务
- 使用 Celery 异步执行分析
- 保存分析结果
- 在前端查看已完成分析结果

目前图片来源主要围绕 `SiYuan` 本地资源。

### 调试能力

当前还有两个明显偏内部/管理员使用的调试入口：

- `Debug SQL`：执行 SiYuan SQL 查询
- `Debug Vector`：执行向量检索，查看相似度和命中 chunk

这说明“向量检索底座”已经能验证，但它还不是面向普通用户的正式搜索产品。

## 当前页面

前端当前主要页面包括：

- `/`：Dashboard，当前主要展示 `Dayflow` 同步卡片
- `/datasources`：数据源管理
- `/llm-models`：LLM 模型配置管理
- `/llm-prompts`：Prompt 模板管理
- `/image-analyses`：图片分析结果查看
- `/admin`：用户管理
- `/debug-siyuan-sql`：管理员 SQL 调试
- `/debug-vector-search`：管理员向量检索调试
- `/settings`：用户设置

如果你期待的是“个人知识库首页 / 搜索框 / AI 问答页 / 报告页”，这些目前都还没有落地。

## 技术栈

### 后端

- FastAPI
- SQLModel
- PostgreSQL
- pgvector
- Alembic
- Agno
- Celery
- Loguru

### 前端

- React 18
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Tailwind CSS
- shadcn/ui

### 基础设施

- Docker Compose
- Traefik
- Playwright

## 快速开始

### 前置要求

- Docker
- Docker Compose
- `uv`，用于本地 Python 开发
- `pnpm`，用于本地前端开发

### 启动整套服务

```bash
docker compose watch
```

启动后可访问：

- 前端：<http://localhost:5173>
- 后端 API：<http://localhost:8000>
- Swagger：<http://localhost:8000/docs>
- Adminer：<http://localhost:8080>
- Traefik UI：<http://localhost:8090>
- MailCatcher：<http://localhost:1080>

更详细的本地开发说明见 [development.md](development.md)。

## 本地开发

### 后端

```bash
cd backend
make dev
make test
make lint
```

### 前端

```bash
cd frontend
pnpm dev
pnpm build
```

## 项目结构

```text
TraceWeaver/
├── backend/
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── clients/        # 外部客户端封装
│   │   ├── connectors/     # 数据源接入层
│   │   ├── crud/           # 数据访问层
│   │   ├── models/         # SQLModel 模型
│   │   ├── schemas/        # Pydantic/SQLModel schema
│   │   ├── services/       # 同步、向量化等服务
│   │   └── workers/        # Celery 任务
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── hooks/
│   │   └── client/         # 生成的 API client
│   └── tests/
├── docs/
├── docker-compose.yml
└── README.md
```

## 当前系统边界

如果只按现在的仓库状态来描述，比较准确的数据流是：

```text
数据源配置 -> 连接器抓取数据 -> 统一 Activity -> 数据库存储 -> 文本切块 -> 向量化 -> pgvector
                                                       \
                                                        -> 图片分析相关配置与异步任务
```

已经实现的是“采集、规范化、向量化、配置管理、分析任务”这层。

还没有实现的是“真正面向最终用户的知识库产品层”。

## TODO

下面这些方向在仓库文档和架构里经常出现，但当前代码里还没有完整落地：

- 面向普通用户的语义搜索页面和正式搜索 API
- 基于个人数据的 RAG 问答 / AI 助手
- 日报、周报等自动化报告生成
- 报告保存、编辑和版本管理
- 可视化时间线或活动流页面
- 围绕 `Activity` 的用户可读浏览页
- 非调试用途的检索结果展示与上下文拼装
- 更完整的嵌入模型支持
- 更通用的 Dayflow 接入方式，例如远程 API

## 相关文档

- [development.md](development.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_SOURCE_GUIDE.md](docs/DATA_SOURCE_GUIDE.md)
- [docs/API_CONVENTIONS.md](docs/API_CONVENTIONS.md)

## 说明

`docs/ARCHITECTURE.md` 和旧版 README 中有一些内容描述的是目标架构或未来形态，不完全等同于当前实现。判断当前功能是否真的可用时，请优先以 `backend/app`、`frontend/src/routes` 和实际 API 路由为准。
