# FRAMEFLOW V4 项目清理审计

审计目标：将当前新工作台整理为正式 FRAMEFLOW V4 Git 工程，并保持既有工作流和下游资产通路连续。

## 1. V4 发布边界

- 当前产品版本：`4.0.0`。
- 正式远程仓库：https://github.com/suyu5757-lab/-suyu5757-lab-FRAMEFLOW-V4
- 正式分支：`main`。
- V4 包含当前新工作台的源码、测试、CI、公开文档和剧本/分镜规则升级。
- 旧项目数据、旧运行时状态和旧 Prompt/Server 备份不属于 V4 发布内容。

## 2. 必须保留

- `server.py` 和 `frameflow/` 后端源码；
- `web/src/`、`web/index.html` 和前端构建配置；
- `tests/`、`web/src/*.test.*` 和 `web/tests/` 测试源码；
- `requirements.txt`、前端锁文件、CI、工程脚本和公开文档；
- 剧本/分镜规则、自动审查、版本指纹和资产交接实现。

## 3. 不进入 Git

- `.env`、系统凭据、CLI 登录态和本机配置；
- `data/`、`generated/`、数据库、SQLite WAL/SHM、媒体和日志；
- `.venv/`、`node_modules/`、`web/dist/`、`__pycache__/`、构建缓存；
- Playwright 输出、测试生成文件、编辑器附件和临时目录；
- `docs/prompt-generation-backups/` 历史 Prompt/Server 备份。

上述路径由 `.gitignore` 覆盖；清理发布副本时不会删除源项目中的用户数据。

## 4. V4 版本收口

- 根目录 README、贡献规范、公开报告和清理审计均以 V4 为正式身份。
- 前端包名和版本为 `frameflow-v4-studio` / `4.0.0`。
- FastAPI 应用标题和版本为 FRAMEFLOW V4 / `4.0.0`。
- 启动脚本和 OpenCode 诊断脚本使用 FRAMEFLOW V4 标识。
- `frameflow/v4.py` 和 V4 测试文件名承载原有工作流实现。
- API 路径、字段和资产 Prompt 核心规则不因版本命名更新而改变。
- 数据库中的 `*_v3` 表名和迁移编号仅表示既有存储结构，不作为公开产品版本；直接重命名会破坏运行时数据连续性，因此保留。

## 5. 验证要求

- Python AST 检查通过；
- 后端和前端测试通过；
- TypeScript、生产构建和 bundle gate 通过；
- Git 暂存区 `git diff --check` 通过；
- 提交树无环境变量、数据库、运行时数据、依赖目录或构建产物；
- 远程 `main` 提交与本地 V4 发布提交完成核对。

本审计只针对正式 V4，不迁移、不修复、不重算旧项目。
