"""Pydantic schemas for SiYuan API responses and database tables.

本模块定义了思源笔记 API 响应和数据库表的 Pydantic Schema。

包含以下内容:

- **枚举类型**: 块类型、行内元素类型、引用类型、属性类型等
- **数据库表 Schema**: blocks, refs, attributes, assets, file_annotation_refs, spans 等表的 Schema
- **API 响应 Schema**: 笔记本信息、导出结果、文件信息等 API 响应的 Schema

参考文档: https://docs.siyuan-note.club/zh-Hans/reference/database/table.html
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class BlockType(str, Enum):
    """Block main type (blocks.type).

    字段值    说明
    audio    音频块 (audio block)
    av       属性表 (attribute table)
    b        引述块 (quote block)
    c        代码块 (code block)
    d        文档块 (document block)
    h        标题块 (heading block)
    html     HTML 块 (HTML block)
    i        列表项 (list item)
    iframe   iframe 块 (iframe block)
    l        列表块 (list block)
    m        公式块 (math/formula block)
    p        段落块 (paragraph block)
    query_embed  嵌入块 (query embed block)
    s        超级块 (super block)
    t        表格块 (table block)
    tb       分割线 (table break / divider block)
    video    视频块 (video block)
    widget   挂件块 (widget block)
    """

    AUDIO = "audio"                # 音频块
    ATTRIBUTE_TABLE = "av"         # 属性表
    QUOTE = "b"                    # 引述块
    CODE = "c"                     # 代码块
    DOCUMENT = "d"                 # 文档块
    HEADING = "h"                  # 标题块
    HTML = "html"                  # HTML 块
    LIST_ITEM = "i"                # 列表项
    IFRAME = "iframe"              # iframe 块
    LIST = "l"                     # 列表块
    FORMULA = "m"                  # 公式块
    PARAGRAPH = "p"                # 段落块
    QUERY_EMBED = "query_embed"    # 嵌入块
    SUPER = "s"                    # 超级块
    TABLE = "t"                    # 表格块
    DIVIDER = "tb"                 # 分割线
    VIDEO = "video"                # 视频块
    WIDGET = "widget"              # 挂件块


class BlockSubtype(str, Enum):
    """Block subtype (blocks.subtype).

    块次类型，默认为空字符串。仅用于 type 为 'h' (标题块) 和 'l' (列表块) 的情况。

    ===========  =========  ===================
    字段值       关联 type   说明
    ===========  =========  ===================
    h1           h          一级标题块
    h2           h          二级标题块
    h3           h          三级标题块
    h4           h          四级标题块
    h5           h          五级标题块
    h6           h          六级标题块
    o            l          有序列表块
    u            l          无序列表块
    t            l          任务列表块
    ===========  =========  ===================
    """

    H1 = "h1"  # 一级标题块 (Heading level 1)
    H2 = "h2"  # 二级标题块 (Heading level 2)
    H3 = "h3"  # 三级标题块 (Heading level 3)
    H4 = "h4"  # 四级标题块 (Heading level 4)
    H5 = "h5"  # 五级标题块 (Heading level 5)
    H6 = "h6"  # 六级标题块 (Heading level 6)
    OREDERD_LIST = "o"  # 有序列表块 (Ordered list)
    UNOREDERD_LIST = "u"  # 无序列表块 (Unordered list)
    TASK_LIST = "t"  # 任务列表块 (Task list)


class SpanType(str, Enum):
    """Inline element type (spans.type).

    行内元素类型，用于 spans 表的 type 字段。

    ===================  ===================
    字段值               说明
    ===================  ===================
    img                 图片
    tag                 文档标签
    textmark a          链接
    textmark block-ref  引用
    textmark code       行内代码
    textmark inline-memo 备注
    textmark tag        #标签#
    textmark inline-math 行内公式
    textmark mark       高亮标记
    textmark em         HTML tag (emphasis)
    textmark s          HTML tag (strikethrough)
    textmark strong     HTML tag (strong)
    textmark sub        HTML tag (subscript)
    textmark sup        HTML tag (superscript)
    textmark u          HTML tag (underline)
    ===================  ===================
    """

    IMG = "img"  # 图片
    TAG = "tag"  # 文档标签
    TEXTMARK_A = "textmark a"  # 链接
    TEXTMARK_BLOCK_REF = "textmark block-ref"  # 引用
    TEXTMARK_CODE = "textmark code"  # 行内代码
    TEXTMARK_INLINE_MEMO = "textmark inline-memo"  # 备注
    TEXTMARK_TAG = "textmark tag"  # #标签#
    TEXTMARK_INLINE_MATH = "textmark inline-math"  # 行内公式
    TEXTMARK_MARK = "textmark mark"  # 高亮标记
    TEXTMARK_EM = "textmark em"  # HTML tag (emphasis)
    TEXTMARK_S = "textmark s"  # HTML tag (strikethrough)
    TEXTMARK_STRONG = "textmark strong"  # HTML tag (strong)
    TEXTMARK_SUB = "textmark sub"  # HTML tag (subscript)
    TEXTMARK_SUP = "textmark sup"  # HTML tag (superscript)
    TEXTMARK_U = "textmark u"  # HTML tag (underline)


class RefType(str, Enum):
    """Reference type (refs.type).

    引用类型，用于 refs 表的 type 字段。

    .. note::
        refs.type 字段可能包含其他值，本枚举仅定义常见类型。
    """

    REF_ID = "ref_id"  # 引用ID (常见类型)
    BLOCK_REF = "block-ref"  # 块引用


class AttributeType(str, Enum):
    """Attribute type (attributes.type).

    属性类型，用于 attributes 表的 type 字段。

    .. note::
        attributes.type 字段可以包含各种值，本枚举仅定义常见类型。
        最常见的类型是 'b' (块属性)。
    """

    B = "b"  # 块属性 (Block attribute, 最常见)
    DOC = "doc"  # 文档属性
    NAMESPACE = "namespace"  # 命名空间属性


# ============================================================================
# Database Table Schemas
# ============================================================================


class BlockSchema(BaseModel):
    """Block schema (blocks table).

    存储了所有的内容块数据。对应思源笔记数据库中的 blocks 表。

    时间字段格式: YYYYMMDDHHmmss (例如: 20210104091228)
    """

    id: str = Field(..., description="内容块 ID")
    parent_id: Optional[str] = Field(None, description="上级块的 ID，文档块该字段为空")
    root_id: Optional[str] = Field(None, description="顶层块的 ID，即文档块 ID")
    hash: Optional[str] = Field(None, description="content 字段的 SHA256 校验和")
    box: str = Field(..., description="笔记本 ID")
    path: str = Field(..., description="内容块所在文档路径")
    hpath: str = Field(..., description="人类可读的内容块所在文档路径")
    name: Optional[str] = Field(None, description="内容块名称")
    alias: Optional[str] = Field(None, description="内容块别名")
    memo: Optional[str] = Field(None, description="内容块备注")
    tag: Optional[str] = Field(None, description="标签：非文档块为块内包含的标签，文档块为文档的标签")
    content: str = Field(..., description="去除了 Markdown 标记符的文本")
    fcontent: Optional[str] = Field(None, description="第一个子块去除了 Markdown 标记符的文本 (1.9.9 添加)")
    markdown: str = Field(..., description="包含完整 Markdown 标记符的文本")
    length: Optional[int] = Field(None, description="fcontent 字段文本长度")
    type: str = Field(..., description="内容块主类型，参考 BlockType 枚举")
    subtype: Optional[str] = Field(None, description="内容块次类型，参考 BlockSubtype 枚举，默认为空字符串")
    ial: Optional[str] = Field(None, description="内联属性列表，形如 {: name=\"value\"}")
    sort: Optional[int] = Field(None, description="排序权重，数值越小排序越靠前")
    created: str = Field(..., description="创建时间，格式: YYYYMMDDHHmmss")
    updated: str = Field(..., description="更新时间，格式: YYYYMMDDHHmmss")


class RefSchema(BaseModel):
    """Reference schema (refs table).

    存储了所有的引用双链结构。对应思源笔记数据库中的 refs 表。
    """

    id: str = Field(..., description="引用 ID")
    def_block_id: str = Field(..., description="被引用块的块 ID")
    def_block_parent_id: Optional[str] = Field(None, description="被引用块的双亲节点的块 ID")
    def_block_root_id: Optional[str] = Field(None, description="被引用块所在文档的 ID")
    def_block_path: Optional[str] = Field(None, description="被引用块所在文档的路径")
    block_id: str = Field(..., description="引用所在内容块 ID")
    root_id: Optional[str] = Field(None, description="引用所在文档块 ID")
    box: str = Field(..., description="引用所在笔记本 ID")
    path: str = Field(..., description="引用所在文档块路径")
    content: Optional[str] = Field(None, description="引用锚文本")
    markdown: Optional[str] = Field(None, description="包含完整 Markdown 标记符的文本")
    type: Optional[str] = Field(None, description="引用类型，参考 RefType 枚举")


class AttributeSchema(BaseModel):
    """Attribute schema (attributes table).

    存储块属性。对应思源笔记数据库中的 attributes 表。
    """

    id: str = Field(..., description="属性 ID")
    name: str = Field(..., description="属性名称")
    value: Optional[str] = Field(None, description="属性值")
    type: Optional[str] = Field(None, description="属性类型，参考 AttributeType 枚举")
    block_id: str = Field(..., description="块 ID")
    root_id: Optional[str] = Field(None, description="文档 ID")
    box: str = Field(..., description="笔记本 ID")
    path: Optional[str] = Field(None, description="文档文件路径")


class AssetSchema(BaseModel):
    """Asset schema (assets table).

    资源引用。对应思源笔记数据库中的 assets 表，用于存储资源文件（如图片、附件等）的引用信息。
    """

    id: str = Field(..., description="引用 ID")
    block_id: Optional[str] = Field(None, description="块 ID")
    root_id: Optional[str] = Field(None, description="文档 ID")
    box: str = Field(..., description="笔记本 ID")
    docpath: Optional[str] = Field(None, description="文档路径")
    path: str = Field(..., description="资源文件路径")
    name: Optional[str] = Field(None, description="资源文件名")
    title: Optional[str] = Field(None, description="资源标题")
    hash: Optional[str] = Field(None, description="资源哈希值")


class FileAnnotationRefSchema(BaseModel):
    """File annotation reference schema (file_annotation_refs table).

    文件 PDF 的注释引用。对应思源笔记数据库中的 file_annotation_refs 表。
    """

    id: str = Field(..., description="引用 ID")
    file_path: str = Field(..., description="关联文件路径")
    annotation_id: str = Field(..., description="被引用注释 ID")
    block_id: Optional[str] = Field(None, description="引用所在内容块 ID")
    root_id: Optional[str] = Field(None, description="引用所在文档块 ID")
    box: Optional[str] = Field(None, description="引用所在笔记本 ID")
    path: Optional[str] = Field(None, description="引用所在文档块路径")
    content: Optional[str] = Field(None, description="引用锚文本")
    type: Optional[str] = Field(None, description="注释类型")


class SpanSchema(BaseModel):
    """Span schema (spans table).

    行内元素。对应思源笔记数据库中的 spans 表，用于存储块内的行内元素（如链接、代码、公式等）。
    """

    id: str = Field(..., description="行内元素 ID")
    block_id: str = Field(..., description="元素所在内容块 ID")
    root_id: Optional[str] = Field(None, description="元素所在文档块 ID")
    box: str = Field(..., description="元素所在笔记本 ID")
    path: Optional[str] = Field(None, description="元素所在文档块路径")
    content: Optional[str] = Field(None, description="元素内容")
    markdown: Optional[str] = Field(None, description="包含完整 Markdown 标记符的元素内容")
    type: str = Field(..., description="元素类型，参考 SpanType 枚举")
    ial: Optional[str] = Field(None, description="元素样式（内联属性列表）")


# ============================================================================
# API Response Schemas
# ============================================================================


class NotebookInfo(BaseModel):
    """Notebook information."""

    id: str = Field(..., description="Notebook ID")
    name: str = Field(..., description="Notebook name")
    icon: str = Field(..., description="Notebook icon (emoji code)")
    sort: int = Field(..., description="Sort order")
    closed: bool = Field(..., description="Whether the notebook is closed")


class ExportResult(BaseModel):
    """Export result for Markdown content."""

    hPath: str = Field(..., description="Human-readable path")
    content: str = Field(..., description="Markdown content")


class FileInfo(BaseModel):
    """File information."""

    isDir: bool = Field(..., description="Whether it is a directory")
    name: str = Field(..., description="File or directory name")


class SystemProgress(BaseModel):
    """System boot progress."""

    details: str = Field(..., description="Progress details")
    progress: int = Field(..., description="Progress percentage (0-100)")


class MessageResult(BaseModel):
    """Message push result."""

    id: str = Field(..., description="Message ID")


class DocumentInfo(BaseModel):
    """Document information (returned by create_doc_with_markdown)."""

    id: str = Field(..., description="Document ID")


class BlockInfo(BaseModel):
    """Block information (returned by block operations)."""

    id: str = Field(..., description="Block ID")

