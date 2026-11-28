"""Fetch the pinned Mandarin voice and verify the exact files used for this recording."""
import argparse
import hashlib
import tempfile
from pathlib import Path
from urllib.request import urlopen

MODEL="https://huggingface.co/csukuangfj/vits-melo-tts-zh_en/resolve/a0d5c6a264c0ef92d70d8661d8cc502d79627cd6/"
FILES={
    "model.int8.onnx":"f085f5079e05f039b800aeb542f5253c26a303211b0c6465d0d9387977855a63",
    "tokens.txt":"d18664a7e12bd7ea1022ddaf951e534e136815016c5a809d6b64156bffb4369d",
    "lexicon.txt":"7236884b02435ac5d10cf69b4be40a61b45aa676b5300f0e412f185748fee528",
    "LICENSE":"88a50e5a02bbc2a5c2f084dc19da751aa97b1690f5fda76cd8005c8634d1ca70",
}


def digest(path):
    with path.open("rb") as stream:return hashlib.file_digest(stream,"sha256").hexdigest()


def fetch(folder):
    folder.mkdir(parents=True,exist_ok=True)
    for name,expected in FILES.items():
        target=folder/name
        if target.is_file() and digest(target)==expected:continue
        with tempfile.TemporaryDirectory(dir=folder) as tmp:
            image=Path(tmp)/name
            with urlopen(MODEL+name+"?download=true",timeout=90) as remote,image.open("wb") as out:
                while chunk:=remote.read(1024*1024):out.write(chunk)
            if digest(image)!=expected:raise ValueError("Model checksum differs: "+name)
            image.replace(target)
        print("Verified",name)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("folder",type=Path)
    fetch(p.parse_args().folder)
