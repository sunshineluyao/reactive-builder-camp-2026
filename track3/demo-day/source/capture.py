"""Capture the real Wanim scene and the read-only RPC-verified review application."""
import argparse
import functools
import importlib.util
import json
import os
from contextlib import ExitStack
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("project_capture",BASE/"video/capture.py")
existing=importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)


def capture(work, chrome, cache):
    work.mkdir(exist_ok=True,parents=True)
    with ExitStack() as stack:
        site=stack.enter_context(existing.server(functools.partial(existing.QuietFiles,directory=BASE)))
        visual=stack.enter_context(existing.server(existing.visual_handler(cache)))
        pw=stack.enter_context(sync_playwright())
        browser=pw.chromium.launch(executable_path=chrome,args=["--disable-dev-shm-usage","--no-sandbox"])
        stack.callback(browser.close)
        page=browser.new_page(viewport={"width":1280,"height":820},device_scale_factor=1)
        page.goto(visual+"/?offline=1&mode=film")
        page.locator('#stage[data-ready="true"]').wait_for(timeout=65000)
        page.evaluate("() => { stopSequence(); selectQuote(0,9990); }")
        plot=page.locator(".chart-panel")
        prices=[9990,9950,9930]
        for stage,price in enumerate(prices):
            page.evaluate("([s,p]) => selectQuote(s,p,1)",[stage,price])
            expect(page.locator("#quote-value")).to_have_text(f"{price/10000:.4f}")
            plot.screenshot(path=work/f"chart-{stage}.png")
        # Each image below is rendered by Wanim from the original Python scene.
        for move in [1,2]:
            for frame in range(17):
                t=frame/16; ease=t*t*(3-2*t)
                value=round(prices[move-1]+(prices[move]-prices[move-1])*ease)
                page.evaluate("([s,p,k]) => selectQuote(s,p,k)",[move,value,ease])
                page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                plot.screenshot(path=work/f"chart-{move}-{frame:02}.png",animations="disabled")
        print("Wanim captured both threshold transitions.",flush=True)
        page.goto(site+"/review/?source=local")
        existing.use_host_rpc(page)
        page.locator("#manifest-input").set_input_files(BASE/"evidence/public-run.json")
        page.locator('.run-notice[data-state="live"]').wait_for(timeout=90000)
        expect(page.locator("#count")).to_have_text("3 / 3")
        expect(page.locator("#price")).to_have_text("0.9930")
        expect(page.locator("#trace .leg-ids a")).to_have_count(3)
        expect(page.locator("#result-box")).to_have_attribute("data-decision","insufficient")
        page.locator("#trace").screenshot(path=work/"trace.png",animations="disabled")
        results={}
        for kind,decision in [(None,"insufficient"),("corroborated","escalate"),("pool-only","observe")]:
            if kind: page.locator(f'button[data-kind="{kind}"]').click()
            expect(page.locator("#result-box")).to_have_attribute("data-decision",decision)
            page.locator("#result-box").screenshot(path=work/f"model-{decision}.png",animations="disabled")
            results[decision]=page.locator("#result-box").inner_text()
        (work/"review-states.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
        print(results,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("work",type=Path);p.add_argument("--chrome",default=os.environ.get("CHROMIUM_PATH"))
    p.add_argument("--cache",type=Path,default=Path.home()/".cache/reactive-wanim")
    a=p.parse_args();capture(a.work,a.chrome,a.cache)
