#!/usr/bin/env python3
"""buildPrompt：把「被测 SKILL.md 快照 + fixture 任务」组装成喂给 harness/model 的 prompt。

这是绕开「cs skill 无法无头执行」的桥接点：被测 skill 以快照文本注入，不读宿主已装版本。
按 fixture.task["kind"] 分派（review / fix / audit），支撑自举扩容。
"""

from __future__ import annotations

from _model import Fixture

_INTRO = (
    "你在扮演一个 CodeStable skill。下面是该 skill 的完整 SKILL.md 指令（权威、需严格遵循）。"
    "请**仅**依据这些指令处理随后的任务，产出该 skill 规定的结构化结果。\n"
)

# 补齐 skill 设计所依赖的 onboard 运行环境，公平测「主路径」而非 bare-input。
# （回应「haiku 拒审是否因缺 cs-onboard 上下文」：inject 后 preflight 满足，模型不应再拒绝）
_CONTEXT_BLOCK = (
    "\n## 已就绪的 CodeStable 上下文（preflight 已满足——请直接执行本轮任务，"
    "不要因缺 attention.md / 来源 spec / git 环境而拒绝或退回 onboard）\n"
    "- `.codestable/attention.md`：本仓已 onboard；报告语言=中文；无特殊命令陷阱或路径约定。\n"
    "- 来源/范围已确认：本轮任务的目标与范围 = 下方给定内容（等价于用户已确认的 spec/范围）。\n"
    "- 环境限制：独立 reviewer / OCR / gate / 外部工具在本评测环境不可用；按 protocol 记录跳过原因即可，不要因此 `blocked` 或退回。\n"
)


def build_prompt(fixture: Fixture, variant_text: str, inject_context: bool = False) -> str:
    kind = (fixture.task or {}).get("kind", "review")
    builder = _BUILDERS.get(kind, build_review_prompt)
    prompt = builder(fixture, variant_text)
    if inject_context:
        marker = "===== SKILL.md 结束 ====="
        idx = prompt.find(marker)
        if idx != -1:
            at = prompt.find("\n", idx) + 1
            prompt = prompt[:at] + _CONTEXT_BLOCK + prompt[at:]
    return prompt


def build_review_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    diff = task.get("diff", "")
    spec = task.get("spec", "")
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待审查改动",
    ]
    if spec:
        parts += ["\n### 来源 spec", spec.strip()]
    parts += [
        "\n### diff / 代码",
        "```diff",
        diff.strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 review 契约输出。**Findings** 一节逐条列出你发现的问题，"
        "每条以 `- [file:line] 简述` 开头，按 severity 分组（blocking/important/nit）。"
        "只要真实存在的问题，不要臆造。",
    ]
    return "\n".join(parts)


def build_fix_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待修复问题",
        task.get("spec", "").strip(),
        "\n### 相关代码",
        "```",
        task.get("diff", "").strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 fix 契约给出根因、修复方案与验证方式。",
    ]
    return "\n".join(parts)


def build_design_prompt(fixture: Fixture, variant_text: str) -> str:
    """design 生成型（如 cs-feat 的 design 阶段）：给需求，要求产出一份 design。

    注意：离线 mock harness 不产 design（无信号）；本 kind 的有效评测需真实 harness。
    """
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 需求",
        task.get("spec", "").strip(),
    ]
    if task.get("context"):
        parts += ["\n### 背景", str(task["context"]).strip()]
    parts += [
        "\n## 输出要求",
        "按该 skill 的 design 契约产出一份 design：明确验收标准、必须处理的边界/异常、范围边界（做什么/不做什么）、"
        "DoD 契约与验证方式。逐条列出你识别到的**必须覆盖的关注点**（`- 关注点：…`），不要遗漏隐含需求。",
    ]
    return "\n".join(parts)


def build_docs_prompt(fixture: Fixture, variant_text: str) -> str:
    """docs 生成型（如 cs-docs 的 tutorial/API reference）：给文档任务，要求产出文档。

    离线 mock 不产文档（无信号）；有效评测需真实 harness。
    """
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 文档任务",
        task.get("spec", "").strip(),
    ]
    if task.get("audience"):
        parts += [f"\n受众：{task['audience']}"]
    if task.get("diff"):   # 被文档化的材料（配置/API/代码/清单）——效度铁律 3
        parts += ["\n## 待文档化的材料（依此写文档，不要臆造）", "```", task["diff"].strip(), "```"]
    parts += [
        "\n## 输出要求",
        "按该 skill 的文档契约产出文档，并逐条列出你**覆盖到的关键要素**（`- 要素：…`）："
        "必要的参数/返回/错误、前置条件、可运行示例、边界与常见坑，不要遗漏。",
    ]
    return "\n".join(parts)


def build_audit_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待审计代码",
        "```",
        task.get("diff", "").strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 audit 契约列出发现，逐条 `- [file:line] 简述`。",
    ]
    return "\n".join(parts)


def build_routing_prompt(fixture: Fixture, variant_text: str) -> str:
    """路由决策型：给仓库状态快照，要求 agent 按 skill 规则选下一步。

    测的是「skill 文本能否让模型做出正确路由决策」——decision fixture 的执行引擎。
    输出强制 JSON，交 routing_decision scorer 机械比对（measured）。
    """
    task = fixture.task or {}
    state = task.get("state") or {}
    intent = task.get("intent") or {}
    state_lines = [f"- {k}: {v}" for k, v in state.items()]
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 当前仓库状态（已从仓库事实恢复，权威）",
        "\n".join(state_lines) if state_lines else "-（无既有产物）",
    ]
    if intent:
        parts += ["\n## 本次调用意图", "\n".join(f"- {k}: {v}" for k, v in intent.items())]
    if task.get("utterance"):
        parts += ["\n## 用户原话", str(task["utterance"]).strip()]
    parts += [
        "\n## 输出要求",
        "按该 skill 的路由规则，决定当前这一步该做什么。**只输出一个 JSON 对象，不要其他任何文本**：",
        '{"result_type": "<RoutedTo|HumanCheckpoint|NeedsHuman|Completed|GoalHandoff|ChildDesignBatch>",'
        ' "target": "<stage 名或 checkpoint reason；Completed/NeedsHuman 可为简述>", "reason": "<一句话依据>"}',
    ]
    return "\n".join(parts)


def build_e2e_prompt(fixture: Fixture, variant_text: str) -> str:
    """e2e 执行型：agent 在真实 seed 仓库工作目录中按 skill 流程处理 issue。

    workdir 是真实 seed 仓库（runner 负责准备），prompt 不内嵌 diff。
    """
    scenario = (fixture.raw or {}).get("scenario") or {}
    issue_report = scenario.get("issue_report", "")
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "你在一个已 onboard 的真实仓库工作目录中（当前目录即仓库根），"
        "按该 skill 的流程处理下面这个 issue，直接修改文件并运行测试验证。",
        "\n## Issue 报告",
        issue_report.strip(),
        "\n## 输出要求",
        "- 修复代码直接落盘到仓库文件（不要只输出 diff）。",
        "- 按 skill 契约生成产物（如 `.codestable/issues/<issue-id>/fix-note.md` 记录根因与修改说明）。",
        "- 运行仓库已有测试（`python3 -m pytest tests -q`）确认回归绿色。",
        "- 最后用一段话总结：改了哪些文件、根因是什么、验证结果如何。",
    ]
    return "\n".join(parts)


_BUILDERS = {
    "review": build_review_prompt,
    "fix": build_fix_prompt,
    "audit": build_audit_prompt,
    "design": build_design_prompt,
    "docs": build_docs_prompt,
    "routing": build_routing_prompt,
    "e2e": build_e2e_prompt,
}
