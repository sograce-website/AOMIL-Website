"""Repository-local SEO and link validation for the static site."""
from __future__ import annotations

import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://aomil.com"
SKIP_PAGES = {"projectors.html"}  # permanent redirect source


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.h1 = 0
        self.title = ""
        self._title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "a" and data.get("href"):
            self.links.append(data["href"] or "")
        elif tag == "img":
            self.images.append(data)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self._title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._title = False

    def handle_data(self, data: str) -> None:
        if self._title:
            self.title += data


def local_target(href: str, source: Path) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    clean = parsed.path
    if not clean:
        return None
    target = ROOT / clean.lstrip("/") if clean.startswith("/") else source.parent / clean
    if clean.endswith("/"):
        target /= "index.html"
    if not target.suffix and not target.is_dir():
        target = target.with_suffix(".html")
    if target.is_dir():
        target /= "index.html"
    return target


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    titles: dict[str, list[str]] = defaultdict(list)
    descriptions: dict[str, list[str]] = defaultdict(list)
    canonicals: dict[str, str] = {}
    alternates: dict[str, dict[str, str]] = {}
    page_links: dict[str, list[str]] = {}
    pages = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts]
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        if rel in SKIP_PAGES:
            continue
        content = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(content)
        page_links[rel] = parser.links
        if parser.h1 != 1:
            errors.append(f"{rel}: expected one H1, found {parser.h1}")
        if parser.title:
            titles[parser.title.strip()].append(rel)
        desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.I | re.S)
        if desc:
            descriptions[desc.group(1).strip()].append(rel)
        else:
            errors.append(f"{rel}: missing meta description")
        canonical_matches = re.findall(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)', content, re.I)
        if len(canonical_matches) != 1:
            errors.append(f"{rel}: expected one canonical, found {len(canonical_matches)}")
        else:
            canonicals[rel] = canonical_matches[0]
        alt = dict(re.findall(r'<link\s+rel=["\']alternate["\']\s+hreflang=["\']([^"\']+)["\']\s+href=["\']([^"\']+)', content, re.I))
        alternates[rel] = alt
        for schema_text in re.findall(r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', content, re.I | re.S):
            try:
                json.loads(schema_text)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON-LD: {exc}")
        if not re.search(r'property=["\']og:title["\']', content, re.I) or not re.search(r'name=["\']twitter:card["\']', content, re.I):
            errors.append(f"{rel}: incomplete social metadata")
        for image in parser.images:
            if "alt" not in image or not (image.get("alt") or "").strip():
                errors.append(f"{rel}: image missing non-empty alt ({image.get('src')})")
            if not image.get("loading") or not image.get("decoding"):
                errors.append(f"{rel}: image missing loading/decoding ({image.get('src')})")
            target = local_target(image.get("src") or "", page)
            if target and not target.exists():
                errors.append(f"{rel}: missing image {image.get('src')}")
            if target and target.exists() and (not image.get("width") or not image.get("height")):
                warnings.append(f"{rel}: image dimensions unavailable ({image.get('src')})")
        for href in parser.links:
            target = local_target(href, page)
            if target and not target.exists():
                errors.append(f"{rel}: broken internal link {href}")

    for label, values in (("title", titles), ("description", descriptions)):
        for value, rels in values.items():
            if len(rels) > 1:
                warnings.append(f"duplicate {label}: {rels}")

    url_to_rel = {url: rel for rel, url in canonicals.items()}
    for rel, langs in alternates.items():
        for lang, url in langs.items():
            if lang == "x-default":
                continue
            target_rel = url_to_rel.get(url)
            if not target_rel:
                errors.append(f"{rel}: hreflang target is not canonical: {url}")
                continue
            source_url = canonicals[rel]
            if source_url not in alternates.get(target_rel, {}).values():
                errors.append(f"{rel}: hreflang not reciprocal with {target_rel}")

    sitemap_urls: set[str] = set()
    for sitemap in ("sitemap.xml", "sitemap-es.xml", "sitemap-fr.xml"):
        try:
            tree = ET.parse(ROOT / sitemap)
        except Exception as exc:
            errors.append(f"{sitemap}: invalid XML: {exc}")
            continue
        for loc in tree.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            if loc.text:
                sitemap_urls.add(loc.text.strip())
    expected = set(canonicals.values())
    missing = expected - sitemap_urls
    extra = sitemap_urls - expected
    if missing:
        errors.append("canonical URLs missing from sitemaps: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("non-canonical URLs in sitemaps: " + ", ".join(sorted(extra)))

    # Redirect architecture: canonical .html files must be direct 200 targets,
    # while extensionless duplicates redirect exactly once to those canonicals.
    try:
        netlify = tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"netlify.toml: invalid TOML: {exc}")
        netlify = {}
    pretty_urls = netlify.get("build", {}).get("processing", {}).get("html", {}).get("pretty_urls")
    if pretty_urls is not False:
        errors.append("netlify.toml: build.processing.html.pretty_urls must be false for .html canonicals")

    redirect_rules: dict[str, tuple[str, str]] = {}
    redirect_file = ROOT / "_redirects"
    if not redirect_file.exists():
        errors.append("missing _redirects file")
    else:
        for line_number, raw in enumerate(redirect_file.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) != 3:
                errors.append(f"_redirects:{line_number}: expected source target status")
                continue
            source, target, status = fields
            if source in redirect_rules:
                errors.append(f"_redirects:{line_number}: duplicate source {source}")
            redirect_rules[source] = (target, status)

    canonical_paths = {urlparse(url).path for url in expected}
    for source, (target, status) in redirect_rules.items():
        if source in canonical_paths:
            errors.append(f"canonical URL is also a redirect source: {source}")
        if status not in {"301", "301!"}:
            errors.append(f"redirect is not permanent: {source} -> {target} ({status})")
        if target not in canonical_paths:
            errors.append(f"redirect target is not canonical: {source} -> {target}")
        if target in redirect_rules:
            errors.append(f"redirect chain detected: {source} -> {target} -> {redirect_rules[target][0]}")

    for canonical_path in sorted(path for path in canonical_paths if path.endswith(".html")):
        extensionless = canonical_path[:-5]
        rule = redirect_rules.get(extensionless)
        if rule != (canonical_path, "301!"):
            errors.append(f"missing one-hop forced redirect: {extensionless} -> {canonical_path}")

    # Internal links must use the final canonical URL rather than a redirecting
    # extensionless alias.
    for rel, links in page_links.items():
        for href in links:
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if parsed.path in redirect_rules:
                errors.append(f"{rel}: internal link points to redirect source {parsed.path}")

    print(f"Validated {len(pages) - len(SKIP_PAGES)} canonical pages")
    print(f"Errors: {len(errors)}")
    for item in errors:
        print("ERROR", item)
    print(f"Warnings: {len(warnings)}")
    for item in warnings:
        print("WARN", item)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
