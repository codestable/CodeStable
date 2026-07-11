from __future__ import annotations

import re


PATH_SEGMENT_PATTERN = (
    r"[^\s`'\"<>/\\,;:!?()\[\]{}，。；：！？、（）【】《》〈〉「」『』"
    r"〔〕〖〗〘〙〚〛“”‘’…—·～]+"
)
PATH_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_.~-])(?:~[/\\]{PATH_SEGMENT_PATTERN}(?:[/\\]{PATH_SEGMENT_PATTERN})*"
    rf"|/(?!(?i:goal)(?:\b|/)){PATH_SEGMENT_PATTERN}(?:/{PATH_SEGMENT_PATTERN})*"
    rf"|[A-Za-z]:\\{PATH_SEGMENT_PATTERN}(?:\\{PATH_SEGMENT_PATTERN})*)"
)
PATH_SPACED_CONTINUATION_PATTERN = re.compile(
    rf"[ \t]+({PATH_SEGMENT_PATTERN})(?:[/\\]{PATH_SEGMENT_PATTERN})+"
)
PATH_SPACED_WORD_PATTERN = re.compile(rf"[ \t]+({PATH_SEGMENT_PATTERN})")
PATH_EXTENSION_PATTERN = re.compile(r"[\w+-]+")
CJK_PATH_GLUE_PATTERN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff](?=[A-Za-z0-9_.+~-])"
)
PATH_QUOTE_PAIRS = {"\"": "\"", "'": "'", "`": "`", "“": "”", "‘": "’"}
URL_PATTERN = re.compile(r"(?:https?|ssh|git)://[^\s`'\"<>]+")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
REMOTE_PATTERN = re.compile(r"(?:[\w.+-]+@[\w.-]+:[^\s`'\"<>]+)")
SECRET_KEY_PATTERN = re.compile(
    r"""(?imx)['"]?(?P<key>api[_-]?key|token|secret|password|authorization|bearer)['"]?
    \s*[:=：＝]\s*"""
)
AUTHORIZATION_HEADER_PATTERN = re.compile(
    r"(?im)(?<![A-Za-z0-9])(?:(?:http|proxy)[-_])?authorization\s*[:=]\s*"
    r"[A-Za-z][A-Za-z0-9._~-]*\s+[^\r\n]+"
)
AUTH_SCHEME_PATTERN = re.compile(
    r"(?i)\b(?:(?:proxy-)?authorization\s*[:=]\s*)?"
    r"(?:basic|bearer)\s+[A-Za-z0-9._~+/=-]{6,}"
)
USER_CREDENTIAL_PATTERN = re.compile(
    r"(?ix)(?<!\S)(?:-u|--user)(?:\s+|=)"
    r"(?:\"[^\"\r\n]+\"|'[^'\r\n]+'|[^\s`'\"]+)"
)
CREDENTIAL_REDACTIONS = (
    (AUTHORIZATION_HEADER_PATTERN, "<auth-credential>"),
    (USER_CREDENTIAL_PATTERN, "<user-credential>"),
    (AUTH_SCHEME_PATTERN, "<auth-credential>"),
)
ENV_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*[^\s`'\"<>]+")
ENV_NAME_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
INLINE_JSON_PATTERN = re.compile(
    r"(?:\{[^{}]*\}|\[[^\[\]]*\])", re.DOTALL
)
JSON_DELIMITER_PATTERN = re.compile(r"[{}\[\]]")


def _quoted_segment_end(text: str, start: int) -> tuple[int, int]:
    quote = text[start]
    index = start + 1
    logical_length = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            elif text[index + 1] in "\r\n":
                index += 2
            else:
                logical_length += 1
                index += 2
            continue
        if char == quote:
            return index + 1, logical_length
        if char not in "\r\n":
            logical_length += 1
        index += 1
    return len(text), logical_length


def _shell_expansion_end(text: str, start: int) -> int:
    stack = [")" if text.startswith("$(", start) else "}"]
    index = start + 2
    while index < len(text) and stack:
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            else:
                index += 2
            continue
        if char in "'\"`":
            index, _length = _quoted_segment_end(text, index)
            continue
        if text.startswith("$(", index):
            stack.append(")")
            index += 2
            continue
        if text.startswith("${", index):
            stack.append("}")
            index += 2
            continue
        opener = "(" if stack[-1] == ")" else "{"
        if char == opener:
            stack.append(stack[-1])
        elif char == stack[-1]:
            stack.pop()
        index += 1
    return index


def _secret_value_end(text: str, start: int) -> int | None:
    placeholder_end = start + len("<redacted>")
    if text.startswith("<redacted>", start) and (
        placeholder_end == len(text) or text[placeholder_end].isspace()
    ):
        return None

    index = start
    logical_length = 0
    has_expansion = False
    starts_quoted = (
        index < len(text) and text[index] in "'\"`"
    ) or text.startswith(("$'", '$"'), index)
    while index < len(text) and not text[index].isspace():
        char = text[index]
        if text.startswith(("$(", "${"), index):
            has_expansion = True
            index = _shell_expansion_end(text, index)
            continue
        if char == "$" and index + 1 < len(text) and text[index + 1] in "'\"":
            index += 1
            continue
        if char in "'\"`":
            index, segment_length = _quoted_segment_end(text, index)
            logical_length += segment_length
            continue
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            elif text[index + 1] == "\n":
                index += 2
            else:
                logical_length += 1
                index += 2
            continue
        logical_length += 1
        index += 1

    minimum = 4 if starts_quoted else 6
    return index if has_expansion or logical_length >= minimum else None


def secret_assignment_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    while match := SECRET_KEY_PATTERN.search(text, cursor):
        end = _secret_value_end(text, match.end())
        if end is None:
            cursor = match.end()
            continue
        spans.append((match.start(), end, match.group("key")))
        cursor = end
    return spans


def contains_secret_assignment(text: str) -> bool:
    return bool(secret_assignment_spans(text))


def redact_secret_assignments(text: str) -> str:
    spans = secret_assignment_spans(text)
    if not spans:
        return text
    pieces: list[str] = []
    cursor = 0
    for start, end, key in spans:
        pieces.extend((text[cursor:start], f"{key}=<redacted>"))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def redact_credentials(text: str) -> str:
    for pattern, replacement in CREDENTIAL_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def redact(text: str, limit: int = 1200) -> str:
    text = redact_credentials(text)
    text = redact_secret_assignments(text)
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "sk-<redacted>", text)
    text = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "gh_<redacted>", text)
    text = text.replace("\x00", "")
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def redact_inline_json(text: str) -> str:
    while True:
        redacted, count = INLINE_JSON_PATTERN.subn("<tool-arguments>", text)
        text = redacted
        if count == 0:
            break
    if JSON_DELIMITER_PATTERN.search(text):
        return "<tool-arguments>"
    return text


def contains_inline_json(text: str) -> bool:
    return bool(INLINE_JSON_PATTERN.search(text) or JSON_DELIMITER_PATTERN.search(text))


def _filename_extension(value: str) -> str | None:
    base, separator, extension = value.rpartition(".")
    if not base or not separator or not PATH_EXTENSION_PATTERN.fullmatch(extension):
        return None
    if extension.isnumeric():
        return None
    if not extension.isascii() and len(extension) > 3:
        return None
    return extension


def _has_cjk_path_glue(value: str, *, terminal_filename: bool = False) -> bool:
    extension = _filename_extension(value) if terminal_filename else None
    for transition in CJK_PATH_GLUE_PATTERN.finditer(value):
        if extension is not None and value[transition.end()] == ".":
            continue
        return True
    return False


def _absolute_path_end(text: str, match: re.Match[str]) -> int:
    end = match.end()
    while end > match.start() and text[end - 1] == ".":
        end -= 1

    opener = text[match.start() - 1] if match.start() else ""
    closer = PATH_QUOTE_PAIRS.get(opener)
    if closer:
        close = text.find(closer, end)
        if close >= 0:
            return close

    while continuation := PATH_SPACED_CONTINUATION_PATTERN.match(text, end):
        if _has_cjk_path_glue(continuation.group(1)):
            break
        end = continuation.end()
        while end > match.start() and text[end - 1] == ".":
            end -= 1

    cursor = end
    for _ in range(2):
        word = PATH_SPACED_WORD_PATTERN.match(text, cursor)
        if not word:
            break
        token_end = word.end(1)
        while token_end > word.start(1) and text[token_end - 1] == ".":
            token_end -= 1
        token = text[word.start(1):token_end]
        if (
            _filename_extension(token) is not None
            and not _has_cjk_path_glue(token, terminal_filename=True)
            and (token_end == len(text) or text[token_end] not in "/\\")
        ):
            return token_end
        cursor = word.end()
    return end


def redact_absolute_paths(text: str) -> str:
    pieces: list[str] = []
    cursor = 0
    for match in PATH_PATTERN.finditer(text):
        if match.start() < cursor:
            continue
        pieces.extend((text[cursor:match.start()], "<local-path>"))
        cursor = _absolute_path_end(text, match)
    pieces.append(text[cursor:])
    return "".join(pieces)


def public_redact(text: str, limit: int = 300) -> str:
    text = re.sub(r"```.*?(?:```|\Z)", "<code-block>", text, flags=re.DOTALL)
    text = redact_credentials(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = redact_inline_json(text)
    text = ENV_PATTERN.sub("<env>", text)
    text = redact(text, limit=limit * 4)
    text = REMOTE_PATTERN.sub("<repo-remote>", text)
    text = URL_PATTERN.sub("<url>", text)
    text = redact_absolute_paths(text)
    text = EMAIL_PATTERN.sub("<email>", text)
    text = ENV_NAME_PATTERN.sub("<env-name>", text)
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text
