.PHONY: help dcdev dcdev-up dcdev-down dcdev-logs dcdev-build

# 默认目标：显示帮助信息
help:
	@echo "TraceWeaver - 项目常用命令"
	@echo ""
	@echo "Docker Compose 开发环境："
	@echo "  make dcdev       - 启动开发环境并进入 watch 模式（推荐）"
	@echo "  make dcdev-up    - 启动开发环境（后台运行）"
	@echo "  make dcdev-down  - 停止开发环境"
	@echo "  make dcdev-logs - 查看开发环境日志"
	@echo "  make dcdev-build - 重新构建开发环境镜像"
	@echo ""
	@echo "其他："
	@echo "  查看 backend/Makefile 了解后端相关命令"
	@echo "  查看 frontend/package.json 了解前端相关命令"

# ============ Docker Compose 开发环境 ============

# 启动开发环境并进入 watch 模式（推荐）
dcdev:
	@echo "🚀 启动开发环境（watch 模式）..."
	@echo "   Backend:  http://localhost:8010"
	@echo "   Frontend: http://localhost:5173"
	@echo ""
	docker compose -f docker-compose.dev.yml watch

# 启动开发环境（后台运行）
up:
	@echo "🚀 启动开发环境（后台运行）..."
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅ 开发环境已启动"
	@echo "   查看日志: make dcdev-logs"
	@echo "   进入 watch: make dcdev"

# 停止开发环境
down:
	@echo "🛑 停止开发环境..."
	docker compose -f docker-compose.dev.yml down
	@echo "✅ 开发环境已停止"

# 查看开发环境日志
logs:
	docker compose -f docker-compose.dev.yml logs -f

# 重新构建开发环境镜像
build:
	@echo "🔨 重新构建开发环境镜像..."
	docker compose -f docker-compose.dev.yml build --no-cache
	@echo "✅ 镜像构建完成"

.DEFAULT_GOAL := help
