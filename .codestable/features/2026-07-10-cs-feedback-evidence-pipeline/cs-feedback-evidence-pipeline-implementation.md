---
doc_type: feature-implementation
feature: 2026-07-10-cs-feedback-evidence-pipeline
status: ready-for-review
created: 2026-07-10
baseline_ref: 30fecaae5e747dbad1f0e599d592d7c04cc7f0c4
---

# CS Feedback Evidence Pipeline 实现报告

## 结果

实现已完成并通过本地 implementation gates，当前等待固定配置的独立代码评审。checklist
Step 1-6 已 done。Step 6 的 `done` 表示 implementation 验证与 review 输入已就绪；独立 review
仍由紧随其后的 review stage 执行并单独落盘，避免 `cs-code-review` 要求 steps 全 done 与 Step 6
文案包含 review 的生命周期循环。

## Step 证据

### Step 1：行为等价拆分

- TDD exception：纯职责搬迁不改变外部行为，使用拆分前后兼容测试代替 RED。
- 基线：拆分前 `tests/test_cs_feedback.py` 为 `9 passed`。
- VERIFY：拆分后原 9 个 capture/reporting 行为分文件仍全绿；collector 降为 186 行编排层。
- 交付：`feedback_models.py`、`feedback_privacy.py`、`feedback_transcripts.py`、
  `feedback_incidents.py`、`feedback_repo_context.py`、`feedback_triage.py`；reporting/candidate/
  promotion tests 分责。

### Step 2：证据编排

- RED：扩展契约测试首次运行 `18 failed, 20 passed`；失败覆盖弱 cwd 误选、无 anchor 丢
  incident、provider/adjacency 歧义、user-turn 未分离、Claude tool block 未规范化与 repo
  context 缺失。
- GREEN：current 只接受 cwd 精确唯一；ambiguity 走 metadata-only；JSONL/JSON 使用单次
  snapshot；trigger cutoff、跨 provider 规范化和 file-level repo enrich 已实现。
- VERIFY：snapshot EOF、单 transcript 单次 snapshot、Codex/Claude JSON/JSONL 同构、两个
  user-turn incident 分离及 v1 compatibility tests 全绿。

### Step 3：分诊与隐私投影

- RED：同一轮首次失败包含 triage 混入 evidence、质量门信任缺 ref 字段、public body
  缺二次拒绝和手工字段被覆盖风险。
- GREEN：`triage.json` 独立持久化；Assessment 带 source/confidence/evidence refs；
  `triage_ready` 与 `regression_ready` 机械重算；重复采集保留用户 reproduction/privacy 补充。
- VERIFY：secret、绝对路径、remote、env、raw tool JSON、代码块负向用例通过；public event
  精确 8 字段，public incident 精确 7 字段；reporter 未确认时不调用 `gh`。

### Step 4：candidate 与 promotion

- RED：旧实现会接受非 canonical triage、把 assessment 回填 oracle，并在缺 scorer、mock
  judge、target/profile 错配和通用绝对路径时 fail open。
- GREEN：shipped converter 只写同目录 candidate；repo-local promotion 校验 config、profile、
  target、input、privacy、真实 scorer/judge/harness、buildPrompt 与 commit-safe 字段。
- VERIFY：有效 findings/routing 正向 promotion、缺 config 与 15 类负向 gate、candidate 到
  promotion 的 JSON-only 串联均通过；旧 `--failure --experiment` 非零且无 fixture 目录。

### Step 5：入口与文档

- TDD exception：协议、模板、ADR 和公开说明属于声明投影，使用 static contract、runtime
  copy `cmp`、Markdown 行数和 runtime sync 代替行为 RED。
- 更新：cs-feedback current 默认、incident/triage/quality、candidate-only、确认上传；
  shared/execution/system-overview 模板与 runtime copy；ADR-003；中英文 README/WORKFLOW/
  catalog；`rt-c17` feedback 路由 fixture。
- VERIFY：目标文档均少于 300 行；README.en 从 363 行收敛到 291 行；三组 template/runtime
  copy 逐字一致。

### Step 6：验证闭环

- unit/contract/decision fixtures 已覆盖 provider 同构、隐私边界、readiness、candidate/promotion
  fail-closed 与 feedback 路由。
- fresh DoD runner：CMD-001 `91 passed`、CMD-002 `261 passed`、CMD-003 `65 passed`；runtime
  sync 与 `git diff --check` 通过。
- package gate 仅返回 design 已记录的根 `cs-onboard/` legacy baseline，无新增 finding。
- 独立代码评审不伪装成 implementation 证据；由 review stage 使用固定 Fable 5 high 配置执行并
  回填 review report。

## 验证结果

| Gate | 结果 |
|---|---|
| `pytest tests/test_cs_feedback*.py tests/test_cs_skill_bootstrap.py tests/test_skill_entry_simplification.py` | 148 passed |
| `pytest tests` | 318 passed |
| eval/convergence/release/bootstrap/selfref pytest | 65 passed |
| runtime sync `--check --json` | status=ok |
| `git diff --check` | passed |
| plugin package | 仅既有根 `cs-onboard/` legacy finding；无新增 finding |

所有 pytest 均使用 `PYTHONDONTWRITEBYTECODE=1`。package 诊断过程中生成的一次本地 pyc 已清理，
复测后无 `__pycache__`。

## 兼容与范围

- collector 直接调用仍保留 `since_days=3` v1 默认；skill 默认 current 且不传 since-days。
- `matched_events` 与 public v1 events 继续保留，failure_type 值域不扩张。
- reporter 网络/代理策略未重构，只增加确认和隐私边界。
- shipped skill 不 import repo-local eval 工具；正式 promotion 只存在维护仓库。
- 没有后台 telemetry、自动上传、默认全历史扫描或自动修改目标 skill。

## Review Fix Round 1

- triage 的 incident id 漂移或定位失败不再覆盖已有用户补充；保留 reproduction/privacy，清空
  当前选择并写 previous/pending id，quality 强制未就绪，待用户重新选择。
- public redaction 覆盖 pretty-printed JSON quoted secret 与 `/repo` 这类单段绝对路径；reporter
  网络边界同步拒绝单段路径和 env name，同时保留 `/goal` 命令文本。
- Assessment 缺 source/evidence refs 或 inferred confidence 时，`triage_ready` 与
  `regression_ready` 均 fail closed，不再出现 ready 与 missing_fields 同时成立。
- converter 对 canonical nested object 做类型验证；promotion 增 safe fixture id、目标目录
  containment 与 `fixture_classes` compatibility gate。
- 配套修正显式 stale mtime 与超过 9999 records 的 numeric timeline ordering。
- VERIFY：feedback 专项 `62 passed`，targeted `98 passed`，全量 `268 passed`，eval 专门 gate
  `65 passed`。

## Review Fix Round 2

- RED：round 2 聚焦命令得到 `5 failed, 8 passed`，分别复现 brace-in-value/超长 JSON 穿透、
  pending incident 无采纳出口、same-id 语义漂移、reporter raw-json 漏检与 quoted-key secret
  promotion fail-open。
- GREEN：public JSON 清理改为无长度上限并迭代到不动点；triage 新增 local-private incident
  fingerprint，same-id/different-fingerprint 也进入 unresolved 状态；collector 新增
  `--accept-incident`，严格核对 pending/current fingerprint，保留 reproduction、归档旧
  assessment/privacy，并把 active privacy review 重置为 pending。
- 契约加固：reporter 复用同一 raw-json detector；promotion secret matcher 覆盖 quoted JSON
  key；converter AST 守护分别读取 `Import` alias 与 `ImportFrom.module`；SKILL/report template
  明确人工采纳协议。
- VERIFY：聚焦 GREEN `14 passed`，feedback 专项 `66 passed`，targeted `102 passed`，全量
  `272 passed`，eval 专门 gate `65 passed`；runtime sync 与 diff check 通过，package 仅既有
  根 `cs-onboard/` legacy baseline。

## QA Fix Round 1

- QA 在真实 provider smoke 后按 review focus 复现 `password=hunter2` 与
  `authorization=abcdefg`：public redaction 原样放行且 confirmed-upload scanner 无 reason，
  因违反场景 8 核心隐私契约记为 `QA-PRIV-001`，未降级成 residual-risk。
- RED：新增 public/reporter 两条短 secret 负向测试，首次运行 `2 failed`。
- GREEN：仅把两条链路共用的 `feedback_privacy.SECRET_PATTERN` 最小长度从 8 对齐到 6；
  promotion 侧已为 6，无第二套修改。
- VERIFY：聚焦 `2 passed`、feedback 专项 `68 passed`、targeted `104 passed`、全量
  `274 passed`、eval `65 passed`；runtime sync/diff check 通过，package 仅既有 baseline。

## Review Fix Round 4

- RED：Fable/local 实跑确认 `Authorization: Basic <credential>` 完全穿透，Bearer 仅擦除
  scheme 而保留 token；新增 public/reporter Basic、Bearer、大小写、Proxy-Authorization、
  standalone 与 sanitized-output 二次扫描测试，首次 `2 failed`。
- GREEN：新增 shared `AUTH_SCHEME_PATTERN`，在普通 key=value redaction 前整段替换 credential；
  reporter 的 `secret` reason 同时复用 assignment/auth 两个 matcher。
- VERIFY：聚焦 `2 passed`、curl/Basic/Bearer 对抗 smoke 无 credential，feedback `70 passed`、
  targeted `106 passed`、full `276 passed`、eval `65 passed`；其余 gate 通过且 package baseline
  未扩张。

## Review Fix Round 5

- RED：新增 ENV 风格 Authorization、任意 auth scheme header、curl `-u/--user` 与 promotion
  commit-safe 负向用例；聚焦命令真实得到 `7 failed, 9 passed`。
- GREEN：新增 Authorization header、standalone Basic/Bearer、user-option 三类 credential
  matcher；public redaction 在空白折叠和 ENV/PATH/URL 占位前清理 credential，reporter 复用
  shared matcher 集合，repo-local promotion 按独立安装边界复制同构规则。
- VERIFY：聚焦 `16 passed`，feedback `77 passed`、targeted `113 passed`、full `283 passed`、
  eval `65 passed`；scope/evidence/runtime/diff gates 通过，package 仅既有 legacy baseline。
- Resolution：R5-001 的 matcher ordering、R5-002 的 scheme 白名单缺口、R5-003 的 curl
  userinfo 和 R5-004 的 promotion 边界不对称均有旧实现下会失败的回归测试锁定。

## Review Fix Round 6

- RED：特殊字符/quoted secret、confirmed title 与空 incident identity 聚焦命令真实得到
  `6 failed, 16 passed`；其中 promotion 两个新增值形态会实际写入 fixture。
- GREEN：shared/promotion matcher 完整识别 quoted value 与特殊字符 bare token；confirmed
  title 复用 private-reason scanner；canonical converter 拒绝非字符串或空白 `incident_id`。
- VERIFY：聚焦 `22 passed`，值形态 smoke `6 passed` 且 sanitized 不自锁；feedback
  `85 passed`、targeted `121 passed`、full `291 passed`、eval `65 passed`。
- Resolution：R6-B1 public/reporter/promotion 三层盲区、R6-I1 title 旁路、R6-I2 空 incident
  candidate 均由旧实现下会失败的行为回归锁定；package 仍只有既有 legacy baseline。

## Review Fix Round 7

- RED：angle/backtick/full-width separator、未闭合 quote、shell escape 与 placeholder 自锁
  聚焦命令真实得到 `9 failed, 21 passed`；失败 promotion case 会实际写入 fixture。
- GREEN：secret value parser 改为 double/single/backtick quoted 分支与 escaped bare 分支，
  exact exempt `<redacted>`，并支持 `：/＝`；shared/promotion 两份规则保持同构。
- VERIFY：聚焦 `30 passed`，feedback `95 passed`、targeted `131 passed`、full `301 passed`、
  eval `65 passed`；sanitized placeholders 经 reporter 二次扫描保持无 reason。
- Resolution：R7-B1 的值字符集、自锁张力、本地化 separator 与未闭合 value 终止规则均由
  旧实现下会失败的三层回归锁定；carry nits 未借机修改。

## Review Fix Round 8

- Reviewer：Fable agent 异常提前结束；implementation driver 随后错误使用 Codex fallback。
  用户未授权该降级，因此 Round 8 不计入有效 review gate；其 findings 仅作本地工程输入。
- RED：六项 Round 8 finding 聚焦命令真实得到 `16 failed, 26 passed`；其中 shell segment、
  unsafe task key 与 correlation bridge 均复现 reviewer 反例。补充 shell expansion 对抗再得
  `3 failed, 31 passed`；targeted 首轮另捕获代码 fence ordering 回归 `1 failed, 147 passed`。
- GREEN：secret assignment 改为连续 bare/quoted/backtick/escape parser，支持 ANSI-C quote 与
  command expansion fail-closed，同时保留 exact placeholder 和 code-fence 边界；promotion
  扫描 dict key/value、env/private marker，并按 profile 白名单 task keys。
- 状态与持久化：correlation 窗口按连通分量全量合并；collector 拒绝损坏 triage 与输出路径
  碰撞，三份输出先 staging 再原子 replace；triage 以 `observation_ids` 验证 source/ref；repo
  context 先解析 Git top-level。
- VERIFY：聚焦 `42 passed`，补充 shell `34 passed`，feedback `110 passed`，targeted
  `148 passed`，full `318 passed`，eval `65 passed`；runtime sync/diff check 通过，package
  仍仅既有根 `cs-onboard/` legacy baseline。
- Resolution：R8-B1/B2/B3 与 R8-I1/I2/I3 均有当前旧实现下真实失败的行为回归；Round 8 nits
  未借机修改。

## Review Fix Round 9

- Reviewer：Fable 与 OCR 均返回 `503 No available accounts`；implementation driver 再次错误
  使用 Codex fallback。用户未授权该降级，因此 Round 9 不计入有效 review gate；其 findings
  仅作本地工程输入。
- Privacy RED：跨物理换行 quote/ANSI-C/expansion、collector 泄漏与未闭合 fence 聚焦得到
  `6 failed, 35 passed`；GREEN 后同组 `41 passed`，privacy/reporting/promotion 三文件
  `107 passed`。shared/promotion parser 现在平衡扫描 nested `$()`/`${}`、quote/escape/CRLF，
  未闭合结构 fail-closed 到 EOF；未闭合 fence 整段替换。
- Integrity/schema RED：伪造 incident/fingerprint/observation refs 与 object/list/string-bool
  candidate 得到 `2 failed, 3 passed`；GREEN 后 `5 passed`、candidate+promotion `66 passed`。
  converter 以 sibling `evidence.json` 只做 canonical integrity 校验，candidate 内容仍只来自
  triage；promotion 在 validator/buildPrompt 前验证精确值类型，非法 JSON 统一 rc=2/no-write。
- Persistence/privacy lifecycle RED：fsync temp 泄漏、replace mixed generation 与 Git ignore
  得到 `4 failed, 1 passed`；GREEN 后 `5 passed`，并补 write/flush 注入回归。writer 创建后立即
  登记 temp、为旧 generation 建 rollback snapshot；onboard template/runtime 默认忽略 report、
  evidence、triage、candidate，public preview 与 GitHub body 仍可跟踪。
- VERIFY：feedback targeted `166 passed`、full `336 passed`、eval `65 passed`；runtime sync、
  scope gate、evidence pack、template/runtime cmp 与 `git diff --check` 通过。package gate 仍仅
  既有根 `cs-onboard/` legacy baseline，无新增 finding；无 bytecode/cache artifact。
- Resolution：R9-B1/B2/B3/B4 与 R9-I1/I2 均由旧实现下真实失败的行为回归锁定；carry nit
  未借机修改。

## Review Fix Round 10

- Reviewer：有效 Paseo Fable 5/high Round 10 复审完成；本地核验后保留 REV-10-01/02 两个
  important，驳回 promotion temp 的不可复现碰撞/逃逸论据，REV-10-03/04 nits 未借机修改。
- RED：新增环境 metadata 来源资格与无 user anchor public eligibility 两条行为断言，聚焦命令
  真实得到 `2 failed`；分别复现 tool payload 的 model/version 污染和未就绪 public event。
- GREEN：environment context 只接受 session/meta/turn-context 或无正文顶层 metadata，并支持
  Codex `cli_version`；collector 只在唯一 primary incident 且 triage-ready 时构建 public
  events/incidents，local-private evidence/triage 仍保留。
- VERIFY：聚焦 `2 passed`、feedback `131 passed`、targeted `167 passed`、full `337 passed`、
  eval `65 passed`；runtime sync 与 `git diff --check` 通过，package 仍仅既有根 `cs-onboard/`
  legacy baseline。
- Resolution：REV-10-01/02 均有旧实现下真实失败的回归测试锁定；旧 public redaction fixtures
  补为 tool failure + 明确 user correction，未放宽 public eligibility gate。

## Review Fix Round 11

- Reviewer：有效 Paseo Fable 5/high Round 11 复审完成；本地用 Windows、POSIX 和
  `Application Support` 三个反例确认 REV-11-01，REV-11-02/03 nits 未借机修改。
- RED：在 public redaction 与 reporter 两层新增含空格绝对路径端到端断言，聚焦命令真实得到
  `2 failed`；旧实现分别残留 `plan.docx`、`contracts` 和 `Support`，且 reporter 放行脱敏结果。
- GREEN：共享 `PATH_PATTERN` 只扩展两类可判定空格尾部——仍含目录分隔符或带扩展名文件；
  reporter 继续直接复用同一 matcher，无复制规则。新增用例 `2 passed`。
- VERIFY：evidence-pipeline + reporting `60 passed`；targeted `169 passed`、full `339 passed`、
  eval `65 passed`；runtime sync、scope gate、evidence pack 与 `git diff --check` 通过，package
  仍仅既有根 `cs-onboard/` baseline。
- Resolution：REV-11-01 有旧实现下真实失败的两层回归锁定；保留 `/goal` 例外，未改 promotion
  commit-safe 或两个非阻塞 nit。

## Review Fix Round 12

- Reviewer：有效 Paseo Fable 5/high Round 12 复审完成；本地复现引号包裹的 POSIX/Windows
  路径和句末句点三例，确认 REV-12-01；三个 nit 与一条 suggestion 未借机修改。
- RED：扩展两层空格路径参数矩阵，覆盖单双引号、backtick、ASCII/CJK 句末标点及标点后闭合
  引号；聚焦命令真实得到 `2 failed`，旧实现残留 `merger notes.txt` / `plan.docx` / `report.docx`。
- GREEN：新增共享 `PATH_FILE_BOUNDARY_PATTERN`；直接闭合符可终止，句末标点仅在后续为空白、
  闭合符或行尾时终止。reporter 继续复用 `PATH_PATTERN`，无第二份规则；新增矩阵 `2 passed`。
- VERIFY：evidence-pipeline + reporting `60 passed`；targeted `169 passed`、full `339 passed`、
  eval `65 passed`；runtime sync、scope gate、evidence pack 与 `git diff --check` 通过，package
  仍仅既有根 `cs-onboard/` baseline。
- Resolution：REV-12-01 的真实 transcript 定界符上下文由旧实现下失败的两层回归锁定；未改
  promotion commit-safe，也未把不可判定的无扩展名尾部目录纳入本轮范围。

## Review Fix Round 13

- Reviewer：有效 Paseo Fable 5/high Round 13 复审完成；本地复现 4 个中文连写标点反例，
  并确认长扩展名与 Unicode 扩展名残留；carry nits/suggestions 未修改。
- RED：两层参数矩阵新增 `，。；）` 后直接连写正文、中文弯引号、`.presentation` 与 `.文档`；
  聚焦命令真实得到 `2 failed`，脱敏产物均被 reporter 放行。
- GREEN：CJK 标点/全角闭合符本身改为终止边界；扩展名改用无固定长度的 Unicode
  `word/+/-` 集合，删除 `{1,10}` 阈值。reporter 继续复用 shared matcher；矩阵 `2 passed`。
- VERIFY：privacy/reporting `60 passed`、targeted `169 passed`、full `339 passed`、eval
  `65 passed`；runtime、scope、evidence、diff 通过，package 仅既有根 `cs-onboard/` baseline。
- Resolution：REV-13-01/02 均有旧实现下真实失败的两层回归；未扩大到无扩展名尾部目录或
  promotion/carry nit。

## Review Fix Continuation

Round 14 起的修复证据见 `cs-feedback-evidence-pipeline-implementation-review-fixes.md`。

## 清洁度

- 无调试输出、临时 TODO/FIXME/XXX、注释掉代码、cache artifact 或方案外业务代码修改。
- `print` 仅用于 shipped CLI 的结构化结果/错误；TODO/TBD 仅出现在 placeholder 拒绝规则与
  对应负向测试。
- `.codestable/attention.md` 与 feature 目录为本 goal 既有资产，未回滚用户改动。

## 下一步

按 goal protocol 只使用 Paseo Fable 5/high 只读审查本轮 diff；Fable 因额度/provider 异常
无法完成时必须 handoff，不得换模型。
