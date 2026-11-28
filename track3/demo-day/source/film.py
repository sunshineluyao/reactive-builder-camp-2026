"""Composite the timed Wanim capture, live app, slide deck and two-pose speaker into one MP4."""
import argparse
import bisect
import functools
import json
import math
import re
import subprocess
import wave
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageFont

from layout import make_spec, TITLE, TEAM

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
W,H,FPS,TOTAL=1280,720,24,280
FONT_ZH="Noto Sans CJK SC"
FONT_EN="DejaVu Sans"


def timecode(sec):
    ticks=round(100*sec)
    return f"{ticks//360000}:{ticks//6000%60:02}:{ticks//100%60:02}.{ticks%100:02}"


def srt_rows(path):
    def value(s):
        h,m,ss,ms=map(int,re.split("[:,]",s))
        return h*3600+m*60+ss+ms/1000
    for block in path.read_text().strip().split("\n\n"):
        fields=block.splitlines()
        if len(fields)>=3:
            a,b=fields[1].split(" --> ")
            yield value(a),value(b)," ".join(fields[2:])


def ass(work):
    head="""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Zh,Noto Sans CJK SC,31,&H00F9FAFA,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: En,DejaVu Sans,21,&H00D8DEC9,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Disclosure,Noto Sans CJK SC,20,&H00E4D3D0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[head]
    def font_path(family):
        return subprocess.check_output(["fc-match","-f","%{file}",family],text=True)
    for lang,key,family,size,y in [("zh","Zh",FONT_ZH,31,653),("en","En",FONT_EN,21,694)]:
        path=font_path(family)
        for a,b,t in srt_rows(OUT/f"captions.{lang}.srt"):
            fsize=size
            while ImageFont.truetype(path,fsize).getlength(t)>1180 and fsize>16: fsize-=1
            if ImageFont.truetype(path,fsize).getlength(t)>1205: raise ValueError("Split long subtitle: "+t)
            lines.append(f"Dialogue: 0,{timecode(a)},{timecode(b)},{key},,0,0,0,,{{\\pos(640,{y})\\fs{fsize}}}{t}\n")
    timing=json.loads((work/"sound/timing.json").read_text())
    first_transition=next(c["slideStart"] for c in timing if c["slide"]==2)
    lines.append(f"Dialogue: 0,0:00:00.00,{timecode(first_transition)},Disclosure,,0,0,0,,{{\\pos(736,570)}}预录 · AI 数字分身与合成旁白\n")
    (work/"captions.ass").write_text("".join(lines))


def audio_motion(path):
    with wave.open(str(path),"rb") as wav:
        if wav.getframerate()!=24000 or wav.getnchannels()!=1:raise ValueError("Expected 24 kHz mono")
        samples=np.frombuffer(wav.readframes(wav.getnframes()),"<i2").astype(np.float32)/32768
    chunks=samples.reshape(-1,24000//FPS)
    rms=np.sqrt(np.mean(chunks**2,axis=1))
    peak=np.percentile(rms[rms>.008],89)
    value=np.clip((rms-.009)/(peak-.009),0,1)
    for i in range(1,len(value)):value[i]=.29*value[i-1]+.71*value[i]
    return np.rint(value*15).astype(int)


def speaker_frames(size):
    def source(name):
        return np.asarray(Image.open(OUT/"media"/name).convert("RGB").resize((size,size),Image.Resampling.LANCZOS),dtype=np.float32)
    rest,spoken=source("avatar.jpg"),source("avatar-speaking.jpg")
    y,x=np.ogrid[:size,:size]
    dist=((x/size-.544)/.165)**2+((y/size-.628)/.104)**2
    mask=np.clip((1-dist)/.42,0,1)[:,:,None]
    return [Image.fromarray((rest+(spoken-rest)*mask*(i/15)).clip(0,255).astype("uint8")) for i in range(16)]


def mastering_filter(wav_path):
    target = "loudnorm=I=-16:LRA=9:TP=-1.5"
    analysis = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav_path), "-af",
         target + ":print_format=json", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    )
    measured, _ = json.JSONDecoder().raw_decode(analysis.stderr[analysis.stderr.rfind("{"):])
    return (f"{target}:measured_I={measured['input_i']}:measured_LRA={measured['input_lra']}"
            f":measured_TP={measured['input_tp']}:measured_thresh={measured['input_thresh']}"
            f":offset={measured['target_offset']}:linear=true")


def build(work,pdf,target):
    timing=json.loads((work/"sound/timing.json").read_text())
    first=[c for c in timing if c["first"]]
    starts=[c["slideStart"] for c in first]
    assert len(first)==10 and starts[6]==170
    end_times=starts[1:]+[TOTAL]
    chapters=[f";FFMETADATA1\ntitle={TITLE}\nartist=Sunshine\ncomment={TEAM} · Reactive Meets AI · Prerecorded presentation and simulated Q&A\n"]
    for c,end in zip(first,end_times):
        name=("模拟问答 / " if c["part"]=="qa" else "")+c["name"]
        chapters.append(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['slideStart']*1000)}\nEND={round(end*1000)}\ntitle={name}\n")
    (work/"chapters.txt").write_text("".join(chapters))
    ass(work)
    spec=make_spec(); doc=fitz.open(pdf); assert len(doc)==10
    back=[]
    for page in doc:
        pagepix=page.get_pixmap(matrix=fitz.Matrix(W/page.rect.width,H/page.rect.height),alpha=False)
        frame=Image.frombytes("RGB",(pagepix.width,pagepix.height),pagepix.samples)
        back.append(frame.resize((W,H),Image.Resampling.LANCZOS) if frame.size!=(W,H) else frame)
    capture=work/"capture"
    poses={}
    facebox={}
    for i,slide in enumerate(spec,1):
        for thing in slide["items"]:
            if thing["kind"]=="image" and thing["file"]=="avatar.jpg":
                x,y,w,h=thing["box"];facebox[i]=(x,y,w)
                if w not in poses:poses[w]=speaker_frames(w)
    envelope=audio_motion(work/"sound/programme.wav")
    s2=[c for c in timing if c["slide"]==2]
    s4=[c for c in timing if c["slide"]==4][-1]
    moves=[s2[1]["start"]+.49*(s2[1]["end"]-s2[1]["start"]),s2[2]["start"]+.27]
    swaps=[s4["start"]+k*(s4["end"]-s4["start"]) for k in (.42,.76)]
    @functools.lru_cache(maxsize=24)
    def frame_bytes(slide,state):
        img=back[slide-1].copy()
        if slide in facebox:
            x,y,w=facebox[slide];img.paste(poses[w][state],(x,y))
        elif slide==2:
            chart=Image.open(capture/("chart-"+state+".png")).convert("RGB")
            img.paste(chart.resize((728,411),Image.Resampling.LANCZOS),(59,189))
        elif slide==4:
            shot=Image.open(capture/("model-"+state+".png")).convert("RGB")
            h=round(600*shot.height/shot.width)
            img.paste(shot.resize((600,h),Image.Resampling.LANCZOS),(63,459 if state=="insufficient" else 450))
        return img.tobytes()
    ff=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
        "-framerate",str(FPS),"-i","pipe:0","-i",str(work/"sound/programme.wav"),"-i",str(OUT/"captions.en.srt"),
        "-i",str(OUT/"captions.zh.srt"),"-f","ffmetadata","-i",str(work/"chapters.txt"),"-map","0:v:0","-map","1:a:0",
        "-map","2:s:0","-map","3:s:0","-map_metadata","4","-map_chapters","4","-vf",
        "drawbox=x=0:y=625:w=1280:h=95:color=0x11182B:t=fill,ass=captions.ass,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","26","-threads","3","-profile:v","high",
        "-af",mastering_filter(work/"sound/programme.wav"),"-ar","48000","-c:a","aac","-b:a","88k",
        "-c:s","mov_text","-metadata:s:a:0","language=zho","-metadata:s:s:0","language=eng","-metadata:s:s:1","language=zho",
        "-disposition:s:0","0","-disposition:s:1","0","-t",str(TOTAL),"-movflags","+faststart",str(target)]
    proc=subprocess.Popen(ff,cwd=work,stdin=subprocess.PIPE)
    previous=0
    try:
        for frame in range(TOTAL*FPS):
            t=frame/FPS;slide=bisect.bisect_right(starts,t)
            if slide!=previous:
                print(f"{t:7.2f}s  slide {slide}",flush=True);previous=slide
            state=0
            if slide in facebox:state=int(envelope[frame])
            if slide==2:
                state="0"
                for j,change in enumerate(moves,1):
                    if t>=change:
                        index=math.floor((t-change)*16/.94)
                        state=f"{j}-{index:02}" if index<16 else str(j)
            if slide==4:state=["insufficient","escalate","observe"][bisect.bisect_right(swaps,t)]
            proc.stdin.write(frame_bytes(slide,state))
    finally:
        proc.stdin.close()
    if proc.wait():raise RuntimeError("Video encode failed")
    still=starts[2]+.66*(end_times[2]-starts[2])
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(still),"-i",str(target),
        "-frames:v","1","-q:v","2",str(OUT/"demo-screenshot.jpg")],check=True)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("work",type=Path)
    ap.add_argument("pdf",type=Path);ap.add_argument("video",type=Path);args=ap.parse_args()
    build(args.work.resolve(),args.pdf.resolve(),args.video.resolve())
