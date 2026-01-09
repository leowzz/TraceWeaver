.PHONY: help dev api celery flower install test format lint db-migrate db-upgrade db-downgrade db-reset embed-dayflow clean

# 默认目标：显示帮助信息
help:
	@echo "TraceWeaver Backend - 常用命令"
	@echo ""
	@echo "开发服务："
	@echo "  make dev          - 启动开发服务器（热重载，端口 8010）"
	@echo "  make api          - 同 dev"
	@echo "  make celery       - 启动 Celery worker"
	@echo "  make flower       - 启动 Flower（Celery 监控，端口 5555）"
	@echo ""
	@echo "依赖管理："
	@echo "  make install      - 安装基础依赖"
	@echo "  make install-all  - 安装所有依赖（包括可选项）"
	@echo "  make install-dev  - 安装开发依赖"
	@echo ""
	@echo "数据库管理："
	@echo "  make db-migrate   - 生成数据库迁移脚本"
	@echo "  make db-upgrade   - 应用数据库迁移"
	@echo "  make db-downgrade - 回滚上一次迁移"
	@echo "  make db-reset     - 重置数据库（危险！）"
	@echo "  make db-revision  - 创建空迁移脚本"
	@echo ""
	@echo "代码质量："
	@echo "  make format       - 格式化代码（ruff）"
	@echo "  make lint         - 代码检查（ruff + mypy）"
	@echo "  make test         - 运行测试"
	@echo "  make test-cov     - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "向量化："
	@echo "  make embed-dayflow USER_ID=xxx - 向量化 Dayflow 数据"
	@echo "  make embed-test   - 测试向量化（前10条）"
	@echo ""
	@echo "其他："
	@echo "  make clean        - 清理临时文件"
	@echo "  make shell        - 进入 Python shell"

# ============ 开发服务 ============

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

api:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

celery:
	uv run celery -A app.core.celery_app:celery_app worker --concurrency=2 --loglevel=info --pool=solo

flower:
	uv run celery -A app.core.celery_app:celery_app flower --port=5555

# ============ 依赖管理 ============

install:
	uv sync

install-all:
	uv sync --all-extras

install-dev:
	uv sync --all-extras --dev

# ============ 数据库管理 ============

db-migrate:
	@echo "生成数据库迁移脚本..."
	@read -p "迁移描述: " desc; \
	uv run alembic revision --autogenerate -m "$$desc"
	@echo "⚠️  请检查生成的迁移脚本！"

db-upgrade:
	@echo "应用数据库迁移..."
	uv run alembic upgrade head
	@echo "✅ 迁移完成"

db-downgrade:
	@echo "回滚上一次迁移..."
	uv run alembic downgrade -1
	@echo "✅ 回滚完成"

db-reset:
	@echo "⚠️  警告：这将删除所有数据！"
	@read -p "确认重置数据库？(yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		uv run alembic downgrade base; \
		uv run alembic upgrade head; \
		echo "✅ 数据库已重置"; \
	else \
		echo "❌ 已取消"; \
	fi

db-revision:
	@read -p "迁移描述: " desc; \
	uv run alembic revision -m "$$desc"

# ============ 代码质量 ============

format:
	@echo "格式化代码..."
	bash scripts/format.sh
	@echo "✅ 格式化完成"

lint:
	@echo "代码检查..."
	bash scripts/lint.sh
	@echo "✅ 检查完成"

test:
	@echo "运行测试..."
	bash scripts/test.sh
	@echo "✅ 测试完成"

test-cov:
	@echo "运行测试并生成覆盖率报告..."
	uv run pytest --cov=app --cov-report=html --cov-report=term
	@echo "✅ 测试完成，覆盖率报告：htmlcov/index.html"

# ============ 向量化 ============

embed-dayflow:
	@if [ -z "$(USER_ID)" ]; then \
		echo "❌ 错误：请提供 USER_ID"; \
		echo "用法：make embed-dayflow USER_ID=your-uuid-here"; \
		exit 1; \
	fi
	@echo "向量化 Dayflow 数据（用户: $(USER_ID))..."
	uv run python scripts/embed_dayflow.py --user-id $(USER_ID)
	@echo "✅ 向量化完成"

embed-test:
	@if [ -z "$(USER_ID)" ]; then \
		echo "❌ 错误：请提供 USER_ID"; \
		echo "用法：make embed-test USER_ID=your-uuid-here"; \
		exit 1; \
	fi
	@echo "测试向量化（前10条）..."
	uv run python scripts/embed_dayflow.py --user-id $(USER_ID) --limit 10
	@echo "✅ 测试完成"

# ============ 其他 ============

clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	@echo "✅ 清理完成"

shell:
	uv run python

# ============ Docker 相关 ============

docker-build:
	docker build -t traceweaver-backend .

docker-run:
	docker run -p 8010:8010 traceweaver-backend

# ============ 帮助信息 ============

.DEFAULT_GOAL := help
