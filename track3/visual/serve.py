"""Serve the presentation with the verified Wanim/npm files from a local cache."""
import argparse
import base64
import hashlib
import io
import tarfile
import tempfile
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


PACKAGES = {
    "wanim": (
        "https://registry.npmjs.org/@wanimjs/wanim/-/wanim-0.1.3.tgz",
        "n1XAq73ZDN2oOT38NSeapW99a9KWrREknXcr8u/0ymeCn3iTlmgtNHICKLmoGjkIr39UnJFqhj1XzEXERy0afg==",
    ),
    "numpy": (
        "https://registry.npmjs.org/numpy-ts/-/numpy-ts-1.7.0.tgz",
        "pOWdSyfbdN2pb5P2XBDxz6JR3I5XPqxJvR0i/hi6QIFrt1FLoEDUi8nLqb9KdlleUNBgWM1i9xCaO7IBD2j1bQ==",
    ),
}


def runtime_files(cache):
    cache.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, (url, integrity) in PACKAGES.items():
        path = cache / (name + ".tgz")
        if path.is_file():
            data = path.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
        if hashlib.sha512(data).digest() != base64.b64decode(integrity):
            raise ValueError(f"Unexpected content for {path}. Remove that cached file and retry.")
        if not path.is_file():
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temp:
                temp.write(data)
            Path(temp.name).replace(path)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for item in archive:
                if not item.isfile():
                    continue
                if name == "wanim" and item.name.startswith("package/browser/") and item.name.endswith(".js"):
                    key = "/_runtime/wanim/" + item.name.removeprefix("package/")
                elif name == "numpy" and item.name == "package/dist/numpy-ts.browser.js":
                    key = "/_runtime/numpy.js"
                else:
                    continue
                files[key] = archive.extractfile(item).read()
    return files


class LocalPlayer(SimpleHTTPRequestHandler):
    def __init__(self, *args, runtime, **kwargs):
        self.runtime = runtime
        super().__init__(*args, **kwargs)

    def send_head(self):
        path = urlsplit(self.path).path
        if path in self.runtime:
            data = self.runtime[path]
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return io.BytesIO(data)
        return super().send_head()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "reactive-wanim")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    handler = partial(LocalPlayer, directory=directory, runtime=runtime_files(args.cache))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Player: http://127.0.0.1:{server.server_port}/?offline=1", flush=True)
        server.serve_forever()
