"""Deterministic SEO normalization for the static AOMIL site."""
from __future__ import annotations

import html
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://aomil.com"
PRODUCT_SLUGS = {
    item["slug"]: item["category"]
    for item in json.loads((ROOT / "AOMIL_V2.5_PRODUCT_MAPPING.json").read_text(encoding="utf-8"))
}

EQUIVALENTS = {
    "index.html": {"en": "/", "es": "/es/", "fr": "/fr/"},
    "projector.html": {"en": "/projector.html", "es": "/es/projector.html", "fr": "/fr/projecteur-noel.html"},
    "snow-globe.html": {"en": "/snow-globe.html", "es": "/es/snow-globe.html", "fr": "/fr/decorations-noel.html"},
    "tree-topper.html": {"en": "/tree-topper.html", "fr": "/fr/decorations-sapin-noel.html"},
    "dual-lens-projector.html": {"en": "/dual-lens-projector.html", "fr": "/fr/projecteur-noel-exterieur.html"},
    "window-lantern.html": {"en": "/window-lantern.html", "fr": "/fr/decoration-fenetre-noel.html"},
    "es/index.html": {"en": "/", "es": "/es/", "fr": "/fr/"},
    "es/projector.html": {"en": "/projector.html", "es": "/es/projector.html", "fr": "/fr/projecteur-noel.html"},
    "es/snow-globe.html": {"en": "/snow-globe.html", "es": "/es/snow-globe.html", "fr": "/fr/decorations-noel.html"},
    "fr/index.html": {"en": "/", "es": "/es/", "fr": "/fr/"},
    "fr/projecteur-noel.html": {"en": "/projector.html", "es": "/es/projector.html", "fr": "/fr/projecteur-noel.html"},
    "fr/decorations-noel.html": {"en": "/snow-globe.html", "es": "/es/snow-globe.html", "fr": "/fr/decorations-noel.html"},
    "fr/decorations-sapin-noel.html": {"en": "/tree-topper.html", "fr": "/fr/decorations-sapin-noel.html"},
    "fr/projecteur-noel-exterieur.html": {"en": "/dual-lens-projector.html", "fr": "/fr/projecteur-noel-exterieur.html"},
    "fr/decoration-fenetre-noel.html": {"en": "/window-lantern.html", "fr": "/fr/decoration-fenetre-noel.html"},
}


def canonical_path(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel in ("es/index.html", "fr/index.html"):
        return "/" + rel.split("/")[0] + "/"
    return "/" + rel.replace("\\", "/")


def text_content(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def meta_value(content: str, pattern: str) -> str:
    match = re.search(pattern, content, re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else ""


def image_size(src: str, page: Path) -> tuple[int, int] | None:
    if src.startswith(("http:", "https:", "data:")):
        return None
    target = ROOT / src.lstrip("/") if src.startswith("/") else page.parent / src
    try:
        data = target.read_bytes()
    except OSError:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            if marker in range(0xC0, 0xC4):
                height, width = struct.unpack(">HH", data[offset + 5:offset + 9])
                return width, height
            if offset + 4 > len(data):
                break
            length = struct.unpack(">H", data[offset + 2:offset + 4])[0]
            offset += 2 + length
    return None


def repair_image_src(src: str, page: Path) -> str:
    """Replace known broken gallery references with an existing repository image."""
    if src.startswith(("http:", "https:", "data:")):
        return src
    target = ROOT / src.lstrip("/") if src.startswith("/") else page.parent / src
    if target.exists():
        return src
    normalized = src.lstrip("/").replace("\\", "/")
    match = re.match(r"assets/products/([^/]+)/([^/]+)$", normalized)
    if not match:
        return src
    slug, filename = match.groups()
    root_copy = ROOT / slug / filename
    if root_copy.exists():
        return f"/{slug}/{filename}"
    for candidate in (ROOT / "assets" / "products" / slug).glob("main.*"):
        return "/" + candidate.relative_to(ROOT).as_posix()
    for candidate in (ROOT / slug).glob("main.*"):
        return "/" + candidate.relative_to(ROOT).as_posix()
    return src


def schema_for(rel: str, title: str, description: str, image: str | None) -> list[dict]:
    url = SITE + canonical_path(rel)
    language = "fr-FR" if rel.startswith("fr/") else "es-ES" if rel.startswith("es/") else "en"
    nodes: list[dict] = []
    if rel in ("index.html", "es/index.html", "fr/index.html"):
        nodes.extend([
            {"@type": "Organization", "@id": SITE + "/#organization", "name": "AOMIL", "url": SITE + "/", "email": "info@aomil.com", "contactPoint": {"@type": "ContactPoint", "telephone": "+86-18617029976", "contactType": "sales"}},
            {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "AOMIL", "publisher": {"@id": SITE + "/#organization"}, "inLanguage": ["en", "es", "fr"]},
        ])
    if canonical_path(rel) not in ("/", "/es/", "/fr/"):
        home = "/fr/" if rel.startswith("fr/") else "/es/" if rel.startswith("es/") else "/"
        home_name = "Accueil" if rel.startswith("fr/") else "Inicio" if rel.startswith("es/") else "Home"
        nodes.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": home_name, "item": SITE + home},
            {"@type": "ListItem", "position": 2, "name": title.split("|")[0].strip(), "item": url},
        ]})
    slug = Path(rel).stem
    product_category = PRODUCT_SLUGS.get(slug)
    if rel == "fr/projecteur-noel-exterieur.html":
        product_category = "Projecteur de Noël"
    elif rel == "fr/decoration-fenetre-noel.html":
        product_category = "Décoration de Noël"
    if product_category:
        product = {"@type": "Product", "name": title.split("|")[0].strip(), "description": description, "url": url, "brand": {"@type": "Brand", "name": "AOMIL"}, "category": product_category}
        if image:
            product["image"] = image
        nodes.append(product)
    return [{"@context": "https://schema.org", "@graph": nodes}] if nodes else []


def normalize_page(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    content = path.read_text(encoding="utf-8")
    title = text_content(meta_value(content, r"<title[^>]*>(.*?)</title>")) or "AOMIL"
    description = meta_value(content, r"<meta\s+name=[\"']description[\"']\s+content=[\"'](.*?)[\"']")
    if not description:
        description = title.split("|")[0].strip() + " from AOMIL Holiday Decorations."
    canonical = SITE + canonical_path(rel)
    first_img = meta_value(content, r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']")
    if first_img:
        first_img = repair_image_src(first_img, path)
        image = first_img if first_img.startswith("http") else SITE + "/" + first_img.lstrip("/")
    else:
        image = SITE + "/assets/products/dual-lens-projector/main.jpg"

    content = re.sub(r"\s*<link\s+rel=[\"']canonical[\"'][^>]*>", "", content, flags=re.I)
    content = re.sub(r"\s*<link\s+rel=[\"']alternate[\"'][^>]*hreflang[^>]*>", "", content, flags=re.I)
    content = re.sub(r"\s*<meta\s+(?:property|name)=[\"'](?:og:|twitter:)[^>]*>", "", content, flags=re.I)
    content = re.sub(r"\s*<script\s+type=[\"']application/ld\+json[\"'][^>]*>.*?</script>", "", content, flags=re.I | re.S)

    alternates = EQUIVALENTS.get(rel, {})
    head_lines = [f'<link rel="canonical" href="{canonical}">']
    for lang, href in alternates.items():
        head_lines.append(f'<link rel="alternate" hreflang="{lang}" href="{SITE}{href}">')
    if alternates:
        head_lines.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{alternates.get("en", alternates.get("fr"))}">')
    escaped_title = html.escape(title, quote=True)
    escaped_desc = html.escape(description, quote=True)
    head_lines.extend([
        f'<meta property="og:title" content="{escaped_title}">',
        f'<meta property="og:description" content="{escaped_desc}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{image}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{escaped_title}">',
        f'<meta name="twitter:description" content="{escaped_desc}">',
        f'<meta name="twitter:image" content="{image}">',
    ])
    schemas = schema_for(rel, title, description, image)
    for schema in schemas:
        head_lines.append('<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + "</script>")
    insertion = "\n" + "\n".join(head_lines) + "\n"
    content = re.sub(r"</head>", insertion + "</head>", content, count=1, flags=re.I)

    # Safe image defaults: retain explicit author choices, eager-load the first image, lazy-load the rest.
    img_index = 0
    def improve_img(match: re.Match[str]) -> str:
        nonlocal img_index
        tag = match.group(0)
        src = meta_value(tag, r"\bsrc=[\"']([^\"']+)[\"']")
        if src:
            repaired_src = repair_image_src(src, path)
            if repaired_src != src:
                tag = re.sub(r"(\bsrc=[\"'])[^\"']+([\"'])", rf"\g<1>{repaired_src}\g<2>", tag, count=1, flags=re.I)
                src = repaired_src
        if not re.search(r"\balt\s*=", tag, re.I):
            fallback = title.split("|")[0].strip()
            tag = tag[:-1] + f' alt="{html.escape(fallback, quote=True)}">'
        if not re.search(r"\bdecoding\s*=", tag, re.I):
            tag = tag[:-1] + ' decoding="async">'
        if not re.search(r"\bloading\s*=", tag, re.I):
            mode = "eager" if img_index == 0 else "lazy"
            tag = tag[:-1] + f' loading="{mode}">'
        if src and not re.search(r"\bwidth\s*=|\bheight\s*=", tag, re.I):
            dimensions = image_size(src, path)
            if dimensions:
                tag = tag[:-1] + f' width="{dimensions[0]}" height="{dimensions[1]}">'
        img_index += 1
        return tag
    content = re.sub(r"<img\b[^>]*>", improve_img, content, flags=re.I)
    if rel == "index.html":
        # These tags contain a literal '>' in their onerror fallback, which the simple
        # tag matcher intentionally does not consume. They are below the hero/LCP area.
        content = re.sub(r"<img\s+src=", "<img loading='lazy' decoding='async' src=", content, flags=re.I)
        def add_home_dimensions(match: re.Match[str]) -> str:
            tag, src = match.group(0), match.group(1)
            dimensions = image_size(src, path)
            return tag[:-1] + (f" width='{dimensions[0]}' height='{dimensions[1]}'>" if dimensions else ">")
        content = re.sub(r"<img\s+loading='lazy'\s+decoding='async'\s+src='([^']+)'[^>]*>", add_home_dimensions, content, flags=re.I)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    for page in sorted(ROOT.rglob("*.html")):
        if ".git" not in page.parts:
            normalize_page(page)


if __name__ == "__main__":
    main()
