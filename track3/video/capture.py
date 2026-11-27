"""Record the real local Wanim player and receipt-review UI with Playwright."""
import argparse
import functools
import http.server
import importlib.util
import json
import os
import threading
import time
import urllib.request
from contextlib import ExitStack, contextmanager
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


VIDEO = Path(__file__).resolve().parent
PROJECT = VIDEO.parent


class QuietFiles(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def server(handler):
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{httpd.server_port}'
        finally:
            httpd.shutdown()
            thread.join()


def visual_handler(cache):
    spec = importlib.util.spec_from_file_location('visual_server', PROJECT / 'visual/serve.py')
    player = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(player)
    class QuietPlayer(player.LocalPlayer):
        def log_message(self, *args):
            pass
    return functools.partial(QuietPlayer, directory=PROJECT / 'visual', runtime=player.runtime_files(cache))


# The pointer follows actual Playwright mouse activity. It inserts no application data.
POINTER = '''(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const pointer = document.createElement('div');
    pointer.setAttribute('aria-hidden','true');
    pointer.style.cssText='position:fixed;z-index:9999;pointer-events:none;width:17px;height:17px;border:2px solid white;background:#0c5547;border-radius:50%;box-shadow:0 0 0 1.5px #173e35,0 2px 5px #164d3b40;opacity:0;left:-30px;top:-30px;';
    document.body.append(pointer);
    document.addEventListener('mousemove', e => {pointer.style.left=(e.clientX - 8)+'px';pointer.style.top=(e.clientY - 8)+'px';pointer.style.opacity='1';});
    document.addEventListener('mousedown', () => pointer.animate([{transform:'scale(1.7)',background:'#f1ae62'},{transform:'scale(1)'}],{duration:400}));
  });
})();'''


def wait_until(page, started, seconds):
    remaining = (started + seconds - time.monotonic()) * 1000
    if remaining > 0:
        page.wait_for_timeout(remaining)


def move_to(page, item, x_offset=12):
    box = item.bounding_box()
    if not box:
        raise RuntimeError('Cannot point to an invisible UI element')
    x = box['x'] + min(x_offset, box['width'] / 2)
    y = box['y'] + box['height'] / 2
    page.mouse.move(x, y, steps=12)
    return x, y


def click(page, item):
    x, y = move_to(page, item)
    page.wait_for_timeout(100)
    page.mouse.click(x, y)


def scroll_to(page, selector, top=23):
    page.locator(selector).evaluate('''(e,gap) => window.scrollTo({top:scrollY + e.getBoundingClientRect().top-gap,behavior:'smooth'})''',top)
    page.wait_for_timeout(610)


def record(browser, work, filename, width, scene, duration):
    size = {'width':width, 'height':612}
    with browser.new_context(viewport=size,record_video_dir=work,record_video_size=size) as context:
        page = context.new_page()
        page.set_default_timeout(25000)
        video = page.video
        started = scene(page)
        wait_until(page, started, duration + 0.12)
    final = work / (filename + '.webm')
    video.save_as(final)
    video.delete()
    return final


def cards(browser, work, base):
    with browser.new_context(viewport={'width':1280,'height':612}) as context:
        page = context.new_page()
        for name in ['title','end']:
            page.goto(base + '/video/cards.html?card=' + name,wait_until='load')
            page.locator('body[data-card="' + name + '"]').wait_for()
            page.screenshot(path=work / (name + '.png'), animations='disabled')


def education(page, url):
    page.goto(url + '/?mode=film&offline=1')
    page.locator('#stage[data-ready="true"]').wait_for(timeout=60000)
    # Hold the first quote while it is introduced, then replay the normal Wanim sequence.
    page.locator('[data-sample="0"]').evaluate('(button) => button.click()')
    expect(page.locator('#quote-value')).to_have_text('0.9990')
    page.wait_for_timeout(400)
    started = time.monotonic()
    wait_until(page,started,10.8)
    page.locator('#play-film').evaluate('(button) => button.click()')
    expect(page.locator('#stage')).to_have_attribute('data-signal','boundary',timeout=7000)
    expect(page.locator('#stage')).to_have_attribute('data-signal','trigger',timeout=7000)
    expect(page.locator('#quote-value')).to_have_text('0.9930')
    return started


def use_host_rpc(page):
    """Forward the viewer's read-only RPC calls over the host's HTTPS connection."""
    for role, network in page.evaluate('window.ReceiptProof.networks').items():
        endpoint = os.environ.get(role.upper() + '_RPC') or network['rpc']
        def forward(route, request, endpoint=endpoint):
            body = request.post_data_json
            if not isinstance(body, dict) or body.get('method') not in {
                'eth_chainId', 'eth_getTransactionReceipt', 'eth_getBlockByNumber'
            }:
                route.abort()
                return
            query = urllib.request.Request(endpoint, data=json.dumps(body).encode(),
                                           headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(query, timeout=18) as reply:
                route.fulfill(status=reply.status, content_type='application/json', body=reply.read())
        page.route(network['rpc'].rstrip('/') + '/', forward)


def review(page, base, public_file, host_rpc):
    page.add_init_script(POINTER)
    page.goto(base + '/review/?source=local')
    if public_file:
        if host_rpc:
            use_host_rpc(page)
        page.locator('#manifest-input').set_input_files(public_file)
    mode = 'live' if public_file else 'local'
    page.locator(f'.run-notice[data-state="{mode}"]').wait_for(timeout=90000)
    expect(page.locator('#count')).to_have_text('3 / 3')
    expect(page.locator('#price')).to_have_text('0.9930')
    expect(page.locator('#trace .leg')).to_have_count(3)
    if public_file:
        # Verify inclusion before using public copy. No cached/offline fallback is accepted.
        expect(page.locator('#trace .leg-ids a')).to_have_count(3)
        expect(page.locator('#result-box')).to_have_attribute('data-decision','insufficient')
    started = time.monotonic()
    wait_until(page,started,10.7)
    scroll_to(page,'#trace')
    current = None
    for at, role in [(11.5,'origin'),(22.4,'reactive'),(33.1,'destination')]:
        wait_until(page,started,at)
        if current:
            click(page,current)
        current = page.locator(f'[data-role="{role}"] .leg-detail summary')
        click(page,current)
        expect(page.locator(f'[data-role="{role}"] .leg-detail')).to_have_attribute('open','')
    wait_until(page,started,40.0)
    click(page,current)
    shared = page.locator('#match-details summary')
    click(page,shared)
    expect(page.locator('#match-details')).to_have_attribute('open','')
    wait_until(page,started,42.7)
    click(page,shared)
    scroll_to(page,'#decision')
    for at, kind, output in [(43.8,'corroborated','escalate'),(63.5,'pool-only','observe'),(74.7,'missing','insufficient')]:
        wait_until(page,started,at)
        button = page.locator(f'button[data-kind="{kind}"]')
        click(page,button)
        expect(page.locator('#result-box')).to_have_attribute('data-decision',output)
        expect(button).to_have_attribute('aria-pressed','true')
        move_to(page,page.locator('#features'))
    expect(page.locator('#score')).to_have_text('Score withheld')
    wait_until(page,started,85.5)
    inspector = page.locator('.model-detail summary')
    click(page,inspector)
    expect(page.locator('.model-detail')).to_have_attribute('open','')
    scroll_to(page,'.model-detail',92)
    expect(page.locator('#context-data')).to_contain_text('synthetic')
    return started


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work',type=Path,help='Temporary raw capture directory')
    parser.add_argument('--chrome',default=os.environ.get('CHROMIUM_PATH'),help='Optional path to Chromium/Chrome for Testing')
    parser.add_argument('--cache',type=Path,default=Path.home()/'.cache/reactive-wanim')
    parser.add_argument('--public-manifest',type=Path,help='Use a signed run only after live RPC inclusion verification')
    parser.add_argument('--host-rpc',action='store_true',help='Use host HTTPS for live RPC reads when recording behind a proxy')
    args=parser.parse_args()
    work=args.work.resolve()
    work.mkdir(parents=True,exist_ok=True)
    # A failed new capture cannot reuse an old manifest for the requested evidence mode.
    marker = work/'capture.json'
    marker.unlink(missing_ok=True)
    with ExitStack() as stack:
        site=stack.enter_context(server(functools.partial(QuietFiles,directory=PROJECT)))
        visual=stack.enter_context(server(visual_handler(args.cache)))
        pw=stack.enter_context(sync_playwright())
        browser=pw.chromium.launch(executable_path=args.chrome,args=['--disable-dev-shm-usage'])
        stack.callback(browser.close)
        cards(browser,work,site)
        record(browser,work,'threshold',1088,lambda p:education(p,visual),29.1)
        record(browser,work,'review',1280,lambda p:review(p,site,args.public_manifest,args.host_rpc),97)
    marker.write_text(json.dumps({'mode':'public' if args.public_manifest else 'local', 'thresholdSeconds':29.1, 'reviewSeconds':97},indent=2)+'\n')
    print(f'Saved verified screen captures in {work}')


if __name__=='__main__':
    main()
