"""
CS Browser Bridge - Structured browser extraction for LLM agents.

The core idea: instead of scraping raw HTML and sending it to an LLM,
execute JavaScript directly in the browser and get back structured results
with DOM change detection and transient text monitoring.

Usage:
    import sys
    sys.path.insert(0, '<skill-dir>/scripts')
    from tmwd_bridge import init_browser, web_execute_js, web_scan, list_tabs

    init_browser()
    result = web_execute_js("document.title")
"""

import time
import json
import sys

from .TMWebDriver import TMWebDriver
from . import simphtml

_driver = None


def _log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def init_browser(host='127.0.0.1', port=18765, wait=True):
    """Initialize the browser bridge.

    Starts the WebSocket server and waits for the Chrome extension to connect.
    Call once at the start of a session.

    Args:
        host: Bind address (default 127.0.0.1)
        port: WebSocket port (default 18765)
        wait: If True, block until at least one browser tab connects (up to 20s)

    Returns:
        TMWebDriver instance
    """
    global _driver
    if _driver is not None:
        return _driver
    _driver = TMWebDriver(host=host, port=port)
    if wait:
        for i in range(20):
            sess = _driver.get_all_sessions()
            if len(sess) > 0:
                break
            time.sleep(1)
        if len(_driver.get_all_sessions()) == 0:
            _log("[CS] Warning: No browser tabs connected. Make sure the extension is installed.")
    return _driver


def get_driver():
    """Get the current driver instance, initializing if needed (non-blocking)."""
    global _driver
    if _driver is None:
        return init_browser(wait=False)
    return _driver


def web_execute_js(script, switch_tab_id=None, no_monitor=False, wait_selector=None, wait_ms=10000, timeout=None):
    """Execute JavaScript in the browser with rich result capture.

    This is the PRIMARY interface for browser control. Write JavaScript
    that directly queries/manipulates the DOM and returns structured data.

    The system automatically:
    - Takes a baseline HTML snapshot before execution
    - Injects your JavaScript into the page (with CDP fallback for CSP-restricted pages)
    - Captures transient text that appears during execution (toasts, notifications)
    - Takes an after-snapshot and diffs the DOM
    - Returns a structured summary of what changed

    Args:
        script: JavaScript code to execute in the page context
        switch_tab_id: Optional tab ID to switch to before execution
        no_monitor: If True, skip DOM diff and transient monitoring (faster)
        wait_selector: CSS selector to wait for before executing script
        wait_ms: Max wait time in ms (default: 10000)
        timeout: Execution timeout in seconds (default: 15)

    Returns:
        dict with keys:
            status: "success" or "failed"
            js_return: The return value of your JavaScript (after smart processing)
            diff: DOM change summary string
            transients: List of ephemeral text snippets captured during execution
            newTabs: List of new tabs opened during execution
            tab_id: The tab where the script executed
            error: Error message if status is "failed"
            reloaded: True if the page reloaded during execution
            suggestion: Hint about what happened (e.g. "页面无明显变化")
    """
    driver = get_driver()
    sessions = driver.get_all_sessions()
    if len(sessions) == 0:
        return {"status": "error", "msg": "No browser tabs available. Is the extension connected?"}
    if switch_tab_id:
        driver.default_session_id = switch_tab_id
    elif driver.default_session_id is None and sessions:
        driver.default_session_id = str(sessions[0].get('id'))
    if wait_selector:
        wait_js = f'await new Promise((resolve, reject) => {{ const start = Date.now(); const check = () => {{ const el = document.querySelector({json.dumps(wait_selector)}); if (el) return resolve(el); if (Date.now() - start > {wait_ms}) return reject(new Error("Timeout waiting for: " + {json.dumps(wait_selector)})); setTimeout(check, 200); }}; check(); }});'
        script = wait_js + '\n' + script
    return simphtml.execute_js_rich(script, driver, no_monitor=no_monitor, timeout=timeout)


def web_scan(tabs_only=False, switch_tab_id=None, text_only=False, size_only=False,
             wait_selector=None, wait_ms=10000):
    """Get simplified HTML content of the current page.

    The HTML is processed through a multi-stage simplification pipeline:
    - Spatial analysis: classifies elements as main/secondary/noise
      based on bounding rects, visibility, and z-index
    - Removes floating ads, covered elements, invisible content
    - Strips inline styles, non-semantic attributes, truncates long URLs
    - Detects repeated list patterns and keeps only representative samples
    - Budgeted truncation: recursively divides token budget by element importance

    Args:
        tabs_only: Only return tab list, no HTML content (saves tokens)
        switch_tab_id: Switch to this tab before scanning
        text_only: Return only text content (most token-efficient)
        size_only: Only return content size, not content itself (check if page rendered)
        wait_selector: CSS selector to wait for before scanning (SPA-friendly)
        wait_ms: Max wait time in ms (default: 10000)

    Returns:
        dict with keys:
            status: "success" or "error"
            html: Simplified HTML string (unless size_only or tabs_only)
            size: Content size in characters (when size_only)
            url: Current tab URL (unless tabs_only)
            tab_id: Current tab ID (unless tabs_only)
            sessions: List of {id, url, title} for all tabs (tabs_only only)
            msg: Error message if status is "error"
    """
    driver = get_driver()
    sessions = driver.get_all_sessions()
    if len(sessions) == 0:
        return {"status": "error", "msg": "No browser tabs available. Is the extension connected?"}
    if switch_tab_id:
        driver.default_session_id = switch_tab_id
    elif driver.default_session_id is None and sessions:
        driver.default_session_id = str(sessions[0].get('id'))
    if wait_selector:
        wait_result = simphtml.execute_js_rich(
            f'await new Promise((resolve, reject) => {{ const start = Date.now(); const check = () => {{ const el = document.querySelector({json.dumps(wait_selector)}); if (el) return resolve(el); if (Date.now() - start > {wait_ms}) return reject(new Error("Timeout waiting for: " + {json.dumps(wait_selector)})); setTimeout(check, 200); }}; check(); }});',
            driver, no_monitor=True)
        if wait_result.get('status') == 'failed':
            return {"status": "error", "msg": f"Timeout waiting for selector: {wait_selector}"}
    try:
        if tabs_only:
            return {"status": "success", "sessions": sessions}
        html = simphtml.get_html(driver, text_only=text_only)
        cur = next((s for s in sessions if s['id'] == driver.default_session_id), {})
        result = {"status": "success", "html": html, "url": cur.get('url', ''), "tab_id": driver.default_session_id}
        if size_only:
            result["size"] = len(html)
            result["text_only"] = text_only
            result.pop("html", None)
        return result
    except Exception as e:
        return {"status": "error", "msg": str(e)}


def _wait_for_page_load(driver, timeout_ms=30000):
    """Poll until document.readyState is 'complete' or timeout."""
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            result = driver.execute_js("return document.readyState", timeout=5)
            if result.get('data') == 'complete':
                return True
        except Exception:
            pass
    return False


def web_navigate(url, wait_load=True):
    """Navigate the current tab to a URL.

    Args:
        url: The URL to navigate to
        wait_load: If True, wait for page to finish loading (up to 30s)

    Returns:
        dict with status, navigated_to, loaded (bool)
    """
    driver = get_driver()
    driver.jump(url)
    loaded = False
    if wait_load:
        loaded = _wait_for_page_load(driver)
    return {'status': 'success', 'navigated_to': url, 'loaded': loaded}


def web_back(wait_load=True):
    """Navigate back in browser history.

    Args:
        wait_load: If True, wait for page to finish loading

    Returns:
        dict with status and loaded (bool)
    """
    driver = get_driver()
    driver.back()
    loaded = False
    if wait_load:
        loaded = _wait_for_page_load(driver)
    return {'status': 'success', 'loaded': loaded}


def web_forward(wait_load=True):
    """Navigate forward in browser history.

    Args:
        wait_load: If True, wait for page to finish loading

    Returns:
        dict with status and loaded (bool)
    """
    driver = get_driver()
    driver.forward()
    loaded = False
    if wait_load:
        loaded = _wait_for_page_load(driver)
    return {'status': 'success', 'loaded': loaded}


def web_reload(wait_load=True):
    """Reload the current page.

    Args:
        wait_load: If True, wait for page to finish loading

    Returns:
        dict with status and loaded (bool)
    """
    driver = get_driver()
    driver.reload()
    loaded = False
    if wait_load:
        loaded = _wait_for_page_load(driver)
    return {'status': 'success', 'loaded': loaded}


def web_newtab(url=None):
    """Open a new browser tab.

    Args:
        url: Optional URL to open in the new tab

    Returns:
        dict with status and newtab URL
    """
    driver = get_driver()
    before = {str(s.get('id')) for s in driver.get_all_sessions()}
    raw = driver.newtab(url)
    tab = raw.get('data') if isinstance(raw, dict) else None
    if not isinstance(tab, dict):
        tab = {}
    tab_id = str(tab.get('id')) if tab.get('id') is not None else None

    # Scriptable pages report back through tabs_update after load. Poll briefly so
    # callers can immediately pass the returned id to --tab for normal http(s) URLs.
    deadline = time.time() + 5
    while time.time() < deadline:
        sessions = driver.get_all_sessions()
        if tab_id and any(str(s.get('id')) == tab_id for s in sessions):
            driver.default_session_id = tab_id
            break
        new_sessions = [s for s in sessions if str(s.get('id')) not in before]
        if new_sessions:
            tab_id = str(new_sessions[0].get('id'))
            tab = {**tab, **new_sessions[0]}
            driver.default_session_id = tab_id
            break
        time.sleep(0.2)

    result = {'status': 'success', 'newtab': url or 'about:blank'}
    if tab_id:
        result['tab_id'] = tab_id
    if tab:
        result['tab'] = tab
    return result


def web_close(tab_id=None):
    """Close a browser tab.

    Args:
        tab_id: Tab ID to close. If None, closes the current tab.

    Returns:
        dict with status and closed_tab_id
    """
    driver = get_driver()
    closed_id = str(tab_id) if tab_id else driver.default_session_id
    driver.close_tab(tab_id)
    return {'status': 'success', 'closed_tab_id': closed_id}


def web_screenshot(filepath=None):
    """Capture a screenshot of the current tab via CDP.

    Args:
        filepath: Path to save the PNG. If None, auto-generates a name.

    Returns:
        dict with status and filepath (or error)
    """
    import base64
    import os
    import tempfile
    driver = get_driver()
    try:
        result = driver.screenshot()
        data = result.get('data', {})
        # Navigate CDP response: {data: {data: "base64..."}}
        b64 = data.get('data') if isinstance(data, dict) else None
        if not b64:
            return {'status': 'error', 'msg': 'Screenshot returned no image data'}
        if filepath is None:
            filepath = os.path.join(tempfile.gettempdir(), f'screenshot_{int(time.time())}.png')
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(b64))
        return {'status': 'success', 'filepath': filepath}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}


def list_tabs():
    """List all open browser tabs.

    Returns:
        List of dicts with keys: id, url, title, connected_at
    """
    return get_driver().get_all_sessions()


def switch_tab(url_pattern):
    """Switch to a tab whose URL matches the given pattern.

    Args:
        url_pattern: String to match against tab URLs

    Returns:
        The session ID of the matched tab, or None
    """
    return get_driver().set_session(url_pattern)
