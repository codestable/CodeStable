# doc-api 参考模板

本文件提供 `cs-doc-api` 使用的 manifest、条目文档模板和源码提取清单。

## 1. `manifest.yaml` 格式

```yaml
project: {项目名}
entry_type: component | function | endpoint | command
source_root: {源码根路径}
last_scanned: YYYY-MM-DD

entries:
  - {entry: button, category: 基础组件, source_files: [src/components/Button.vue], doc_path: docs/api/button.md, status: pending, note: ""}
 ```

status 语义：`pending` / `draft` / `current` / `outdated` / `skipped`。

## 2. 条目文档 frontmatter

```yaml
---
doc_type: lib-api-ref
entry: {entry}
category: {category}
status: draft | current | outdated
source_files: [{source_files}]
summary: {summary}
tags: []
last_reviewed: YYYY-MM-DD
---
```

## 3. 条目文档模板

```markdown
## 概述

## API 参考

## 基本用法

## 典型场景

## 注意事项

## 相关条目
```

模板是最大集，按条目实际情况裁剪。

## 4. 源码提取清单

生成条目前必须从源码提取：

1. 接口签名
2. 类型定义
3. 默认值
4. 已有注释
5. 导出方式
6. 项目类型特有的附加表面（如 Slots、Events、flag、schema）

规则：

- 以源码为事实源，不编造接口
- 注释缺失时可根据类型和命名推断，但需说明
- 源码与方案不一致时，以源码为准写文档