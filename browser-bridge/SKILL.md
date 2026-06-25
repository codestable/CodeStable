---
name: browser-bridge
description: 通过 Chrome 扩展控制真实浏览器。需要访问网页、抽取网页数据、点击按钮、填写表单、执行浏览器自动化、提取渲染后的组件证据，或以程序方式操作页面时使用。通过 DOM diff、简化 HTML 和 component evidence pack 返回节省 token 的结构化结果。适用于 browser control、web automation、page scraping、web data extraction、execute JS in browser、web_scan、web_execute_js、open browser、navigate to URL、get page content、fill form、click button、extract component、rendered DOM、computed styles、component evidence。
---

# Browser Bridge

Browser Bridge 通过 Chrome 扩展连接真实浏览器，提供结构化的网页操作和抽取能力。它不把整页原始 HTML 直接塞给模型，而是在浏览器里执行 JavaScript，再返回结构化结果、DOM 变化摘要和短暂出现的提示文本。

## 使用定位

Browser Bridge 是一个独立技能。它只说明自己的安装方式、命令接口和使用模式。

使用前确认三件事：

- Python 依赖和 Chrome 扩展已经安装。
- `python <skill-dir>/scripts/browser.py tabs` 能看到浏览器 tab。
- 频繁执行命令时，先启动常驻 master，避免每次 CLI 调用都等待扩展重连。

## 架构

```text
CLI (browser.py)  ->  Python (TMWebDriver)  <-WebSocket->  Chrome 扩展  <-CDP/scripting->  浏览器 Tab
```

- Python WebSocket server 运行在 `ws://127.0.0.1:18765`。
- Chrome 扩展连接到 server，并把命令转发给浏览器 tab。
- JavaScript 在页面上下文中执行；如果 CSP 阻止执行，会回退到 CDP。
- 返回结果是结构化 JSON，不是原始 HTML。

## 一次性安装

首次使用前安装依赖：

```bash
pip install bs4 simple-websocket-server bottle requests
```

然后安装 Chrome 扩展：

1. 打开 Chrome 的 `chrome://extensions/`。
2. 启用 "Developer mode / 开发者模式"。
3. 点击 "Load unpacked / 加载已解压的扩展程序"，选择 `<skill-dir>/assets/extension/`。
4. 打开任意网页验证：右下角应看到绿色的 `ljq_driver: connected` 标记。

## CLI 参考

所有命令第一次调用时都会自动启动 bridge server。CLI 位于：

```text
<skill-dir>/scripts/browser.py
```

下面的 `<skill-dir>` 指包含本 `SKILL.md` 的目录。

### 推荐：启动常驻 master

如果直接反复调用 `browser.py exec ...`，每个短命 CLI 进程都可能重新启动 bridge server，并等待 Chrome 扩展重连，通常会多出数秒冷启动时间。频繁操作浏览器时，先单独启动：

```bash
python <skill-dir>/scripts/browser_master.py
```

保持这个进程运行。之后正常使用 `browser.py exec`、`scan`、`tabs` 等命令，它们会自动通过 `http://127.0.0.1:18766/link` 转发到常驻 master。

只需要 JS 返回值、不需要 DOM diff 和 toast 捕获时，给 `exec` 加 `--no-monitor`：

```bash
python <skill-dir>/scripts/browser.py exec --no-monitor "document.title"
```

### exec: 在浏览器里执行 JavaScript

这是最常用的主命令。直接写 JavaScript 查询或操作 DOM。系统会捕获返回值、DOM 变化和执行期间出现的短暂文本，例如 toast、通知、loading 文案。

```bash
python <skill-dir>/scripts/browser.py exec "<javascript>"
```

参数：

- `--tab <id>`：指定 tab。
- `--no-monitor`：跳过 DOM diff，更快。
- `--wait <selector>`：执行前等待 CSS selector 出现，适合 SPA。
- `--wait-ms <ms>`：`--wait` 的最长等待时间，默认 `10000`。
- `--timeout <s>`：执行超时秒数，默认 `15`。

示例：

```bash
# 获取页面标题
python <skill-dir>/scripts/browser.py exec "document.title"

# 点击元素并查看页面变化
python <skill-dir>/scripts/browser.py exec "document.querySelector('.submit-btn').click()"

# 抽取结构化数据
python <skill-dir>/scripts/browser.py exec "Array.from(document.querySelectorAll('.item')).map(e=>({name:e.querySelector('.name')?.textContent,price:e.querySelector('.price')?.textContent}))"

# 填写表单字段，并触发 React/Vue 绑定
python <skill-dir>/scripts/browser.py exec "const e=document.querySelector('#email');e.value='u@x.com';e.dispatchEvent(new Event('input',{bubbles:true}))"

# 向下滚动
python <skill-dir>/scripts/browser.py exec "window.scrollBy(0,800)"

# 等待元素出现后再交互
python <skill-dir>/scripts/browser.py exec --wait ".loaded" "return document.querySelector('.loaded').textContent"

# 长时间操作
python <skill-dir>/scripts/browser.py exec --timeout 30 "await fetch('/api/slow'); return 'done'"
```

返回字段：

- `status`：`success` 或 `failed`。
- `js_return`：JavaScript 返回值；DOM 元素会被智能处理成 `outerHTML`。
- `diff`：DOM 变化摘要，说明哪些元素出现或改变。
- `transients`：执行期间短暂出现的文本，例如 toast 或 loading。
- `newTabs`：执行期间打开的新 tab。
- `tab_id`：执行所在 tab ID。
- `error`：失败时的错误信息。
- `reloaded`：执行期间页面是否发生 reload。
- `suggestion`：页面无明显变化时给出的提示。

### scan: 获取简化后的页面内容

需要页面概览时使用。HTML 会经过空间和语义简化：移除 sidebar、浮动广告、被遮挡元素、不可见内容；重复列表截断到 3 项；删除非语义属性。

```bash
python <skill-dir>/scripts/browser.py scan              # 简化 HTML + tab 列表
python <skill-dir>/scripts/browser.py scan --tabs-only  # 只返回 tab 列表，不返回 HTML
python <skill-dir>/scripts/browser.py scan --text-only  # 只返回文本，token 最少
python <skill-dir>/scripts/browser.py scan --size-only  # 只返回内容大小，用于确认页面是否渲染
python <skill-dir>/scripts/browser.py scan --tab <id>   # 扫描指定 tab
python <skill-dir>/scripts/browser.py scan --wait ".result-card"  # 等待 SPA 内容出现
```

返回字段：

- `status`：`success` 或 `error`。
- `html`：简化 HTML；`tabs-only` 或 `size-only` 时不会返回。
- `url` / `tab_id`：当前 tab 信息。
- `sessions`：所有 tab 的 id、url、title 列表。
- `size`：内容字符数，仅 `size-only` 返回。
- `msg`：失败时的错误信息。

### tabs: 列出所有浏览器 tab

```bash
python <skill-dir>/scripts/browser.py tabs
# -> {"status":"success","sessions":[{"id":"123","url":"https://...","title":"..."},...]}
```

### navigate: 打开 URL

导航当前 tab，并等待页面加载完成，最长 30 秒。

```bash
python <skill-dir>/scripts/browser.py navigate "https://example.com"
python <skill-dir>/scripts/browser.py navigate "https://example.com" --no-wait  # 跳过加载等待
```

返回：

```json
{"status":"success","navigated_to":"https://...","loaded":true}
```

### back: 后退

```bash
python <skill-dir>/scripts/browser.py back
```

### forward: 前进

```bash
python <skill-dir>/scripts/browser.py forward
```

### reload: 重新加载当前页

```bash
python <skill-dir>/scripts/browser.py reload
```

### newtab: 打开新 tab

```bash
python <skill-dir>/scripts/browser.py newtab
python <skill-dir>/scripts/browser.py newtab "https://example.com"
```

返回里会尽量包含 `tab_id` 和 `tab`，后续可以直接传给 `--tab`。

### close: 关闭 tab

```bash
python <skill-dir>/scripts/browser.py close
python <skill-dir>/scripts/browser.py close <tab_id>
```

### switch: 按 URL 片段切换 tab

```bash
python <skill-dir>/scripts/browser.py switch "github"
# -> {"status":"success","session_id":"456"}
```

多个 tab 同时匹配时，默认选择第一个。需要精确选择时，先用 `tabs` 查看所有 tab 的 ID。

### screenshot: 截图

通过 Chrome DevTools Protocol 截取当前 tab 的 PNG 图。

```bash
python <skill-dir>/scripts/browser.py screenshot
python <skill-dir>/scripts/browser.py screenshot page.png
```

返回：

```json
{"status":"success","filepath":"/tmp/screenshot_1714650000.png"}
```

### evidence: 导出渲染后的组件证据

用于设计系统抽取和组件还原。对于 switch、slider、tabs、select、menu、dialog、command input、date picker、chart 等小而细节敏感的组件，仅靠截图不可靠。`evidence` 会从真实浏览器 tab 中捕获渲染后的组件结构。

```bash
python <skill-dir>/scripts/browser.py evidence 'button[role="switch"]' --name Switch --out component-evidence/switch
python <skill-dir>/scripts/browser.py evidence '[data-slot="switch"]' --name Switch --index 0 --depth 4
python <skill-dir>/scripts/browser.py evidence '.tabs-root' --name Tabs --wait '.tabs-root' --wait-ms 8000
```

参数：

- `--name <name>`：组件名，用于 metadata 和输出目录。
- `--out <dir>`：输出目录，默认 `component-evidence/<name>`。
- `--index <n>`：selector 匹配序号，默认 `0`。
- `--depth <n>`：后代结构深度，默认 `4`。
- `--tab <id>`：指定 tab。
- `--wait <selector>` / `--wait-ms <ms>`：等待 SPA 渲染组件。
- `--all-styles`：捕获全部 computed styles，而不是精简后的 UI 样式集合。

输出文件：

```text
component-evidence/<name>/
  README.md
  metadata.json
  dom.html
  attributes.json
  class-list.txt
  box-model.json
  computed-styles.json
  anatomy.json
  screenshot.png
  page.png
```

把这些证据当作组件结构的权威来源。把组件翻译成源码时，保留有意义的 `role`、`aria-*`、`data-state`、`data-size`、`data-slot`、尺寸、transform 和状态类名。`evidence` 不可用时，先向调用方索取复制出来的 rendered DOM、class list 或源码，再把细节敏感组件标为已验证。

## 进一步参考

使用模式、SPA 抽取示例、调研速查表和排障说明在 `reference.md`。操作 Grok 时读取 `grok.md`。只有命令说明不够用时再读取这些参考。
