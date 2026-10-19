"""Opt-in public HTTPS retrieval with address pinning and no redirects/proxy/auth."""

import ipaddress
import json
import socket
from urllib.parse import urlencode, urlsplit

from .core import Error
from .httpio import DeadlineHTTP, read_exchange


def validate_public_url(url, allowed_hosts):
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower()
        if (
            u.scheme != "https"
            or host not in allowed_hosts
            or u.port not in {None, 443}
            or u.username
            or u.password
            or u.fragment
            or any(c in url for c in "\r\n\t")
            or len(url) > 2000
        ):
            raise Error("URL must be HTTPS on an explicitly allowed public hostname, without credentials/fragments")
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        ips = sorted({r[4][0] for r in records})
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise Error("Private, reserved or mixed public/private source addresses are blocked")
        return host, (u.path or "/") + ("?" + u.query if u.query else ""), ips[0]
    except (ValueError, OSError):
        raise Error("Invalid or unresolved public source URL") from None


class PinnedHTTPS(DeadlineHTTP):
    def __init__(self, host, ip, timeout):
        super().__init__(host, 443, timeout, tls=True, ip=ip)


def fetch_https(
    url,
    allowed_hosts,
    *,
    timeout=20,
    max_bytes=524_288,
    accepted=("text/plain", "text/html"),
):
    if not 1 <= timeout <= 120 or not 1 <= max_bytes <= 524_288:
        raise Error("Fetch limits out of bounds")
    host, path, ip = validate_public_url(url, set(allowed_hosts))
    conn = PinnedHTTPS(host, ip, timeout)
    status, headers, raw = read_exchange(
        conn,
        "GET",
        path,
        {"User-Agent": "EvidenceRoom/0.1 (source-audit)", "Accept": ", ".join(accepted), "Accept-Encoding": "identity"},
        timeout=timeout,
        max_bytes=max_bytes,
    )
    if status != 200:
        raise Error(f"Source HTTP {status}; redirects are not followed")
    mime = headers.get("content-type", "").split(";")[0].lower()
    if mime not in accepted or headers.get("content-encoding", "identity") != "identity":
        raise Error("Unsupported source type or content encoding")
    return raw, mime


def discover(query, *, fetcher=fetch_https):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 500:
        raise Error("Discovery query must contain 1–500 characters")
    url = "https://api.crossref.org/works?" + urlencode(
        {
            "query.bibliographic": query,
            "rows": 5,
            "select": "DOI,title,URL,publisher,published,type",
        }
    )
    raw, _ = fetcher(url, {"api.crossref.org"}, accepted=("application/json",))
    try:
        items = json.loads(raw)["message"]["items"]
        if not isinstance(items, list) or any(not isinstance(i, dict) for i in items):
            raise Error("Malformed discovery item list")
        results = [
            {
                "title": i.get("title", ["Untitled"])[0],
                "url": i["URL"],
                "doi": i["DOI"],
                "publisher": i.get("publisher", "Unknown"),
                "type": i.get("type", "unknown"),
            }
            for i in items[:5]
        ]
    except (ValueError, KeyError, TypeError, IndexError, AttributeError):
        raise Error("Malformed discovery response") from None
    return {
        "provider": "Crossref public metadata",
        "query": query,
        "results": results,
        "notice": "Discovery candidates only; metadata is not evidence for a claim. Review and add primary source URLs to a case.",
    }
