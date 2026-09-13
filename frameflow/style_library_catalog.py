"""Versioned runtime snapshot of the gpt-image-2-style-library.

The authoring source for this catalog is the Codex skill
``gpt-image-2-style-library`` v1.0.4.  Keeping the compact catalog in the
application makes prompt generation deterministic and prevents production
from depending on a developer's home-directory skill installation.
"""
from __future__ import annotations

from typing import Any


STYLE_LIBRARY_VERSION = "1.0.4"
STYLE_LIBRARY_SOURCE = "awesome-gpt-image-2/style-library"
STYLE_LIBRARY_SOURCE_PATH = "frameflow/style_library_runtime/style-library-1.0.4.md"
STYLE_LIBRARY_SKILL_PATH = "frameflow/style_library_runtime/SKILL-1.0.4.md"
# Keep provenance portable. The application reads the versioned files under
# ``style_library_runtime``; this symbolic path records the authoring source
# without making a production process depend on a developer's home directory.
STYLE_LIBRARY_UPSTREAM_PATH = "gpt-image-2-style-library/references/style-library.md"

SELECTION_ORDER = (
    "output_target",
    "template_category",
    "visual_style_tag",
    "scene_tag",
    "nearest_example_case",
    "template_pitfalls",
)

PROMPT_BLOCKS = (
    "subjectTask",
    "compositionLayout",
    "visualStyleMaterials",
    "textLabels",
    "aspectRatioOutput",
    "constraintsNegative",
)

# This is deliberately a data-only catalog.  The prompt compiler consumes the
# entries below; it does not maintain a second set of visual prompt rules.
STYLE_LIBRARY_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "id": "ui-screenshot-system",
        "category": "UI & Interfaces",
        "styles": ["UI"],
        "scenes": ["Tech", "Social"],
        "tags": ["UI", "Dashboard", "Screenshot"],
        "examples": ["case 17", "case 2", "case 4"],
        "guidance": "锁定平台、比例、布局层级和准确可见文字；明确状态栏、Tab、操作区和评论层。",
        "pitfalls": "避免平台描述过泛；约束文字可读性和平台特征。",
        "keywords": ["ui", "interface", "dashboard", "app", "website", "界面", "仪表盘", "截图"],
    },
    {
        "id": "infographic-engine",
        "category": "Charts & Infographics",
        "styles": ["Infographic", "Charts"],
        "scenes": ["Education", "Tech"],
        "tags": ["Infographic", "Chart", "Education"],
        "examples": ["case 334", "case 1", "case 8"],
        "guidance": "定义3到5个模块、信息流、视觉层级、短标签、色彩分组、箭头和留白。",
        "pitfalls": "避免把长段正文塞进画面；先限制模块数量，再补视觉细节。",
        "keywords": ["infographic", "diagram", "chart", "timeline", "信息图", "图解", "流程图", "知识卡"],
    },
    {
        "id": "scientific-scale-diagram",
        "category": "Charts & Infographics",
        "styles": ["Infographic", "Charts", "Realistic"],
        "scenes": ["Education", "Tech"],
        "tags": ["Infographic", "Chart", "Education"],
        "examples": ["case 341"],
        "guidance": "使用6到8个尺度框，展示单位、倍率和彼此可区分的尺度细节。",
        "pitfalls": "避免所有尺度框视觉相同；避免通用放大镜式布局。",
        "keywords": ["scale", "micro", "macro", "science", "尺度", "微观", "宏观", "科普"],
    },
    {
        "id": "poster-layout-system",
        "category": "Posters & Typography",
        "styles": ["Poster"],
        "scenes": ["Commerce", "Social"],
        "tags": ["Poster", "Typography", "Campaign"],
        "examples": ["case 345", "case 5", "case 10"],
        "guidance": "锁定主体、标题、版式、配色和比例，明确标题层级与主视觉。",
        "pitfalls": "成品海报不要生成混合情绪板或流程板；约束多余文字和装饰符号。",
        "keywords": ["poster", "cover", "海报", "封面", "活动", "电影海报"],
    },
    {
        "id": "sports-campaign-poster",
        "category": "Posters & Typography",
        "styles": ["Poster", "Realistic"],
        "scenes": ["Commerce", "Fashion"],
        "tags": ["Poster", "Campaign", "Typography"],
        "examples": ["case 350", "case 3"],
        "guidance": "定义运动项目、运动员姿态、核心道具、标题和品牌配色；使用强光影与干净构图。",
        "pitfalls": "避免错误运动器材和杂乱拼贴；让运动员与核心道具占据主导。",
        "keywords": ["sports", "athlete", "运动", "运动员", "球员", "赛事"],
    },
    {
        "id": "conceptual-typography-poster",
        "category": "Posters & Typography",
        "styles": ["Poster"],
        "scenes": ["Creative", "Social"],
        "tags": ["Typography", "Poster", "Style"],
        "examples": ["case 355"],
        "guidance": "让准确标题成为主视觉结构，人物、物体或景观服务于标题含义。",
        "pitfalls": "避免默认字效、无关图标和错字；控制配色数量。",
        "keywords": ["typography", "title", "文字海报", "字体", "标题"],
    },
    {
        "id": "ink-double-exposure-poster",
        "category": "Posters & Typography",
        "styles": ["Poster", "Illustration", "Classical"],
        "scenes": ["Story", "History"],
        "tags": ["Poster", "Classical", "Style"],
        "examples": ["case 359"],
        "guidance": "融合人像剪影、水墨纹理、氛围和留白，保持构图克制、高级、可读。",
        "pitfalls": "避免廉价奇幻拼贴和景物堆叠；非必要时减少文字。",
        "keywords": ["ink", "double exposure", "水墨", "双重曝光", "诗意", "文化"],
    },
    {
        "id": "nature-science-poster",
        "category": "Posters & Typography",
        "styles": ["Poster", "Infographic"],
        "scenes": ["Education"],
        "tags": ["Poster", "Education", "Style"],
        "examples": ["case 339"],
        "guidance": "使用清晰主体、少量文案、柔和阴影和有纪律的留白。",
        "pitfalls": "避免广告感过重和密集百科正文。",
        "keywords": ["nature", "science poster", "自然", "科普海报", "植物", "动物"],
    },
    {
        "id": "product-commerce-visual",
        "category": "Products & E-commerce",
        "styles": ["Product", "Realistic"],
        "scenes": ["Commerce", "Food"],
        "tags": ["Product", "Commerce", "Packaging"],
        "examples": ["case 373", "case 358"],
        "guidance": "定义商品、卖点、材质、场景、光线和版块；区分主商品、卖点标签和辅助道具。",
        "pitfalls": "避免无关道具削弱商品识别；约束包装文字和卖点表达。",
        "keywords": ["product", "packaging", "commerce", "商品", "产品", "包装", "电商", "卖点"],
    },
    {
        "id": "personalized-beauty-report",
        "category": "Products & E-commerce",
        "styles": ["Product", "UI"],
        "scenes": ["Commerce", "Fashion"],
        "tags": ["Product", "Layout", "Style"],
        "examples": ["case 353"],
        "guidance": "使用诊断、推荐和商品卡片的报告层级，对齐商品图、标签和评分。",
        "pitfalls": "避免医疗化结论和难读小字；保持推荐逻辑清楚。",
        "keywords": ["beauty", "skincare", "makeup", "美妆", "护肤", "肤质", "美容"],
    },
    {
        "id": "brand-identity-package",
        "category": "Brand & Logos",
        "styles": ["Brand"],
        "scenes": ["Commerce"],
        "tags": ["Brand", "Logo", "Identity"],
        "examples": ["case 354"],
        "guidance": "定义品牌名、定位、配色、字体、Logo 用法和触点，生成统一对齐的品牌板。",
        "pitfalls": "避免无关 Logo 变体和混乱配色；保持品牌文字准确。",
        "keywords": ["brand", "logo", "identity", "品牌", "标志", "视觉识别", "vi"],
    },
    {
        "id": "brand-touchpoint-board",
        "category": "Brand & Logos",
        "styles": ["Brand", "Product"],
        "scenes": ["Commerce", "Social"],
        "tags": ["Brand", "Identity", "Campaign"],
        "examples": ["case 362"],
        "guidance": "指定触点清单、统一视觉规则和样机排列，让所有面板共享配色与字体逻辑。",
        "pitfalls": "避免混入多个无关 Campaign 风格；可读性下降时减少触点。",
        "keywords": ["touchpoint", "campaign board", "品牌触点", "campaign", "落地"],
    },
    {
        "id": "architecture-space",
        "category": "Architecture & Spaces",
        "styles": ["Architecture"],
        "scenes": ["Travel", "Commerce"],
        "tags": ["Architecture", "Interior", "Map"],
        "examples": ["case 331", "case 11"],
        "guidance": "定义视角、尺度、材质、光线和空间功能；地图需要明确地标、标签和相对位置。",
        "pitfalls": "概念图之外避免不合理透视；锁定地图标签语言和相对位置。",
        "keywords": ["architecture", "interior", "space", "environment", "building", "建筑", "室内", "空间", "环境"],
    },
    {
        "id": "realistic-photography",
        "category": "Photography & Realism",
        "styles": ["Photography", "Realistic"],
        "scenes": ["Fashion", "Commerce"],
        "tags": ["Photography", "Realistic", "Lens"],
        "examples": ["case 377"],
        "guidance": "指定机位、镜头、光源、质感、背景和动作；纪实写实保留可信的小瑕疵。",
        "pitfalls": "商业美妆之外避免塑料皮肤；需要时加入手部、文字和人体结构约束。",
        "keywords": ["photo", "photography", "realistic", "camera", "portrait", "摄影", "写实", "人像", "写真"],
    },
    {
        "id": "street-accident-moment",
        "category": "Photography & Realism",
        "styles": ["Photography", "Realistic"],
        "scenes": ["Travel", "Social"],
        "tags": ["Photography", "Realistic", "Scene"],
        "examples": ["case 376"],
        "guidance": "描述具体瞬间、机位高度、运动模糊和街景，避免摆拍和广告棚拍感。",
        "pitfalls": "避免画面过于干净；让事件可信并符合物理关系。",
        "keywords": ["street", "candid", "accident", "phone photo", "街拍", "抓拍", "意外", "手机摄影"],
    },
    {
        "id": "illustration-art-style",
        "category": "Illustration & Art",
        "styles": ["Illustration"],
        "scenes": ["Story", "Creative"],
        "tags": ["Illustration", "Art", "Style"],
        "examples": ["case 346", "case 6"],
        "guidance": "定义构图、主体、配色、笔触材质、情绪和完成度；参考图任务说明需要保留的特征。",
        "pitfalls": "避免只写风格不写构图；使用参考图时锁定角色识别。",
        "keywords": ["illustration", "painting", "watercolor", "anime", "插画", "绘画", "水彩", "动漫", "艺术"],
    },
    {
        "id": "character-design-sheet",
        "category": "Characters & People",
        "styles": ["Character", "Illustration"],
        "scenes": ["Story"],
        "tags": ["Character", "Pose", "Style"],
        "examples": ["case 347"],
        "guidance": "定义身份特征、服装、体型比例、视图数量和参考板版式；保持脸、发型和服装一致。",
        "pitfalls": "避免不同视图服装细节变化；画面拥挤时减少视图数量。",
        "keywords": ["character", "avatar", "pose", "角色", "人物", "人设", "设定", "三视图", "四视图"],
    },
    {
        "id": "3d-collectible-toy",
        "category": "Characters & People",
        "styles": ["3D", "Character"],
        "scenes": ["Commerce", "Creative"],
        "tags": ["Character", "3D", "Style"],
        "examples": ["case 378"],
        "guidance": "保留参考图中的脸和服装锚点，指定材质、包装、底座、光线和收藏比例。",
        "pitfalls": "避免没有身份细节的通用玩具；包装文字保持少量且准确。",
        "keywords": ["3d", "toy", "collectible", "blind box", "公仔", "潮玩", "收藏玩具", "盲盒"],
    },
    {
        "id": "scene-storytelling",
        "category": "Scenes & Storytelling",
        "styles": ["Scenes", "Illustration"],
        "scenes": ["Story", "Social"],
        "tags": ["Scene", "Story", "Storyboard"],
        "examples": ["case 330"],
        "guidance": "定义人物、地点、时间、冲突、情绪和机位，让场景细节服务故事。",
        "pitfalls": "避免通用幻想背景；让叙事线索在画面中可见。",
        "keywords": ["scene", "story", "storyboard", "world", "live", "场景", "故事", "分镜", "世界观", "叙事"],
    },
    {
        "id": "history-classical-themes",
        "category": "History & Classical Themes",
        "styles": ["History", "Classical", "Illustration"],
        "scenes": ["History", "Story"],
        "tags": ["History", "Classical", "Scroll"],
        "examples": ["case 375", "case 338"],
        "guidance": "指定朝代、服饰制度、器物参考、版式和文化气质，明确长卷、册页或海报形式。",
        "pitfalls": "需要历史准确时避免朝代混搭；约束随机现代物件。",
        "keywords": ["history", "dynasty", "ancient", "classical", "历史", "古风", "古代", "朝代", "长卷"],
    },
    {
        "id": "document-publishing",
        "category": "Documents & Publishing",
        "styles": ["Documents", "Infographic"],
        "scenes": ["Education", "Tech"],
        "tags": ["Document", "Publishing", "Layout"],
        "examples": ["case 360"],
        "guidance": "定义页面尺寸、分栏、目录、图表系统和字体层级，使用可读标题、表格和页面节奏。",
        "pitfalls": "避免密集小字；让图表和说明对齐页面网格。",
        "keywords": ["document", "manual", "white paper", "report", "文档", "手册", "报告", "出版"],
    },
    {
        "id": "concept-product-breakdown",
        "category": "Other Use Cases",
        "styles": ["Other Use Cases", "Product"],
        "scenes": ["Creative", "Tech"],
        "tags": ["Creative", "R&D", "Special"],
        "examples": ["case 370", "case 361"],
        "guidance": "定义产物类型、组件、标签、材质逻辑和展示格式，使用清晰标注和受控技术风格。",
        "pitfalls": "避免任务边界过泛；标签要短，组件关系要清楚。",
        "keywords": ["concept", "r&d", "exploded", "breakdown", "研发", "拆解", "概念产品", "结构图"],
    },
)

CATEGORIES = (
    "UI & Interfaces",
    "Charts & Infographics",
    "Posters & Typography",
    "Products & E-commerce",
    "Brand & Logos",
    "Architecture & Spaces",
    "Photography & Realism",
    "Illustration & Art",
    "Characters & People",
    "Scenes & Storytelling",
    "History & Classical Themes",
    "Documents & Publishing",
    "Other Use Cases",
)

STYLES = (
    "3D", "Architecture", "Brand", "Character", "Characters", "Charts", "Classical",
    "Documents", "History", "Illustration", "Infographic", "Other Use Cases", "Photography",
    "Poster", "Product", "Products", "Realistic", "Scenes", "UI",
)

SCENES = (
    "Creative", "Tech", "Commerce", "Education", "Social", "Fashion", "Food", "Travel", "Story", "History",
)

TEMPLATES_BY_ID = {str(item["id"]): item for item in STYLE_LIBRARY_TEMPLATES}


def style_library_snapshot() -> dict[str, Any]:
    """Return a JSON-serialisable read-only-style catalog snapshot."""

    return {
        "version": STYLE_LIBRARY_VERSION,
        "source": STYLE_LIBRARY_SOURCE,
        "sourcePath": STYLE_LIBRARY_SOURCE_PATH,
        "skillPath": STYLE_LIBRARY_SKILL_PATH,
        "upstreamSourcePath": STYLE_LIBRARY_UPSTREAM_PATH,
        "selectionOrder": list(SELECTION_ORDER),
        "promptBlocks": list(PROMPT_BLOCKS),
        "categories": list(CATEGORIES),
        "styles": list(STYLES),
        "scenes": list(SCENES),
        "templates": [dict(item) for item in STYLE_LIBRARY_TEMPLATES],
    }


__all__ = [
    "CATEGORIES",
    "PROMPT_BLOCKS",
    "SCENES",
    "SELECTION_ORDER",
    "STYLE_LIBRARY_SOURCE",
    "STYLE_LIBRARY_SOURCE_PATH",
    "STYLE_LIBRARY_SKILL_PATH",
    "STYLE_LIBRARY_TEMPLATES",
    "STYLE_LIBRARY_VERSION",
    "STYLES",
    "TEMPLATES_BY_ID",
    "style_library_snapshot",
]
