"""Voice, caption and encode the measured 150-second walkthrough."""
import argparse
import array
import json
import math
import subprocess
import wave
from pathlib import Path

VIDEO = Path(__file__).resolve().parent
FREQ = 22050


def ffmpeg(*args, cwd=None):
    subprocess.run(['ffmpeg','-hide_banner','-nostdin','-v','error','-y',*map(str,args)],cwd=cwd,check=True)


def duration(path):
    result = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True)
    return float(result)


def piper_voice(path):
    from onnxruntime import InferenceSession, SessionOptions, disable_telemetry_events
    disable_telemetry_events()
    from piper import PiperVoice
    from piper.config import PiperConfig
    options = SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
    config = PiperConfig.from_dict(json.loads(Path(str(path)+'.json').read_text()))
    return PiperVoice(config=config,session=session)


def read_voice(path):
    with wave.open(str(path),'rb') as file:
        if file.getnchannels()!=1 or file.getframerate()!=FREQ or file.getsampwidth()!=2:
            raise ValueError(f'Unexpected WAV format in {path}')
        pcm = array.array('h',file.readframes(file.getnframes()))
    voiced = [i for i, sample in enumerate(pcm) if abs(sample)>150]
    if not voiced:
        raise ValueError(f'Empty voice cue {path}')
    shoulder = round(.055*FREQ)
    return pcm[max(0,voiced[0]-shoulder):min(len(pcm),voiced[-1]+shoulder+1)]


def write_wave(path, samples):
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(FREQ)
        out.writeframes(samples.tobytes())


def soundtrack(work, cues, total, model):
    engine = piper_voice(model) if model else None
    combined = array.array('h',[0])*round(total*FREQ)
    for i,cue in enumerate(cues):
        raw = work/f'voice-{i:02d}.wav'
        if engine:
            from piper import SynthesisConfig
            with wave.open(str(raw),'wb') as dest:
                engine.synthesize_wav(cue['en'],dest,syn_config=SynthesisConfig(length_scale=1.03,noise_scale=.55,noise_w_scale=.65))
        else:
            textfile=raw.with_suffix('.txt')
            textfile.write_text(cue['en'])
            ffmpeg('-f','lavfi','-i',f'flite=textfile={textfile.name}:voice=slt','-ar',FREQ,'-ac',1,raw.name,cwd=work)
        samples=read_voice(raw)
        slot=cue['end']-cue['t']-.20
        if len(samples)>slot*FREQ:
            write_wave(raw,samples)
            speed=len(samples)/FREQ/slot
            if speed>1.35:
                raise ValueError(f'Cue {i+1} needs a shorter script (speed {speed:.2f}).')
            fixed=work/f'fit-{i:02d}.wav'
            ffmpeg('-i',raw,'-af',f'atempo={speed:.5f}',fixed)
            samples=read_voice(fixed)
        if len(samples)>math.floor((cue['end']-cue['t'])*FREQ):
            raise ValueError(f'Cue {i+1} exceeds its subtitle window')
        offset=round(cue['t']*FREQ)
        combined[offset:offset+len(samples)]=samples
        print(f"{i+1:02d} {cue['t']:5.1f}s  speech {len(samples)/FREQ:4.1f}s",flush=True)
    write_wave(work/'voice.wav',combined)


def stamp(seconds, ass=False):
    unit=100 if ass else 1000
    ticks=round(seconds*unit)
    whole,fraction=divmod(ticks,unit)
    hours,rest=divmod(whole,3600)
    mins,secs=divmod(rest,60)
    if ass:
        return f'{hours}:{mins:02d}:{secs:02d}.{fraction:02d}'
    return f'{hours:02d}:{mins:02d}:{secs:02d},{fraction:03d}'


def english(text):
    return text.replace('U S D T','USDT').replace('U S D C','USDC').replace('E V M','EVM')


def provenance(t,public):
    if t<7: return 'TRACK 3  /  REACTIVE MEETS AI'
    if t<36: return 'WANIM  /  SIMULATED QUOTES'
    if t<79: return 'PUBLIC TESTNET  /  RPC VERIFIED' if public else 'LOCAL EVM  /  THREE PRIVATE CHAINS'
    if t<133: return 'INFERENCE  /  SYNTHETIC CONTEXT'
    return 'PROJECT REPOSITORY'


def subtitles(work, cues, total, public):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Zh,Noto Sans CJK SC,26,&H00F0F5E9,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,48,48,0,1
Style: Chapter,DejaVu Sans,16,&H00BEDEAD,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0.45,0,1,0,0,7,0,0,0,1
Style: Proof,DejaVu Sans Mono,13,&H00BFCDC1,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0.25,0,1,0,0,9,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[header]
    def caption(style, start, end, text, x,y):
        lines.append(f'Dialogue: 0,{stamp(start,True)},{stamp(end,True)},{style},,0,0,0,,{{\\pos({x},{y})}}{text}\n')
    for idx,cue in enumerate(cues):
        begin=0 if idx==0 else cue['t']
        end=total if idx==len(cues)-1 else cues[idx+1]['t']
        caption('Chapter',begin,end,cue['chapter'],48,624)
        caption('Proof',begin,end,provenance(cue['t'],public),1232,626)
        caption('Zh',cue['t'],cue['end'],cue['zh'],48,656)
    (work/'captions.ass').write_text(''.join(lines))
    for lang in ['zh','en']:
        lines=[]
        for i,cue in enumerate(cues,1):
            words=english(cue['en']) if lang=='en' else cue['zh']
            lines.append(f"{i}\n{stamp(cue['t'])} --> {stamp(cue['end'])}\n{words}\n\n")
        (work/f'demo.{lang}.srt').write_text(''.join(lines))


def film(work, target, manifest):
    layout=[('title.png',7.2),('threshold.webm',manifest['thresholdSeconds']),('review.webm',manifest['reviewSeconds']),('end.png',16.7)]
    inputs=[]
    filters=[]
    for i,(name,seconds) in enumerate(layout):
        path=work/name
        if path.suffix=='.png':
            inputs+=['-loop','1','-framerate','15','-t',str(seconds+.2)]
        else:
            start=max(0,duration(path)-seconds-.12)
            inputs+=['-ss',f'{start:.4f}']
        inputs+=['-i',str(path)]
        pad=',pad=1280:612:(ow-iw)/2:0:color=0x101b1f' if i==1 else ''
        filters.append(f'[{i}:v]fps=15{pad},setsar=1,tpad=stop_mode=clone:stop_duration=1,trim=duration={seconds},setpts=PTS-STARTPTS,format=yuv420p[v{i}]')
    filters.append('[v0][v1][v2][v3]concat=n=4:v=1:a=0,pad=1280:720:0:0:color=0x10272d,ass=captions.ass[v]')
    ffmpeg(*inputs,'-i',work/'voice.wav','-filter_complex_threads',2,'-filter_complex',';'.join(filters),'-map','[v]','-map','4:a',
           '-af','loudnorm=I=-17:TP=-2:LRA=8','-ar',44100,'-c:v','libx264','-threads',3,'-preset','medium','-tune','stillimage','-crf',24,
           '-pix_fmt','yuv420p','-r',15,'-c:a','aac','-b:a','56k','-movflags','+faststart','-t',150,
           '-metadata','title=Stablecoin Alerts | Reactive Builder Camp Track 3',target,cwd=work)


def stills(path, public):
    folder = path.parent / 'stills'
    folder.mkdir(exist_ok=True)
    mode = 'public' if public else 'local'
    frames = [(30, '01-wanim-threshold-crossing'), (64, f'02-{mode}-receipts-ai-decision')]
    for sec, name in frames:
        ffmpeg('-ss', sec, '-i', path, '-frames:v', 1, '-c:v', 'libwebp', '-lossless', 1,
               '-compression_level', 6, '-pix_fmt', 'bgra', folder / (name + '.webp'))


def github_media(video, work):
    """Export the captioned film, Wanim chapter and original narration separately."""
    sampling = 'fps=5,scale=896:-2:flags=lanczos'
    palette = work / 'readme-palette.png'
    ffmpeg('-threads', 2, '-filter_threads', 2, '-i', video,
           '-vf', sampling + ',palettegen=stats_mode=diff', '-frames:v', 1, palette)
    palette_filter = f'[0:v]{sampling}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle'
    cues = json.loads((VIDEO / 'narration.json').read_text())['cues']
    start = next(c['t'] for c in cues if c['chapter'] == 'The price threshold')
    end = next(c['t'] for c in cues if c['t'] > start and c['chapter'] != 'The price threshold')
    for suffix, input_args in [('.gif', []), ('.threshold.gif', ['-ss', start, '-t', end - start])]:
        ffmpeg('-threads', 2, '-filter_complex_threads', 2, *input_args, '-i', video, '-i', palette,
               '-filter_complex', palette_filter, '-an', '-loop', 0, video.with_suffix(suffix))
    ffmpeg('-i', video, '-map', '0:a:0', '-c:a', 'copy', '-movflags', '+faststart', video.with_suffix('.en.m4a'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work',type=Path,help='Temporary directory used by capture.py')
    parser.add_argument('--voice-model',type=Path,help='Optional Piper ONNX model with .onnx.json adjacent. Otherwise uses FFmpeg Flite.')
    parser.add_argument('--public',action='store_true',help='Use narration for a run verified by public RPCs')
    parser.add_argument('--prepare',action='store_true',help='Generate speech and subtitles while screen recording runs')
    parser.add_argument('--reuse-voice',action='store_true',help='Use the prepared voice only when its mode and narration match')
    parser.add_argument('--out',type=Path,default=VIDEO/'demo.mp4')
    parser.add_argument('--media-only', action='store_true', help='Export GitHub animations and narration from the existing MP4 at --out.')
    args=parser.parse_args(); work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    path = args.out.resolve()
    if args.media_only:
        github_media(path, work)
        return
    data=json.loads((VIDEO/'narration.json').read_text());cues=data['cues'];total=data['duration']
    mode='public' if args.public else 'local'
    for i,cue in enumerate(cues):
        for language in ['en','zh']:
            if args.public: cue[language]=cue.get('public_'+language,cue[language])
        cue['end']=(cues[i+1]['t']-.12) if i+1<len(cues) else total-.22
    preparation={'mode':mode,'script':cues}
    if args.reuse_voice:
        if json.loads((work/'prepared.json').read_text())!=preparation: raise ValueError('The prepared voice does not match the script and evidence mode.')
    else:
        soundtrack(work,cues,total,args.voice_model)
        subtitles(work,cues,total,args.public)
        (work/'prepared.json').write_text(json.dumps(preparation,ensure_ascii=False))
    if args.prepare:return
    manifest=json.loads((work/'capture.json').read_text())
    if manifest['mode']!=mode: raise ValueError('Capture and narration evidence modes differ.')
    film(work,path,manifest)
    stills(path,args.public)
    github_media(path, work)
    for lang in ['en','zh']:
        path.with_suffix(f'.{lang}.srt').write_bytes((work/f'demo.{lang}.srt').read_bytes())
    print(f'Saved {path} ({duration(path):.2f}s)')


if __name__=='__main__':
    main()
