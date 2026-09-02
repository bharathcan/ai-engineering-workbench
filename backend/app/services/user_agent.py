"""A deliberately lightweight User-Agent classifier — substring heuristics,
not a maintained device/browser database (no such dependency is added, per
this project's minimal-dependency preference). This will misclassify
uncommon or spoofed User-Agent strings; it is good enough for a rough
device_type/browser breakdown, not claimed to be authoritative. See
docs/adr/ADR-005-advanced-analytics-privacy.md.
"""

DeviceType = str  # "MOBILE" | "TABLET" | "DESKTOP" | "BOT" | "UNKNOWN"
Browser = str  # "CHROME" | "SAFARI" | "FIREFOX" | "EDGE" | "OTHER" | "UNKNOWN"

_BOT_MARKERS = ("bot", "spider", "crawler", "curl", "wget", "httpx", "python-requests")


def classify_device(user_agent: str | None) -> DeviceType:
    if not user_agent:
        return "UNKNOWN"
    ua = user_agent.lower()
    if any(marker in ua for marker in _BOT_MARKERS):
        return "BOT"
    if "ipad" in ua or "tablet" in ua:
        return "TABLET"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        return "MOBILE"
    if "mozilla" in ua or "windows" in ua or "macintosh" in ua or "linux" in ua:
        return "DESKTOP"
    return "UNKNOWN"


def classify_browser(user_agent: str | None) -> Browser:
    if not user_agent:
        return "UNKNOWN"
    ua = user_agent.lower()
    # Order matters: Edge and Chrome both include "safari" in their UA
    # string for legacy compatibility reasons, so more specific tokens
    # must be checked first.
    if "edg/" in ua or "edge" in ua:
        return "EDGE"
    if "firefox" in ua:
        return "FIREFOX"
    if "chrome" in ua or "chromium" in ua:
        return "CHROME"
    if "safari" in ua:
        return "SAFARI"
    if any(marker in ua for marker in _BOT_MARKERS):
        return "OTHER"
    return "UNKNOWN"
