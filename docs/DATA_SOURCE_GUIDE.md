# 数据源接入指南

本文档详细说明如何为 TraceWeaver 添加新的数据源。

## 目录

- [1. 概述](#1-概述)
- [2. 连接器接口](#2-连接器接口)
- [3. 实现步骤](#3-实现步骤)
- [4. 配置 Schema 设计](#4-配置-schema-设计)
- [5. 测试规范](#5-测试规范)
- [6. 前端集成](#6-前端集成)
- [7. 最佳实践](#7-最佳实践)

---

## 1. 概述

### 1.1 什么是数据源连接器？

数据源连接器（Connector）是 TraceWeaver 架构中的**适配器层**组件，负责：

1. 连接外部系统（Git、API、本地文件等）
2. 抓取原始数据
3. 将原始数据转换为统一的 `Activity` 模型
4. 处理错误和重试

### 1.2 为什么需要连接器？

通过连接器模式，TraceWeaver 实现了：

- **解耦**：核心业务逻辑与数据源无关
- **扩展性**：添加新数据源无需修改核心代码
- **一致性**：所有数据源使用统一的接口
- **可测试性**：连接器可以独立测试

### 1.3 现有连接器

| 连接器 | 数据源 | 配置参数 |
|--------|--------|----------|
| `GitConnector` | Git 仓库 | `repo_path`, `branch` |
| `SiYuanConnector` | 思源笔记 | `api_url`, `api_token` |
| `DayflowConnector` | 时间记录 | `api_url`, `api_token` |

---

## 2. 连接器接口

### 2.1 BaseConnector 抽象类

所有连接器必须继承 `BaseConnector` 并实现其抽象方法：

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from app.schemas.activity import ActivityCreate

class BaseConnector(ABC):
    """所有数据源连接器的基类"""
    
    def __init__(self, config):
        """初始化连接器
        
        Args:
            config: 数据源配置 Schema（Pydantic BaseModel）
        """
        self.config = config
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """返回数据源类型标识
        
        Returns:
            数据源类型字符串（如 "git", "jira", "notion"）
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """验证配置有效性
        
        Returns:
            True 如果配置有效
            
        Raises:
            ValueError: 配置格式错误
            ConnectionError: 无法连接到数据源
        """
        pass
    
    @abstractmethod
    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ActivityCreate]:
        """抓取指定时间范围内的活动数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            ActivityCreate 对象列表
            
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
        """生成活动指纹（用于去重）
        
        Args:
            source_type: 数据源类型
            source_id: 来源方的唯一 ID
            occurred_at: 发生时间
            
        Returns:
            SHA256 哈希字符串
        """
        import hashlib
        content = f"{source_type}:{source_id}:{occurred_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 2.2 为什么使用同步方法？

注意 `validate_config` 和 `fetch_activities` 是 `async` 方法，但项目使用同步 ORM：

- 连接器方法可以是异步的（网络 I/O）
- 数据库操作在调用方使用同步 Session
- 这种混合模式在 FastAPI 中是支持的

---

## 3. 实现步骤

### 步骤 1：创建配置 Schema

在 `backend/app/schemas/source_config.py` 中定义配置：

```python
from pydantic import BaseModel, HttpUrl

class JiraConfig(BaseModel):
    """Jira 数据源配置"""
    api_url: HttpUrl  # Jira 实例地址
    api_token: str  # API Token
    project_key: str  # 项目键（如 "PROJ"）
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_url": "https://your-domain.atlassian.net",
                "api_token": "your-api-token",
                "project_key": "PROJ"
            }
        }
```

### 步骤 2：创建连接器类

在 `backend/app/connectors/impl/` 创建新文件，如 `jira_connector.py`：

```python
from datetime import datetime
from typing import List
import httpx
from loguru import logger

from app.connectors.base import BaseConnector
from app.models.enums import SourceType
from app.schemas.activity import ActivityCreate
from app.schemas.source_config import JiraConfig


class JiraConnector(BaseConnector):
    """Jira 数据源连接器"""
    
    def __init__(self, config: JiraConfig):
        """初始化 Jira 连接器
        
        Args:
            config: JiraConfig 配置对象
        """
        super().__init__(config)
        self.config: JiraConfig = config
    
    @property
    def source_type(self) -> str:
        return SourceType.JIRA.value  # 需要在 enums.py 中添加
    
    async def validate_config(self) -> bool:
        """验证 Jira 配置
        
        测试连接并验证 API Token 是否有效
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.api_url}/rest/api/3/myself",
                    headers={"Authorization": f"Bearer {self.config.api_token}"},
                    timeout=5.0,
                )
                
                if response.status_code != 200:
                    raise ConnectionError(f"Jira API 返回状态 {response.status_code}")
                
                logger.info("Jira 配置验证成功")
                return True
                
        except httpx.RequestError as e:
            raise ConnectionError(f"无法连接到 Jira: {e}")
    
    async def fetch_activities(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ActivityCreate]:
        """从 Jira 获取 Issues
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            ActivityCreate 对象列表
        """
        # 构建 JQL 查询
        jql = (
            f'project = {self.config.project_key} '
            f'AND updated >= "{start_time.strftime("%Y-%m-%d")}" '
            f'AND updated <= "{end_time.strftime("%Y-%m-%d")}"'
        )
        
        # 调用 Jira API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.api_url}/rest/api/3/search",
                headers={"Authorization": f"Bearer {self.config.api_token}"},
                params={"jql": jql, "maxResults": 100},
            )
            response.raise_for_status()
            data = response.json()
        
        # 转换为 Activity
        activities = []
        for issue in data.get("issues", []):
            activity = ActivityCreate(
                user_id=None,  # 由服务层设置
                source_type=SourceType.JIRA,
                source_id=issue["key"],  # 如 "PROJ-123"
                occurred_at=datetime.fromisoformat(
                    issue["fields"]["updated"].replace("Z", "+00:00")
                ),
                title=issue["fields"]["summary"],
                content=issue["fields"].get("description", ""),
                extra_data={
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"].get("assignee", {}).get("displayName"),
                    "priority": issue["fields"].get("priority", {}).get("name"),
                    "issue_type": issue["fields"]["issuetype"]["name"],
                },
                fingerprint=self.generate_fingerprint(
                    SourceType.JIRA.value,
                    issue["key"],
                    datetime.fromisoformat(issue["fields"]["updated"].replace("Z", "+00:00")),
                ),
            )
            activities.append(activity)
        
        logger.info(
            f"从 Jira 获取了 {len(activities)} 个 Issues",
            project=self.config.project_key,
            count=len(activities)
        )
        
        return activities
```

### 步骤 3：添加枚举值

在 `backend/app/models/enums.py` 中添加新的数据源类型：

```python
from enum import Enum

class SourceType(str, Enum):
    GIT = "git"
    SIYUAN = "siyuan"
    DAYFLOW = "dayflow"
    JIRA = "jira"  # 新增
```

### 步骤 4：注册连接器

在 `backend/app/connectors/registry.py` 中注册：

```python
from app.connectors.impl.git_connector import GitConnector
from app.connectors.impl.siyuan_connector import SiYuanConnector
from app.connectors.impl.dayflow_connector import DayflowConnector
from app.connectors.impl.jira_connector import JiraConnector  # 导入

class ConnectorRegistry:
    def __init__(self):
        self._connectors = {
            "git": GitConnector,
            "siyuan": SiYuanConnector,
            "dayflow": DayflowConnector,
            "jira": JiraConnector,  # 注册
        }
    
    def get(self, source_type: str):
        if source_type not in self._connectors:
            raise ValueError(f"Unknown connector type: {source_type}")
        return self._connectors[source_type]

# 全局实例
registry = ConnectorRegistry()
```

### 步骤 5：更新数据库模型（如果需要）

如果需要迁移，提醒用户执行：

```bash
cd backend
alembic revision --autogenerate -m "添加 Jira 数据源支持"
alembic upgrade head
```

---

## 4. 配置 Schema 设计

### 4.1 基本原则

- 使用 Pydantic `BaseModel`
- 明确字段类型（`HttpUrl`、`EmailStr` 等）
- 提供默认值和示例
- 添加验证逻辑

### 4.2 常见字段类型

```python
from pydantic import BaseModel, HttpUrl, Field, validator

class MySourceConfig(BaseModel):
    # HTTP(S) URL
    api_url: HttpUrl
    
    # 字符串（带长度限制）
    api_token: str = Field(min_length=10, max_length=200)
    
    # 可选字段
    project_id: Optional[str] = None
    
    # 枚举
    environment: Literal["production", "staging"] = "production"
    
    # 整数（带范围）
    timeout: int = Field(default=30, ge=1, le=300)
    
    # 自定义验证
    @validator("api_token")
    def validate_token(cls, v):
        if not v.startswith("sk-"):
            raise ValueError("Token 必须以 'sk-' 开头")
        return v
```

### 4.3 敏感信息处理

对于 API Token 等敏感信息：

```python
class MySourceConfig(BaseModel):
    api_token: str = Field(..., json_schema_extra={"format": "password"})
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_token": "sk-***"  # 示例中隐藏
            }
        }
```

---

## 5. 测试规范

### 5.1 单元测试

在 `backend/tests/connectors/` 创建测试文件：

```python
import pytest
from datetime import datetime
from app.connectors.impl.jira_connector import JiraConnector
from app.schemas.source_config import JiraConfig
from unittest.mock import AsyncMock, patch

@pytest.fixture
def jira_config():
    return JiraConfig(
        api_url="https://test.atlassian.net",
        api_token="test-token",
        project_key="TEST",
    )

@pytest.fixture
def jira_connector(jira_config):
    return JiraConnector(jira_config)

@pytest.mark.asyncio
async def test_validate_config_success(jira_connector):
    """测试配置验证成功"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(status_code=200)
        
        result = await jira_connector.validate_config()
        assert result is True

@pytest.mark.asyncio
async def test_validate_config_failure(jira_connector):
    """测试配置验证失败"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection error")
        
        with pytest.raises(ConnectionError):
            await jira_connector.validate_config()

@pytest.mark.asyncio
async def test_fetch_activities(jira_connector):
    """测试活动抓取"""
    mock_response = {
        "issues": [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue",
                    "description": "Test Description",
                    "updated": "2023-10-27T10:00:00.000Z",
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Task"},
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        
        start = datetime(2023, 10, 1)
        end = datetime(2023, 10, 31)
        
        activities = await jira_connector.fetch_activities(start, end)
        
        assert len(activities) == 1
        assert activities[0].source_id == "TEST-1"
        assert activities[0].title == "Test Issue"
```

### 5.2 集成测试

测试真实的 API 连接（需要测试环境）：

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jira_real_connection():
    """集成测试：连接真实的 Jira 实例"""
    config = JiraConfig(
        api_url="https://test-instance.atlassian.net",
        api_token=os.getenv("JIRA_TEST_TOKEN"),
        project_key="TEST",
    )
    
    connector = JiraConnector(config)
    
    # 验证配置
    is_valid = await connector.validate_config()
    assert is_valid
    
    # 抓取数据
    start = datetime.now() - timedelta(days=7)
    end = datetime.now()
    activities = await connector.fetch_activities(start, end)
    
    assert isinstance(activities, list)
```

---

## 6. 前端集成

### 6.1 添加配置表单

在 `frontend/src/components/DataSources/` 创建配置表单组件：

```typescript
import { FC } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const jiraConfigSchema = z.object({
  api_url: z.string().url('请输入有效的 URL'),
  api_token: z.string().min(10, 'Token 长度不足'),
  project_key: z.string().min(1, '项目键不能为空'),
})

type JiraConfigForm = z.infer<typeof jiraConfigSchema>

interface JiraConfigProps {
  onSubmit: (data: JiraConfigForm) => void
  loading?: boolean
}

export const JiraConfigForm: FC<JiraConfigProps> = ({ onSubmit, loading }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<JiraConfigForm>({
    resolver: zodResolver(jiraConfigSchema),
  })
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>配置 Jira 数据源</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Jira 地址</label>
            <Input 
              {...register('api_url')} 
              placeholder="https://your-domain.atlassian.net"
            />
            {errors.api_url && (
              <span className="text-sm text-destructive">{errors.api_url.message}</span>
            )}
          </div>
          
          <div>
            <label className="text-sm font-medium">API Token</label>
            <Input 
              {...register('api_token')} 
              type="password"
              placeholder="your-api-token"
            />
            {errors.api_token && (
              <span className="text-sm text-destructive">{errors.api_token.message}</span>
            )}
          </div>
          
          <div>
            <label className="text-sm font-medium">项目键</label>
            <Input 
              {...register('project_key')} 
              placeholder="PROJ"
            />
            {errors.project_key && (
              <span className="text-sm text-destructive">{errors.project_key.message}</span>
            )}
          </div>
          
          <Button type="submit" disabled={loading}>
            {loading ? '验证中...' : '保存配置'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
```

### 6.2 更新数据源列表

在数据源选择器中添加新选项：

```typescript
const dataSourceOptions = [
  { value: 'git', label: 'Git 仓库', icon: GitIcon },
  { value: 'siyuan', label: '思源笔记', icon: BookIcon },
  { value: 'dayflow', label: '时间记录', icon: ClockIcon },
  { value: 'jira', label: 'Jira', icon: JiraIcon },  // 新增
]
```

---

## 7. 最佳实践

### 7.1 错误处理

```python
from app.core.exceptions import ConnectorError

async def fetch_activities(self, start_time, end_time):
    try:
        # API 调用
        response = await client.get(...)
        response.raise_for_status()
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 错误: {e.response.status_code}")
        raise ConnectorError(f"API 返回错误: {e.response.text}")
        
    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        raise ConnectionError(f"无法连接到数据源: {e}")
        
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        raise ConnectorError(f"处理数据时出错: {e}")
```

### 7.2 日志记录

使用 loguru 记录关键操作：

```python
logger.info(
    "开始同步 Jira Issues",
    project=self.config.project_key,
    start_time=start_time,
    end_time=end_time
)

logger.debug(f"JQL 查询: {jql}")

logger.info(
    f"同步完成，获取了 {len(activities)} 个 Issues",
    count=len(activities)
)
```

### 7.3 分页处理

对于大量数据，使用分页：

```python
async def fetch_activities(self, start_time, end_time):
    all_activities = []
    start_at = 0
    max_results = 100
    
    while True:
        response = await client.get(
            url,
            params={
                "startAt": start_at,
                "maxResults": max_results,
            }
        )
        data = response.json()
        
        # 转换数据
        activities = self._convert_to_activities(data["items"])
        all_activities.extend(activities)
        
        # 检查是否还有更多数据
        if len(data["items"]) < max_results:
            break
        
        start_at += max_results
    
    return all_activities
```

### 7.4 重试机制

使用 `tenacity` 库添加重试：

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def _fetch_with_retry(self, url, params):
    """带重试的 API 调用"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
```

### 7.5 数据转换

提取数据转换逻辑为独立方法：

```python
def _convert_to_activity(self, raw_item: dict) -> ActivityCreate:
    """将原始数据转换为 Activity
    
    Args:
        raw_item: 数据源返回的原始数据
        
    Returns:
        ActivityCreate 对象
    """
    return ActivityCreate(
        source_type=self.source_type,
        source_id=raw_item["id"],
        occurred_at=self._parse_datetime(raw_item["updated_at"]),
        title=raw_item["title"],
        content=raw_item.get("description"),
        extra_data=self._extract_metadata(raw_item),
        fingerprint=self.generate_fingerprint(
            self.source_type,
            raw_item["id"],
            self._parse_datetime(raw_item["updated_at"]),
        ),
    )

def _parse_datetime(self, dt_string: str) -> datetime:
    """解析日期时间字符串"""
    # 处理不同的日期格式
    ...

def _extract_metadata(self, raw_item: dict) -> dict:
    """提取元数据"""
    return {
        "status": raw_item.get("status"),
        "priority": raw_item.get("priority"),
        # ...
    }
```

---

## 检查清单

在提交代码前，确保：

- [ ] 实现了 `BaseConnector` 的所有抽象方法
- [ ] 创建了类型安全的配置 Schema
- [ ] 在 `SourceType` 枚举中添加了新类型
- [ ] 在 Registry 中注册了连接器
- [ ] 编写了单元测试（覆盖率 > 80%）
- [ ] 添加了错误处理和日志记录
- [ ] 提供了前端配置表单
- [ ] 更新了文档和示例
- [ ] 提醒用户生成 Alembic 迁移（如果需要）

---

## 常见问题

### Q: 数据源需要认证怎么办？

A: 在配置 Schema 中添加认证字段，并在 `validate_config` 中验证：

```python
class MySourceConfig(BaseModel):
    api_token: str
    # 或者
    username: str
    password: str

async def validate_config(self):
    # 测试认证
    response = await client.get(
        f"{self.config.api_url}/auth/verify",
        headers={"Authorization": f"Bearer {self.config.api_token}"}
    )
    return response.status_code == 200
```

### Q: 如何处理速率限制？

A: 使用重试和延迟：

```python
from tenacity import retry, wait_fixed, stop_after_delay

@retry(wait=wait_fixed(60), stop=stop_after_delay(300))
async def fetch_with_rate_limit(self):
    try:
        return await self._fetch_data()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:  # Too Many Requests
            logger.warning("触发速率限制，等待重试")
            raise  # 重试
        raise
```

### Q: 数据量很大怎么办？

A: 使用分页和增量同步：

```python
async def fetch_activities(self, start_time, end_time):
    # 1. 分页抓取
    activities = await self._fetch_paginated(start_time, end_time)
    
    # 2. 只返回新数据（基于 fingerprint）
    # 由服务层处理去重
    
    return activities
```

### Q: 需要调用多个 API 怎么办？

A: 并发调用：

```python
import asyncio

async def fetch_activities(self, start_time, end_time):
    # 并发调用多个 API
    tasks = [
        self._fetch_issues(),
        self._fetch_comments(),
        self._fetch_attachments(),
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 合并结果
    activities = self._merge_results(results)
    return activities
```
