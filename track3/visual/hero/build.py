"""Rebuild the desktop and phone README covers in both languages. Run with Python 3 from any directory."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET


HERE = Path(__file__).resolve().parent
TRACK = HERE.parents[1]
PAPER = "#f8f5ff"
MUTED = "#c4c3df"
MINT = "#48efda"
VIOLET = "#c298ff"
GOLD = "#ffca69"
SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"
MONO = "ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
PARITY = 10_000
CUTOFF = 50
CONTROL = 9990  # Control transaction linked in track3/README.md.


def node(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k.replace("_", "-"): str(v) for k, v in attrs.items()})


def rect(parent, x, y, w, h, fill, **attrs):
    return node(parent, "rect", x=x, y=y, width=w, height=h, fill=fill, **attrs)


def path(parent, d, stroke, width=1, fill="none", **attrs):
    return node(parent, "path", d=d, stroke=stroke, stroke_width=width, fill=fill,
                stroke_linecap="round", stroke_linejoin="round", **attrs)


def text(parent, x, y, value, size, color=PAPER, weight=400, *, mono=False, anchor="start", space=0):
    el = node(parent, "text", x=x, y=y, fill=color, font_size=size, font_weight=weight,
              font_family=MONO if mono else SANS, text_anchor=anchor, letter_spacing=space)
    el.text = str(value)
    return el


def gradient(defs, ident, stops, x2="100%", y2="65%"):
    el = node(defs, "linearGradient", id=ident, x1="0%", y1="0%", x2=x2, y2=y2)
    for offset, color in stops:
        node(el, "stop", offset=offset, stop_color=color)


def light(defs, ident, color, opacity):
    el = node(defs, "radialGradient", id=ident)
    node(el, "stop", offset="0%", stop_color=color, stop_opacity=opacity)
    node(el, "stop", offset="100%", stop_color=color, stop_opacity=0)


def backdrop(svg, w, h, compact):
    defs = node(svg, "defs")
    gradient(defs, "field", [("0%", "#080915"), ("51%", "#180c2b"), ("100%", "#071e26")])
    gradient(defs, "origin", [("0%", "#10313a"), ("100%", "#101225")])
    gradient(defs, "gate", [("0%", "#34214f"), ("100%", "#19112e")])
    gradient(defs, "sink", [("0%", "#342736"), ("100%", "#191629")])
    gradient(defs, "review", [("0%", "#151a2a"), ("100%", "#151629")])
    gradient(defs, "metal", [("0%", "#52e6d7"), ("37%", "#225966"), ("74%", "#262249"), ("100%", "#b193ff")])
    gradient(defs, "coin", [("0%", "#24515a"), ("49%", "#0e2938"), ("100%", "#261c43")])
    gradient(defs, "spectrum", [("0%", MINT), ("51%", VIOLET), ("100%", GOLD)], y2="0%")
    light(defs, "orchid-light", "#8748ff", ".29")
    light(defs, "teal-light", "#17cbb9", ".11")
    light(defs, "gold-light", "#ffb939", ".28")
    grid = node(defs, "pattern", id="grid", width=34, height=34, patternUnits="userSpaceOnUse")
    path(grid, "M34 0 H0 V34", "#ab8bd2", 0.8, opacity=".12")
    hatch = node(defs, "pattern", id="tail-hatch", width=8, height=8, patternUnits="userSpaceOnUse")
    path(hatch, "M-2 2 L2 -2 M0 8 L8 0 M6 10 L10 6", VIOLET, 0.75, opacity=".28")
    rect(svg, 0, 0, w, h, "url(#field)")
    node(svg, "ellipse", cx=w * .86, cy=h * .21, rx=w * .44, ry=h * .48, fill="url(#orchid-light)")
    node(svg, "ellipse", cx=0, cy=h * .48, rx=w * .47, ry=h * .6, fill="url(#teal-light)")
    rect(svg, 0, 0, w, h, "url(#grid)")
    cx, cy, rx, ry = (w + 30, 94, 144, 68) if compact else (w - 60, 112, 240, 98)
    contours = node(svg, "g", transform=f"rotate(-19 {cx} {cy})", opacity=".14")
    for i in range(5):
        node(contours, "ellipse", cx=cx, cy=cy, rx=rx + i * 18, ry=ry + i * 11,
             fill="none", stroke=VIOLET, stroke_width=1)


def peg_illustration(svg, x, y, scale):
    """An engraved parity token, a reference orbit and a crossing diamond."""
    g = node(svg, "g", transform=f"translate({x} {y}) scale({scale})")
    node(g, "ellipse", cx=7, cy=5, rx=133, ry=77, fill="url(#orchid-light)")
    orbit = node(g, "g", transform="rotate(-22)")
    node(orbit, "ellipse", cx=0, cy=5, rx=104, ry=32, fill="none", stroke="#9a65ea", stroke_width=1.6)
    node(orbit, "ellipse", cx=0, cy=5, rx=120, ry=39, fill="none", stroke="#9272ce",
         stroke_width=1, stroke_dasharray="2 7", opacity=".7")
    coin = node(g, "g", transform="rotate(-18)")
    node(coin, "ellipse", cx=-10, cy=1, rx=47, ry=53, fill="#31264c", stroke="#ad7ef4", stroke_width=2)
    node(coin, "ellipse", cx=-15, cy=-3, rx=47, ry=53, fill="url(#metal)", stroke="#c7bcff", stroke_width=1.4)
    node(coin, "ellipse", cx=-20, cy=-6, rx=44, ry=52, fill="url(#coin)", stroke=MINT, stroke_width=2.1)
    node(coin, "ellipse", cx=-20, cy=-6, rx=37, ry=44, fill="none", stroke="#509795", stroke_width=1.1)
    path(coin, "M-45 -29 Q-34 -49 -15 -49 M1 29 Q7 24 12 14", MINT, 1.7)
    path(coin, "M-33 -11 H-6 M-33 1 H-6", MINT, 5.0)
    path(g, "M-96 40 C-62 55 9 33 73 -13", VIOLET, 2.5)
    path(g, "M43 3 Q62 -5 86 -24", GOLD, 1.8)
    node(g, "circle", cx=-95, cy=40, r=5, fill="#102c37", stroke=MINT, stroke_width=2.4)
    node(g, "circle", cx=88, cy=-25, r=23, fill="url(#gold-light)")
    marker(g, 88, -25, True, 9)
    path(g, "M93 -42 L98 -50 M102 -29 L111 -32", GOLD, 1.5)


def logo(parent, x, y, scale=1):
    g = node(parent, "g", transform=f"translate({x} {y}) scale({scale})")
    node(g, "circle", cx=18, cy=18, r=17, fill="#102c37", stroke=MINT, stroke_width=1.7)
    path(g, "M2 19 H10 L14 12 L19 26 L24 10 L27 19 H34", MINT, 2.5)
    node(g, "circle", cx=31, cy=6, r=3.7, fill=GOLD, stroke="#102633", stroke_width=1.5)


def brand(svg, x, y, compact):
    logo(svg, x, y - (27 if compact else 29), 0.87 if compact else 1)
    el = text(svg, x + (42 if compact else 50), y, "", 27 if compact else 31, weight=700, space=-0.7)
    node(el, "tspan").text = "Reactive "
    node(el, "tspan", fill=MINT).text = "PegPulse"


def panel(svg, x, y, w, h, gradient_id, stroke):
    rect(svg, x, y + 4, w, h, "#050916", rx=18, opacity=".6")
    rect(svg, x, y, w, h, "url(#" + gradient_id + ")", rx=18, stroke=stroke, stroke_width=1.6)
    if gradient_id != "review":
        color = {"origin": MINT, "gate": VIOLET, "sink": GOLD}[gradient_id]
        path(svg, f"M{x+23} {y+1} h{w * .23:.1f}", color, 2.6, opacity=".92")


def tag(svg, x, y, label, color, size=22):
    text(svg, x, y, label, size, color, 700, space=1.35)


def marker(svg, x, y, active, size=7):
    if active:
        path(svg, f"M{x} {y-size} l{size} {size} l{-size} {size} l{-size} {-size} z",
             GOLD, 1.6, GOLD)
    else:
        node(svg, "circle", cx=x, cy=y, r=size, fill="#172c38", stroke=MINT, stroke_width=2.7)


def scale_plot(svg, x, y, w, trigger, *, compact=False):
    """A shared basis-point axis. The two observations are separate samples."""
    right = x + w
    unit = w / 80
    threshold = x + unit * CUTOFF
    size = 20 if compact else 22
    rect(svg, threshold, y - 29, right - threshold, 48, "#51365d", rx=5, opacity=".56")
    rect(svg, threshold, y - 29, right - threshold, 48, "url(#tail-hatch)", rx=5)
    path(svg, f"M{x} {y} H{right}", "#a8b3d0", 2.1)
    path(svg, f"M{threshold} {y} H{x + abs(PARITY-trigger)*unit}", GOLD, 2.7)
    for bp in range(0, 81, 10):
        tick = x + bp * unit
        path(svg, f"M{tick} {y+2} v{7 if bp in (0, 80) else 5}", "#9baac7", 1.25)
    path(svg, f"M{threshold} {y-31} V{y+21}", VIOLET, 2, stroke_dasharray="3 4")
    for quote, active in ((CONTROL, False), (trigger, True)):
        bp = abs(PARITY - quote)
        dot = x + unit * bp
        if active:
            node(svg, "circle", cx=dot, cy=y, r=19, fill="url(#gold-light)")
        marker(svg, dot, y, active)
        text(svg, dot, y - 13, f"{bp} bp", size + 1, GOLD if active else MINT, 700, anchor="middle")
    text(svg, x, y + 42, "0", size, MUTED, anchor="middle")
    text(svg, right, y + 42, "80", size, MUTED, anchor="middle")
    text(svg, threshold, y + 42, "50 bp cutoff", size, VIOLET, 600, anchor="middle")


def arrow(svg, x, y, color, *, down=False, length=24):
    g = node(svg, "g", transform=f"translate({x} {y})" + (" rotate(90)" if down else ""))
    path(g, f"M1 0 H{length-3} m-6 -4 l6 4 l-6 4", color, 2.2)


def receipt_mark(parent, x, y):
    g = node(parent, "g", transform=f"translate({x} {y})", fill="none")
    path(g, "M2 1 H27 V31 L23 28 L19 31 L15 28 L11 31 L7 28 L2 31 Z", GOLD, 1.9)
    path(g, "M7 10 L11 14 L20 7 M8 21 H21", GOLD, 1.8)


def status_dot(svg, x, y):
    node(svg, "circle", cx=x, cy=y, r=6, fill="none", stroke=MINT, stroke_width=1.6)
    node(svg, "circle", cx=x, cy=y, r=2.3, fill=MINT)


def desktop(svg, trigger, log_index):
    backdrop(svg, 1280, 646, False)
    brand(svg, 48, 67, False)
    rect(svg, 800, 33, 432, 43, "#17162a", rx=21, stroke="#66547e")
    status_dot(svg, 825, 54)
    text(svg, 845, 62, "PUBLIC TESTNET", 22, MINT, 700, space=1.15)
    path(svg, "M1063 44 V64", "#685975")
    text(svg, 1080, 62, "27 NOV 2026", 22, MUTED, 600)
    peg_illustration(svg, 1105, 160, 1.10)
    el = text(svg, 46, 151, "Which quote triggered ", 61, weight=700, space=-2.3)
    node(el, "tspan", fill="#ffe4ae").text = "the alert?"
    text(svg, 49, 193, "Two simulated USDC/USDT quotes, measured against a 1:1 peg.", 25, MUTED)
    rect(svg, 49, 216, 82, 3.5, "url(#spectrum)", rx=1.75)

    panel(svg, 48, 247, 291, 261, "origin", "#298c88")
    panel(svg, 366, 247, 496, 261, "gate", "#9565d4")
    panel(svg, 889, 247, 343, 261, "sink", "#af8950")
    arrow(svg, 339, 391, MINT, length=27)
    arrow(svg, 862, 391, VIOLET, length=27)

    tag(svg, 73, 283, "ETHEREUM SEPOLIA", MINT)
    text(svg, 72, 326, "Publish quotes", 33, weight=650, space=-1.0)
    for quote, y, active in ((CONTROL, 378, False), (trigger, 431, True)):
        marker(svg, 84, y - 11, active, 7)
        text(svg, 100, y, f"{quote / PARITY:.4f}", 37, GOLD if active else PAPER, 650,
             mono=True, space=-1.6)
        text(svg, 319, y - 3, f"{(quote - PARITY) / 100:+.2f}%".replace("-", "−"), 22,
             MUTED, anchor="end")
    path(svg, "M74 454 H313", "#3e535f")
    text(svg, 73, 485, "PriceObserved", 22, MUTED, mono=True)

    tag(svg, 393, 283, "REACTIVE LASNA", VIOLET)
    text(svg, 392, 326, "Request a callback", 34, weight=650, space=-1.0)
    text(svg, 393, 358, "Only above 50 basis points from parity.", 22, MUTED)
    rect(svg, 389, 380, 450, 108, "#17132a", rx=10, stroke="#50346e")
    scale_plot(svg, 409, 428, 410, trigger)

    tag(svg, 915, 283, "BASE SEPOLIA", GOLD)
    text(svg, 914, 326, "Record one alert", 33, weight=650, space=-1.0)
    path(svg, "M919 347 H1197 L1205 355 V378 Q1193 385 1205 392 V429 H919 "
         "L910 420 V393 Q923 385 910 378 V355 Z", "#a67b42", 1.45, "#2b2130")
    path(svg, "M1143 351 V425", "#a48768", 1.25, stroke_dasharray="3 4")
    text(svg, 932, 385, f"{trigger / PARITY:.4f}", 38, GOLD, 650, mono=True, space=-1.6)
    text(svg, 932, 413, "PriceDeviation", 22, PAPER, 500, mono=True)
    node(svg, "circle", cx=1172, cy=388, r=21, fill="#3f3032", stroke=GOLD, stroke_width=1.8)
    node(svg, "circle", cx=1172, cy=388, r=16, fill="none", stroke="#ba954f", stroke_width=1)
    path(svg, "M1164 388 l6 6 11 -14", GOLD, 2.8)
    path(svg, "M916 454 H1205", "#534b59")
    text(svg, 915, 485, f"Source log #{log_index}", 22, MUTED, mono=True)

    panel(svg, 48, 536, 1184, 77, "review", "#42536b")
    text(svg, 74, 569, "OFF-CHAIN AI REVIEW", 22, MUTED, 700, space=1.1)
    text(svg, 73, 598, "Scoring deferred", 26, weight=650, space=-0.4)
    path(svg, "M372 553 V596", "#43536d")
    text(svg, 400, 584, "Matching USDC/USD and USDT/USD quotes were missing.", 24, PAPER)


def phone(svg, trigger, log_index):
    backdrop(svg, 440, 798, True)
    brand(svg, 24, 48, True)
    peg_illustration(svg, 362, 43, .49)
    status_dot(svg, 31, 84)
    text(svg, 47, 90, "PUBLIC TESTNET", 20, MINT, 700, space=1.0)
    text(svg, 250, 90, "27 NOV 2026", 20, MUTED, 600)
    text(svg, 23, 140, "Which quote", 42, weight=700, space=-1.5)
    el = text(svg, 23, 183, "triggered ", 42, weight=700, space=-1.5)
    node(el, "tspan", fill="#ffe4ae").text = "the alert?"
    rect(svg, 25, 202, 64, 3, "url(#spectrum)", rx=1.5)

    panel(svg, 24, 229, 392, 116, "origin", "#298c88")
    tag(svg, 43, 257, "ETHEREUM SEPOLIA", MINT, 20)
    text(svg, 43, 284, "Simulated USDC/USDT quotes", 20, PAPER, 550)
    for x, quote, active in ((53, CONTROL, False), (240, trigger, True)):
        marker(svg, x, 314, active, 6)
        text(svg, x + 16, 324, f"{quote / PARITY:.4f}", 29, GOLD if active else PAPER, 650,
             mono=True, space=-1.2)
    arrow(svg, 220, 345, MINT, down=True, length=20)

    panel(svg, 24, 365, 392, 180, "gate", "#9565d4")
    tag(svg, 43, 394, "REACTIVE LASNA", VIOLET, 20)
    text(svg, 42, 427, "Call back only above 50 bp", 26, weight=650, space=-0.7)
    scale_plot(svg, 55, 479, 326, trigger, compact=True)
    arrow(svg, 220, 545, VIOLET, down=True, length=20)

    panel(svg, 24, 565, 392, 106, "sink", "#af8950")
    tag(svg, 43, 595, "BASE SEPOLIA", GOLD, 20)
    text(svg, 43, 626, f"One alert for {trigger / PARITY:.4f}", 27, weight=650, space=-0.6)
    text(svg, 43, 653, f"PriceDeviation  ·  source log #{log_index}", 20, MUTED, mono=True)
    receipt_mark(svg, 367, 589)

    panel(svg, 24, 691, 392, 91, "review", "#42536b")
    tag(svg, 43, 717, "OFF-CHAIN AI REVIEW", MUTED, 20)
    text(svg, 43, 747, "Scoring deferred", 26, weight=650, space=-0.5)
    text(svg, 43, 771, "Missing both USD reference prices.", 20, MUTED)


def chinese_cover(svg, trigger, log_index):
    """Localize the same scale, marks and run-specific result."""
    price = f"{trigger / PARITY:.4f}"
    labels = {
        "PUBLIC TESTNET": "公开测试网", "27 NOV 2026": "2026.11.27",
        "Which quote triggered ": "哪笔报价触发了", "the alert?": "告警？",
        "Which quote": "哪笔报价", "triggered ": "触发了",
        "Two simulated USDC/USDT quotes, measured against a 1:1 peg.": "对照两笔 USDC/USDT 模拟报价与 1:1 平价的距离。",
        "Publish quotes": "发布报价", "Request a callback": "请求跨链回调",
        "Only above 50 basis points from parity.": "偏离平价超过 50 个基点时触发。",
        "50 bp cutoff": "50 基点阈值", "10 bp": "10 基点",
        f"{abs(trigger - PARITY)} bp": f"{abs(trigger - PARITY)} 基点",
        "Record one alert": "写入一条告警", f"Source log #{log_index}": f"源日志序号 {log_index}",
        "OFF-CHAIN AI REVIEW": "链下 AI 复核", "Scoring deferred": "暂缓评分",
        "Matching USDC/USD and USDT/USD quotes were missing.": "缺少对应时点的 USDC/USD 和 USDT/USD 参考价。",
        "Simulated USDC/USDT quotes": "USDC/USDT 模拟报价",
        "Call back only above 50 bp": "超出 50 基点才请求回调",
        f"One alert for {price}": f"{price} 触发一条告警",
        f"PriceDeviation  ·  source log #{log_index}": f"PriceDeviation · 源日志 {log_index}",
        "Missing both USD reference prices.": "缺少两项美元参考价。",
    }
    svg.set("lang", "zh-CN")
    svg.find("title").text = "Reactive PegPulse · 哪笔报价触发了告警？"
    svg.find("desc").text = (f"Ethereum Sepolia 发布两笔模拟报价。0.9990 处于观察区间，{price} 超过 50 个基点的阈值。"
                             f"Reactive Lasna 请求回调，Base Sepolia 写入一条告警，对应源日志 {log_index}。因缺少同期美元参考价，链下 AI 暂缓评分。")
    for elem in svg.iter():
        if elem.text in labels:
            elem.text = labels[elem.text]
            elem.set("font-family", "'Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif")
            elem.set("letter-spacing", "0")


def main():
    run = json.loads((TRACK / "evidence/public-run.json").read_text(encoding="utf-8"))
    trigger = run["alert"]["priceBps"]
    reference = run["receipts"]["reactive"]
    log_index = int(reference["refEventIndex"], 16)
    origin = run["receipts"]["origin"]
    if (run["mode"] != "public-testnet" or reference["refTx"] != origin["transactionHash"] or
            not any(int(event["logIndex"], 16) == log_index for event in origin["logs"]) or
            run["triage"]["decision"] != "insufficient" or run["triage"]["inferenceRan"] or
            not (abs(CONTROL - PARITY) < CUTOFF < abs(trigger - PARITY) < 80)):
        raise ValueError("The public run changed. Review the cover's scale, labels and interpretation.")
    description = (f"Two simulated USDC/USDT quotes were published on Ethereum Sepolia. "
                   f"{CONTROL / PARITY:.4f} stayed below the 50 basis point threshold. "
                   f"{trigger / PARITY:.4f} crossed it. Reactive Lasna requested a callback. "
                   f"Base Sepolia recorded one alert linked to source log {log_index}. Off-chain AI "
                   "scoring was deferred because matching USD price evidence was missing.")
    for filename, width, height, draw in (("desktop.svg", 1280, 646, desktop),
                                          ("mobile.svg", 440, 798, phone)):
        svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", width=str(width),
                         height=str(height), viewBox=f"0 0 {width} {height}", role="img",
                         attrib={"aria-labelledby": "title description", "lang": "en"})
        node(svg, "title", id="title").text = "Reactive PegPulse — Which quote triggered the alert?"
        node(svg, "desc", id="description").text = description
        draw(svg, trigger, log_index)
        ET.indent(svg, space="  ")
        (HERE / filename).write_text(ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")
        chinese_cover(svg, trigger, log_index)
        (HERE / filename.replace(".svg", ".zh-CN.svg")).write_text(
            ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
