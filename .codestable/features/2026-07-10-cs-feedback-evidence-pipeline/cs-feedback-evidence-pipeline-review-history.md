---
doc_type: feature-review-history
feature: 2026-07-10-cs-feedback-evidence-pipeline
updated: 2026-07-11
---

# CS Feedback Evidence Pipeline Review History

本文件保留已完成轮次的压缩 resolution ledger；当前结论以
`cs-feedback-evidence-pipeline-review.md` 为准。

## Round 1

- Verdict: changes-requested。
- 解决：重采集保留用户 triage、多行 JSON 与单段路径脱敏、assessment readiness、fixture id
  containment、malformed triage、regression class gate，以及测试的 stale mtime/长序号问题。

## Round 2

- Verdict: changes-requested。
- 解决：nested/超长 JSON fail-closed、incident fingerprint、pending `--accept-incident` 出口、
  `ImportFrom.module` AST 守护、promotion quoted-key secret。

## Round 3

- Verdict: passed；reviewer `subagent+ocr`。
- QA focus：真实 provider、problem-not-last-turn、reporter 误报、短 secret 与大历史性能。

## Round 4

- Verdict: changes-requested。
- 解决：`Authorization: Basic/Bearer` credential 穿透；public 与 reporter 共用 auth matcher。

## Round 5

- Verdict: changes-requested。
- 解决：ENV 替换顺序、任意 Authorization scheme header、curl `-u/--user` userinfo，及
  repo-local promotion credential matcher 对称性。
- Round 5 DoD：feedback 70、targeted 106、full 276、eval 65 passed。

## Round 6

- Verdict: changes-requested。
- 解决：特殊字符与 quoted secret 值、confirmed issue title 隐私扫描、canonical converter
  空 incident identity 拒绝；修复后 targeted 121、full 291、eval 65 passed。

## Round 7

- Verdict: changes-requested。
- 解决：angle/backtick/full-width separator、未闭合 quote、shell escaped bare value，及
  exact sanitized placeholder exemption；修复后 targeted 131、full 301、eval 65 passed。

## Round 8

- Fable 异常提前结束后，implementation driver 错误使用 Codex fallback；用户未授权该降级，
  因此本轮不计入有效 review gate，findings 仅作本地工程输入。
- 解决：连续 shell segment/expansion、promotion key/schema、correlation 连通分量、collector
  路径与 staging、triage source/ref 校验、Git root 恢复；修复后 targeted 148、full 318、
  eval 65 passed。

## Round 9

- Fable 与 OCR 均返回 503；implementation driver 再次错误使用 Codex fallback，用户未授权，
  因此本轮不计入有效 review gate。
- 其本地 findings 已用于 review-fix：multiline privacy、canonical evidence binding、promotion
  schema、atomic persistence 与 private gitignore；修复后 targeted 166、full 336、eval 65 passed。

## Round 10

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：环境上下文只接受 metadata 来源；无 user anchor / 非唯一 primary incident / triage
  未就绪时不生成 public events/incidents。修复后 targeted 167、full 337、eval 65 passed。

## Round 11

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：共享路径 matcher 覆盖仍含目录分隔符或带扩展名的空格尾部，reporter 继续复用同一规则；
  修复后 targeted 169、full 339、eval 65 passed。

## Round 12

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：含空格文件名支持单双引号、backtick、ASCII/CJK 句末标点及标点后闭合符；修复后
  targeted 169、full 339、eval 65 passed。Round 13 证明中文标点后连写正文仍需继续收敛。

## Round 13

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：CJK 标点自身作为终止边界，扩展名支持长值与 Unicode；targeted 169、full 339、
  eval 65 passed。Round 14 证明枚举终止符与无界 suffix 仍需改为结构化扫描。

## Round 14

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：改为绝对路径 core + 有界 span scanner，新增泄漏/保真双向矩阵；targeted 171、
  full 341、eval 65 passed。Round 15 继续定位 continuation 与词位谓词缺口。

## Round 15

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：spaced continuation 收紧为单步、spaced filename 拒绝纯数字/长 CJK 句子扩展名、
  浅路径双词文件名完整脱敏，并阻止相对路径内部斜杠重启；targeted 171、full 341、
  eval 65 passed。Round 16 继续定位中文无空格粘连边界。

## Round 16

- Verdict: changes-requested；有效 reviewer 为 Paseo Fable 5 / high。
- 解决：continuation 与终端文件名共享 CJK→ASCII/`.` 粘连谓词，补单跳/多跳保真矩阵及
  `Program Files`、纯 CJK 目录、Unicode 文件名隐私对照；targeted 171、full 341、
  eval 65 passed。Round 17 判定该可判定类别已闭合。

各轮完整审查输出亦保留在实现报告、goal ledger 与对应独立 reviewer transcript 中。
