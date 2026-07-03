# Step 内 TDD 策略

本文件是 `cs-feat` implementation 阶段的内嵌实现策略。只约束当前 step 的测试-实现微循环，不切换到全局 `tdd` skill，也不接管 CodeStable 的 gate、checklist、evidence、review / QA 流程。

## 什么时候用

当前 step 改变代码行为，并且行为能用自动化测试可靠观察时，默认必须使用 TDD micro-loop。不能先把实现写完再补测试。

允许例外：

- 纯搬迁 / 纯配置 / 纯文档，没有行为变化。
- 行为只能靠类型系统、浏览器手工流程、外部环境或人工检查观察。
- 自动化测试成本明显高于本 step 风险。

例外必须在 step evidence 写 `TDD exception: {原因 + 替代证据}`。不要为了 TDD 改变已批准 design 的范围。

## 微循环

每次只处理一个可观察行为：

1. RED：写一个测试，测试必须先真实失败。
2. GREEN：只写通过当前测试所需的最小实现。
3. VERIFY：重跑当前测试；必要时跑本 step 的相关验证。
4. REFACTOR：只能在 GREEN 后做，且每个重构小步后重跑验证。

循环结束后，把测试、命令和结果写回当前 step 的 evidence block。

## 需求迭代边界

实现中出现用户新增点或新边界时，先分类：

- 仍是 approved design 内某个验收行为的细化：追加一个 TDD micro-case，重新 RED / GREEN。
- 改变 public behavior、接口、错误语义、feature 范围或公开契约：停下回 `cs-feat` design 阶段 / 用户确认。
- review-fix / qa-fix：只为对应 blocking / failed item 写最小 RED 测试；修完按协议重跑 review / QA。

不要用 TDD 当现场扩 scope 的许可证。测试先红只能证明当前行为缺口存在，不能替用户批准新需求。

## 硬约束

- 一个行为一个测试；不先批量写完整测试再批量实现。
- 测试描述行为，不描述内部实现步骤。
- 测试走 public API；不要测 private 方法、内部 helper、内部调用次数或调用顺序。
- 不预写未来行为；当前测试没要求的代码不写。
- RED 失败要和目标行为有关；如果因为环境、fixture 或语法错误失败，先修测试基线。
- GREEN 后仍要满足当前 step 的 exit_signal；测试通过不等于 step 完成。

## 好测试判据

优先写 integration-style 测试：通过真实入口执行真实代码路径，断言用户 / 调用者可观察到的结果。

好测试应满足：

- 名字描述 WHAT，而不是 HOW。
- 每个测试只验证一个逻辑行为。
- 内部重构不改变行为时，测试仍应通过。
- 持久化、状态变化或副作用优先通过系统 public API 观察，不绕过接口直接查内部表 / 内部对象。

坏味道：

- mock 本模块内部协作者。
- 断言内部函数被调用几次、按什么顺序调用。
- 测试私有方法或为了测试暴露私有结构。
- 行为没坏，只是重命名 / 拆函数 / 移文件就导致测试失败。

## Mock 边界

只 mock 系统边界：外部 API、第三方服务、时间 / 随机性、文件系统；数据库优先使用测试数据库，确实成本过高时才 mock。

不要 mock 自己控制的 class / module / 内部协作者。为了方便 mock 而改内部设计，通常说明测试写到了实现细节。

如果当前 step 新增外部边界，优先把边界设计成可注入的窄接口：

- 外部 client 由参数 / 构造器传入，不在业务函数内部硬创建。
- 相比通用 fetcher，优先提供具体 SDK-style 方法，例如 `getUser`、`createOrder`。
- mock setup 里不写复杂条件逻辑；每个 mock 返回一种具体 shape。

这些设计只能服务当前 step 的已批准行为，不能借 TDD 扩大架构范围。

## GREEN 后重构

RED 时不重构。所有当前测试 GREEN 后，才检查这些候选：

- 重复逻辑：抽函数 / 类型。
- 长方法：拆 private helper，但测试仍只覆盖 public API。
- shallow module：合并或深化模块，让接口小、实现深。
- feature envy：把逻辑移到数据或领域对象所在处。
- primitive obsession：在确有行为约束时引入 value object。
- 新代码暴露的既有问题：若超出本 feature 范围，按 `cs-feat` implementation 阶段的"顺手发现"记录，不顺手修。

## 证据格式

在 step 证据里补一段：

```markdown
TDD 证据：
- Step: {step id}
- 行为：{一句话描述}
- RED：{测试名 / 命令 / 失败摘要，确认失败原因是目标行为未实现}
- GREEN：{最小实现位置 + 命令结果}
- VERIFY：{当前测试 / step 验证命令结果}
- REFACTOR：{无 / 做了什么 + 重跑结果}
- 需求迭代：{无 / 用户新增点 / 是否仍在 approved design 内}
```
