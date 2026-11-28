# Stablecoin Alerts walkthrough

**English** · [简体中文](README.zh-CN.md)

## Hackathon submission · public testnets

**[Watch the 2:30 narrated recording](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@main/track3/video/public/demo.mp4)** · [Download MP4](https://raw.githubusercontent.com/sunshineluyao/reactive-builder-camp-2026/main/track3/video/public/demo.mp4) · [English subtitles](public/demo.en.srt) · [中文字幕](public/demo.zh.srt)

The review screen verifies one signed Ethereum Sepolia quote, the Lasna execution, and the Base Sepolia callback against public RPCs. The quote is simulated. In the original public run the alert had no independent market data packet, so the review service withheld its score. The next chapter uses the same event with labeled synthetic reference data to demonstrate the neural network's decisions. [Contracts and transaction links](../README.en.md) · [Public receipts](../evidence/public-run.json)

| Time | What the reviewer sees |
| --- | --- |
| 00:07 | A 0.9990 control stays in the band. A 0.9930 quote exceeds the 50-basis-point threshold. |
| 00:36 | Three public receipts identify one source event. The reviewer opens each transaction's details. |
| 01:19 | The public alert has no market evidence packet. Labeled synthetic replays show escalation, continued observation and a withheld score. |
| 02:13 | The source, evidence and model files needed to reproduce the run. |

[![Public testnet review showing the matched transaction receipts](public/stills/02-public-receipts-ai-decision.webp)](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@main/track3/video/public/demo.mp4)

## Local Anvil walkthrough

![Full 2:30 silent demo with Chinese captions. A simulated 0.9930 quote triggers a callback; three receipts and the model's review decision are shown.](demo.gif)

[Download the narrated MP4 (2:30)](https://raw.githubusercontent.com/sunshineluyao/reactive-builder-camp-2026/main/track3/video/demo.mp4) · [English audio only](demo.en.m4a) · [English subtitles](demo.en.srt) · [中文字幕](demo.zh.srt) · [Wanim animation and source](../visual/README.md)

The GIF loops inline when your GitHub motion settings allow it. The [original MP4](demo.mp4) includes English narration and the same burned-in Chinese captions. Both files play offline after cloning the repository.

The recording follows a simulated 0.9930 USDT/USDC quote through three private Anvil chains and into the review queue. It shows each application's receipt and three outcomes from the same fixed alert. Corroborating USD references escalate review, near-par USD references support continued observation, and a missing reference withholds the score. The runtime uses the actual Solidity rehearsal and frozen model. The USD reference packets and the transport between these private chains are simulated.

| Time | What to look for |
| --- | --- |
| 00:07 | Wanim draws a quote inside the band, one on its boundary, and one 70 basis points below parity. |
| 00:36 | The review application matches three receipts. Expand each leg to see its transaction and emitter. |
| 01:19 | The reviewer changes the synthetic reference context and compares all three decisions. |
| 02:13 | Source, evidence and model files needed to reproduce the example. |

## Screenshots

**00:30 · A quote of 0.9930 crosses the 50-basis-point threshold.**

![Wanim chart showing a 70-basis-point deviation and the decision to request a callback.](stills/01-wanim-threshold-crossing.webp)

**01:04 · Three local EVM receipts lead to a model decision.**

![The review page shows the origin, Reactive and destination receipts alongside the escalation decision and its synthetic USD references.](stills/02-local-receipts-ai-decision.webp)

## Rebuild

The capture script starts private loopback HTTP servers, records the running Wanim player and receipt-review application in Chromium, and asserts the visible outcomes. It uses the Wanim player's pinned package cache. On first use, the player downloads the two packages into `~/.cache/reactive-wanim`. Temporary footage and synthesized audio are written to the directory supplied on the command line.

From the `track3` directory, install Python 3, FFmpeg with libx264, libass, libwebp, Flite and AAC, and the Noto Sans CJK SC font. Install the Python browser driver and its Chromium build, then capture the screen.

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 video/capture.py /tmp/stablecoin-film
python3 video/render.py /tmp/stablecoin-film
```

The renderer writes the full-length README GIF, the Wanim chapter GIF, and an M4A copy of the original narration next to the MP4. To export those three assets from the checked-in recording, run this command from `track3/`. This step uses Python 3 and FFmpeg.

```bash
python3 video/render.py /tmp/stablecoin-media --media-only
```

The default encoder uses FFmpeg's `slt` text-to-speech voice. The published cut uses Piper's `en_US-ljspeech-medium` voice and `piper-tts==1.3.0`. To use that voice, download the two files below into the same directory, install `piper-tts==1.3.0`, and pass `--voice-model /path/to/en_US-ljspeech-medium.onnx` to `render.py`. The model card identifies the underlying speech recordings as public domain. [Voice model](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx) · [Voice configuration](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx.json) · [Model card](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD)

Rebuild the submitted public recording from the `track3/` directory. Prepare the same dependencies listed above. The review scene checks the three canonical blocks and the two synthetic inference outcomes before the film can render.

```bash
mkdir -p /tmp/stablecoin-public-cut
python3 video/capture.py /tmp/stablecoin-public-film --public-manifest evidence/public-run.json
python3 video/render.py /tmp/stablecoin-public-film --public --out /tmp/stablecoin-public-cut/demo.mp4
```

Behind a browser network proxy, add `--host-rpc` to the capture command to forward read-only queries over the host's HTTPS connection. `ORIGIN_RPC`, `REACTIVE_RPC` and `DESTINATION_RPC` can select endpoints in this mode. The recorded public cut used `DESTINATION_RPC=https://base-sepolia-rpc.publicnode.com`. The viewer checks the chain IDs, receipts and canonical blocks through the same verification code. Use `--chrome /path/to/chrome` for an existing compatible Chromium and `--cache /path/to/cache` for verified Wanim packages.

`narration.json` contains the bilingual script. `cards.html` contains the opening and closing titles. `capture.py` operates the on-screen controls. `render.py` aligns the spoken cues, burns in Chinese captions, combines the screen recordings and exports H.264/AAC video, two subtitle files and two stills.
