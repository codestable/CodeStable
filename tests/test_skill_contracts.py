"""CodeStable skills 的直接语义守卫与 routing fixture 回归。"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"
# 工具 skill（authoring/eval，不随插件交付）也必须使用标准 frontmatter。
LOCAL_SKILLS = ROOT / ".claude/skills"

TASK_SKILLS = ("cs-feat", "cs-issue", "cs-refactor", "cs-epic")
ORDINARY_TASK_SKILLS = ("cs-feat", "cs-issue", "cs-refactor")
LEGACY_KNOWLEDGE_DIRS = {
    ".codestable/roadmap/",
    ".codestable/features/",
    ".codestable/issues/",
    ".codestable/refactors/",
    ".codestable/goals/",
    ".codestable/compound/",
    ".codestable/audits/",
    ".codestable/brainstorms/",
    ".codestable/feedback/",
}

LESSON_READ_REPAIR_CONTRACT = {
    "经验命中：{path}（{status}）；核验：{fact}；影响：{plan_or_check}",
    "旧 lesson 缺 `status` 按 `observed` 读取",
    "`retired` 不应用",
    "`observed` / `validated` 先核实再用",
    "只做一次有界、最低成本的定向核实",
    "不得仅为核实 lesson 运行大范围测试或反复复现",
    "仍不足时跳过该 lesson，不阻塞正常任务",
    "只是相关但没有改变行为时不制造复用证据",
    "明确排除一个具体且合理的错误路径",
    "当前事实明确反证时立即停止应用",
    "证据不足时不猜",
}

CRYSTALLIZATION_SIGNAL_CONTRACT = {
    "任务内只在内存保留最多 3 条候选",
    "不暂停或询问",
    "owner 纠正实际改变方案/代码/术语/验证",
    "可复现证据推翻根因",
    "同一路径失败两次后更换假设",
    "blocking/important finding 暴露未编码不变量",
    "新 red -> green 捕获可复发失败",
    "lesson 真实改变本次行为或被反证",
    "重复 workaround",
    "方法显著降低重试、成本或风险",
    "可追溯证据",
    "能写成未来动作",
    "本次精确 diff 之外",
    "没有现成 canonical owner",
    "网络波动、拼写、泛化口号、活动记录",
    "已被机械 owner 完整覆盖",
}

NARROW_LESSON_MAINTENANCE_CONTRACT = {
    "仅对已有且有效命中的 lesson",
    "`observed -> validated`",
    "独立后续任务确实采用并验证成功",
    "只补一次代表性证据",
    "必须记录 lesson 实际改变的计划或验证",
    "本次通过的验收证据",
    "`observed|validated -> retired`",
    "当前仓库事实直接反证",
    "发现已有 canonical owner",
    "只写原因与替代/反证指针",
    "不新建事实",
    "不改规则",
    "不扩 scope",
    "不新增 gate",
    "稳定 validated 命中不写文件",
    "需要改写结论或证据不足时只给候选",
    "新结论不得通过复活 retired 条目",
    "最终报告列出文件变化",
}

THIN_SKILL_SAFETY_INVARIANTS = {
    "cs": (
        "同轮直转",
        "只推荐入口",
        "导览与推荐本身不写任何文件",
        "讨论只存在于当前会话",
        "不创建 `.codestable/work/discussion-*`",
    ),
    "cs-review": (
        "只读",
        "叶子执行器",
        "禁止创建、委派或唤醒任何子 agent",
        "不得再次调用 `cs-review`",
        "不保存复审轮次",
        "blocking 未解决",
    ),
    "cs-code-review": (
        "兼容别名",
        "canonical entry `cs-review`",
        "不得读取 sibling skill 文件",
    ),
    "cs-epic": (
        "拆解方案必须经用户确认",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
        "不代替用户做整体验收",
    ),
    "cs-feat": (
        "不得代替用户确认设计",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
        "与声明相称的可核验证据",
    ),
    "cs-issue": (
        "能明确变红的验证",
        "变红的验证必须变绿",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
    ),
    "cs-keep": ("没有可追溯证据不写", "`.codestable/compound/` 是只读历史知识源"),
    "cs-onboard": ("存量文件一律不动", "不复制"),
    "cs-refactor": (
        "行为等价",
        "先有能自证等价的验证",
        "由当前主流程创建一个 fresh reviewer",
        "本轮失败且不计轮次",
        "不得盲目重发",
    ),
}

THIN_SKILL_FORBIDDEN_TEXT = {
    "cs": ("L0-L4",),
    "cs-review": (
        "git push",
        "read all references",
        "用独立 subagent reviewer",
        "派发 reviewer 时",
        "探测全部已配置的审查 agent/model",
        "累计最多 3 轮",
    ),
    "cs-code-review": ("按 `cs-review` 的 SKILL.md 执行",),
    "cs-epic": ("ConfirmGoalCommitAuthorization", "git push", "read all references"),
    "cs-feat": ("git push", "read all references"),
    "cs-issue": ("git push", "read all references"),
    "cs-refactor": ("git push", "read all references"),
}


def _read_skill(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, frontmatter, body = text.split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def _contains_contract(text: str, anchor: str) -> bool:
    return "".join(anchor.split()) in "".join(text.split())


def test_active_skills_do_not_use_legacy_frontmatter_contracts() -> None:
    for root in (SKILLS, LOCAL_SKILLS):
        for path in sorted(root.glob("*/SKILL.md")):
            frontmatter, _ = _read_skill(path)
            assert "contracts" not in frontmatter, path


def test_thin_skills_keep_explicit_safety_invariants() -> None:
    active_skills = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert set(THIN_SKILL_SAFETY_INVARIANTS) == active_skills

    for skill_name, invariants in THIN_SKILL_SAFETY_INVARIANTS.items():
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for invariant in invariants:
            assert invariant in body, f"{skill_name}: missing {invariant!r}"

    for skill_name, forbidden_texts in THIN_SKILL_FORBIDDEN_TEXT.items():
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for forbidden in forbidden_texts:
            assert forbidden not in body, f"{skill_name}: forbidden {forbidden!r}"

    review_openai = yaml.safe_load(
        (SKILLS / "cs-review/agents/openai.yaml").read_text(encoding="utf-8")
    )
    review_frontmatter, _ = _read_skill(SKILLS / "cs-review/SKILL.md")
    review_prompt = review_openai["interface"]["default_prompt"]
    assert str(review_frontmatter["description"]).startswith("只读审查叶子执行器")
    assert "$cs-review" in review_prompt
    assert "不创建任何子 agent" in review_prompt
    assert "独立" not in review_openai["interface"]["short_description"]
    assert "独立" not in review_prompt
    assert "派发独立 subagent reviewer" not in review_prompt


def test_cs_discusses_in_session_then_hands_off_same_turn() -> None:
    _, cs = _read_skill(SKILLS / "cs/SKILL.md")
    for anchor in (
        "用户显式要求先讨论",
        "默认优先级最高",
        "产品决策会实质改变建档或改代码路径",
        "讨论只存在于当前会话",
        "仓库可核实的事实由 agent 自行调查",
        "一次只问一个真正需要 owner 决定的问题",
        "目标入口、原始诉求、目标或期望行为、范围、非目标、验收口径",
        "已核实仓库事实及来源",
        "owner 已确认的术语与决策",
        "已有执行授权时同轮移交",
        "不再询问“是否继续”",
        "讨论过程本身不产生授权",
        "不创建 `.codestable/work/discussion-*`",
        "未收敛讨论不跨会话恢复",
        "三个已确认出口",
        "不附带 handoff 的不重复确认契约",
        "原始问答、未决讨论和候选分支不落盘",
        "canonical 术语归宿",
        "难逆转、缺少上下文会令人意外且源于真实取舍",
        "永久 Epic 文档",
        "`attention.md`",
        "`lessons/`",
    ):
        assert anchor in cs

    work = ROOT / ".codestable/work"
    assert not any(path.name.startswith("discussion-") for path in work.glob("*.md"))
    assert not (SKILLS / "cs-align").exists()


def test_confirmed_cs_handoff_avoids_duplicate_intake_without_expanding_authority() -> None:
    handoff_owners = ("cs-feat", "cs-issue", "cs-epic")
    for skill_name in handoff_owners:
        _, owner = _read_skill(SKILLS / skill_name / "SKILL.md")
        for anchor in (
            "同一会话由 `cs` 交入且带已确认 handoff",
            "packet 精确范围内已确认的事项不重复询问",
            "owner 已确认的术语与决策",
            "canonical 资产指针或资产候选",
            "仓库事实冲突",
            "会改变结果的新风险",
            "缺少会改变方向的事实",
            "超出已确认边界",
            "不扩大实现、commit、发布或写入授权",
            "不替代本 skill 的 review、验证与确认门槛",
        ):
            assert anchor in owner, skill_name

    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "handoff 只用于起草 proposed 永久 Epic 文档" in epic
    assert "不替代 fresh design review、批准 hash 或第一道 owner gate" in epic

    _, refactor = _read_skill(SKILLS / "cs-refactor/SKILL.md")
    assert "同一会话由 `cs` 交入且带已确认 handoff" not in refactor


def test_task_skills_retrieve_legacy_knowledge_read_only() -> None:
    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        kickoff = body.split("## 开工", 1)[1].split("\n## ", 1)[0]
        found = {
            path for path in LEGACY_KNOWLEDGE_DIRS if f"`{path}`" in kickoff
        }
        assert found == LEGACY_KNOWLEDGE_DIRS, skill_name
        assert "关键词" in kickoff, skill_name
        assert "检索" in kickoff or "grep" in kickoff, skill_name
        assert "只读" in kickoff, skill_name
        assert "命中要报告来源路径" in kickoff, skill_name
        assert "不得继续生成" in kickoff, skill_name
        assert "原地改写" in kickoff, skill_name
        assert "批量迁移" in kickoff, skill_name


def test_task_skills_share_the_complete_lesson_read_repair_contract() -> None:
    signatures = {}
    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        signatures[skill_name] = {
            anchor
            for anchor in LESSON_READ_REPAIR_CONTRACT
            if _contains_contract(body, anchor)
        }

    assert len({frozenset(signature) for signature in signatures.values()}) == 1
    for skill_name, signature in signatures.items():
        assert signature == LESSON_READ_REPAIR_CONTRACT, skill_name


def test_task_skills_share_the_bounded_strong_signal_contract() -> None:
    signatures = {}
    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        signatures[skill_name] = {
            anchor
            for anchor in CRYSTALLIZATION_SIGNAL_CONTRACT
            if _contains_contract(body, anchor)
        }

    assert len({frozenset(signature) for signature in signatures.values()}) == 1
    for skill_name, signature in signatures.items():
        assert signature == CRYSTALLIZATION_SIGNAL_CONTRACT, skill_name


def test_crystallization_closing_is_quiet_and_prefers_mechanical_guards() -> None:
    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for anchor in (
            "当前任务范围内能直接落成 red -> green 测试/checker",
            "优先机械化",
            "不另写重复 lesson",
            "会扩大范围时只给候选",
        ):
            assert _contains_contract(body, anchor), skill_name

    for skill_name in ORDINARY_TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for anchor in (
            "普通任务只在强信号成立时展示最高价值一条",
            "`晶化候选：{rule}`",
            "证据、范围和建议归宿",
            "无强信号完全不显示模板",
            "没有记忆写入授权时不落盘",
        ):
            assert _contains_contract(body, anchor), skill_name

    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        for anchor in (
            "用户已明确说“记住 / 更新 / 退役”",
            "同轮按 `cs-keep` 处理",
            "不重复确认",
        ):
            assert _contains_contract(body, anchor), skill_name

    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    for anchor in (
        "Epic 子项不展示、不询问",
        "每个子项至多把一条去重候选写入既有游标证据区",
        "最终毕业清单一次处理",
        "复用最终 owner gate",
        "不得询问“是否继续下一项”",
        "不得把普通子项完成当作终态返回",
    ):
        assert _contains_contract(epic, anchor)


def test_task_skills_allow_only_two_narrow_lesson_maintenance_paths() -> None:
    signatures = {}
    for skill_name in TASK_SKILLS:
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        signatures[skill_name] = {
            anchor
            for anchor in NARROW_LESSON_MAINTENANCE_CONTRACT
            if _contains_contract(body, anchor)
        }
        assert _contains_contract(body, "创建、改写规则/scope、晋升、删除与跨项目反馈仍须")
        assert _contains_contract(body, "随当次代码、证据和游标进入同一语义原子 milestone")

    assert len({frozenset(signature) for signature in signatures.values()}) == 1
    for skill_name, signature in signatures.items():
        assert signature == NARROW_LESSON_MAINTENANCE_CONTRACT, skill_name


def test_keep_never_writes_v1_compound() -> None:
    _, keep = _read_skill(SKILLS / "cs-keep/SKILL.md")
    assert "`.codestable/compound/` 是只读历史知识源" in keep
    assert "有增量时" in keep
    assert "`.codestable/lessons/`" in keep
    assert "能合并就更新旧文件" not in keep


def test_keep_owns_the_three_state_lesson_lifecycle() -> None:
    frontmatter, keep = _read_skill(SKILLS / "cs-keep/SKILL.md")
    assert str(frontmatter["description"]).startswith(
        "管理有证据的项目事实、lesson 生命周期与 canonical 归宿"
    )
    for anchor in (
        "status: observed",
        "scope: 模块 / 命令 / 场景关键词",
        "适用 / 不适用：边界与停止应用信号",
        "证据：最多三个代表性路径、测试、diff 或任务指针",
        "候选归宿：test | checker | attention | project-doc | adr | codestable-eval",
        "`observed`",
        "尚未在独立后续任务验证",
        "`validated`",
        "非创建该 lesson 的任务和 agent invocation 中有效命中",
        "真实改善行为并验证成功",
        "明确排除一个具体且合理的错误路径",
        "必须记录 lesson 实际改变的计划或验证",
        "本次通过的验收证据",
        "`retired`",
        "不得应用且不再复活原结论",
        "旧 lesson 缺 `status` 按 `observed` 读取",
        "不批量迁移",
        "不得保存原始对话、逐次命中日志或无限 evidence history",
        "Epic 最终毕业 gate 批准候选",
    ):
        assert _contains_contract(keep, anchor)


def test_keep_promotes_or_retires_without_creating_parallel_truth() -> None:
    _, keep = _read_skill(SKILLS / "cs-keep/SKILL.md")
    for anchor in (
        "机械 guard 优先",
        "测试、checker、lint、类型或 deterministic helper",
        "高频必读事实进入 `attention.md`",
        "全文保持 ≤25 条",
        "难回退、缺少上下文会令人意外、源于真实取舍",
        "其他稳定方法进入项目既有文档",
        "目标不存在时请 owner 选择",
        "不发明目录",
        "先验证新 owner",
        "同一更新中删除重复 lesson",
        "约 50 条预算",
        "`codestable-eval` 只标记未来上游候选",
        "不导出、不上传、不改 skill",
    ):
        assert _contains_contract(keep, anchor)

    for anchor in (
        "新建、改写规则/scope、晋升、删除或跨项目分享仍需用户显式授权",
        "不能把创建该 lesson 的同一任务自证为 validated",
        "retired 条目上的新结论必须另建 observed lesson",
        "不因命中次数或模型自评晋级",
    ):
        assert _contains_contract(keep, anchor)


def test_onboard_keeps_the_base_skeleton_minimal() -> None:
    _, onboard = _read_skill(SKILLS / "cs-onboard/SKILL.md")
    skeleton = onboard.split("```text", 1)[1].split("```", 1)[0]
    assert "epics/" not in skeleton
    assert "requirements/" not in skeleton
    assert "首次 Epic" in onboard
    assert "`.codestable/epics/` 不属于基础骨架" in onboard
    assert "按需创建" in onboard
    for path in LEGACY_KNOWLEDGE_DIRS:
        assert f"`{path}`" in onboard


def test_requirements_only_follow_an_explicit_canonical_owner() -> None:
    for skill_name in ("cs-feat", "cs-epic"):
        _, body = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "`.codestable/attention.md` 明确记录" in body, skill_name
        assert "canonical requirement" in body, skill_name
        assert "不存在时不新建 `.codestable/requirements/`" in body, skill_name


def test_review_delegation_discovers_subagent_management_then_selects() -> None:
    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "当前主流程创建 reviewer 前" in caller, skill_name
        assert "当前会话可调用的 subagent 创建与管理能力" in caller, skill_name
        assert "项目上下文有显式创建方式/model 约束时先遵守" in caller, skill_name
        assert "达到审查质量基线后" in caller, skill_name
        assert "优先选择与实现者异构的 agent" in caller, skill_name
        assert "受管理的结构化委派能力" in caller, skill_name
        assert "宿主 subagent" in caller, skill_name
        assert "本机有界 agent CLI 回退" in caller, skill_name
        assert "不得只扫 PATH" in caller, skill_name
        assert "显式指定最强稳定 `model`" in caller, skill_name
        assert "禁止依赖默认模型" in caller, skill_name
        assert "最终创建方式、agent/model 与回退原因写入 task packet" in caller, skill_name
        assert "通道" not in caller, skill_name
        anchors = (
            "当前主流程创建 reviewer 前",
            "当前会话可调用的 subagent 创建与管理能力",
            "项目上下文有显式创建方式/model 约束时先遵守",
            "达到审查质量基线后",
            "优先选择与实现者异构的 agent",
            "受管理的结构化委派能力",
            "宿主 subagent",
            "本机有界 agent CLI 回退",
            "最终创建方式、agent/model 与回退原因写入 task packet",
        )
        positions = [caller.index(anchor) for anchor in anchors]
        assert positions == sorted(positions), skill_name


def test_review_delegation_keeps_a_healthy_run_bound() -> None:
    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "reviewer 创建后绑定该运行" in caller, skill_name
        assert "状态健康时等待终态报告" in caller, skill_name
        assert "`Awaiting` 携带可查询的同一 run identity" in caller, skill_name
        assert "后来发现更优创建方式" in caller, skill_name
        assert "取消、重复创建或并行补发" in caller, skill_name
        assert "能力不满足或目标失效" in caller, skill_name


def test_review_reuses_one_reviewer_lineage_for_finding_driven_repairs() -> None:
    lineage_contract = (
        "每个独立审查阶段的首轮必须由当前主流程创建一个 fresh reviewer",
        "一个独立审查阶段由单一审查目的界定",
        "design review、change review、contract review 与 Epic final acceptance 是不同阶段",
        "只有为本阶段 findings 所作修复的复审",
        "先修复并重跑验证，再冻结新的完整审查目标",
        "同一 reviewer 的同一 session",
        "完整当前候选与本轮修复增量",
        "`resolved` / `unresolved` / `new findings`",
        "不得只核对旧 finding 或机械打勾",
        "累计最多 3 个有终态报告的轮次",
        "更换 reviewer 不重置计数",
        "只有原 run/session 失败或不可恢复、能力不满足、目标、范围、设计或核心路径发生重大变化",
        "reviewer 声明无法继续独立判断",
        "owner 要求第二意见",
        "独立于实现者，不要求对自身上一轮审查失忆",
    )

    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        for anchor in lineage_contract:
            assert _contains_contract(caller, anchor), f"{skill_name}: missing {anchor!r}"
        assert "处理后重跑验证、重新冻结审查目标并创建 fresh reviewer" not in caller
        assert "需要复审时重新创建 reviewer" not in caller
        assert "按需重新创建 reviewer" not in caller
        assert "需要时重新创建 reviewer" not in caller
        assert "按需重新发起" not in caller

    trigger_contract = {
        "cs-feat": "改动完成后默认进入 change review 审查阶段",
        "cs-issue": "修复完成后默认进入 change review 审查阶段",
        "cs-refactor": "完成后进入 change review 审查阶段",
        "cs-epic": "交确认前进入 design review 审查阶段",
    }
    for skill_name, anchor in trigger_contract.items():
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert _contains_contract(caller, anchor), skill_name

    _, review = _read_skill(SKILLS / "cs-review/SKILL.md")
    for anchor in (
        "首轮 task packet 传入单一审查目的",
        "design review、change review、contract review 与 Epic final acceptance 使用不同阶段",
        "同一 reviewer 的同一 session",
        "完整当前候选与本轮修复增量",
        "`resolved` / `unresolved` / `new findings`",
        "独立于实现者，不要求对自身上一轮审查失忆",
    ):
        assert anchor in review
    assert "不修复、不自行发起复审" in review
    assert "可承接来源流程发给同一 session 的 follow-up" in review
    assert "目标变化则本轮失效，由调用方重新冻结后创建 fresh reviewer" not in review
    assert "在进入本 skill 前完成 reviewer 创建方式与 agent/model 选择并创建 fresh reviewer" not in review


def test_epic_final_acceptance_starts_a_separate_fresh_reviewer_lineage() -> None:
    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "final acceptance 是独立审查阶段" in epic
    assert "另建 fresh reviewer" in epic
    assert "不得沿用子项、此前 design review 或 contract review 的 reviewer lineage" in epic
    assert "主流程按同一 lineage 处理该阶段 findings" in epic
    assert "契约变化形成新的 contract review 审查阶段" in epic
    assert "永久文档已批准后的执行中" in epic


def test_shipped_skills_do_not_bind_review_backend_products() -> None:
    forbidden = (
        "cs-agent-mcp",
        "cs_agent",
        "paseo",
        "claude",
        "codex",
        "anthropic",
        "openai",
        "gpt-",
    )
    paths = [path for path in sorted(SKILLS.rglob("*")) if path.is_file()]
    assert paths
    # Host registration filenames are packaging surfaces, not runtime backend selection.
    allowed_product_named_paths = {Path("cs-review/agents/openai.yaml")}
    product_named_paths = {
        path.relative_to(SKILLS)
        for path in paths
        if any(name in path.relative_to(SKILLS).as_posix().lower() for name in forbidden)
    }
    assert product_named_paths == allowed_product_named_paths
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for product_name in forbidden:
            assert product_name not in text, f"{path}: bound to {product_name!r}"


def test_review_snapshots_and_milestone_commits_are_not_conflated() -> None:
    _, review = _read_skill(SKILLS / "cs-review/SKILL.md")
    assert "冻结一个明确的审查目标" in review
    assert "审查目标标识" in review
    assert "reviewer 返回前不得移动该目标" in review
    assert "diff review 优先 staged diff" in review
    assert "design review 冻结对应文档版本" in review
    assert "audit 冻结 commit + 范围标识" in review

    for skill_name in ("cs-feat", "cs-issue", "cs-refactor", "cs-epic"):
        _, caller = _read_skill(SKILLS / skill_name / "SKILL.md")
        assert "diff review 优先 staged diff" in caller, skill_name
        assert "design review 冻结对应文档版本" in caller, skill_name
        assert "audit 冻结 commit + 范围标识" in caller, skill_name
        assert "目标标识写入 task packet" in caller, skill_name
        assert "重新冻结完整审查目标" in caller, skill_name
        assert "有 blocking 或未被用户明确接受的 important 时不提交当前候选" in caller, skill_name
        assert "正式里程碑 commit" in caller, skill_name
        assert "WIP/checkpoint commit" in caller, skill_name
        assert "不代表 review 通过" in caller, skill_name

    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "同一时间只允许一个 `current_item`" in epic
    assert "不把多个子项堆进同一 diff" in epic
    assert "milestone_commit" in epic


def test_epic_continues_without_a_per_item_owner_gate() -> None:
    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    for anchor in (
        "串行约束，不是每个子项的人工 gate",
        "永久文档顺序中第一个依赖已满足的未完成子项",
        "在同一受托主流程中继续执行",
        "不得询问“是否继续下一项”",
        "不得把普通子项完成当作终态返回",
        "拆解确认本身不等于版本控制授权",
        "按已记录的逐项 checkpoint 策略暂停",
        "需要 owner 明确接受的 important findings",
        "子项 owning skill 自身的确认门槛",
        "进入 executing 前不得保留 `pending` 或非法组合",
        "恢复后沿用游标策略，不重新询问是否继续",
        "旧游标缺字段或组合非法时暂停一次补记/修正",
        "每个语义原子 commit 后按项目、宿主或 owner 已确定的 branch/remote 策略发布",
        "在集成验证与 final acceptance review 通过后、请求 owner 最终接受前发布一次",
        "agent 不执行远端发布",
        "发布失败时写入 `blocked_by` 并暂停",
        "Epic 内的已有 commit 授权只指 `milestone_commit: authorized`",
    ):
        assert anchor in epic

    for field in ("item_progression", "milestone_commit", "remote_publish"):
        assert field in epic
    assert "`milestone_commit: manual` 只能搭配 `item_progression: per-item`" in epic
    assert "`milestone_commit: manual` 只能搭配 `remote_publish: manual`" in epic
    assert "`remote_publish: each-milestone` 只能搭配 `milestone_commit: authorized`" in epic
    assert "`authorized + per-item` 是合法的显式逐项暂停策略" in epic
    assert "每次只推进一个已确认子项" not in epic


def test_epic_separates_durable_record_from_execution_cursor() -> None:
    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "项目已有明确 Epic、RFC 或 initiative 归宿时沿用" in epic
    assert "`.codestable/epics/{slug}.md`" in epic
    assert "永久 Epic 文档" in epic
    assert "`.codestable/work/epic-{slug}.md`" in epic
    assert "执行游标" in epic

    permanent = epic.split("永久文档最小结构", 1)[1].split(
        "work 游标最小结构", 1
    )[0]
    for field in (
        "起点",
        "目标",
        "范围",
        "非目标",
        "验收标准",
        "子项契约",
        "关键决策",
        "最终交付索引",
        "整体验收",
        "遗留风险",
    ):
        assert field in permanent

    cursor_owner = epic.split("- **执行游标**", 1)[1].split(
        "永久文档最小结构", 1
    )[0]
    for field in (
        "永久文档指针",
        "approved_revision",
        "phase",
        "当前子项",
        "下一步",
        "blocked_by",
        "item_progression",
        "milestone_commit",
        "remote_publish",
        "临时决策",
        "证据",
        "commit 指针",
    ):
        assert field in cursor_owner
    assert "不得复制目标、验收、子项定义或最终结论" in epic
    assert "shasum -a 256 <epic-file>" in epic
    assert "确认前保持 `pending`" in epic
    assert "active 期间永久文档冻结" in epic
    assert "终态 `accepted` / `superseded` / `cancelled`" in epic
    assert "永久 Epic 文档不得删除" in epic


def test_epic_internalizes_goal_semantics_without_v1_runtime() -> None:
    _, epic = _read_skill(SKILLS / "cs-epic/SKILL.md")
    assert "拆解方案必须经用户确认" in epic
    assert "目标、边界、验收、子项契约" in epic
    assert "重新 review 并征得同意" in epic
    assert "最新 owner 已批准的验收标准" in epic
    assert "audit/acceptance review" in epic
    assert "owner 最终接受" in epic
    assert "不恢复 `cs-goal` 入口" in epic
    assert "`state.yaml`" in epic
    assert "逐轮 iteration 报告" in epic

    assert not (SKILLS / "cs-goal").exists()
    assert not any(
        path.name in {"state.yaml", "goal-state.yaml", "goal-plan.md"}
        for path in (SKILLS / "cs-epic").rglob("*")
    )
    assert not any(
        "iterations" in path.parts for path in (SKILLS / "cs-epic").rglob("*")
    )


def test_build_cs_skill_requires_semantic_and_host_safe_validation() -> None:
    build_root = LOCAL_SKILLS / "build-cs-skill"
    build = (build_root / "SKILL.md").read_text(encoding="utf-8")
    openai = yaml.safe_load(
        (build_root / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    spec = (build_root / "references/cs-skill-spec-standard.md").read_text(
        encoding="utf-8"
    )
    gates = (build_root / "references/cs-skill-quality-gates.md").read_text(
        encoding="utf-8"
    )

    for path in build_root.rglob("*.md"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 300, path
    assert "$build-cs-skill" in openai["interface"]["default_prompt"]
    assert "thin harness" in build
    assert "thick context" in build
    assert "data SkillShape" in build
    assert "ThinOperator" in build
    assert "ContextualWorkflow" in build
    assert "ToolBackedWorkflow" in build
    assert "data RulePlacement" in build
    assert "placeRule :: Rule -> RulePlacement" in build
    assert "not (independentSkillNeeded kind source) = NoActiveSkill" in build
    assert "CompatibilityShim -> ShimSkill" in build
    assert "ContextPlan" in build
    assert "buildContextPlan" in build
    assert "discover subagent creation and management capabilities callable in the current session" in build
    assert "Reviewer creation methods prefer" in build
    assert "Do not substitute a `PATH` executable scan for capability discovery" in build
    assert "A healthy running delegation stays bound" in build
    assert "idle without a return payload and no recoverable run identity" in " ".join(
        build.split()
    )
    assert "subagent 创建与管理能力契约" in spec
    assert "健康运行的 delegation" in gates
    assert "无可恢复 run identity" in gates
    assert "能力不匹配" in gates
    assert "target 失效" in gates
    assert "Haskell Contract Gate" in build
    assert "CompatibilityShim -> ShimRoute" in build
    assert "lifecycleDriven source -> LifecycleProtocol" in build
    assert "algorithmic source -> AlgorithmProtocol" in build
    placement = build[build.index("placeRule r"):build.index("buildContextPlan ::")]
    placement_guards = (
        "mechanizable r",
        "nonMechanizableSafety r",
        "projectSpecific r",
        "stageSpecific r",
        "everyInvocationNeeds r",
        "otherwise",
    )
    positions = [placement.index(guard) for guard in placement_guards]
    assert positions == sorted(positions)
    assert "data RulePlacement" in spec
    assert "NoActiveSkill" in spec
    assert "ShimSkill" in spec
    assert "ReferenceSkill" in spec
    assert "placeRule :: Rule ->" not in spec
    assert "Responsibility Contract" in spec
    assert "Context Contract" in spec
    assert "Collaboration Contract" in spec
    assert "contractDecision :: Input -> State -> Outcome" in spec
    assert "contractDecision _ _ = Blocked InvalidTransition" in spec
    assert "`HumanCheckpoint` only for an actual owner decision" in spec
    assert "`Awaiting` for already-started external work" in spec
    assert "Every `HumanCheckpoint` must have an explicit resume input" in spec
    assert "cross-skill handoff must retain its target and complete context" in spec
    assert "## Haskell Contract Semantics Gate" in gates
    assert "## Thin Harness Gate" in gates
    assert "## Context Plan Gate" in gates
    assert "## Evolution Compression Gate" in gates
    assert "## Regression Ladder" in gates
    assert "## Live Host Safety Gate" in gates
    assert "## Family Audit Coverage Gate" in gates
    assert "compare it with the reviewed/classified set by equality" in gates
    assert "target the canonical main entry without selecting its internal stage/lane" in gates
    assert "process start identity" in gates
    assert "CI or a quiet disposable host" in gates
    fixtures = (build_root / "references/cs-skill-fixture-patterns.md").read_text(
        encoding="utf-8"
    )
    normalized_build = " ".join(build.split())
    assert "data DelegationRole = Orchestrator | LeafExecutor" in build
    assert "A `LeafExecutor` must not dispatch another agent" in build
    assert "idle without a return payload" in normalized_build
    assert "The calling orchestrator owns integration" in normalized_build
    assert "outermost orchestrator" not in build
    assert "`LeafExecutor`" in spec
    assert "不得创建、委派、唤醒或跟进子 agent" in spec
    assert "调用该 `LeafExecutor` 的 `Orchestrator`" in spec
    assert "最外层 `Orchestrator`" not in spec
    assert "idle/silence without return payload" in gates
    assert "calling `Orchestrator`" in gates
    assert "最外层 agent" not in gates
    assert "review-leaf-does-not-delegate" in fixtures
    assert "spawn_subagent" in fixtures
    assert "wake_subagent" in fixtures
    assert "follow_up_child" in fixtures
    assert "invoke_cs_code_review" in fixtures
    assert "return_idle_without_report" in fixtures
    assert "review-prefers-managed-subagent-creation" in fixtures
    assert "review-cli-is-bounded-fallback" in fixtures
    assert "healthy-review-run-stays-bound" in fixtures
    assert fixtures.count("step: selectReviewCreationMethod") >= 2
    assert fixtures.count("step: monitorReviewRun") >= 2
    assert "path_only_discovery" in fixtures
    assert "selected_creation_method" in fixtures
    assert "selected_channel" not in fixtures
    assert "cancel_reviewer" in fixtures
    assert "spawn_duplicate_reviewer" in fixtures
    assert "当前 v2 活动 skill 不因历史 goal driver" not in fixtures
    assert "read `.codestable/attention.md` just to author" not in build
