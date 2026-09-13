# FRAMEFLOW V4 Public Release Report

状态：`FRAMEFLOW_V4_PUBLIC_RELEASE = VERIFIED`

正式版本：`4.0.0`

发布目标：[suyu5757-lab/-suyu5757-lab-FRAMEFLOW-V4](https://github.com/suyu5757-lab/-suyu5757-lab-FRAMEFLOW-V4)

## 1. 发布内容

FRAMEFLOW V4 是当前新工作台的正式版本。V4 包含当前工作树中的剧本与分镜规则替换、自动审查与自动修复门禁、资产需求交接、来源版本追踪和现有资产 Prompt 通路适配。

本版本保持原有工作流顺序、页面入口、API 路径和资产 Prompt 状态流，不把旧项目数据或本机运行时状态带入公开仓库。

## 2. Git 工程边界

- `main` 为 V4 正式分支。
- 仓库使用独立的干净 Git 历史，不继承本机开发工作目录的运行时数据和旧远程配置。
- `.gitignore` 覆盖环境变量、数据库、媒体、生成结果、缓存、依赖目录和构建产物。
- `.env.example` 只保留变量名称和空值，不包含真实凭据。
- 旧的 `docs/prompt-generation-backups/` 历史备份不进入 V4 仓库。

## 3. 下游兼容性

- 剧本 → 分镜 → 资产监管 → 资产创作意图 → 资产 Prompt 的数据链路保持连续。
- `sourceBeatIds`、`sceneId`、`shotId`、`assetRequirements`、`mustPreserve`、`mustAvoid` 和版本指纹继续作为来源交接信息传递。
- 资产 Prompt 的既有模板、编译规则、QA 规则、修复次数和状态流不被重写。
- API 入口保持现有路径，包括 `/api/v2` 及既有 Story Run、Asset Intent 和 Asset Prompt Run 接口。
- 数据库中的 `*_v3` 表名和历史迁移编号属于持久化兼容标识，不代表产品版本；V4 通过现有存储边界继续使用它们。

## 4. 清理与安全审计

未进入 V4 Git 历史的内容包括：

- `.env`、本机密钥、登录态和凭据文件；
- `data/`、`generated/`、数据库、SQLite WAL/SHM、媒体和日志；
- `.venv/`、`node_modules/`、`web/dist/`、Python/TypeScript 缓存；
- Playwright 输出、测试产物、编辑器附件和本机临时文件；
- 旧项目备份和带有本机运行时状态的历史副本。

## 5. 验证

- Python 源码 AST 语法检查通过。
- 后端测试、前端测试、TypeScript 检查、生产构建和 bundle gate 已通过。
- V4 提交树通过 `git diff --check` 和禁止路径扫描。
- GitHub `main` 远程提交已完成只读核对。

本报告只描述正式 V4 发布状态，不代表需要恢复或迁移旧项目。
