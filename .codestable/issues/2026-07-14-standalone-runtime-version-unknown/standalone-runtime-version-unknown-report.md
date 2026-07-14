---
doc_type: issue-report
issue: standalone-runtime-version-unknown
status: confirmed
severity: P1
summary: standalone skill 安装后的 runtime manifest 版本为 unknown
tags: [runtime, versioning, standalone-install]
---

# Standalone Runtime 版本 Unknown Issue Report

## 1. 问题现象

通过 `skills` CLI standalone 安装 CodeStable skills 后，运行 runtime refresh 会成功生成 `.codestable/runtime-manifest.json`，但其中 `plugin_version` 和 `runtime_version` 都是 `unknown`。

## 2. 复现步骤

1. 将 `cs-onboard` 作为 standalone skill 安装，不携带插件级祖先目录。
2. 在已接入 CodeStable 的临时仓库运行该 skill 自带的 `codestable-runtime-sync.py`。
3. 读取生成的 `.codestable/runtime-manifest.json`。
4. 观察到：两处版本字段均为 `unknown`，命令仍成功退出。

复现频率：稳定复现。

## 3. 期望 vs 实际

**期望行为**：任何受支持的安装形式都能把实际 CodeStable 版本写入 runtime manifest。

**实际行为**：standalone 安装缺少版本发现所需的祖先元数据，manifest 回退为 `unknown`。

## 4. 环境信息

- 涉及模块 / 功能：`cs-onboard` standalone package、runtime sync、release version bump、plugin package checker。
- 相关文件 / 函数：`plugins/codestable/skills/cs-onboard/tools/codestable_runtime.py::discover_plugin_version` 与 `sync_runtime`。
- 运行环境：隔离 standalone skill 目录与临时已接入仓库。
- 其他上下文：关联 #43。

## 5. 严重程度

**P1** — runtime refresh 给出成功信号却写入不可验证的版本，破坏版本漂移检测与升级判断。

## 备注

GitHub Issue：#47。
