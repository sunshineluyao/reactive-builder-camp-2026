"""Synthesize the 3+2 minute programme and write one frame-accurate cue sheet."""
import argparse
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
import sherpa_onnx as sherpa

HERE = Path(__file__).resolve().parent
RATE, FPS = 24000, 24
TOTALS = {"talk": 170, "qa": 110}


def ff(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def speakable(text):
    substitutions = {"0.9930":"零点九九三零","0.9950":"零点九九五零","0.9990":"零点九九九零",
                     "DAO":"去中心化组织","USDC":"U S D C","USDT":"U S D T",
                     "Base Sepolia":"贝斯测试网","PriceDeviation":"价格偏离","Reactive":"瑞艾克提夫"}
    for source,target in substitutions.items(): text = text.replace(source,target)
    return text


def save_wav(path, data, rate=RATE):
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1,2,rate,0,"NONE","not compressed"))
        stream.writeframes(np.asarray(data, dtype="<i2").tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as f:
        assert f.getnchannels()==1 and f.getsampwidth()==2 and f.getframerate()==RATE
        return np.frombuffer(f.readframes(f.getnframes()), dtype="<i2")


def synthesize(root, model):
    vits = sherpa.OfflineTtsVitsModelConfig(model=str(model/"model.int8.onnx"),
           tokens=str(model/"tokens.txt"), lexicon=str(model/"lexicon.txt"))
    engine = sherpa.OfflineTts(sherpa.OfflineTtsConfig(
        model=sherpa.OfflineTtsModelConfig(vits=vits, num_threads=3, provider="cpu")))
    story = json.loads((HERE/"story.json").read_text())
    clock, schedule, soundtrack = 0, [], []
    for part, scenes in story.items():
        raw = []
        for scene in scenes:
            for j, (zh, en) in enumerate(scene["cues"]):
                spoken = speakable(zh)
                key = hashlib.sha256(spoken.encode()).hexdigest()[:16]
                path = root/(key+".wav")
                if not path.is_file():
                    audio = engine.generate(spoken, sid=0, speed=1.08)
                    signal = np.asarray(audio.samples,dtype=np.float32)
                    voiced = np.flatnonzero(abs(signal)>.012)
                    if not len(voiced): raise ValueError("Empty speech: "+zh)
                    margin = round(.08*audio.sample_rate)
                    signal = signal[max(0,voiced[0]-margin):voiced[-1]+margin+1]
                    tmp = root/"new-cue.wav"
                    save_wav(tmp,np.clip(signal*32760,-32768,32767),audio.sample_rate)
                    ff("-i",tmp,"-ac","1","-ar",RATE,path)
                duration=len(read_wav(path))/RATE
                raw.append((scene,j,zh,en,path,duration))
                print(f"{scene['slide']:2}  {duration:4.1f}s  {zh[:12]}",flush=True)
        # Leave modest pauses within a paragraph and longer pauses at slide changes.
        gaps = [0.76 if j==0 else 0.33 for _,j,*_ in raw]
        tail = 0.72
        factor = sum(x[-1] for x in raw)/(TOTALS[part]-sum(gaps)-tail)
        print(part,"tempo",round(factor,3),flush=True)
        if not .70 < factor < 1.40: raise ValueError("Revise the script for a comfortable speaking pace")
        part_start = clock
        section = np.zeros(TOTALS[part]*RATE,dtype="<i2")
        local_clock = 0.
        for i,(scene,j,zh,en,path,duration) in enumerate(raw):
            slide_at=part_start+local_clock
            local_clock += gaps[i]
            start = part_start+local_clock
            fixed=root/"tempo.wav"
            ff("-i",path,"-af",f"atempo={factor:.8f}",fixed)
            voice=read_wav(fixed)
            target=round(duration/factor*RATE)
            # One resampling window at the end can differ across FFmpeg builds.
            voice=voice[:min(target,len(voice))]
            offset=round(local_clock*RATE)
            section[offset:offset+len(voice)] = voice
            local_clock += target/RATE
            schedule.append(dict(part=part,slide=scene["slide"],name=scene["name"],first=(j==0),
                       slideStart=round(slide_at,4),start=round(start,4),end=round(part_start+local_clock,4),zh=zh,en=en))
        soundtrack.append(section)
        clock+=TOTALS[part]
    save_wav(root/"programme.wav",np.concatenate(soundtrack))
    (root/"timing.json").write_text(json.dumps(schedule,ensure_ascii=False,indent=2)+"\n")
    return schedule


def clocktext(sec):
    ms=round(sec*1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def caption_parts(text, lang):
    if lang=="zh":
        return [s for s in re.findall(r"[^，。！？；：]+[，。！？；：]?",text) if s.strip()]
    return [s.strip() for s in re.findall(r"[^.,?!]+(?:[.](?=\d)[^.,?!]+)*[.,?!]?",text) if s.strip()]


def subtitles(schedule, folder):
    for lang in ("zh","en"):
        lines=[]
        for c in schedule:
            # Keep English sentences intact; decimal prices are single tokens.
            segments = caption_parts(c["zh"],"zh") if lang=="zh" else re.split(r"(?<=[.!?])\s+",c["en"])
            phrases=[]
            maximum=33 if lang=="zh" else 92
            for text in segments:
                glue="" if lang=="zh" else " "
                if phrases and len(phrases[-1])+len(text)+len(glue)<=maximum: phrases[-1]+=glue+text
                else: phrases.append(text)
            total=sum(len(x) for x in phrases); at=c["start"]
            for x in phrases:
                end=at+(c["end"]-c["start"])*len(x)/total
                lines.append(f"{len(lines)+1}\n{clocktext(at)} --> {clocktext(end)}\n{x}\n")
                at=end
        (folder/f"captions.{lang}.srt").write_text("\n".join(lines).rstrip()+"\n")


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work",type=Path);ap.add_argument("model",type=Path)
    args=ap.parse_args();args.work.mkdir(exist_ok=True,parents=True)
    subtitles(synthesize(args.work,args.model.resolve()),HERE.parent)
