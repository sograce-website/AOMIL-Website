"""Apply the English-only on-page SEO improvements approved in September 2026.

The script deliberately touches root-level English HTML pages only. French and
Spanish files, canonical URLs, hreflang declarations, and redirect behavior are
left intact.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://aomil.com"


# title, description, H1. These assignments give every important English URL a
# distinct search intent rather than repeating the broad "Christmas decorations"
# theme across the catalog.
PAGE_META: dict[str, tuple[str, str, str]] = {
    "index.html": (
        "Christmas Decorations Manufacturer & Wholesale Supplier | AOMIL",
        "Explore AOMIL Christmas decorations, lighted lanterns, tree toppers and holiday projectors for wholesale, OEM and private-label seasonal programs.",
        "Christmas Decorations Manufacturer & Wholesale Supplier",
    ),
    "about.html": (
        "About AOMIL | Seasonal Decoration Supplier",
        "Learn about AOMIL, a commercial supplier of Christmas and Halloween decorations for importers, wholesalers, retailers and e-commerce sellers.",
        "About AOMIL Holiday Decorations",
    ),
    "contact.html": (
        "Contact AOMIL | Christmas Decoration Supplier",
        "Contact AOMIL about wholesale Christmas decorations, seasonal product sourcing, private-label packaging and OEM or ODM project requirements.",
        "Contact AOMIL About Your Seasonal Product Project",
    ),
    "factory.html": (
        "Christmas Decoration Factory & OEM Production | AOMIL",
        "Review AOMIL's documented production process and quality-control support for OEM Christmas and Halloween decoration programs.",
        "Christmas Decoration Factory & Production Process",
    ),
    "faq.html": (
        "Wholesale Christmas Decorations FAQ | AOMIL",
        "Answers for seasonal decoration buyers about wholesale inquiries, OEM packaging, samples, order quantities, labels and export cartons.",
        "Wholesale Seasonal Decoration Buyer FAQ",
    ),
    "oem-odm.html": (
        "OEM & ODM Christmas Decorations Service | AOMIL",
        "Discuss custom Christmas decorations, private-label presentation and OEM or ODM seasonal product development with AOMIL.",
        "OEM & ODM Christmas Decoration Service",
    ),
    "oem-service.html": (
        "OEM Christmas Decorations & Private Label Service | AOMIL",
        "AOMIL supports OEM Christmas decorations, seasonal product development, custom packaging and private-label programs for commercial buyers.",
        "OEM Christmas Decorations & Private Label Service",
    ),
    "packaging.html": (
        "Custom Christmas Decoration Packaging & Labels | AOMIL",
        "Explore custom boxes, labels, shipping cartons and Amazon FBA preparation for wholesale Christmas and Halloween decoration programs.",
        "Custom Packaging for Seasonal Decorations",
    ),
    "snow-globe.html": (
        "Wholesale Christmas Snow Globes & Lanterns | AOMIL",
        "Browse lighted Christmas snow globes, water lanterns and candle lantern designs supplied for wholesale and private-label seasonal collections.",
        "Wholesale Christmas Snow Globes & Lanterns",
    ),
    "snow-globe-lanterns.html": (
        "Lighted Christmas Lantern Decorations | AOMIL",
        "Explore lighted Christmas lantern decorations with snow-globe scenes, warm LED light and glitter effects for seasonal retail collections.",
        "Lighted Christmas Lantern Decorations",
    ),
    "christmas-tree.html": (
        "Christmas Tree Snow Globes & Water Lanterns | AOMIL",
        "Browse lighted Christmas tree-shaped snow globes and water lanterns with angel, reindeer and snowman scenes for wholesale seasonal collections.",
        "Christmas Tree Snow Globes & Water Lanterns",
    ),
    "tree-topper.html": (
        "Christmas Tree Topper Manufacturer & Supplier | AOMIL",
        "Browse projection tree toppers in star, snowflake and Santa designs for wholesale, OEM and private-label Christmas collections.",
        "Christmas Tree Toppers for Wholesale Programs",
    ),
    "tree-toppers.html": (
        "Decorative & Projection Christmas Tree Toppers | AOMIL",
        "Compare angel, glitter bow and projection Christmas tree topper styles for retail ranges and custom seasonal decoration programs.",
        "Decorative & Projection Christmas Tree Toppers",
    ),
    "projector.html": (
        "Christmas Light Projector Manufacturer & Supplier | AOMIL",
        "Source dual-lens Christmas light projectors for outdoor holiday displays, wholesale programs and private-label seasonal collections.",
        "Christmas Light Projectors for Wholesale & OEM",
    ),
    "projectors.html": (
        "Holiday Projector Lights Manufacturer & Supplier | AOMIL",
        "AOMIL holiday projector lights support Christmas and Halloween displays with changeable slides, water-ripple effects and outdoor use.",
        "Holiday Projector Lights",
    ),
    "halloween.html": (
        "Wholesale Halloween Decorations & Lanterns | AOMIL",
        "Browse flameless Halloween candles and snow globe lanterns with pumpkin, skeleton and haunted-house scenes for seasonal buyers.",
        "Wholesale Halloween Decorations",
    ),
}


PRODUCTS: dict[str, tuple[str, str, str, str]] = {
    # file: (SEO product name, category URL, category anchor, verified descriptor)
    "window-lantern.html": ("Christmas Window Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a lighted window-shaped Christmas scene"),
    "ski-candle-lantern.html": ("Skiing Christmas Candle Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a candle-shaped lantern with a skiing Christmas scene"),
    "santa-candle-lantern.html": ("Santa Christmas Candle Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a candle-shaped lantern with a Santa Christmas scene"),
    "new-santa-candle-lantern.html": ("Santa Christmas Candle Lantern Design", "/snow-globe.html", "Christmas snow globes and lanterns", "a Santa-themed candle lantern design"),
    "snowman-candle-lantern.html": ("Snowman Christmas Candle Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a candle-shaped lantern with a snowman scene"),
    "reindeer-christmas-tree.html": ("Flying Reindeer Christmas Tree Snow Globe", "/christmas-tree.html", "Christmas Tree Snow Globes & Water Lanterns", "a tree-shaped snow globe with a flying reindeer scene"),
    "snowman-christmas-tree.html": ("Snowman Christmas Tree Snow Globe", "/christmas-tree.html", "Christmas Tree Snow Globes & Water Lanterns", "a tree-shaped snow globe with a snowman scene"),
    "angel-christmas-tree.html": ("Angel Christmas Tree Snow Globe", "/christmas-tree.html", "Christmas Tree Snow Globes & Water Lanterns", "a tree-shaped snow globe with an angel scene"),
    "oval-fireplace-lantern.html": ("Oval Fireplace Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "an oval lantern with a fireplace Christmas scene"),
    "oval-reindeer-lantern.html": ("Oval Flying Reindeer Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "an oval lantern with a flying reindeer scene"),
    "long-santa-lantern.html": ("Long Santa Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a long-format lantern with a Santa Christmas scene"),
    "classic-angel-lantern.html": ("Classic Angel Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "an angel-themed Christmas lantern"),
    "church-nativity-lantern.html": ("Church Nativity Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a church Nativity Christmas lantern"),
    "angel-lantern.html": ("Angel Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "an angel-themed snow globe lantern"),
    "big-ben-lantern.html": ("Big Ben Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a London Big Ben themed Christmas lantern"),
    "flying-reindeer-lantern.html": ("Flying Reindeer Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a Christmas lantern with a flying Santa and reindeer scene"),
    "nativity-lantern.html": ("Nativity Christmas Snow Globe Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a religious Nativity lantern with the Holy Family scene"),
    "telephone-booth-lantern.html": ("London Telephone Booth Christmas Lantern", "/snow-globe.html", "Christmas snow globes and lanterns", "a London telephone-booth themed lighted lantern"),
    "holiday-projector.html": ("2-in-1 Outdoor Christmas & Halloween Projector", "/projector.html", "Christmas light projectors", "a dual-lens LED projector with changeable slides and a water-ripple effect"),
    "dual-lens-projector.html": ("Dual-Lens Outdoor Christmas Light Projector", "/projector.html", "Christmas light projectors", "a dual-lens holiday projector for Christmas and Halloween themes"),
    "gold-angel-tree-topper.html": ("Gold Angel Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a gold glitter angel tree topper"),
    "silver-angel-tree-topper.html": ("Silver Angel Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a silver glitter angel tree topper"),
    "red-bow-tree-topper.html": ("Red Glitter Bow Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a red glitter bow tree topper"),
    "santa-tree-topper.html": ("Santa Projection Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a Christmas tree topper with a Santa projection design"),
    "snowflake-tree-topper.html": ("Snowflake Projection Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a Christmas tree topper with a snowflake projection design"),
    "star-tree-topper.html": ("Star Projection Christmas Tree Topper", "/tree-topper.html", "Christmas tree toppers", "a Christmas tree topper with a star projection design"),
    "green-halloween-candle.html": ("Green Halloween Flameless Candle", "/halloween.html", "wholesale Halloween decorations", "a green flameless candle for Halloween displays"),
    "orange-halloween-candle.html": ("Orange Halloween Flameless Candle", "/halloween.html", "wholesale Halloween decorations", "an orange flameless candle for Halloween displays"),
    "pink-halloween-candle.html": ("Pink Halloween Flameless Candle", "/halloween.html", "wholesale Halloween decorations", "a pink flameless candle for Halloween displays"),
    "single-skeleton-lantern.html": ("Single Skeleton Halloween Snow Globe Lantern", "/halloween.html", "wholesale Halloween decorations", "a Halloween lantern with a single-skeleton scene"),
    "double-skeleton-lantern.html": ("Double Skeleton Halloween Snow Globe Lantern", "/halloween.html", "wholesale Halloween decorations", "a Halloween lantern with a two-skeleton scene"),
    "haunted-house-lantern.html": ("Haunted House Halloween Snow Globe Lantern", "/halloween.html", "wholesale Halloween decorations", "a Halloween lantern with a haunted-house scene"),
    "pumpkin-lantern.html": ("Pumpkin Halloween Snow Globe Lantern", "/halloween.html", "wholesale Halloween decorations", "a Halloween lantern with a pumpkin scene"),
    "skeleton-lantern.html": ("Skeleton Halloween Snow Globe Lantern", "/halloween.html", "wholesale Halloween decorations", "a lighted Halloween lantern with a skeleton scene"),
}


RELATED: dict[str, list[str]] = {
    "/snow-globe.html": ["window-lantern.html", "nativity-lantern.html", "oval-reindeer-lantern.html"],
    "/christmas-tree.html": ["angel-christmas-tree.html", "reindeer-christmas-tree.html", "snowman-christmas-tree.html"],
    "/tree-topper.html": ["star-tree-topper.html", "snowflake-tree-topper.html", "santa-tree-topper.html"],
    "/projector.html": ["dual-lens-projector.html", "holiday-projector.html"],
    "/halloween.html": ["pumpkin-lantern.html", "haunted-house-lantern.html", "orange-halloween-candle.html"],
}


def replace_once(content: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.I | re.S)
    if count != 1:
        raise RuntimeError(f"Expected one match for {pattern!r}, found {count}")
    return updated


def repair_section_placement(content: str) -> str:
    """Move SEO sections accidentally nested in a footer by an interrupted run."""
    pattern = r'(<footer[^>]*>)(.*?)<section class="section (seo-(?:copy|links))">(.*?)</section></footer>'
    return re.sub(pattern, r'<section class="section \3">\4</section>\1\2</footer>', content, flags=re.I | re.S)


def update_meta(content: str, title: str, description: str) -> str:
    escaped_title = html.escape(title, quote=True)
    escaped_desc = html.escape(description, quote=True)
    content = replace_once(content, r"<title[^>]*>.*?</title>", f"<title>{escaped_title}</title>")
    content = replace_once(content, r"<meta\s+name=['\"]description['\"]\s+content=['\"].*?['\"]\s*/?>", f'<meta name="description" content="{escaped_desc}">')
    for key, value in (
        ("og:title", escaped_title), ("og:description", escaped_desc),
        ("twitter:title", escaped_title), ("twitter:description", escaped_desc),
    ):
        attr = "property" if key.startswith("og:") else "name"
        content = replace_once(content, rf"<meta\s+{attr}=['\"]{re.escape(key)}['\"]\s+content=['\"].*?['\"]\s*/?>", f'<meta {attr}="{key}" content="{value}">')
    return content


def image_alts(content: str, name: str) -> str:
    index = 0
    labels = ("front view", "detail view", "side view", "display view", "product detail", "seasonal scene", "alternate view", "collection image")

    def improve(match: re.Match[str]) -> str:
        nonlocal index
        tag = match.group(0)
        label = name if index == 0 else f"{name} - {labels[(index - 1) % len(labels)]}"
        escaped = html.escape(label, quote=True)
        if re.search(r"\balt\s*=", tag, re.I):
            tag = re.sub(r"\balt=(['\"]).*?\1", f'alt="{escaped}"', tag, count=1, flags=re.I | re.S)
        else:
            tag = tag[:-1] + f' alt="{escaped}">'
        index += 1
        return tag

    return re.sub(r"<img\b[^>]*>", improve, content, flags=re.I)


def contextual_card_alts(content: str) -> str:
    """Use the visible card heading as the image alt on collection grids."""
    def improve(match: re.Match[str]) -> str:
        block = match.group(0)
        heading_match = re.search(r"<h3[^>]*>(.*?)</h3>", block, re.I | re.S)
        if not heading_match:
            return block
        heading = re.sub(r"<[^>]+>", "", heading_match.group(1)).strip()
        return re.sub(
            r"(<img\b[^>]*?)\balt=(['\"]).*?\2",
            lambda image: image.group(1) + f'alt="{html.escape(heading, quote=True)}"',
            block,
            count=1,
            flags=re.I | re.S,
        )
    return re.sub(r"<article\b.*?</article>", improve, content, flags=re.I | re.S)


def product_schema(content: str, filename: str, name: str, description: str, category_url: str, category_anchor: str) -> str:
    scripts = list(re.finditer(r"<script\s+type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>", content, re.I | re.S))
    if not scripts:
        raise RuntimeError(f"No JSON-LD in {filename}")
    schema_match = scripts[-1]
    data = json.loads(schema_match.group(1))
    graph = data.setdefault("@graph", [])
    url = SITE + "/" + filename
    breadcrumb = next((node for node in graph if node.get("@type") == "BreadcrumbList"), None)
    if breadcrumb is None:
        breadcrumb = {"@type": "BreadcrumbList"}
        graph.insert(0, breadcrumb)
    category_label = category_anchor if category_url == "/christmas-tree.html" else category_anchor.title()
    breadcrumb["itemListElement"] = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": category_label, "item": SITE + category_url},
        {"@type": "ListItem", "position": 3, "name": name, "item": url},
    ]
    product = next((node for node in graph if node.get("@type") == "Product"), None)
    if product is None:
        image_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', content, re.I)
        product = {"@type": "Product", "brand": {"@type": "Brand", "name": "AOMIL"}}
        if image_match:
            product["image"] = image_match.group(1)
        graph.append(product)
    product.update({"name": name, "description": description, "url": url, "category": category_anchor})
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return content[:schema_match.start()] + f'<script type="application/ld+json">{encoded}</script>' + content[schema_match.end():]


def related_section(filename: str, category_url: str, category_anchor: str) -> str:
    links = []
    for related in RELATED[category_url]:
        if related == filename:
            continue
        related_name = PRODUCTS[related][0]
        links.append(f'<li><a href="/{related}">{html.escape(related_name)}</a></li>')
    return (
        '<section class="section seo-links"><h2>Explore More Seasonal Products</h2>'
        f'<p>Return to the <a href="{category_url}">{html.escape(category_anchor)}</a> collection or compare related designs:</p>'
        f'<ul>{"".join(links[:3])}</ul>'
        '<p>Commercial buyers can also review our <a href="/oem-service.html">OEM and private-label service</a> or '
        '<a href="/contact.html">request product details</a>.</p></section>'
    )


def optimize_product(path: Path, product: tuple[str, str, str, str]) -> None:
    filename = path.name
    name, category_url, category_anchor, descriptor = product
    if len(name) > 42:
        title = f"{name} | AOMIL"
    elif category_url == "/halloween.html":
        title = f"{name} Wholesale | AOMIL"
    elif category_url == "/projector.html":
        title = f"{name} Supplier | AOMIL"
    else:
        title = f"{name} Wholesale Supplier | AOMIL"
    description = f"Wholesale {name} from AOMIL for seasonal retail and private-label ranges. View verified images and request product details."
    content = repair_section_placement(path.read_text(encoding="utf-8"))
    content = content.replace('<a href="/christmas-tree.html">Christmas Trees</a>', '<a href="/christmas-tree.html">Tree Snow Globes</a>')
    content = content.replace("<a href='/christmas-tree.html'>Christmas Trees</a>", "<a href='/christmas-tree.html'>Tree Snow Globes</a>")
    content = update_meta(content, title, description)
    content = replace_once(content, r"<h1[^>]*>.*?</h1>", f"<h1>{html.escape(name)}</h1>")
    # Replace the short hero statement while retaining all verified media/specification content.
    hero_intro = f"Explore {html.escape(descriptor)} for wholesale seasonal ranges. AOMIL supports commercial inquiries and private-label project discussions."
    content = replace_once(content, r"(<section\s+class=['\"][^'\"]*hero[^'\"]*['\"][^>]*>.*?<h1[^>]*>.*?</h1>)\s*<p>.*?</p>", rf"\1<p>{hero_intro}</p>")
    if category_url == "/christmas-tree.html":
        content = content.replace("<span class='tag'>Christmas Tree</span>", "<span class='tag'>Tree Snow Globe</span>")
    content = image_alts(content, name)
    content = product_schema(content, filename, name, description, category_url, category_anchor)
    if "seo-links" not in content:
        content = replace_once(content, r"<footer", related_section(filename, category_url, category_anchor) + "<footer")
    path.write_text(content, encoding="utf-8", newline="\n")


CATEGORY_COPY: dict[str, str] = {
    "snow-globe.html": '<section class="section seo-copy"><h2>Lighted Christmas Decorations for Seasonal Buyers</h2><p>This collection brings together Christmas snow globes, water lanterns and candle-shaped lanterns for importers, wholesalers, retailers and e-commerce ranges. Browse individual pages for verified imagery, then contact AOMIL to discuss the designs that fit your program.</p><p>Explore <a href="/window-lantern.html">Christmas window lantern decorations</a>, <a href="/nativity-lantern.html">Nativity Christmas lanterns</a> and <a href="/christmas-tree.html">tree-shaped Christmas snow globes</a>.</p></section>',
    "christmas-tree.html": '<section class="section seo-copy"><h2>Christmas Tree-Shaped Water Lantern Collection</h2><p>These are decorative snow globes and water lanterns shaped like Christmas trees—not artificial or natural Christmas trees. Angel, reindeer and snowman scenes make them suitable for commercial buyers building coordinated Christmas gift, tabletop and lighted decoration assortments.</p><p>Compare the <a href="/angel-christmas-tree.html">angel tree-shaped snow globe</a>, <a href="/reindeer-christmas-tree.html">flying reindeer tree-shaped snow globe</a> and <a href="/snowman-christmas-tree.html">snowman tree-shaped snow globe</a>, or browse our <a href="/snow-globe.html">wider wholesale Christmas snow globe collection</a>.</p></section>',
    "tree-topper.html": '<section class="section seo-copy"><h2>Projection Christmas Tree Topper Designs</h2><p>AOMIL offers star, snowflake and Santa projection tree toppers for wholesale seasonal ranges and private-label discussions. Each product page contains the verified gallery and inquiry route for that design.</p><p>Compare <a href="/star-tree-topper.html">star projection toppers</a>, <a href="/snowflake-tree-topper.html">snowflake projection toppers</a> and <a href="/santa-tree-topper.html">Santa projection toppers</a>. For decorative angel and bow styles, see the <a href="/tree-toppers.html">decorative tree topper guide</a>.</p></section>',
    "projector.html": '<section class="section seo-copy"><h2>Outdoor Christmas Projector Options</h2><p>The AOMIL projector range covers dual-lens holiday lighting for Christmas and Halloween displays. Review the verified product pages for available imagery and documented features, then send an inquiry for current commercial details.</p><p>View the <a href="/dual-lens-projector.html">dual-lens outdoor Christmas projector</a> or the <a href="/holiday-projector.html">2-in-1 Christmas and Halloween projector</a>. Buyers planning custom seasonal ranges can also review our <a href="/oem-service.html">OEM service</a>.</p></section>',
    "halloween.html": '<section class="section seo-copy"><h2>Halloween Lanterns and Flameless Candles</h2><p>Build a Halloween assortment from snow globe lanterns and colored flameless candles shown in the verified AOMIL product catalog. Product pages link to available images and direct commercial inquiry options.</p><p>Browse <a href="/pumpkin-lantern.html">pumpkin lanterns</a>, <a href="/haunted-house-lantern.html">haunted-house lanterns</a>, <a href="/skeleton-lantern.html">skeleton lanterns</a> and <a href="/orange-halloween-candle.html">Halloween flameless candles</a>.</p></section>',
}


def optimize_standard(path: Path, meta: tuple[str, str, str]) -> None:
    title, description, h1 = meta
    content = repair_section_placement(path.read_text(encoding="utf-8"))
    content = update_meta(content, title, description)
    content = content.replace('<a href="/christmas-tree.html">Christmas Trees</a>', '<a href="/christmas-tree.html">Tree Snow Globes</a>')
    content = content.replace("<a href='/christmas-tree.html'>Christmas Trees</a>", "<a href='/christmas-tree.html'>Tree Snow Globes</a>")
    content = replace_once(content, r"<h1[^>]*>.*?</h1>", f"<h1>{html.escape(h1)}</h1>")
    content = image_alts(content, h1)
    content = contextual_card_alts(content)
    if path.name == "index.html":
        content = replace_once(
            content,
            r"(<section\s+class=['\"]hero['\"][^>]*>.*?<h1[^>]*>.*?</h1>)\s*<p>.*?</p>",
            r"\1<p>AOMIL supplies Christmas decorations, lighted snow globe lanterns, projection tree toppers and holiday projectors for importers, wholesalers, retailers and e-commerce sellers. Explore wholesale products or discuss OEM and private-label requirements.</p>",
        )
        content = content.replace("<h2>Product Categories</h2>", "<h2>Wholesale Christmas &amp; Seasonal Product Categories</h2>", 1)
        content = content.replace("<h3>Christmas Trees</h3>", "<h3>Christmas Tree-Shaped Snow Globes</h3>", 1)
        content = content.replace("<h3>Tree-Shaped Snow Globes</h3>", "<h3>Christmas Tree-Shaped Snow Globes</h3>", 1)
        content = content.replace('alt="Christmas Trees"', 'alt="Tree-Shaped Christmas Snow Globes"', 1)
        content = content.replace('>Christmas Trees</div>\'"><h3>Christmas Tree-Shaped Snow Globes</h3>', '>Tree Snow Globes</div>\'"><h3>Christmas Tree-Shaped Snow Globes</h3>', 1)
        content = content.replace("<a class='btn' href='/christmas-tree.html'>View Collection</a>", "<a class='btn' href='/christmas-tree.html'>View Tree Snow Globes</a>", 1)
    elif path.name in {"snow-globe.html", "christmas-tree.html", "tree-topper.html", "projector.html", "halloween.html", "snow-globe-lanterns.html", "tree-toppers.html"}:
        content = replace_once(
            content,
            r"(<section\s+class=['\"][^'\"]*hero[^'\"]*['\"][^>]*>.*?<h1[^>]*>.*?</h1>)\s*<p>.*?</p>",
            rf"\1<p>{html.escape(description)}</p>",
        )
    if path.name == "christmas-tree.html":
        content = content.replace("<h2>Christmas Tree Products</h2>", "<h2>Christmas Tree Snow Globes</h2>", 1)
        content = content.replace("<p>Christmas Tree for wholesale, OEM and Amazon sellers.</p>", "<p>Tree-shaped snow globe and water lantern for wholesale seasonal collections.</p>")
        content = content.replace("<span class='tag'>Christmas Tree</span>", "<span class='tag'>Tree Snow Globe</span>")
    if path.name == "christmas-tree.html" and "seo-copy" in content:
        content = replace_once(content, r'<section class="section seo-copy">.*?</section>', CATEGORY_COPY[path.name])
    elif path.name in CATEGORY_COPY and "seo-copy" not in content:
        content = replace_once(content, r"<footer", CATEGORY_COPY[path.name] + "<footer")
    # Keep JSON-LD descriptions in sync with visible metadata. Product JSON-LD is
    # handled separately above.
    for schema_match in reversed(list(re.finditer(r"<script\s+type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>", content, re.I | re.S))):
        data = json.loads(schema_match.group(1))
        for node in data.get("@graph", []):
            if node.get("@type") == "BreadcrumbList":
                node["itemListElement"][-1]["name"] = h1
            if path.name == "index.html" and node.get("@type") == "Organization":
                node["description"] = description
                node["knowsAbout"] = ["Christmas decorations", "Christmas snow globe lanterns", "Christmas tree toppers", "holiday projectors", "Halloween decorations"]
            if path.name == "index.html" and node.get("@type") == "WebSite":
                node["description"] = "AOMIL wholesale Christmas and Halloween decoration catalog and OEM service website."
        if path.name == "christmas-tree.html" and not any(node.get("@type") == "CollectionPage" for node in data.get("@graph", [])):
            data.setdefault("@graph", []).append({
                "@type": "CollectionPage",
                "name": h1,
                "description": description,
                "url": SITE + "/christmas-tree.html",
                "isPartOf": {"@id": SITE + "/#website"},
                "about": [
                    {"@type": "Thing", "name": "Christmas tree snow globes"},
                    {"@type": "Thing", "name": "Christmas tree water lanterns"},
                ],
            })
        encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        content = content[:schema_match.start()] + f'<script type="application/ld+json">{encoded}</script>' + content[schema_match.end():]
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    for filename, meta in PAGE_META.items():
        optimize_standard(ROOT / filename, meta)
    for filename, product in PRODUCTS.items():
        optimize_product(ROOT / filename, product)


if __name__ == "__main__":
    main()
