# TraceWeaver 架构设计文档

本文档详细说明 TraceWeaver 项目的系统架构、设计理念和实现细节。

## 目录

- [1. 架构概览](#1-架构概览)
- [2. 核心数据抽象](#2-核心数据抽象)
- [3. 后端工程结构](#3-后端工程结构)
- [4. 连接器接口设计](#4-连接器接口设计)
- [5. 数据库模型设计](#5-数据库模型设计)
- [6. 核心业务流程](#6-核心业务流程)
- [7. 扩展指南](#7-扩展指南)

---

## 1. 架构概览

### 1.1 设计原则

TraceWeaver 采用 **Hexagonal Architecture（六边形架构）**，也称为 **Ports and Adapters Pattern（端口适配器模式）**。这种架构的核心思想是：

- **高内聚、低耦合**：核心业务逻辑与外部系统完全解耦
- **依赖倒置**：核心层定义接口，适配器层实现接口
- **可测试性**：核心逻辑可以独立测试，不依赖外部系统
- **可扩展性**：添加新数据源只需实现接口，无需修改核心代码

### 1.2 架构层次

```mermaid
graph TB
    subgraph External["外部系统"]
        Git["Git 仓库"]
        Dayflow["Dayflow API"]
        SiYuan["思源笔记"]
    end

    subgraph AdapterLayer["适配器层"]
        GitAdapter["Git Adapter"]
        DayflowAdapter["Dayflow Adapter"]
        SiYuanAdapter["SiYuan Adapter"]
    end

    subgraph CoreLayer["核心业务层"]
        Interface["BaseConnector<br/>(接口定义)"]
        ActivityManager["Activity Manager"]
        ReportEngine["Report Engine"]
        LLMService["LLM Service"]
    end

    subgraph Infrastructure["基础设施层"]
        Database[("PostgreSQL")]
        Cache["缓存层"]
    end

    Git --> GitAdapter
    Dayflow --> DayflowAdapter
    SiYuan --> SiYuanAdapter

    GitAdapter --> Interface
    DayflowAdapter --> Interface
    SiYuanAdapter --> Interface

    Interface --> ActivityManager
    ActivityManager --> Database
    ReportEngine --> ActivityManager
    ReportEngine --> LLMService
    LLMService --> Database
```

### 1.3 数据流向

1. **数据采集**：适配器从外部系统获取原始数据
2. **数据转换**：适配器将原始数据转换为统一的活动模型
3. **数据存储**：Activity Manager 处理去重和存储
4. **报告生成**：Report Engine 聚合活动数据，调用 LLM 生成报告
5. **数据展示**：前端从 API 获取数据并展示

---

## 2. 核心数据抽象

### 2.1 统一活动模型 (Unified Activity Model)

为了实现解耦，我们不能在数据库里存储特定数据源的表（如 `GitCommit`、`DayflowTask`）。相反，我们使用一个通用的 `Activity` 模型来存储所有数据源的活动。

#### 2.1.1 数据模型定义

```python
class Activity(SQLModel, table=True):
    """统一活动模型 - 所有数据源的标准化表示"""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    source_config_id: uuid.UUID = Field(foreign_key="source_config.id")
    
    # 核心字段
    source_type: str = Field(index=True)  # "git", "dayflow", "siyuan"
    source_id: str = Field(index=True)     # 来源方的唯一ID
    occurred_at: datetime = Field(index=True)  # 发生时间
    title: str                            # 简短描述
    content: str | None = None            # 详细内容/上下文
    
    # 扩展字段
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    
    # 去重字段
    fingerprint: str = Field(unique=True, index=True)  # 哈希指纹
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 2.1.2 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | UUID | 主键 | `550e8400-e29b-41d4-a716-446655440000` |
| `user_id` | UUID | 用户ID | - |
| `source_config_id` | UUID | 数据源配置ID | - |
| `source_type` | String | 数据源类型 | `"git"`, `"dayflow"`, `"siyuan"` |
| `source_id` | String | 来源方的唯一ID | Git Hash: `"a1b2c3d"` |
| `occurred_at` | DateTime | 发生时间 | `2023-10-27 14:30:00` |
| `title` | String | 简短描述 | `"fix: payment logic"` |
| `content` | Text | 详细内容 | Commit Diff 或笔记正文 |
| `metadata` | JSONB | 源特有数据 | `{"repo": "backend", "branch": "main"}` |
| `fingerprint` | String | 哈希指纹 | SHA256 哈希，用于去重 |

#### 2.1.3 元数据 (Metadata) 设计

`metadata` 字段使用 JSONB 类型存储数据源特有的信息，不同数据源的元数据结构不同：

**Git 数据源**:
```json
{
  "repo": "backend",
  "branch": "main",
  "author": "John Doe",
  "files_changed": 5,
  "insertions": 120,
  "deletions": 30
}
```

**Dayflow 数据源**:
```json
{
  "project": "Project A",
  "tags": ["work", "development"],
  "duration_minutes": 120
}
```

**SiYuan 数据源**:
```json
{
  "notebook": "工作笔记",
  "path": "/工作/2023/10月",
  "tags": ["会议", "总结"]
}
```

### 2.2 数据源配置模型 (Source Config)

用户可以为每个数据源配置连接信息：

```python
class SourceConfig(SQLModel, table=True):
    """数据源配置 - 存储用户的连接配置"""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    
    # 配置信息
    type: str = Field(index=True)  # "git", "dayflow", "siyuan"
    name: str                      # 用户自定义名称
    config_payload: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    
    # 状态
    is_active: bool = Field(default=True)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**配置示例**:

Git 配置:
```json
{
  "repo_path": "/Users/leo/projects/backend",
  "branch": "main"
}
```

Dayflow 配置:
```json
{
  "api_token": "xxx",
  "api_url": "https://api.dayflow.com"
}
```

SiYuan 配置:
```json
{
  "api_url": "http://localhost:6806",
  "api_token": "xxx"
}
```

### 2.3 报告模型 (Report)

生成的报告存储在 `reports` 表中：

```python
class Report(SQLModel, table=True):
    """生成的报告"""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    
    # 报告信息
    report_type: str = Field(index=True)  # "daily", "weekly"
    date: date = Field(index=True)         # 报告日期
    start_date: date | None = None         # 周报开始日期
    end_date: date | None = None           # 周报结束日期
    
    # 内容
    content: str                           # Markdown 格式的报告内容
    content_edited: str | None = None      # 用户编辑后的内容
    
    # 关联的活动
    activity_ids: list[uuid.UUID] = Field(default_factory=list, sa_column=Column(ARRAY(UUID)))
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. 后端工程结构

### 3.1 目录结构

```
backend/
├── app/
│   ├── api/                    # API 路由层
│   │   ├── v1/
│   │   │   └── endpoints/
│   │   │       ├── sources.py      # 数据源配置管理
│   │   │       ├── activities.py   # 活动数据查询
│   │   │       ├── sync.py        # 同步接口
│   │   │       └── reports.py     # 报告生成和查询
│   │   ├── deps.py            # 依赖注入（认证等）
│   │   └── main.py            # API 路由注册
│   │
│   ├── core/                  # 核心配置
│   │   ├── config.py          # 环境变量配置
│   │   ├── db.py              # 数据库连接
│   │   └── security.py        # 安全相关（JWT、密码等）
│   │
│   ├── models/                # SQLModel ORM 模型
│   │   ├── base.py            # 基础模型类
│   │   ├── user.py            # 用户模型
│   │   ├── source_config.py   # 数据源配置模型
│   │   ├── activity.py        # 活动模型
│   │   └── report.py          # 报告模型
│   │
│   ├── schemas/               # Pydantic 模型 (DTOs)
│   │   ├── user.py
│   │   ├── source_config.py
│   │   ├── activity.py
│   │   └── report.py
│   │
│   ├── services/              # 业务逻辑层
│   │   ├── activity_service.py    # 活动管理服务
│   │   ├── report_service.py      # 报告生成服务
│   │   └── llm_service.py        # LLM 调用服务
│   │
│   ├── connectors/            # === 核心解耦层 ===
│   │   ├── base.py            # BaseConnector 抽象基类
│   │   ├── registry.py        # 连接器注册工厂
│   │   └── impl/              # 具体实现
│   │       ├── git_connector.py
│   │       ├── dayflow_connector.py
│   │       └── siyuan_connector.py
│   │
│   ├── crud.py                # CRUD 工具函数
│   └── utils.py              # 工具函数
│
├── alembic/                   # 数据库迁移
│   └── versions/
│
└── tests/                     # 测试代码
    ├── api/
    ├── services/
    └── connectors/
```

### 3.2 模块职责

#### 3.2.1 API 层 (`app/api/`)

- **职责**：处理 HTTP 请求和响应
- **特点**：薄层，只负责参数验证和调用服务层
- **示例**：

```python
@router.post("/sync", response_model=SyncResponse)
async def sync_activities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SyncResponse:
    """同步所有配置的数据源"""
    service = ActivityService(db)
    result = await service.sync_all_sources(user_id=current_user.id)
    return SyncResponse(**result)
```

#### 3.2.2 服务层 (`app/services/`)

- **职责**：实现核心业务逻辑
- **特点**：无状态，可测试，不直接依赖外部系统
- **示例**：

```python
class ActivityService:
    def __init__(self, db: Session):
        self.db = db
        self.connector_registry = ConnectorRegistry()
    
    async def sync_all_sources(self, user_id: UUID) -> dict:
        """同步用户所有配置的数据源"""
        configs = self.get_active_configs(user_id)
        results = []
        
        for config in configs:
            connector = self.connector_registry.get(config.type)
            activities = await connector.fetch_activities(
                config.config_payload,
                start_time=...,
                end_time=...
            )
            # 去重和存储
            saved = self.upsert_activities(user_id, config.id, activities)
            results.append(saved)
        
        return {"total": sum(results)}
```

#### 3.2.3 适配器层 (`app/connectors/`)

- **职责**：与外部系统交互，数据转换
- **特点**：实现统一接口，可插拔
- **位置**：这是实现解耦的关键层

---

## 4. 连接器接口设计

### 4.1 抽象基类定义

所有数据源连接器必须实现 `BaseConnector` 接口：

```python
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from app.schemas.activity import ActivityCreate

class BaseConnector(ABC):
    """所有数据源必须实现的接口"""
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """返回数据源类型标识"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: dict) -> bool:
        """
        验证配置是否有效
        
        Args:
            config: 数据源配置字典
            
        Returns:
            bool: 配置是否有效
            
        Raises:
            ValueError: 配置格式错误
            ConnectionError: 无法连接到数据源
        """
        pass
    
    @abstractmethod
    async def fetch_activities(
        self,
        config: dict,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ActivityCreate]:
        """
        抓取指定时间范围内的活动数据
        
        Args:
            config: 数据源配置字典
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[ActivityCreate]: 活动对象列表
            
        Raises:
            ValueError: 配置错误
            ConnectionError: 连接失败
        """
        pass
    
    def generate_fingerprint(
        self,
        source_type: str,
        source_id: str,
        occurred_at: datetime,
    ) -> str:
        """
        生成活动指纹，用于去重
        
        Args:
            source_type: 数据源类型
            source_id: 来源ID
            occurred_at: 发生时间
            
        Returns:
            str: SHA256 哈希值
        """
        import hashlib
        content = f"{source_type}:{source_id}:{occurred_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 4.2 Git 连接器实现示例

```python
from git import Repo
from app.connectors.base import BaseConnector
from app.schemas.activity import ActivityCreate

class GitConnector(BaseConnector):
    """Git 数据源连接器"""
    
    @property
    def source_type(self) -> str:
        return "git"
    
    async def validate_config(self, config: dict) -> bool:
        """验证 Git 仓库路径是否存在"""
        repo_path = config.get("repo_path")
        if not repo_path:
            raise ValueError("repo_path is required")
        
        try:
            Repo(repo_path)
            return True
        except Exception as e:
            raise ConnectionError(f"Invalid git repository: {e}")
    
    async def fetch_activities(
        self,
        config: dict,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ActivityCreate]:
        """从 Git 仓库读取提交记录"""
        repo_path = config["repo_path"]
        branch = config.get("branch", "main")
        
        repo = Repo(repo_path)
        repo.git.checkout(branch)
        
        activities = []
        for commit in repo.iter_commits(
            rev=branch,
            since=start_time,
            until=end_time,
        ):
            # 转换为统一活动模型
            activity = ActivityCreate(
                source_type="git",
                source_id=commit.hexsha,
                occurred_at=commit.authored_datetime,
                title=commit.message.split("\n")[0],  # 第一行作为标题
                content=commit.message,
                metadata={
                    "repo": repo_path.split("/")[-1],
                    "branch": branch,
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "files_changed": len(commit.stats.files),
                    "insertions": commit.stats.total["insertions"],
                    "deletions": commit.stats.total["deletions"],
                },
                fingerprint=self.generate_fingerprint(
                    "git",
                    commit.hexsha,
                    commit.authored_datetime,
                ),
            )
            activities.append(activity)
        
        return activities
```

### 4.3 连接器注册机制

使用工厂模式管理连接器：

```python
class ConnectorRegistry:
    """连接器注册表 - 工厂模式"""
    
    def __init__(self):
        self._connectors: dict[str, type[BaseConnector]] = {}
    
    def register(self, source_type: str, connector_class: type[BaseConnector]):
        """注册连接器"""
        self._connectors[source_type] = connector_class
    
    def get(self, source_type: str) -> BaseConnector:
        """获取连接器实例"""
        if source_type not in self._connectors:
            raise ValueError(f"Unknown connector type: {source_type}")
        return self._connectors[source_type]()
    
    def list_types(self) -> List[str]:
        """列出所有已注册的连接器类型"""
        return list(self._connectors.keys())

# 全局注册表实例
registry = ConnectorRegistry()

# 自动注册所有连接器
registry.register("git", GitConnector)
registry.register("dayflow", DayflowConnector)
registry.register("siyuan", SiYuanConnector)
```

---

## 5. 数据库模型设计

### 5.1 实体关系图

```mermaid
erDiagram
    User ||--o{ SourceConfig : "has"
    User ||--o{ Activity : "creates"
    User ||--o{ Report : "generates"
    SourceConfig ||--o{ Activity : "produces"
    Activity ||--o{ Report : "included_in"
    
    User {
        uuid id PK
        string email UK
        string hashed_password
        bool is_active
        bool is_superuser
    }
    
    SourceConfig {
        uuid id PK
        uuid user_id FK
        string type
        string name
        jsonb config_payload
        bool is_active
    }
    
    Activity {
        uuid id PK
        uuid user_id FK
        uuid source_config_id FK
        string source_type
        string source_id
        datetime occurred_at
        string title
        text content
        jsonb metadata
        string fingerprint UK
    }
    
    Report {
        uuid id PK
        uuid user_id FK
        string report_type
        date date
        text content
        array activity_ids
    }
```

### 5.2 索引设计

为了提高查询性能，需要在关键字段上创建索引：

- `activities.user_id` + `activities.occurred_at` - 复合索引，用于查询用户的时间范围活动
- `activities.source_type` + `activities.source_id` - 复合索引，用于去重检查
- `activities.fingerprint` - 唯一索引，用于去重
- `reports.user_id` + `reports.date` - 复合索引，用于查询用户报告

---

## 6. 核心业务流程

### 6.1 同步流程 (Sync)

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Service
    participant Registry
    participant Connector
    participant DB

    User->>API: POST /api/v1/sync
    API->>Service: sync_all_sources(user_id)
    Service->>DB: 查询用户的活跃配置
    DB-->>Service: [SourceConfig, ...]
    
    loop 每个配置
        Service->>Registry: get(config.type)
        Registry-->>Service: Connector实例
        Service->>Connector: validate_config(config)
        Connector-->>Service: true/false
        Service->>Connector: fetch_activities(start, end)
        Connector->>Connector: 抓取原始数据
        Connector->>Connector: 转换为ActivityCreate
        Connector-->>Service: [ActivityCreate, ...]
        Service->>Service: 生成fingerprint
        Service->>DB: UPSERT activities
        DB-->>Service: 保存结果
    end
    
    Service-->>API: SyncResult
    API-->>User: 同步完成
```

### 6.2 报告生成流程 (Generate)

```mermaid
sequenceDiagram
    participant User
    participant API
    participant ReportService
    participant ActivityService
    participant LLMService
    participant DB

    User->>API: POST /api/v1/reports/generate
    API->>ReportService: generate_report(user_id, date, type)
    ReportService->>ActivityService: get_activities(user_id, start, end)
    ActivityService->>DB: 查询activities
    DB-->>ActivityService: [Activity, ...]
    ActivityService-->>ReportService: 活动数据
    
    ReportService->>ReportService: 构建Prompt
    ReportService->>LLMService: summarize(activities, prompt)
    LLMService->>LLMService: 调用LLM API
    LLMService-->>ReportService: Markdown报告
    
    ReportService->>DB: 保存Report
    DB-->>ReportService: Report对象
    ReportService-->>API: ReportResponse
    API-->>User: 报告生成完成
```

### 6.3 Prompt 工程

报告生成的 Prompt 设计：

**System Prompt**:
```
你是一个技术专家助手，擅长将开发者的工作痕迹整理成清晰的工作日志。
请基于提供的活动数据，生成一份专业、简洁的工作日报/周报。
```

**User Prompt 模板**:
```
基于以下活动数据，生成一份{report_type}工作报告：

## Git 提交记录
{git_activities_json}

## 时间记录
{dayflow_activities_json}

## 笔记内容
{siyuan_activities_json}

要求：
1. 按时间顺序组织内容
2. 突出重要工作成果
3. 使用 Markdown 格式
4. 保持简洁专业
```

---

## 7. 扩展指南

### 7.1 添加新的数据源

要添加新的数据源（例如 Jira），只需以下步骤：

#### 步骤 1: 创建连接器类

在 `backend/app/connectors/impl/jira_connector.py`:

```python
from app.connectors.base import BaseConnector
from app.schemas.activity import ActivityCreate

class JiraConnector(BaseConnector):
    @property
    def source_type(self) -> str:
        return "jira"
    
    async def validate_config(self, config: dict) -> bool:
        # 验证 Jira API Token 和 URL
        api_url = config.get("api_url")
        api_token = config.get("api_token")
        # ... 验证逻辑
        return True
    
    async def fetch_activities(
        self,
        config: dict,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ActivityCreate]:
        # 调用 Jira API 获取 issues
        # 转换为 ActivityCreate 对象
        activities = []
        # ... 转换逻辑
        return activities
```

#### 步骤 2: 注册连接器

在 `backend/app/connectors/registry.py`:

```python
from app.connectors.impl.jira_connector import JiraConnector

registry.register("jira", JiraConnector)
```

#### 步骤 3: 更新前端配置表单

在 `frontend/src/components/Connectors/` 添加 `JiraConfigForm.tsx`。

### 7.2 自定义报告模板

可以通过修改 `ReportService` 中的 Prompt 模板来自定义报告格式：

```python
class ReportService:
    def _build_prompt(self, activities: List[Activity], report_type: str) -> str:
        # 自定义 Prompt 模板
        template = """
        请生成一份{type}报告，包含以下内容：
        1. 工作概述
        2. 主要成果
        3. 遇到的问题
        4. 下周计划
        """
        # ... 填充数据
        return prompt
```

### 7.3 添加新的报告类型

1. 在 `Report` 模型中添加新的 `report_type` 值
2. 在 `ReportService` 中添加生成逻辑
3. 在前端添加对应的 UI

---

## 8. 性能优化建议

### 8.1 数据同步优化

- **增量同步**：只同步上次同步后的新数据
- **并发同步**：使用 `asyncio.gather` 并发同步多个数据源
- **缓存机制**：缓存数据源配置，避免重复验证

### 8.2 查询优化

- **分页查询**：活动列表使用分页，避免一次性加载大量数据
- **时间范围索引**：在 `occurred_at` 字段上创建索引
- **JSONB 查询**：利用 PostgreSQL 的 JSONB 索引功能

### 8.3 LLM 调用优化

- **批量处理**：将多个活动合并到一个 Prompt 中
- **缓存结果**：相同输入缓存 LLM 结果
- **流式输出**：使用流式 API 提升用户体验

---

## 9. 安全考虑

### 9.1 数据隔离

- 所有查询都基于 `user_id` 进行过滤
- 使用数据库行级安全策略（如果支持）

### 9.2 配置安全

- 敏感配置（如 API Token）加密存储
- 使用环境变量管理密钥

### 9.3 API 安全

- JWT 认证保护所有 API 端点
- 输入验证防止 SQL 注入和 XSS
- 速率限制防止滥用

---

## 10. 测试策略

### 10.1 单元测试

- **连接器测试**：Mock 外部 API，测试数据转换逻辑
- **服务层测试**：测试业务逻辑，不依赖数据库
- **工具函数测试**：测试辅助函数

### 10.2 集成测试

- **API 测试**：测试完整的请求-响应流程
- **数据库测试**：使用测试数据库，测试数据持久化

### 10.3 E2E 测试

- **前端测试**：使用 Playwright 测试用户流程
- **同步流程测试**：测试完整的数据同步流程

---

## 总结

TraceWeaver 的架构设计遵循"高内聚、低耦合"的原则，通过适配器模式实现了核心业务逻辑与外部系统的完全解耦。这种设计使得：

1. **易于扩展**：添加新数据源只需实现接口
2. **易于测试**：核心逻辑可以独立测试
3. **易于维护**：清晰的层次结构，职责分明
4. **易于理解**：统一的抽象模型，降低认知负担

通过这种架构，TraceWeaver 可以轻松接入 Jira、Google Calendar、飞书等新的数据源，而无需重写核心业务逻辑。

