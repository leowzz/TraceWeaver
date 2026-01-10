# API 设计规范

本文档定义 TraceWeaver API 的设计规范和最佳实践。

## 目录

- [1. RESTful 设计原则](#1-restful-设计原则)
- [2. 路由命名规范](#2-路由命名规范)
- [3. Schema 命名约定](#3-schema-命名约定)
- [4. 请求与响应格式](#4-请求与响应格式)
- [5. 错误处理](#5-错误处理)
- [6. 分页规范](#6-分页规范)
- [7. 过滤和排序](#7-过滤和排序)
- [8. 版本管理](#8-版本管理)

---

## 1. RESTful 设计原则

### 1.1 资源导向

API 应以资源为中心，而非动作：

```
✅ 正确：
GET    /api/v1/activities
POST   /api/v1/activities
GET    /api/v1/activities/{id}
PUT    /api/v1/activities/{id}
DELETE /api/v1/activities/{id}

❌ 错误：
POST   /api/v1/get-activities      # 动词在 URL 中
POST   /api/v1/create-activity     # 动词在 URL 中
GET    /api/v1/delete-activity/{id} # GET 用于删除
```

### 1.2 HTTP 方法语义

| 方法 | 用途 | 幂等性 | 示例 |
|------|------|--------|------|
| `GET` | 获取资源 | ✅ | 获取活动列表 |
| `POST` | 创建资源 | ❌ | 创建新活动 |
| `PUT` | 完整更新资源 | ✅ | 更新整个活动 |
| `PATCH` | 部分更新资源 | ❌ | 更新活动标题 |
| `DELETE` | 删除资源 | ✅ | 删除活动 |

### 1.3 复杂操作

对于不适合 RESTful 的操作，使用动词端点：

```
POST /api/v1/sources/{id}/sync      # 同步数据源
POST /api/v1/reports/generate       # 生成报告
POST /api/v1/activities/batch       # 批量操作
```

---

## 2. 路由命名规范

### 2.1 基础结构

```
/api/{version}/{resource}[/{id}][/{sub-resource}][/{action}]
```

**示例：**

```
/api/v1/activities                     # 活动列表
/api/v1/activities/123                 # 单个活动
/api/v1/activities/123/embeddings      # 活动的向量
/api/v1/sources/456/sync               # 同步数据源
```

### 2.2 命名规则

- 使用**小写字母**
- 使用**连字符**（kebab-case）分隔单词
- 使用**复数形式**表示集合
- 路径参数使用 `{param_name}` 格式

```
✅ 正确：
/api/v1/source-configs
/api/v1/activity-embeddings
/api/v1/llm-model-configs

❌ 错误：
/api/v1/sourceConfigs        # 驼峰命名
/api/v1/source_configs       # 下划线
/api/v1/SourceConfig         # 大写字母
```

### 2.3 路由层级

不超过 3 层，避免过深嵌套：

```
✅ 正确：
/api/v1/users/{user_id}/activities

❌ 避免：
/api/v1/users/{user_id}/sources/{source_id}/activities/{activity_id}/embeddings
```

---

## 3. Schema 命名约定

### 3.1 基础模式

| 后缀 | 用途 | 示例 |
|------|------|------|
| `Create` | 创建请求 | `ActivityCreate` |
| `Update` | 更新请求 | `ActivityUpdate` |
| `Public` | 单个资源响应 | `ActivityPublic` |
| `sPublic` | 列表响应 | `ActivitiesPublic` |
| `Filter` | 过滤参数 | `ActivityFilter` |

### 3.2 示例定义

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 创建请求
class ActivityCreate(BaseModel):
    source_type: str
    title: str
    content: Optional[str] = None
    occurred_at: datetime

# 更新请求
class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

# 单个资源响应
class ActivityPublic(BaseModel):
    id: int
    source_type: str
    title: str
    content: Optional[str]
    occurred_at: datetime
    created_at: datetime

# 列表响应
class ActivitiesPublic(BaseModel):
    data: List[ActivityPublic]
    count: int

# 过滤参数
class ActivityFilter(BaseModel):
    source_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
```

### 3.3 字段命名

使用 **snake_case**（Python 约定）：

```python
✅ 正确：
class ActivityPublic(BaseModel):
    source_type: str
    occurred_at: datetime
    created_at: datetime

❌ 错误：
class ActivityPublic(BaseModel):
    sourceType: str        # 驼峰命名
    OccurredAt: datetime   # 大写开头
```

**注意：** FastAPI 会自动转换为前端的 camelCase（如果配置了）。

---

## 4. 请求与响应格式

### 4.1 成功响应

#### 单个资源

```json
{
  "id": 123,
  "source_type": "git",
  "title": "feat: add vector search",
  "content": "Implemented semantic search...",
  "occurred_at": "2023-10-27T10:00:00Z",
  "created_at": "2023-10-27T10:05:00Z"
}
```

#### 资源列表

```json
{
  "data": [
    {
      "id": 123,
      "title": "Activity 1",
      ...
    },
    {
      "id": 124,
      "title": "Activity 2",
      ...
    }
  ],
  "count": 2
}
```

#### 分页列表

```json
{
  "data": [...],
  "count": 100,
  "skip": 0,
  "limit": 20,
  "total": 100
}
```

### 4.2 时间格式

使用 ISO 8601 格式：

```
2023-10-27T10:00:00Z        # UTC 时间
2023-10-27T10:00:00+08:00   # 带时区
```

### 4.3 布尔值

使用小写 `true`/`false`（JSON 标准）：

```json
{
  "is_active": true,
  "is_deleted": false
}
```

---

## 5. 错误处理

### 5.1 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| `200` | OK | 成功获取/更新资源 |
| `201` | Created | 成功创建资源 |
| `204` | No Content | 成功删除资源 |
| `400` | Bad Request | 请求参数错误 |
| `401` | Unauthorized | 未认证 |
| `403` | Forbidden | 无权限 |
| `404` | Not Found | 资源不存在 |
| `409` | Conflict | 资源冲突（如重复） |
| `422` | Unprocessable Entity | 验证失败 |
| `500` | Internal Server Error | 服务器错误 |

### 5.2 错误响应格式

```json
{
  "detail": "Activity not found"
}
```

对于验证错误（422）：

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "occurred_at"],
      "msg": "invalid datetime format",
      "type": "value_error.datetime"
    }
  ]
}
```

### 5.3 错误处理实现

```python
from fastapi import HTTPException, status

# 资源不存在
@router.get("/activities/{id}")
def get_activity(id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity {id} not found"
        )
    return activity

# 验证错误（FastAPI 自动处理）
@router.post("/activities", status_code=status.HTTP_201_CREATED)
def create_activity(
    data: ActivityCreate,  # Pydantic 自动验证
    db: Session = Depends(get_db)
):
    activity = Activity(**data.dict())
    db.add(activity)
    db.commit()
    return activity

# 权限错误
@router.delete("/activities/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    activity = db.get(Activity, id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if activity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this activity"
        )

    db.delete(activity)
    db.commit()
```

---

## 6. 分页规范

### 6.1 查询参数

使用 `skip` 和 `limit`：

```
GET /api/v1/activities?skip=0&limit=20
```

### 6.2 响应格式

```json
{
  "data": [...],
  "count": 20,       # 当前返回的数量
  "skip": 0,         # 跳过的数量
  "limit": 20,       # 每页数量
  "total": 100       # 总数量（可选）
}
```

### 6.3 实现示例

```python
from fastapi import Query
from typing import List

@router.get("/activities", response_model=ActivitiesPublic)
def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 查询总数（可选）
    total = db.exec(
        select(func.count(Activity.id)).where(Activity.user_id == current_user.id)
    ).one()

    # 分页查询
    statement = (
        select(Activity)
        .where(Activity.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Activity.occurred_at.desc())
    )
    activities = db.exec(statement).all()

    return ActivitiesPublic(
        data=activities,
        count=len(activities),
        skip=skip,
        limit=limit,
        total=total,
    )
```

---

## 7. 过滤和排序

### 7.1 过滤参数

使用查询参数：

```
GET /api/v1/activities?source_type=git&start_date=2023-10-01&end_date=2023-10-31
```

### 7.2 排序参数

```
GET /api/v1/activities?sort=-occurred_at,title
```

- `occurred_at` - 升序
- `-occurred_at` - 降序（前缀 `-`）

### 7.3 实现示例

```python
from typing import Optional
from datetime import datetime

class ActivityFilter(BaseModel):
    source_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # 搜索关键词

@router.get("/activities", response_model=ActivitiesPublic)
def list_activities(
    filter: ActivityFilter = Depends(),
    sort: str = Query("-occurred_at"),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 构建查询
    statement = select(Activity).where(Activity.user_id == current_user.id)

    # 应用过滤
    if filter.source_type:
        statement = statement.where(Activity.source_type == filter.source_type)

    if filter.start_date:
        statement = statement.where(Activity.occurred_at >= filter.start_date)

    if filter.end_date:
        statement = statement.where(Activity.occurred_at <= filter.end_date)

    if filter.search:
        statement = statement.where(
            Activity.title.ilike(f"%{filter.search}%")
        )

    # 应用排序
    sort_fields = []
    for field in sort.split(","):
        if field.startswith("-"):
            sort_fields.append(getattr(Activity, field[1:]).desc())
        else:
            sort_fields.append(getattr(Activity, field).asc())

    statement = statement.order_by(*sort_fields)

    # 分页
    statement = statement.offset(skip).limit(limit)

    activities = db.exec(statement).all()

    return ActivitiesPublic(data=activities, count=len(activities))
```

---

## 8. 版本管理

### 8.1 URL 版本化

在 URL 中包含版本号：

```
/api/v1/activities
/api/v2/activities
```

### 8.2 版本迁移策略

- **向后兼容**：尽量保持 v1 可用
- **废弃通知**：在响应头中添加警告

```python
from fastapi import Response

@router.get("/activities", deprecated=True)
def list_activities_v1(response: Response):
    response.headers["X-API-Deprecation"] = "This endpoint is deprecated, use /api/v2/activities"
    response.headers["X-API-Deprecation-Date"] = "2024-12-31"
    # ...
```

### 8.3 OpenAPI 文档

为不同版本生成独立文档：

```python
from fastapi import FastAPI

app_v1 = FastAPI(title="TraceWeaver API", version="1.0")
app_v2 = FastAPI(title="TraceWeaver API", version="2.0")

# 挂载
app.mount("/api/v1", app_v1)
app.mount("/api/v2", app_v2)
```

---

## 9. 认证与授权

### 9.1 JWT 认证

使用 Bearer Token：

```
Authorization: Bearer <jwt_token>
```

### 9.2 权限检查

```python
from app.api.deps import get_current_user, require_admin

@router.delete("/users/{id}")
def delete_user(
    id: str,
    current_user: User = Depends(require_admin),  # 需要管理员权限
    db: Session = Depends(get_db)
):
    # 删除用户逻辑
    ...
```

---

## 10. 最佳实践总结

### 10.1 路由设计

- ✅ 使用名词表示资源
- ✅ 使用 HTTP 方法表示动作
- ✅ 保持 URL 简洁（不超过 3 层）
- ✅ 使用复数形式（`activities` 而非 `activity`）

### 10.2 响应设计

- ✅ 返回完整的资源对象
- ✅ 使用一致的时间格式（ISO 8601）
- ✅ 列表响应包含 `data` 和 `count`
- ✅ 分页响应包含 `skip`、`limit`、`total`

### 10.3 错误处理

- ✅ 使用适当的 HTTP 状态码
- ✅ 提供清晰的错误消息
- ✅ 验证错误返回详细字段信息
- ✅ 记录错误日志（不暴露给客户端）

### 10.4 性能优化

- ✅ 使用分页避免大量数据传输
- ✅ 支持字段选择（`?fields=id,title`）
- ✅ 使用 ETag 支持缓存
- ✅ 对慢查询添加索引

### 10.5 文档

- ✅ 使用 OpenAPI（自动生成）
- ✅ 为每个端点添加描述和示例
- ✅ 标注废弃的端点
- ✅ 提供 Postman Collection

---

## 附录：完整示例

### 活动 API 完整实现

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ActivityPublic,
    ActivitiesPublic,
    ActivityFilter,
)

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])

@router.get("", response_model=ActivitiesPublic)
def list_activities(
    filter: ActivityFilter = Depends(),
    sort: str = Query("-occurred_at", description="排序字段，-前缀表示降序"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivitiesPublic:
    """获取活动列表

    支持过滤、排序和分页
    """
    # 构建基础查询
    statement = select(Activity).where(Activity.user_id == current_user.id)

    # 应用过滤
    if filter.source_type:
        statement = statement.where(Activity.source_type == filter.source_type)
    if filter.start_date:
        statement = statement.where(Activity.occurred_at >= filter.start_date)
    if filter.end_date:
        statement = statement.where(Activity.occurred_at <= filter.end_date)
    if filter.search:
        statement = statement.where(Activity.title.ilike(f"%{filter.search}%"))

    # 统计总数
    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.exec(count_statement).one()

    # 应用排序
    for field in sort.split(","):
        desc = field.startswith("-")
        field_name = field[1:] if desc else field
        order = getattr(Activity, field_name).desc() if desc else getattr(Activity, field_name).asc()
        statement = statement.order_by(order)

    # 应用分页
    statement = statement.offset(skip).limit(limit)

    activities = db.exec(statement).all()

    return ActivitiesPublic(
        data=activities,
        count=len(activities),
        skip=skip,
        limit=limit,
        total=total,
    )

@router.get("/{id}", response_model=ActivityPublic)
def get_activity(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityPublic:
    """获取单个活动"""
    activity = db.get(Activity, id)

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity {id} not found"
        )

    if activity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this activity"
        )

    return activity

@router.post("", response_model=ActivityPublic, status_code=status.HTTP_201_CREATED)
def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityPublic:
    """创建活动"""
    activity = Activity(**data.dict(), user_id=current_user.id)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

@router.patch("/{id}", response_model=ActivityPublic)
def update_activity(
    id: int,
    data: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityPublic:
    """更新活动"""
    activity = db.get(Activity, id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 更新非空字段
    for key, value in data.dict(exclude_unset=True).items():
        setattr(activity, key, value)

    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除活动"""
    activity = db.get(Activity, id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(activity)
    db.commit()
```
