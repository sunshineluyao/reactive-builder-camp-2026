#!/usr/bin/env python3
"""Preview standalone SVG README covers with Chromium. See --help for usage."""

import argparse
import itertools
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit


def validate_svg(path):
    root = ET.parse(path).getroot()
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError(f"{path}: expected an SVG document")
    bounds = [float(v) for v in re.split(r"[\s,]+", root.get("viewBox", "").strip()) if v]
    if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds) or min(bounds[2:]) <= 0:
        raise ValueError(f"{path}: supply a finite, positive viewBox")
    for tag in ("title", "desc"):
        element = root.find("{*}" + tag)
        if element is None or not "".join(element.itertext()).strip():
            raise ValueError(f"{path}: missing {tag}")
    ids = set()
    refs = set()
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in {"foreignObject", "script", "iframe", "image", "feImage"}:
            raise ValueError(f"{path}: {tag} is outside the standalone vector profile")
        ident = node.get("id")
        if ident:
            if ident in ids:
                raise ValueError(f"{path}: duplicate id {ident}")
            ids.add(ident)
        styles = [node.text or ""] if tag == "style" else []
        for key, value in node.attrib.items():
            attr = key.rsplit("}", 1)[-1]
            if attr.startswith("on"):
                raise ValueError(f"{path}: event handler {attr}")
            if attr == "href":
                if not value.startswith("#"):
                    raise ValueError(f"{path}: non-local href {value}")
                refs.add(value[1:])
            styles.append(value)
        for style in styles:
            if "@import" in style.lower():
                raise ValueError(f"{path}: external stylesheet import")
            for ref in re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", style, re.I):
                ref = ref.strip()
                if not ref.startswith("#"):
                    raise ValueError(f"{path}: non-local resource {ref}")
                refs.add(ref[1:])
    unknown = refs - ids
    if unknown:
        raise ValueError(f"{path}: missing referenced ids {sorted(unknown)}")


METRICS = """() => {
  const svg = document.documentElement;
  const frame = svg.getBoundingClientRect();
  const labels = [];
  for (const text of svg.querySelectorAll('text')) {
    if (text.closest('defs, symbol, marker, pattern, clipPath, mask')) continue;
    const css = getComputedStyle(text);
    if (css.visibility === 'hidden' || css.display === 'none') continue;
    const box = text.getBoundingClientRect();
    if (!box.width || !box.height) continue;
    const matrix = text.getScreenCTM();
    labels.push({text: text.textContent.trim(), x: box.x - frame.x, y: box.y - frame.y,
      w: box.width, h: box.height, size: parseFloat(css.fontSize) * Math.hypot(matrix.c, matrix.d)});
  }
  return {width: frame.width, height: frame.height, labels};
}"""


def inspect(metrics, min_px):
    issues = []
    labels = metrics["labels"]
    for label in labels:
        if label["size"] + 0.05 < min_px:
            issues.append(f"small ({label['size']:.1f}px) {label['text']}")
        if (min(label["x"], label["y"]) < -1 or
                label["x"] + label["w"] > metrics["width"] + 1 or
                label["y"] + label["h"] > metrics["height"] + 1):
            issues.append(f"outside canvas: {label['text']}")
    for a, b in itertools.combinations(labels, 2):
        dx = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
        dy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
        if dx > 2 and dy > min(a["h"], b["h"]) * 0.35:
            issues.append(f"inspect text overlap: {a['text']} / {b['text']}")
    return issues


def render(args):
    from playwright.sync_api import Error, sync_playwright

    wide = args.desktop.resolve()
    narrow = args.mobile.resolve() if args.mobile else None
    args.out.mkdir(parents=True, exist_ok=True)
    for asset in {wide, narrow} - {None}:
        validate_svg(asset)
    source = (f'<source media="(max-width: {args.breakpoint}px)" '
              f'srcset="{escape(narrow.as_uri(), quote=True)}">') if narrow else ""
    reports = {}
    with TemporaryDirectory() as tmp, sync_playwright() as playwright:
        candidates = [args.browser] if args.browser else [None]
        if not args.browser:
            candidates.extend(path for name in ("chromium", "google-chrome") if (path := shutil.which(name)))
        for executable in candidates:
            try:
                browser = playwright.chromium.launch(executable_path=executable)
                break
            except Error as error:
                last_error = error
        else:
            raise ValueError("Could not launch Chromium. Install a Playwright browser with "
                             "'python -m playwright install chromium' or pass --browser with "
                             "a working executable.") from last_error
        def offline(route):
            if urlsplit(route.request.url).scheme in {"http", "https"}:
                route.abort()
            else:
                route.continue_()

        measure = browser.new_page(device_scale_factor=1)
        measure.route("**/*", offline)
        for name, width in (("desktop", args.wide_width), ("phone", args.phone_width)):
            viewport = width + 32
            page = browser.new_page(viewport={"width": viewport, "height": 1200}, device_scale_factor=1,
                                    is_mobile=name == "phone", has_touch=name == "phone")
            page.route("**/*", offline)
            for theme, color in (("light", "#ffffff"), ("dark", "#0d1117")):
                wrapper = Path(tmp) / f"{name}-{theme}.html"
                wrapper.write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>*{{box-sizing:border-box}}body{{margin:0;background:{color};padding:16px}}
main{{width:100%}}img{{width:100%;height:auto;display:block}}</style>
<main><picture>{source}<img src="{escape(wide.as_uri(), quote=True)}" alt="Cover preview"></picture></main>""",
                                   encoding="utf-8")
                page.emulate_media(color_scheme=theme)
                page.goto(wrapper.as_uri())
                img = page.locator("img")
                img.evaluate("img => img.decode()")
                src = Path(unquote(urlsplit(img.evaluate("img => img.currentSrc")).path))
                expected = narrow if narrow and viewport <= args.breakpoint else wide
                if src != expected:
                    raise ValueError(f"{name}: selected {src}, expected {expected}")
                image_width = img.bounding_box()["width"]
                if abs(image_width - width) > 1:
                    raise ValueError(f"{name}: unexpected image width {image_width}")
                page.locator("body").screenshot(path=args.out / f"{name}-{theme}.png")
            page.close()
            measure.goto(src.as_uri())
            measure.evaluate("""width => {
              const s = document.documentElement.style;
              s.setProperty('width', width + 'px', 'important');
              s.setProperty('height', 'auto', 'important');
            }""", width)
            measure.evaluate("document.fonts.ready")
            report = measure.evaluate(METRICS)
            report["file"] = src.name
            report["issues"] = inspect(report, args.min_px)
            reports[name] = report
        if args.export_wide:
            measure.goto(wide.as_uri())
            measure.evaluate("document.fonts.ready")
            args.export_wide.parent.mkdir(parents=True, exist_ok=True)
            measure.locator("svg").first.screenshot(path=args.export_wide, type="png")
        browser.close()
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("desktop", type=Path)
    parser.add_argument("--mobile", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--export-wide", type=Path, help="Also export the intrinsic-size desktop SVG as PNG")
    parser.add_argument("--browser", help="Chromium executable, or use the installed Playwright browser")
    parser.add_argument("--breakpoint", type=int, default=720, help="Viewport width for the narrow srcset")
    parser.add_argument("--wide-width", type=int, default=960, help="Desktop image width in CSS pixels")
    parser.add_argument("--phone-width", type=int, default=375, help="Phone image width in CSS pixels")
    parser.add_argument("--min-px", type=float, default=14, help="Report labels below this size")
    args = parser.parse_args()
    try:
        reports = render(args)
    except (ValueError, OSError, ET.ParseError, ImportError) as error:
        parser.exit(2, f"{error}\n")
    (args.out / "metrics.json").write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    for name, report in reports.items():
        print(f"{name}: {report['file']} at {report['width']:.0f}px, {len(report['labels'])} labels")
        for issue in report["issues"]:
            print(f"  {issue}")
    return int(any(report["issues"] for report in reports.values()))


if __name__ == "__main__":
    sys.exit(main())
