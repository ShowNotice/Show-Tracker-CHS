"""Polite HTTP client: honest User-Agent, a delay between requests to the same host,
one retry for rate limits and dropped connections, and bot-challenge detection.

A bot challenge (CAPTCHA, Cloudflare "Just a moment…") raises Blocked. Callers must
treat that as "this source is unavailable this run", never try to get past it.
"""
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "ShowNoticeCHS/1.0 (+https://chs.shownotice.com)"
DEFAULT_DELAY = 1.5           # seconds between requests to one host
HOST_DELAYS = {"charlestonpourhouse.com": 3.0}   # robots.txt Crawl-delay: 3
RATE_LIMIT_WAIT = 60


class Blocked(Exception):
    """The site answered with a bot challenge or CAPTCHA."""


class FetchError(Exception):
    """The request failed after its retry."""


class Http:
    def __init__(self, delay=DEFAULT_DELAY, timeout=40, sleep=time.sleep):
        self.delay = delay
        self.timeout = timeout
        self.sleep = sleep
        self._last = {}
        self.requests = 0

    def _wait_turn(self, host):
        gap = HOST_DELAYS.get(host, self.delay)
        last = self._last.get(host)
        if last is not None:
            remaining = gap - (time.monotonic() - last)
            if remaining > 0:
                self.sleep(remaining)
        self._last[host] = time.monotonic()

    def get(self, url, headers=None):
        """Return the response body as text. Raises Blocked or FetchError."""
        host = urllib.parse.urlsplit(url).hostname or ""
        host = host[4:] if host.startswith("www.") else host
        hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        hdrs.update(headers or {})
        last_err = None
        for attempt in range(2):
            self._wait_turn(host)
            self.requests += 1
            req = urllib.request.Request(url, headers=hdrs)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode(resp.headers.get_content_charset() or "utf-8", "replace")
                    if resp.headers.get("sg-captcha") or "/.well-known/sgcaptcha/" in resp.geturl():
                        raise Blocked(f"{url}: SiteGround CAPTCHA")
                    return body
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace") if e.fp else ""
                if e.headers.get("cf-mitigated") or "Just a moment..." in body or e.headers.get("sg-captcha"):
                    raise Blocked(f"{url}: bot challenge (HTTP {e.code})")
                last_err = f"HTTP {e.code}"
                if e.code == 429 and attempt == 0:
                    retry = e.headers.get("Retry-After")
                    self.sleep(int(retry) if retry and retry.isdigit() else RATE_LIMIT_WAIT)
                    continue
                if 500 <= e.code < 600 and attempt == 0:
                    self.sleep(10)
                    continue
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = str(getattr(e, "reason", e))
                if attempt == 0:
                    self.sleep(10)
                    continue
        raise FetchError(f"{url}: {last_err}")
