# TraceWeaver API 现状与约定

本文档不是抽象 REST 教程，而是面向当前仓库的 API 说明和约定。

目标只有两个：

1. 说明当前已经存在哪些 API 资源
2. 约束后续新增接口时尽量保持一致

## 1. 当前 API 范围

当前后端注册到 `/api/v1` 下的主要资源有：

- `/login`
- `/users`
- `/utils`
- `/items`
- `/source-configs`
- `/llm-model-configs`
- `/llm-prompts`
- `/image-analyses`
- `/debug`

说明：

- `/items` 仍然是模板遗留资源，不是 TraceWeaver 当前核心业务
- `/debug` 是管理员内部调试接口，不应被视为正式产品 API
- 当前没有 `activities`、`reports`、`chat`、`rag` 等正式资源

## 2. 当前资源说明

### 2.1 `/source-configs`

当前用于管理数据源配置，支持：

- 列表
- 详情
- 创建
- 更新
- 删除
- 测试连接
- 同步

这是当前最核心的业务 API 之一。

### 2.2 `/llm-model-configs`

用于管理模型连接配置，支持基础 CRUD。

当前它主要服务于图片分析功能。

### 2.3 `/llm-prompts`

用于管理 Prompt 模板，支持基础 CRUD，并支持通过上传图片测试 Prompt。

当前它也是围绕图片分析能力设计的，不是通用 Prompt 平台。

### 2.4 `/image-analyses`

用于查询图片分析结果和读取原图。

当前主要是结果查看接口，不是任务提交中心。

### 2.5 `/debug`

当前包含：

- `POST /debug/siyuan-sql`
- `POST /debug/vector-search`

它们只适合管理员调试，不应作为面向普通用户的产品接口长期复用。

## 3. 命名约定

后续新增业务接口时，沿用当前仓库已经形成的风格：

- 统一挂在 `/api/v1`
- 资源名使用小写 kebab-case
- 资源集合使用复数或固定资源名
- 自定义动作放在资源后缀

示例：

```text
/api/v1/source-configs
/api/v1/source-configs/{id}
/api/v1/source-configs/{id}/test
/api/v1/source-configs/{id}/sync
```

不建议新增这种风格：

```text
/api/v1/create-source
/api/v1/getActivities
/api/v1/source_configs
```

## 4. Schema 命名约定

当前项目已经形成较稳定的 schema 命名方式：

- `Create`：创建请求
- `Update`：更新请求
- `Public`：单个资源响应
- `sPublic`：列表响应

示例：

- `SourceConfigCreate`
- `SourceConfigUpdate`
- `SourceConfigPublic`
- `SourceConfigsPublic`

建议继续沿用，不要在新模块里再混入其他命名体系。

## 5. 响应结构约定

### 5.1 列表响应

当前项目的大多数列表接口使用：

```json
{
  "data": [],
  "count": 0
}
```

这已经是现有前后端协作的事实格式，新接口应尽量保持一致，除非确实需要更复杂的分页信息。

### 5.2 单个资源响应

单个资源通常直接返回资源对象，而不是额外包一层：

```json
{
  "id": 1,
  "name": "Example"
}
```

### 5.3 简单消息响应

删除、测试连接等场景当前经常返回：

```json
{
  "message": "..."
}
```

## 6. 当前 API 风险和边界

下面这些点是当前 API 的真实状态，需要在新增接口时注意：

- `debug` 路由混入了绕过生成 client 的手写 `fetch` 调用场景
- 某些资源是模板遗留，不代表业务建模成熟
- 当前还没有围绕 `Activity` 建立正式读接口
- 当前还没有统一的过滤、排序、分页规范落地到所有业务资源

所以本文档不再宣称系统已经有一套完整、一致的活动查询 API，只描述已经存在的事实。

## 7. 后续新增接口建议

如果后续要补 TraceWeaver 的核心产品能力，建议优先增加下面这些正式资源，而不是继续扩展 `debug`：

- `/activities`
- `/search`
- `/reports`
- `/assistant` 或 `/chat`

推荐顺序：

1. 先补 `activities`
2. 再补正式 `search`
3. 再做 `reports` 或 `assistant`

## 8. 不再采用的旧描述

旧文档里出现过但当前并不存在的接口，例如：

- `/api/v1/activities`
- `/api/v1/reports/generate`

在真正实现之前，不应继续作为“现有 API”写进文档，只能作为未来规划。
