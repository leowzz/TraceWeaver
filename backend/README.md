# FastAPI Project - Backend

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Configuration

TraceWeaver 使用 YAML 格式的配置文件来管理应用设置。

### 本地开发配置

1. **复制配置模板**

在 `backend/` 目录下，将 `config.yaml.template` 复制为 `config.yaml`：

```console
$ cd backend
$ cp config.yaml.template config.yaml
```

2. **编辑配置文件**

打开 `config.yaml` 并填写必要的配置项：

```yaml
# 应用配置
app:
  project_name: "TraceWeaver"
  environment: "local"
  secret_key: "your-secret-key-here"  # 生产环境请使用强密钥
  frontend_host: "http://localhost:5173"

# 数据库配置
database:
  server: "localhost"  # Docker 环境会自动覆盖为 "db"
  port: 5432
  user: "postgres"
  password: "your-password"
  name: "traceweaver"

# 认证配置
auth:
  first_superuser: "admin@example.com"
  first_superuser_password: "changethis"

# 其他配置项...
```

3. **配置优先级**

配置的优先级（从高到低）：
- 环境变量
- YAML 配置文件 (`backend/config.yaml`)
- 默认值

这意味着你可以在 YAML 中设置基础配置，然后通过环境变量覆盖特定的值。

### Docker 部署配置

在 Docker 环境中，配置文件会被挂载到容器内部：

```yaml
# docker-compose.yml
backend:
  volumes:
    - ./backend/config.yaml:/app/config.yaml:ro
  environment:
    # 覆盖 YAML 配置中的数据库主机名
    - POSTGRES_SERVER=db
```

确保在部署前：
1. 创建 `backend/config.yaml` 文件
2. 填写生产环境的配置值
3. 使用强密钥和安全的密码
4. 不要将 `config.yaml` 提交到版本控制系统（已在 .gitignore 中）

### 配置结构

配置文件按功能模块分组：

- **app**: 应用基础配置（项目名、环境、密钥等）
- **database**: 数据库连接配置
- **redis**: Redis 连接配置
- **celery**: 异步任务队列配置
- **smtp**: 邮件服务配置
- **auth**: 认证相关配置
- **monitoring**: 监控配置（Sentry 等）
- **embedder**: 向量化模型配置（用于语义搜索和 RAG）

详细的配置项说明请参考 `config.yaml.template` 文件中的注释。

### Embedder 配置说明

TraceWeaver 使用 [Agno 框架](https://docs.agno.com/) 进行文本向量化，支持多种 Embedding 提供商：

- **ollama**: 本地或远程 Ollama 服务（隐私保护，开源模型）
- **openai**: OpenAI API（高质量，需要 API Key）
- **huggingface**: HuggingFace 模型
- **gemini**: Google Gemini API
- **cohere**: Cohere API

默认配置使用远程 Ollama 服务上的 `milkey/m3e:base-f16` 模型（768 维向量）。如需更改：

```yaml
embedder:
  provider: "ollama"
  model_name: "milkey/m3e:base-f16"
  dimensions: 768
  base_url: "http://192.168.177.20:11434"  # Ollama 服务地址
```

如果使用 OpenAI：

```yaml
embedder:
  provider: "openai"
  model_name: "text-embedding-3-small"
  dimensions: 1536
  api_key: "sk-your-api-key-here"
```

## Docker Compose

Start the local development environment with Docker Compose following the guide in [../development.md](../development.md).

## General Workflow

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ uv sync
```

Then you can activate the virtual environment with:

```console
$ source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `backend/.venv/bin/python`.

Modify or add SQLModel models for data and SQL tables in `./backend/app/models.py`, API endpoints in `./backend/app/api/`, CRUD (Create, Read, Update, Delete) utils in `./backend/app/crud.py`.

## VS Code

There are already configurations in place to run the backend through the VS Code debugger, so that you can use breakpoints, pause and explore variables, etc.

The setup is also already configured so you can run the tests through the VS Code Python tests tab.

## Docker Compose Override

During development, you can change Docker Compose settings that will only affect the local development environment in the file `docker-compose.override.yml`.

The changes to that file only affect the local development environment, not the production environment. So, you can add "temporary" changes that help the development workflow.

For example, the directory with the backend code is synchronized in the Docker container, copying the code you change live to the directory inside the container. That allows you to test your changes right away, without having to build the Docker image again. It should only be done during development, for production, you should build the Docker image with a recent version of the backend code. But during development, it allows you to iterate very fast.

There is also a command override that runs `fastapi run --reload` instead of the default `fastapi run`. It starts a single server process (instead of multiple, as would be for production) and reloads the process whenever the code changes. Have in mind that if you have a syntax error and save the Python file, it will break and exit, and the container will stop. After that, you can restart the container by fixing the error and running again:

```console
$ docker compose watch
```

There is also a commented out `command` override, you can uncomment it and comment the default one. It makes the backend container run a process that does "nothing", but keeps the container alive. That allows you to get inside your running container and execute commands inside, for example a Python interpreter to test installed dependencies, or start the development server that reloads when it detects changes.

To get inside the container with a `bash` session you can start the stack with:

```console
$ docker compose watch
```

and then in another terminal, `exec` inside the running container:

```console
$ docker compose exec backend bash
```

You should see an output like:

```console
root@7f2607af31c3:/app#
```

that means that you are in a `bash` session inside your container, as a `root` user, under the `/app` directory, this directory has another directory called "app" inside, that's where your code lives inside the container: `/app/app`.

There you can use the `fastapi run --reload` command to run the debug live reloading server.

```console
$ fastapi run --reload app/main.py
```

...it will look like:

```console
root@7f2607af31c3:/app# fastapi run --reload app/main.py
```

and then hit enter. That runs the live reloading server that auto reloads when it detects code changes.

Nevertheless, if it doesn't detect a change but a syntax error, it will just stop with an error. But as the container is still alive and you are in a Bash session, you can quickly restart it after fixing the error, running the same command ("up arrow" and "Enter").

...this previous detail is what makes it useful to have the container alive doing nothing and then, in a Bash session, make it run the live reload server.

## Backend tests

To test the backend run:

```console
$ bash ./scripts/test.sh
```

The tests run with Pytest, modify and add tests to `./backend/tests/`.

If you use GitHub Actions the tests will run automatically.

### Test running stack

If your stack is already up and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

That `/app/scripts/tests-start.sh` script just calls `pytest` after making sure that the rest of the stack is running. If you need to pass extra arguments to `pytest`, you can pass them to that command and they will be forwarded.

For example, to stop on first error:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Test Coverage

When the tests are run, a file `htmlcov/index.html` is generated, you can open it in your browser to see the coverage of the tests.

## Migrations

As during local development your app directory is mounted as a volume inside the container, you can also run the migrations with `alembic` commands inside the container and the migration code will be in your app directory (instead of being only inside the container). So you can add it to your git repository.

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

* Start an interactive session in the backend container:

```console
$ docker compose exec backend bash
```

* Alembic is already configured to import your SQLModel models from `./backend/app/models.py`.

* After changing a model (for example, adding a column), inside the container, create a revision, e.g.:

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

* Commit to the git repository the files generated in the alembic directory.

* After creating the revision, run the migration in the database (this is what will actually change the database):

```console
$ alembic upgrade head
```

If you don't want to use migrations at all, uncomment the lines in the file at `./backend/app/core/db.py` that end in:

```python
SQLModel.metadata.create_all(engine)
```

and comment the line in the file `scripts/prestart.sh` that contains:

```console
$ alembic upgrade head
```

If you don't want to start with the default models and want to remove them / modify them, from the beginning, without having any previous revision, you can remove the revision files (`.py` Python files) under `./backend/app/alembic/versions/`. And then create a first migration as described above.

## Email Templates

The email templates are in `./backend/app/email-templates/`. Here, there are two directories: `build` and `src`. The `src` directory contains the source files that are used to build the final email templates. The `build` directory contains the final email templates that are used by the application.

Before continuing, ensure you have the [MJML extension](https://marketplace.visualstudio.com/items?itemName=attilabuti.vscode-mjml) installed in your VS Code.

Once you have the MJML extension installed, you can create a new email template in the `src` directory. After creating the new email template and with the `.mjml` file open in your editor, open the command palette with `Ctrl+Shift+P` and search for `MJML: Export to HTML`. This will convert the `.mjml` file to a `.html` file and now you can save it in the build directory.
