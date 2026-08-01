from hashlib import sha256
from pathlib import Path
import re

from dispatchboard.job_sequence import next_job_number


def test_epic_current_item_is_complete_and_revision_stays_valid():
    repo = Path.cwd()
    epic = repo / ".codestable/epics/sequence-rollout.md"
    cursor = repo / ".codestable/work/epic-sequence-rollout.md"
    cursor_text = cursor.read_text(encoding="utf-8")

    assert next_job_number([2, 7], [4, 11]) == 12
    assert re.search(r"- \[[xX]\] SEQ-A", cursor_text)
    assert "- [ ] SEQ-B" in cursor_text
    assert sha256(epic.read_bytes()).hexdigest() in cursor_text
    assert cursor_text.count("晶化候选：") == 1
    assert "persisted history sources" in cursor_text
    assert "single snapshot" in cursor_text
    assert "sibling allocator" in cursor_text
