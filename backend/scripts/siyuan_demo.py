import asyncio
import base64
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import ollama
from loguru import logger

from app.api.deps import get_db
from app.connectors import registry
from app.connectors.impl.siyuan_connector import SiYuanConnector
from app.core.context import mock_ctx
from app.crud.source_config import source_config_crud


async def main():
    session = next(get_db())
    # Assuming the SiYuan config is at ID 1. Adjust if necessary.
    config = source_config_crud.get(session=session, id=1)
    if not config:
        logger.error("Source config with ID 1 not found.")
        return

    logger.info(f"Using config: {config.name} ({config.type})")
    connector: SiYuanConnector = registry.get(config)

    # # Target date: 2025-12-19
    # start_time = datetime(2025, 12, 19, 0, 0, 0)
    # end_time = datetime(2025, 12, 19, 23, 59, 59)
    #
    # logger.info(f"Fetching notes from {start_time} to {end_time}...")
    # activities = await connector.fetch_activities(start_time, end_time)
    #
    # logger.info(f"Found {len(activities)} activities.")
    # for activity in activities:
    #     logger.info(f"- [{activity.occurred_at}] {activity.title} (ID: {activity.source_id})")
    #     logger.debug(f"Content: {activity.content}...")

    # ---
    siyuan_client = connector._get_client()
    # content = await siyuan_client.export_md_content('20251219110521-sdsn8e5')
    # logger.info(f"{content}")
    # return

    # r = await siyuan_client.get_file('/data/assets/image-20251218214401-pyec85e.png')
    # >> 火山引擎"更新无状态负载"配置界面，展示环境变量、存储配置（含主目录、挂载卷、生命周期）等核心参数设置项。


    # r = await siyuan_client.get_file('/data/assets/image-20251219112214-yes1aua.png')
    # >> 一张代码编辑器界面截图，显示GitHub项目中的Go配置文件config/reloader.go。
    # 该文件用于增强规则文件热重载管理器功能，支持K8s ConfigMap挂载场景，包含文件重载监控、K8s ConfigMap挂载检测逻辑及相关配置变量和函数。

    r = await siyuan_client.get_file('/data/assets/image-20251219112035-5zqm3ln.png')
    # >> 一个容器日志监控界面，显示近期内Binlog日志信息，包含INFO级别日志记录Binlog文件旋转、MySQL同步操作及连接信息。


    logger.info(f"{len(r)=} bytes")
    logger.debug(f"{r[:100]=}")

    # Save image to temporary file for ollama LLM
    # ollama needs file path (absolute path)
    # with open('1.jpg', 'wb') as f:
    #     f.write(r)

    ollama_client = ollama.AsyncClient(host='http://localhost:11434')
    img_b64 = base64.b64encode(r).decode('utf-8')
    response = await ollama_client.chat(
        model="qwen3-vl:2B",
        messages=[
            {
                "role": "user",
                "content": """\
# Role: Image Analysis Expert

## Profile
- language: Chinese
- description: 专注于分析视觉图像并提取关键要素，将其总结为简洁、有意义的文本描述。
- background: 具备图像识别和机器学习领域的先进知识，能够高效处理和分析图片内容。
- personality: 客观、注重细节、逻辑性强。
- expertise: 转化视觉信息为文本描述，保证准确性和简洁性。
- target_audience: 需要视觉内容分析的专业人士及机构。

## Skills

1. 图像处理技能
   - 图像识别: 识别图片中的主要主题和元素。
   - 图像分类: 将图片内容分类以便于组织和分析。
   - 视觉信息提取: 从复杂的视觉内容中提取关键细节。
   - 数据分析: 分析图像数据以支持文本总结。

2. 文本生成技能
   - 语言处理: 使用自然语言处理技术生成高质量文本。
   - 文本简化: 将复杂信息简化为易理解的内容。
   - 内容筛选: 排除无用和冗余信息。
   - 字数限制: 确保总结在指定字数内且完整。

## Rules

1. 基本原则：
   - 客观描述: 保持总结的客观性和中立性。
   - 信息完整: 确保总结包含图片的重要细节。
   - 清晰准确: 确保信息清晰且精准。
   - 简洁表达: 保证表达简明扼要。

2. 行为准则：
   - 遵循图像分析规范: 严格按照行业标准分析图片。
   - 确保语言简洁: 使用尽量少的文字传达更多含义。
   - 用词专业: 使用专业术语进行汇总。
   - 坚持高效输出: 保持高效处理和输出。

3. 限制条件：
   - 字数限制: 总结不超过100字。
   - 信息过滤: 排除不必要的视觉信息。
   - 内容质量: 保证输出文本的质量不受字数影响。
   - 符合审美标准: 确保文本风格与专业审美标准一致。

## Workflows

- 目标: 提供专业、准确的图片内容总结
- 步骤 1: 识别图片中的主要元素和主题
- 步骤 2: 提炼出核心内容，筛剔冗余信息
- 步骤 3: 生成简洁且重要的信息描述
- 预期结果: 精简且易于理解的图片内容总结

## OutputFormat

1. 文本格式：
   - format: text
   - structure: 单段落结构，无序列表
   - style: 专业且精简
   - special_requirements: 无冗余信息，符合字数限制

2. 格式规范：
   - indentation: 无缩进
   - sections: 单一内容段，不分节
   - highlighting: 无特别强调

3. 验证规则：
   - validation: 确保没有超过字数限制
   - constraints: 提供准确的图片主题和内容
   - error_handling: 确认无信息丢失或过度简化

4. 示例说明：
   1. 示例1：
      - 标题: 晴空中的飞鸟
      - 格式类型: text
      - 说明: 描述一幅关于自然的图像
      - 示例内容: |
          一张展示蓝天背景中飞行鸟类的明亮图片，鸟类清晰且展翅于画面中心。

   2. 示例2：
      - 标题: 城市天际线
      - 格式类型: text
      - 说明: 描述城市建筑物环境图片
      - 示例内容: |
          展现繁忙城市的天际线，高楼大厦在背景中形成现代都市的典型轮廓。

## Initialization
作为Image Analysis Expert，你必须遵守上述Rules，按照Workflows执行任务，并按照文本格式输出。
""",
                "images": [img_b64]
            }
        ],
    )
    logger.info(f"Image analysis result: {response.model_dump(exclude={'message'})=}")
    logger.info(f"{response.message.content}")




if __name__ == "__main__":
    with mock_ctx(user_id=uuid.uuid4()):
        asyncio.run(main())
