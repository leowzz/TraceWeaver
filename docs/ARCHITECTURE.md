# TraceWeaver 架构说明

本文档描述的是当前仓库已经落地的架构，而不是理想状态下的完整产品架构。

如果你在旧文档里见过 `RAG 问答`、`报告引擎`、`时间线页面` 等内容，请把它们理解为未来方向；当前代码的核心仍然是：

- 数据源配置与接入
- 活动同步与去重
- 向量化与向量存储
- LLM 配置和 Prompt 管理
- 图片分析异步任务
- 若干管理员调试页面

## 1. 当前架构概览

TraceWeaver 当前最稳定的主链路可以概括为：

```text
外部数据源 -> Connector -> Activity -> PostgreSQL
                                   \
                                    -> EmbeddingService -> activity_embedding (pgvector)

LLM Model Config + LLM Prompt -> Celery Task -> Image Analysis Result
```

系统仍然遵循明显的分层思路，但还没有完全演化成文档里曾经描述的“完整知识库产品”。

## 2. 当前主要模块

### 2.1 API 层

后端 API 路由当前集中在 `backend/app/api/routes/`，已注册的资源包括：

- `login`
- `users`
- `utils`
- `items`
- `source-configs`
- `llm-model-configs`
- `llm-prompts`
- `image-analyses`
- `debug`

这意味着当前后端已经有：

- 用户认证和基础用户接口
- 数据源配置接口
- 模型配置接口
- Prompt 管理接口
- 图片分析结果接口
- 调试接口

但当前没有：

- `activities` 查询接口
- 面向普通用户的语义搜索接口
- `reports` 接口
- `chat` / `rag` / `assistant` 接口

### 2.2 Connector 层

Connector 是当前最明确的架构边界之一。每个数据源通过统一接口接入，负责：

1. 验证配置
2. 拉取指定时间范围内的数据
3. 转换为统一的 `ActivityCreate`
4. 生成指纹用于去重

当前已注册的连接器：

- `GitConnector`
- `DayflowLocalConnector`
- `SiYuanConnector`

说明：

- `SourceType.DAYFLOW` 当前实际绑定的是本地 SQLite 的 `DayflowLocalConnector`
- 代码库里虽然还保留了 `dayflow_connector.py`，但注册表当前并没有把它作为实际使用入口

### 2.3 统一活动模型

当前所有数据源最终都会归一到 `Activity` 表。这个模型是整个数据处理链路的中枢。

当前 `Activity` 的重要字段包括：

- `id`
- `user_id`
- `source_config_id`
- `source_type`
- `title`
- `content`
- `extra_data`
- `fingerprint`
- `created_at`
- `updated_at`

这里的设计重点是：

- 不为每种数据源建独立业务表
- 使用 `extra_data` 存储源特有字段
- 使用 `fingerprint` 处理幂等同步和去重

### 2.4 同步服务

`SyncService` 当前负责：

1. 根据数据源配置实例化 Connector
2. 拉取活动数据
3. 为活动补充 `user_id`
4. 通过 `fingerprint` 比较新增、更新和未变化数据
5. 提交数据库事务
6. 调用 `EmbeddingService` 生成向量

这个服务目前已经形成完整闭环，是系统里最接近“生产能力”的部分。

### 2.5 向量化服务

`EmbeddingService` 当前负责：

1. 从 `Activity` 中提取可嵌入文本
2. 对文本进行切块
3. 调用 embedder 生成向量
4. 将结果写入 `activity_embedding`

当前实现特点：

- 向量表是 `activity_embedding`
- 向量类型使用 `pgvector`
- 当前 provider 只支持 `Ollama`
- 对 `Dayflow` 的 `detailed_summary` 做了更明确的切块支持

这说明向量底座已经存在，但它目前主要被：

- 同步链路使用
- 管理员调试搜索使用

还没有上升为正式的用户搜索产品。

### 2.6 LLM 相关能力

LLM 相关能力目前分成三部分：

- `LLM Model Config`：模型连接配置
- `LLM Prompt`：Prompt 模板管理
- `Image Analysis`：结合前两者执行图像理解任务

当前 `LLMClient` 支持的 provider 类型包括：

- `OPENAI`
- `ANTHROPIC`
- `OLLAMA`

但它当前主要服务于图片分析任务，并没有形成通用对话、检索增强问答或报告生成链路。

### 2.7 图片分析链路

图片分析是当前唯一比较完整的“LLM 应用能力”：

1. 配置模型
2. 配置 Prompt
3. 提交图片分析任务
4. Celery 异步执行
5. 保存结果
6. 前端查看结果和原图

图片来源当前主要围绕 `SiYuan` 本地资源。

## 3. 前端结构

前端当前更像一个“后台工作台”，而不是终端用户产品。

已落地页面包括：

- `/`
- `/datasources`
- `/llm-models`
- `/llm-prompts`
- `/llm-prompts/$id`
- `/image-analyses`
- `/admin`
- `/debug-siyuan-sql`
- `/debug-vector-search`
- `/settings`
- `/login`
- `/signup`
- `/recover-password`
- `/reset-password`

这些页面对应的重点能力是：

- 数据源管理
- 模型与 Prompt 管理
- 图片分析结果查看
- 管理员调试

当前前端没有：

- 活动列表页
- 时间线页
- 报告页
- AI 助手页
- 面向普通用户的语义搜索页

## 4. 当前数据库重点

就当前实现而言，最关键的表是：

- `source_config`
- `activity`
- `activity_embedding`
- `llm_model_config`
- `llm_prompt`
- `image_analysis`
- `user`

其中：

- `source_config` 存连接配置
- `activity` 存统一活动数据
- `activity_embedding` 存向量切块
- `llm_model_config` 和 `llm_prompt` 支撑图片分析配置
- `image_analysis` 存分析任务和结果

## 5. 当前系统边界

如果只按现在代码判断，TraceWeaver 的系统边界很明确：

### 已实现

- 多数据源配置管理
- 手动同步
- 活动统一建模
- 基于指纹的去重/更新
- 向量化与 pgvector 存储
- LLM 模型配置管理
- Prompt 模板管理
- 图片分析异步任务与结果查看
- 管理员 SQL / 向量调试页面

### 未实现

- 普通用户可用的语义搜索产品
- 基于个人数据的 RAG 问答
- 报告生成与编辑
- 活动流/时间线展示
- `Activity` 浏览和查询 API

## 6. 后续演进方向

未来如果继续往“个人知识库产品”推进，最自然的下一层是：

1. 增加 `Activity` 查询与浏览能力
2. 将调试向量检索升级为正式搜索 API 和页面
3. 在搜索结果基础上实现 RAG 问答
4. 在检索和聚合能力之上实现日报/周报生成
5. 再补时间线和可编辑报告

## 7. 文档约定

本文档优先描述当前落地代码。

如果未来要写“目标架构”，建议单独新建一份 `vision` 或 `roadmap` 文档，不要再把未来设计直接写成现状。
