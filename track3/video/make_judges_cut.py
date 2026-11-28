"""Build the 150-second competition film from the real reviewer and checked research outputs.

python video/make_judges_cut.py --work /tmp/pegpulse-film [--browser /path/to/chromium] [--voice model.onnx]
"""

import argparse
import base64
import functools
import html
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from capture import QuietFiles, server
from render import ffmpeg, soundtrack, stamp

VIDEO = Path(__file__).resolve().parent
TRACK = VIDEO.parent
DATA = TRACK / "evidence" / "market"
PUBLIC = VIDEO / "public"


def card(label, value, foot):
    return f'<div class="card"><small>{label}</small><b>{value}</b><span class="mono">{foot}</span></div>'


def cards(*items):
    return '<div class="cards">' + "".join(card(*row) for row in items) + "</div>"


def note(label, para):
    return f'<div class="wide"><small>{label}</small><p>{para}</p></div>'


def screen(image, label, caption):
    return (
        '<div class="shot"><img src="data:image/png;base64,'
        + base64.b64encode(image).decode()
        + '"><aside><b>'
        + label
        + "</b>"
        + caption
        + "</aside></div>"
    )


def capture_scenes(work, browser_path):
    compare = json.loads((DATA / "comparison.json").read_text())["total"]
    market = json.loads((DATA / "public-context.json").read_text())
    report = json.loads((DATA / "public-assessment.json").read_text())
    public = json.loads((DATA.parent / "public-run.json").read_text())
    selector = '[data-kind="{}"]'
    handler = functools.partial(QuietFiles, directory=str(TRACK))
    with server(handler) as site, sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-background-networking", "--disable-sync", "--no-first-run"],
        )
        page = browser.new_page(viewport={"width": 1250, "height": 910}, device_scale_factor=1)
        page.goto(site + "/review/index.html?lang=en")
        page.wait_for_selector('#result-box[data-decision="observe"]')

        def shot(css):
            return page.locator(css).screenshot(animations="disabled")

        legs = shot("#legs")
        page.locator("#legs > li").last.locator("summary").click()
        destination = shot("#legs > li:last-child")
        page.locator(selector.format("absent")).click()
        withheld = shot("#result-box")
        page.locator(selector.format("market")).click()
        assessed = shot("#result-box")
        features = shot(".input-panel")
        page.locator('[data-answer="observe"]').click()
        task = shot(".review-task")
        page.close()
        route = []
        for name, chain, moment in [
            ("origin", "Ethereum Sepolia", "13:38:12"),
            ("reactive", "Reactive Lasna", "13:38:12"),
            ("destination", "Base Sepolia", "13:38:14"),
        ]:
            tx = public[name]["txHash"]
            route.append((chain, moment + " UTC", tx[:10] + "…" + tx[-8:]))

        def table(headers, rows):
            return (
                "<table><thead><tr>"
                + "".join("<th>" + h + "</th>" for h in headers)
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
                + "</tbody></table>"
            )

        prices = market["references"]
        n = len(market["history"])
        event = report["alert"]["evidenceId"]
        model = report["marketDecision"]
        panels = [
            (
                0,
                "Three receipts for one 0.9930 quote",
                "<p>Would you page the treasury?</p>"
                + cards(*route)
                + note(
                    "27 NOV 2026 · SIGNED TESTNET EVENT",
                    "Source log 2 · one Base callback · controlled USDC/USDT quote",
                ),
            ),
            (
                14,
                "Which quote should trigger a callback?",
                cards(
                    ("CONTROL", "0.9990", "10 bp from parity"), ("TRIGGER", "0.9930", "70 bp from parity")
                )
                + note(
                    "REACTIVE LASNA",
                    "A designated publisher, the correct event, a strict 50 bp threshold and one request per event.",
                ),
            ),
            (
                29,
                "Follow the source log",
                screen(
                    legs,
                    "Same event",
                    "Ethereum Sepolia → Reactive Lasna → Base Sepolia. Each row opens its block explorer.",
                ),
            ),
            (
                37,
                "Inspect the Base callback",
                screen(
                    destination,
                    "Source log 2",
                    "The origin hash and source log index identify the quote across chains.",
                ),
            ),
            (
                45,
                "What was known at signing?",
                screen(
                    withheld,
                    "Original run",
                    "The chain recorded the alert. An independent market packet was unavailable at signing.",
                ),
            ),
            (
                60,
                "Use only prices available by 13:38:12 UTC",
                cards(
                    (
                        "BITSTAMP · USDC/USD",
                        f"${prices['USDC/USD']['usdMicros'] / 1e6:.6f}",
                        "Close 13:38:00 UTC",
                    ),
                    (
                        "COINBASE · USDT/USD",
                        f"${prices['USDT/USD']['usdMicros'] / 1e6:.6f}",
                        "Close 13:38:00 UTC",
                    ),
                    ("BINANCE · USDC/USDT", f"{n} closes", "Positive trading volume"),
                )
                + note(
                    "ARCHIVED MARKET REPLAY",
                    "The inputs precede the signed alert. The team retrieved them afterward.",
                ),
            ),
            (
                78,
                "Run the frozen model on the same alert",
                screen(
                    assessed,
                    "Continue observing",
                    "The largest USD-reference deviation was "
                    + f"{model['features']['usdDeviationBps']:.1f}"
                    + " bp. The on-chain alert remains visible.",
                ),
            ),
            (
                86,
                "Inspect the inputs behind the decision",
                screen(
                    features,
                    "Market evidence",
                    f"None of {n} prior closes crossed the threshold in the same direction.",
                ),
            ),
            (
                94,
                "How often would a reviewer be paged?",
                table(
                    ["Policy", "Referrals", "Short-lived referrals"],
                    [
                        ["Every crossing", compare["baselineReferrals"], compare["baselineUnnecessary"]],
                        ["Written training rule", compare["ruleReferrals"], compare["ruleUnnecessary"]],
                        ["Frozen model", compare["modelReferrals"], compare["modelUnnecessary"]],
                    ],
                )
                + note(
                    "208 COMPARABLE MINUTE CROSSINGS",
                    "Seven fixed one-hour windows · Kraken pair trades · independent dollar references.",
                ),
            ),
            (
                109,
                "What did fewer referrals cost?",
                cards(
                    ("PERSISTENT CROSSINGS", str(compare["persistent"]), "of 208 comparable"),
                    ("MODEL KEPT MONITORING", str(compare["modelMissed"]), "persistent crossings"),
                    ("MODEL ABSTAINED", str(compare["persistentAbstentions"]), "persistent crossing"),
                )
                + note(
                    "OUTCOME",
                    "At least three of the next five minute closes remained beyond the threshold. Treasury incident labels were unavailable.",
                ),
            ),
            (
                125,
                "Make the treasury decision yourself",
                screen(
                    task,
                    "Try the public reviewer",
                    "Open a transaction, compare the market sources and decide whether to escalate. English / 简体中文.",
                ),
            ),
            (
                140,
                "One quote. Three chains. Anyone can verify.",
                note(
                    "SUNSHINE · SUNSHINE SWARM SUPERINTELLIGENCE (3S) LAB",
                    "Open the wallet-free reviewer or reproduce the live decision in your terminal.",
                )
                + note(
                    "FROM THE TRACK3 DIRECTORY",
                    '<span class="mono">python3 scripts/market_evidence.py --live</span>',
                ),
            ),
        ]
        frame = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        template = (VIDEO / "judges-frame.html").read_text()
        for i, (time, title, body) in enumerate(panels):
            frame.set_content(
                template.replace('<h1 id="title"></h1>', "<h1>" + html.escape(title) + "</h1>").replace(
                    '<div id="body"></div>', "<div>" + body + "</div>"
                )
            )
            frame.screenshot(path=str(work / f"frame-{i:02}.png"))
        browser.close()
    Image.open(work / "frame-00.png").convert("RGB").save(
        PUBLIC / "stills/02-public-receipts-ai-decision.webp", quality=91
    )
    return [row[0] for row in panels]


def make(work, browser, voice):
    work.mkdir(parents=True, exist_ok=True)
    cues = json.loads((VIDEO / "judges-cues.json").read_text())
    times = capture_scenes(work, browser)
    narration = [
        {"t": row[0] + 0.23, "end": cues[i + 1][0] - 0.18 if i + 1 < len(cues) else 149.8, "en": row[2]}
        for i, row in enumerate(cues)
    ]
    soundtrack(work, narration, 150, voice)
    for j, lang in [(2, "en"), (3, "zh")]:
        lines = []
        for i, row in enumerate(cues):
            text = row[j].replace("U S D C", "USDC")
            lines.extend(
                [str(i + 1), stamp(narration[i]["t"]) + " --> " + stamp(narration[i]["end"]), text, ""]
            )
        srt = "\n".join(lines).rstrip() + "\n"
        (PUBLIC / f"demo.{lang}.srt").write_text(srt)
        vtt = (
            "WEBVTT\n\n"
            + "\n".join(line.replace(",", ".") if " --> " in line else line for line in lines).rstrip()
            + "\n"
        )
        (PUBLIC / f"demo.{lang}.vtt").write_text(vtt)
    # A fixed lower caption band keeps bilingual projection text off the receipt data.
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1280",
        "PlayResY: 720",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        "Style: ZH,Noto Sans CJK SC,22,&H00EAF4F7,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,30,30,0,1",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    for i, row in enumerate(cues):
        zh = row[3]
        split = len(zh) // 2
        if len(zh) > 45:
            splits = [k + 1 for k, c in enumerate(zh) if c in "。？，、" and 12 < k < len(zh) - 8]
            k = min(splits, key=lambda v: abs(v - split)) if splits else split
            zh = zh[:k] + r"\N" + zh[k:]
        lines.append(
            "Dialogue: 0,"
            + stamp(narration[i]["t"], True)
            + ","
            + stamp(narration[i]["end"], True)
            + r",ZH,,0,0,0,,{\pos(640,651)}"
            + zh
        )
    (work / "review.ass").write_text("\n".join(lines) + "\n")
    concat = []
    for i, t in enumerate(times):
        concat.extend([f"file 'frame-{i:02}.png'", f"duration {(times + [150])[i + 1] - t}"])
    concat.append(f"file 'frame-{len(times) - 1:02}.png'")
    (work / "frames.txt").write_text("\n".join(concat) + "\n")
    encode(work)


def encode(work):
    """Mux only local, already rendered frames, captions and audio. No browser or model runs."""
    temporary = PUBLIC / ".review-encoding.mp4"
    ffmpeg(
        "-protocol_whitelist",
        "file,pipe",
        "-f",
        "concat",
        "-safe",
        0,
        "-i",
        "frames.txt",
        "-i",
        "voice.wav",
        "-vf",
        "fps=15,ass=review.ass",
        "-af",
        "loudnorm=I=-17:TP=-2:LRA=8",
        "-c:v",
        "libx264",
        "-threads",
        3,
        "-preset",
        "medium",
        "-crf",
        22,
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "80k",
        "-ar",
        44100,
        "-t",
        "150",
        "-movflags",
        "+faststart",
        "-metadata",
        "title=Reactive PegPulse | Reactive Meets AI",
        temporary,
        cwd=work,
    )
    temporary.replace(PUBLIC / "demo.mp4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--browser")
    parser.add_argument("--voice", type=Path)
    parser.add_argument(
        "--encode-only", action="store_true", help="offline mux of existing local frames and WAV"
    )
    args = parser.parse_args()
    if args.encode_only:
        encode(args.work.resolve())
    else:
        make(args.work.resolve(), args.browser, args.voice.resolve() if args.voice else None)
