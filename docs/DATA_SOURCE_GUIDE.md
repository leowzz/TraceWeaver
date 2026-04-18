# 数据源接入指南

本文档说明 TraceWeaver 当前是如何接入数据源的，以及新增连接器时应遵循什么模式。

本文档只描述当前仓库已经采用的方式，不再把未落地的通用方案写成既成事实。

## 1. 当前接入模型

TraceWeaver 目前通过 Connector 模式接入外部数据源。

每个 Connector 负责：

1. 接收并校验某种数据源的配置
2. 连接外部系统或本地数据源
3. 抓取指定时间范围内的原始数据
4. 转换为统一的 `ActivityCreate`
5. 生成用于去重的指纹

随后由 `SyncService` 负责把这些活动写入数据库并触发向量化。

## 2. 当前已接入的数据源

当前代码里真正注册并使用的连接器有：

- `GitConnector`
- `DayflowLocalConnector`
- `SiYuanConnector`

说明：

- `Dayflow` 当前实际接入方式是本地 SQLite 数据库
- 仓库中虽然存在 `dayflow_connector.py`，但它当前不是注册表里的实际实现

## 3. Connector 接口

当前所有连接器都继承 `BaseConnector`。

核心接口包括：

- `source_type`
- `validate_config()`
- `fetch_activities(start_time, end_time)`
- `generate_fingerprint(...)`
- `test_connection()`

这些接口的含义分别是：

- `source_type`：声明连接器对应的数据源类型
- `validate_config()`：检查配置是否可用
- `fetch_activities(...)`：按时间范围拉取活动并转换为统一模型
- `generate_fingerprint(...)`：生成稳定指纹，供去重使用
- `test_connection()`：面向 API 的连接测试入口

## 4. 当前配置 Schema

当前数据源配置 schema 位于 `backend/app/schemas/source_config.py`。

实际使用的配置包括：

### 4.1 Git

```json
{
  "repo_path": "/absolute/path/to/repo",
  "branch": "main"
}
```

### 4.2 Dayflow

```json
{
  "db_path": "/absolute/path/to/chunks.sqlite"
}
```

### 4.3 SiYuan

```json
{
  "api_url": "http://localhost:6806",
  "api_token": "token"
}
```

## 5. 数据流

当前数据源同步的真实链路是：

```text
SourceConfig -> ConnectorRegistry -> Connector -> ActivityCreate list
            -> SyncService -> Activity upsert -> EmbeddingService -> activity_embedding
```

职责划分如下：

- `SourceConfig`：保存连接配置
- `ConnectorRegistry`：根据类型创建连接器
- `Connector`：抓取和转换数据
- `SyncService`：去重、写库、统计、触发向量化
- `EmbeddingService`：切块并生成向量

## 6. 新增数据源的推荐步骤

如果现在要新增一个数据源，建议按当前代码结构做，而不是照搬旧文档里的理想化设计。

### 步骤 1：定义配置 schema

在 `backend/app/schemas/source_config.py` 中添加该数据源的配置 schema。

要求：

- 字段只保留当前实现真正需要的最小集合
- 命名和现有 schema 保持一致
- 不要预埋大量暂时不用的字段

### 步骤 2：实现 Connector

在 `backend/app/connectors/impl/` 下新增连接器文件。

要求：

- 继承 `BaseConnector`
- 实现 `source_type`
- 实现 `validate_config()`
- 实现 `fetch_activities()`
- 输出统一的 `ActivityCreate`

### 步骤 3：更新注册表

更新：

- `backend/app/connectors/registry.py`
- `backend/app/connectors/__init__.py`

确保新类型能被 schema 映射和 connector 注册同时识别。

### 步骤 4：补前端数据源表单

如果该数据源要由 UI 配置，还需要同步更新前端数据源管理页：

- 新增创建表单字段
- 新增编辑表单字段
- 处理类型切换和表单校验

### 步骤 5：验证同步闭环

至少验证：

- 能创建配置
- 能测试连接
- 能执行同步
- 能正确写入 `activity`
- 能触发向量化

## 7. Activity 映射原则

无论接入什么数据源，最终都要尽量映射到当前 `Activity` 模型。

建议遵循以下原则：

- `title` 放最容易读懂的摘要
- `content` 放后续检索可能有用的正文
- `extra_data` 放源特有字段
- `fingerprint` 保证同一条源记录重复同步时稳定不变

不要做的事：

- 为了“保持源数据完整”而把整个原始响应无脑塞进 `content`
- 在还没用到的情况下引入独立业务表
- 让同一条源记录在每次同步时产生不同指纹

## 8. 当前实现注意事项

### 8.1 Dayflow 的实际情况

当前 README 和旧文档里曾提到 Dayflow API / CSV，但当前注册并使用的是本地 SQLite 版本。

所以如果你在扩展 Dayflow，不要默认项目已经有稳定的远程 API 接入方案。

### 8.2 活动查询层还不完整

虽然所有连接器都输出 `ActivityCreate`，但当前系统还没有成熟的 `Activity` 浏览和查询 API。

这意味着新增数据源的主要价值目前体现在：

- 同步入库
- 向量化
- 后续可作为搜索/RAG底座

而不是马上就能在完整产品界面里消费。

### 8.3 文档与代码冲突时以代码为准

本仓库过去的文档里混入过不少“未来设计”，新增连接器时请优先参考：

- `backend/app/connectors/base.py`
- `backend/app/connectors/registry.py`
- `backend/app/connectors/__init__.py`
- 现有三个 connector 的实现
- `backend/app/services/sync_service.py`

## 9. TODO

当前数据源接入体系后续最值得完善的方向包括：

- 远程 Dayflow API 接入
- 更统一的连接器测试
- 围绕 `Activity` 的正式读接口
- 更清晰的 connector 单元测试覆盖
- 更多来源类型
