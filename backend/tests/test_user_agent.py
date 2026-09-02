from app.services.user_agent import classify_browser, classify_device

CHROME_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
EDGE_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
)
IPAD_SAFARI = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


def test_classify_device_desktop():
    assert classify_device(CHROME_DESKTOP) == "DESKTOP"


def test_classify_device_mobile():
    assert classify_device(SAFARI_IPHONE) == "MOBILE"


def test_classify_device_tablet():
    assert classify_device(IPAD_SAFARI) == "TABLET"


def test_classify_device_bot():
    assert classify_device(GOOGLEBOT) == "BOT"


def test_classify_device_none_is_unknown():
    assert classify_device(None) == "UNKNOWN"


def test_classify_browser_chrome():
    assert classify_browser(CHROME_DESKTOP) == "CHROME"


def test_classify_browser_safari_on_iphone():
    assert classify_browser(SAFARI_IPHONE) == "SAFARI"


def test_classify_browser_firefox():
    assert classify_browser(FIREFOX_LINUX) == "FIREFOX"


def test_classify_browser_edge_not_misclassified_as_chrome():
    # Edge's UA string also contains "chrome" and "safari" — must be
    # detected as EDGE specifically, not falsely matched as CHROME.
    assert classify_browser(EDGE_DESKTOP) == "EDGE"


def test_classify_browser_none_is_unknown():
    assert classify_browser(None) == "UNKNOWN"
