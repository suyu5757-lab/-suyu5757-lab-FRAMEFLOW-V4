# FRAMEFLOW V4 GitHub Sync Final Report

状态：`FRAMEFLOW_V4_PUBLIC_RELEASE = VERIFIED`

## 发布信息

- GitHub Repository URL: https://github.com/suyu5757-lab/-suyu5757-lab-FRAMEFLOW-V4
- Branch: `main`
- Product version: `4.0.0`
- Release type: clean repository sync

V4 的正式代码基线位于目标仓库 `main`。该仓库由当前新工作台的源码、测试、CI、配置和公开文档组成，不包含本机项目数据、旧远程历史或运行时产物。

## 版本收口

- 本地工作台和远程仓库的产品身份统一为 FRAMEFLOW V4。
- 根目录、前端包、FastAPI 应用标题和启动/诊断脚本统一使用 V4 标识。
- 正式报告、测试文件和工作流模块的产品命名已统一为 V4。
- API 路径和既有调用顺序保持不变，以保证工作台通路连续。
- 数据库 `*_v3` 表名与迁移编号仅作为存储兼容标识保留，不作为产品版本展示。

## 清洁仓库审计

- `.gitignore` 已纳入正式工程。
- 实际 `.env`、数据库、媒体、生成目录、依赖目录、构建输出和缓存未进入 Git。
- `.env.example` 不含真实凭据。
- 旧 Prompt/Server 备份不进入 V4 发布树。
- `git diff --check`、Python AST 检查和提交树禁止路径扫描通过。

## 工作流兼容性

剧本、分镜、自动审查、资产监管、资产创作意图和既有资产 Prompt 生产仍沿用同一条工作流通路。V4 只统一版本身份并承载已经完成的规则升级，不改变八阶段导航、页面顺序或资产 Prompt 的核心生成规则。

本报告确认的是 FRAMEFLOW V4 仓库同步状态；它不要求迁移旧项目数据。
