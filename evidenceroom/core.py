"""Bounded input and immutable normalized source records; no source execution."""

import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


class Error(ValueError):
    pass


def digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def text(value, label, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise Error(f"Invalid {label}")
    return value.strip()


def read_json(path, limit=2_000_000):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise Error("JSON exceeds input budget")
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise Error("Invalid JSON input") from None


def load_case(path):
    c = read_json(path, 64_000)
    if not isinstance(c, dict):
        raise Error("Case must be an object")
    c["question"] = text(c.get("question"), "question", 1000)
    options = c.get("options", [])
    claims = c.get("claims", [])
    if not isinstance(options, list) or len(options) > 6:
        raise Error("At most 6 decision options")
    c["options"] = [text(o, "option", 300) for o in options]
    if not isinstance(claims, list) or len(claims) > 8:
        raise Error("At most 8 claims")
    c["claims"] = [text(x, "claim", 500) for x in claims]
    sources = c.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 12:
        raise Error("Provide 1–12 sources")
    ids = set()
    for s in sources:
        if not isinstance(s, dict):
            raise Error("Source must be an object")
        sid = text(s.get("id"), "source ID", 40)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", sid) or sid in ids:
            raise Error("Invalid or duplicate source ID")
        ids.add(sid)
        text(s.get("title"), "source title", 300)
        text(s.get("publisher"), "source publisher", 200)
        if not isinstance(s.get("kind"), str) or s.get("kind") not in {"primary", "secondary", "unknown"}:
            raise Error("Source kind must be primary, secondary or unknown (user declaration)")
        if ("path" in s) == ("url" in s):
            raise Error("Source needs exactly one path or URL")
        text(s.get("path", s.get("url")), "source location", 2000)
        if "published" in s:
            if not isinstance(s["published"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["published"]):
                raise Error("Published date must be YYYY-MM-DD")
            from datetime import date

            try:
                date.fromisoformat(s["published"])
            except ValueError:
                raise Error("Invalid published date") from None
    return c


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self.hidden += 1
        if not self.hidden and tag in {
            "p",
            "div",
            "li",
            "br",
            "h1",
            "h2",
            "h3",
            "article",
            "section",
            "tr",
        }:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg", "template"} and self.hidden:
            self.hidden -= 1
        if not self.hidden and tag in {"p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def normalize_html(raw):
    p = Extractor()
    p.feed(raw)
    return normalize("".join(p.parts))


def normalize(raw):
    raw = unicodedata.normalize("NFC", raw).replace("\r\n", "\n").replace("\r", "\n")
    return "\n\n".join(" ".join(p.split()) for p in re.split(r"\n\s*\n", raw) if p.strip())


def ingest(case, root, fetcher=None):
    root = Path(root).resolve()
    sources, groups, total = [], {}, 0
    for spec in case["sources"]:
        if "url" in spec:
            if fetcher is None:
                raise Error("URL sources require explicit --allow-network and --allow-host")
            raw, mime = fetcher(spec["url"])
            location = spec["url"]
        else:
            candidate = Path(spec["path"])
            if candidate.is_absolute() or ".." in candidate.parts:
                raise Error("Source path escapes case directory")
            path = root / candidate
            if any((root / Path(*candidate.parts[:i])).is_symlink() for i in range(1, len(candidate.parts) + 1)):
                raise Error("Source symlinks are not allowed")
            if not path.resolve().is_relative_to(root) or not path.is_file():
                raise Error("Source must be a regular file under the case directory")
            with path.open("rb") as stream:
                raw = stream.read(524_289)
            mime = "text/html" if path.suffix.lower() in {".html", ".htm"} else "text/plain"
            location = candidate.as_posix()
        if not isinstance(raw, bytes) or len(raw) > 524_288:
            raise Error("Source exceeds 512 KB")
        try:
            decoded = raw.decode("utf-8")
        except UnicodeError:
            raise Error("Sources must be UTF-8 text or HTML; PDF/binary unsupported") from None
        if "\x00" in decoded:
            raise Error("Binary source is unsupported")
        content = normalize_html(decoded) if mime == "text/html" else normalize(decoded)
        if not content or len(content) > 40_000:
            raise Error("Source must contain 1–40,000 normalized characters")
        total += len(content)
        if total > 160_000:
            raise Error("Combined source text exceeds 160,000 characters")
        sha = hashlib.sha256(content.encode()).hexdigest()
        sources.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "publisher": spec["publisher"],
                "declared_kind": spec["kind"],
                "published": spec.get("published"),
                "location": location,
                "text": content,
                "sha256": sha,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "content_group": sha,
                "duplicate_of": groups.get(sha),
            }
        )
        groups.setdefault(sha, spec["id"])
    return sources
