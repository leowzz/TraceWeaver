# TraceWeaver Frontend

本文档描述当前前端应用的实际情况和开发方式。

前端当前是一个偏后台管理性质的工作台，不是完整的终端用户知识库产品。

## 当前前端职责

前端当前主要提供这些页面和操作：

- 登录、注册、找回密码、重置密码
- Dashboard
- 数据源管理
- LLM 模型配置管理
- Prompt 模板管理
- 图片分析结果查看
- 用户设置
- 管理员用户管理
- 管理员 SQL 调试
- 管理员向量检索调试

当前前端还没有：

- `Activity` 列表页
- 时间线页
- 报告页
- AI 助手页
- 面向普通用户的语义搜索页

## 技术栈

当前前端使用：

- React
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Tailwind CSS
- shadcn/ui

OpenAPI client 通过 `@hey-api/openapi-ts` 生成。

## 开发环境

### 安装依赖

```bash
cd frontend
pnpm install
```

### 启动开发服务器

```bash
pnpm dev
```

### 构建

```bash
pnpm build
```

### 代码检查

```bash
pnpm lint
```

## 当前路由

当前前端实际存在的主要路由包括：

- `/login`
- `/signup`
- `/recover-password`
- `/reset-password`
- `/`
- `/settings`
- `/datasources`
- `/llm-models`
- `/llm-prompts`
- `/llm-prompts/$id`
- `/image-analyses`
- `/admin`
- `/debug-siyuan-sql`
- `/debug-vector-search`

可以直接把它理解成两类页面：

- 面向普通登录用户的后台页面
- 面向管理员的调试和管理页面

## 当前页面结构

### Dashboard

首页当前主要展示的是 `Dayflow` 同步卡片，而不是个人知识库总览。

### Data Sources

这是目前最重要的业务页面之一，支持：

- 新增数据源
- 编辑数据源
- 删除数据源
- 测试连接
- 触发同步

### LLM Models / LLM Prompts

这两页主要服务于图片分析链路。

### Image Analyses

当前用于查看已完成的图片分析记录和详情。

### Debug 页面

管理员可用：

- `Debug SQL`
- `Debug Vector`

这两个页面用于验证底层链路，不应被视为正式产品能力。

## OpenAPI Client

当前前端使用生成的 client，代码位于：

```text
frontend/src/client
```

重新生成 client：

```bash
pnpm generate-client
```

一般需要在后端 OpenAPI 变更后执行。

## 目录结构

```text
frontend/
├── src/
│   ├── client/         # 生成的 API client
│   ├── components/     # 业务组件和 UI 组件
│   ├── hooks/          # 自定义 hooks
│   ├── routes/         # 路由页面
│   └── main.tsx
├── tests/              # Playwright 测试
├── package.json
└── vite.config.ts
```

## 测试

当前前端包含 Playwright 测试。

如果需要运行：

```bash
npx playwright test
```

具体运行方式仍以仓库根目录的开发环境和依赖状态为准。

## 当前边界

如果你要继续开发前端，需要先明确当前产品边界：

### 已有

- 后台式配置与管理页面
- 图片分析结果查看
- 管理员调试页面

### 没有

- 知识库首页
- 活动浏览
- 正式搜索体验
- RAG 聊天
- 报告生成与编辑

后续如果要做用户产品层，优先应该补的是：

1. `Activity` 浏览页
2. 正式搜索页
3. 报告页或 AI 助手页

## 相关文档

- [../README.md](../README.md)
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [../docs/API_CONVENTIONS.md](../docs/API_CONVENTIONS.md)
