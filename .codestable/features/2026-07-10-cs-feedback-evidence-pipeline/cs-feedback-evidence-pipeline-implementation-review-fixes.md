---
doc_type: feature-implementation-history
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: active
updated: 2026-07-11
---

# CS Feedback Evidence Pipeline Review Fix Continuation

本文件承接主 implementation 报告的 Round 14+ 修复证据，避免单个 Markdown 超过 300 行。

## Review Fix Round 14

- Reviewer：有效 Paseo Fable 5/high Round 14 复审完成；本地复现七类开放终止符泄漏和五类
  中文正文过吞，确认 REV-14-01/02；carry nits/suggestions 未修改。
- RED：两层隐私矩阵新增 `…/——/（/(/·/～/“`；两层保真矩阵要求路径消失且 `，随后`、
  `应该 先跑 design-review.md`、`详见 3.2 节` 等正文保留。聚焦命令真实得到 `4 failed`。
- GREEN：枚举式 suffix 替换为绝对路径核心识别 + 确定性 span 扫描；核心 segment 排除句读，
  引号内路径整段处理，带分隔符空格目录精确延伸，未加引号的文件尾部最多检查两个 token，
  多词只允许深路径。reporter 继续复用核心 `PATH_PATTERN`。
- VERIFY：聚焦 `4 passed`、privacy/reporting `62 passed`、targeted `171 passed`、full
  `341 passed`、eval `65 passed`；`/goal`、长文本和关键中文保真 sanity 均通过；runtime/diff
  通过，package 仅既有根 `cs-onboard/` baseline。
- Resolution：REV-14-01 的开放终止符不再靠闭集枚举；REV-14-02 的核心标点与跨正文追逐均有
  旧实现下失败的双向回归。未改 promotion/carry nit。

## Review Fix Round 15

- Reviewer：有效 Paseo Fable 5/high Round 15 复审完成；本地复现相对引用/版本号/dotted 中文
  过吞及浅路径双词文件名泄漏，确认 REV-15-01/02/03；carry nits 未修改。
- RED：双向矩阵补第一/第二词位、浅/深路径和 `.codestable/tests/docs` 相对引用；聚焦命令
  `4 failed`。
- GREEN：spaced continuation 收紧为一个空格组件后立即接斜杠；扩展名拒绝纯数字和 4+ 字
  非 ASCII 句子；双词文件名移除 depth gate。首次 GREEN 发现 core 会从相对路径内部斜杠重启，
  再增加 ASCII path-token 起始边界；最终聚焦 `4 passed`。
- VERIFY：privacy/reporting `62 passed`、targeted `171 passed`、full `341 passed`、eval
  `65 passed`；runtime/diff 通过，清理 reviewer import cache 后 package 仅既有 baseline。
- Resolution：REV-15-01/02/03 均有旧实现失败的词位矩阵；相对 artifact 文本完整保留，浅路径
  文件名完整脱敏。未改引号、`/goal*` 或其他 carry nit。

## Review Fix Round 16

- Reviewer：有效 Paseo Fable 5/high Round 16 复审完成；本地复现中文正文与相对路径无空格
  粘连的单跳/多跳过吞，确认 REV-16-01；carry nits 未修改。
- RED：两层保真矩阵新增 `没生成.codestable/design.md`、`后写到了build/output.json` 与
  两跳链式样例；同时增加 `Program Files`、纯 CJK 目录和 `合同.docx` 隐私对照。旧实现聚焦
  命令真实得到 `2 failed`。
- GREEN：spaced continuation 暴露首组件并用共享 CJK→ASCII/`.` 粘连谓词停止延伸；终端
  文件名仅在扩展名有效且后续不是分隔符时接受，保留 `计划.docx` / `合同.文档`。聚焦四函数
  `4 passed`，三条原反例正文与相对 artifact 均完整保留。
- VERIFY：privacy/reporting `62 passed`、targeted `171 passed`、full `341 passed`、eval
  `65 passed`；runtime/diff 通过，清理本轮 import cache 后 package 仅既有根 `cs-onboard/`
  baseline。
- Resolution：REV-16-01 有旧实现下真实失败的单跳/多跳双向回归。混合脚本真实路径组件如
  `项目logs/` 会停止绝对路径延伸，只留下相对尾段而不暴露根路径，作为窄 residual 交 QA；
  未改 Windows 伪盘符、引号、`/goal*`、transcript 死条件或其他 carry nit。
