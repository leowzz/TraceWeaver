# TraceWeaver Backend

本文档说明当前后端目录的实际情况和开发方式。

它不再沿用 FastAPI 模板项目的泛化描述，而是只记录这个仓库里真正存在的结构和命令。

## 当前后端职责

后端当前主要负责：

- 用户认证和基础用户接口
- 数据源配置管理
- 数据同步与活动去重
- 活动向量化
- LLM 模型配置管理
- Prompt 模板管理
- 图片分析结果接口
- 管理员调试接口

当前后端还没有：

- 正式的 `Activity` 查询 API
- 报告生成 API
- RAG 问答 API

## 目录结构

```text
backend/
├── app/
│   ├── api/            # API 路由
│   ├── clients/        # 外部客户端
│   ├── connectors/     # 数据源连接器
│   ├── core/           # 配置、DB、Celery 等基础设施
│   ├── crud/           # CRUD 封装
│   ├── models/         # SQLModel 模型
│   ├── schemas/        # 输入输出 schema
│   ├── services/       # 同步、向量化等服务
│   └── workers/        # Celery 任务
├── scripts/
├── tests/
├── Makefile
└── pyproject.toml
```

## 开发前准备

### 1. 配置文件

后端当前使用 YAML 配置文件。

在 `backend/` 目录执行：

```bash
cp config.yaml.template config.yaml
```

然后根据本地环境修改 `config.yaml`。

常见配置包括：

- `app`
- `database`
- `redis`
- `celery`
- `auth`
- `embedder`

说明：

- 配置优先级通常是环境变量高于 YAML
- `config.yaml` 是本地/部署配置，不应提交到版本库

### 2. 安装依赖

```bash
cd backend
uv sync
```

如果需要开发相关依赖：

```bash
uv sync --all-extras --dev
```

## 常用命令

当前后端以 `Makefile` 为主入口。

### 开发服务

```bash
make dev
make celery
make flower
```

说明：

- `make dev` 使用 `uvicorn` 热重载启动后端
- 后端开发端口当前是 `8010`

### 代码质量

```bash
make format
make lint
make test
make test-cov
```

### 数据库

```bash
make db-migrate
make db-upgrade
make db-downgrade
make db-revision
```

注意：

- `make db-migrate` 会交互式要求输入迁移描述
- 生成迁移后仍应人工检查脚本内容

### 向量化辅助脚本

```bash
make embed-dayflow USER_ID=<uuid>
make embed-test USER_ID=<uuid>
```

这两个命令主要用于已有 Dayflow 数据的向量化处理和调试。

## 当前核心模块

### Connector

当前已注册的连接器：

- `GitConnector`
- `DayflowLocalConnector`
- `SiYuanConnector`

### Service

当前较关键的服务包括：

- `SyncService`
- `EmbeddingService`
- `ImageAnalysisService`

### Worker

Celery 当前主要承担图片分析异步任务。

## 当前 API 范围

当前注册的 API 资源包括：

- `login`
- `users`
- `utils`
- `items`
- `source-configs`
- `llm-model-configs`
- `llm-prompts`
- `image-analyses`
- `debug`

其中真正贴近 TraceWeaver 业务的重点是：

- `source-configs`
- `llm-model-configs`
- `llm-prompts`
- `image-analyses`
- `debug`

## 测试

后端测试位于 `backend/tests/`。

常用执行方式：

```bash
cd backend
make test
```

或：

```bash
bash scripts/test.sh
```

## 当前边界

如果你正在阅读后端代码，需要先接受一个事实：当前 backend 更像“能力底座”，不是完整产品后端。

当前已经有：

- 同步入库
- 向量化
- 模型/Prompt 管理
- 图片分析

当前还没有：

- `Activity` 浏览 API
- 面向用户的搜索 API
- 报告引擎
- RAG 问答

## 相关文档

- [../README.md](../README.md)
- [../development.md](../development.md)
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [../docs/DATA_SOURCE_GUIDE.md](../docs/DATA_SOURCE_GUIDE.md)
