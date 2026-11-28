"""Make the editable slide specification, or export it with the open-source PowerPoint writer."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = "https://github.com/sunshineluyao/reactive-builder-camp-2026"
SRC = ROOT+"/blob/main/track3/"
PROJECT_URL = ROOT+"/tree/main/track3"
OFFICIAL = "https://blog.reactive.network/reactive-omni-buildathon-thirty-days-to-find-out-what-one-second-buys/"
ORACLES = "https://docs.chain.link/data-feeds/price-feeds"
REACTIVE_DOC = "https://dev.reactive.network/reactive-contracts"
SDG10 = "https://sdgs.un.org/goals/goal10"
SDG16 = "https://sdgs.un.org/goals/goal16"
TEAM = "Sunshine Swarm Superintelligence (3S) Lab"
TITLE = "Reactive PegPulse｜一条报价，三链共证，人人可验。"
run = json.loads((PROJECT/"evidence/public-run.json").read_text())
urls = [prefix+run[role]["txHash"] for prefix,role in
        zip(["https://sepolia.etherscan.io/tx/","https://lasna.reactscan.net/tx/","https://sepolia.basescan.org/tx/"],
            ["origin","reactive","destination"])]
DARK, CREAM, PALE, INK = "#151B32", "#F6F4ED", "#FBF9F2", "#20283B"
MINT, TEAL, MUTED, LAV, SLATE = "#ABE8CA", "#176455", "#526374", "#DAC7FF", "#C9D4E0"
FONT, NUM = "Noto Sans CJK SC", "DejaVu Sans"


def make_spec():
    scenes = json.loads((HERE/"story.json").read_text())
    scenes = scenes["talk"]+scenes["qa"]
    slides=[]
    def new(bg, refs):
        s=dict(bg=bg,items=[],notes="\n".join(pair[0] for pair in scenes[len(slides)]["cues"])+
            "\n\nEnglish\n"+"\n".join(pair[1] for pair in scenes[len(slides)]["cues"])+
            "\n\n"+ "\n".join(refs))
        slides.append(s)
    def txt(x,y,w,h,text,size,colour=INK,bold=False,font=FONT,link=None):
        slides[-1]["items"].append(dict(kind="text",box=[x,y,w,h],text=text,size=size,colour=colour,
                                        bold=bold,font=font,link=link))
    def pic(x,y,w,h,file,desc):
        slides[-1]["items"].append(dict(kind="image",box=[x,y,w,h],file=file,alt=desc))
    def tbl(x,y,widths,rowh,values,dark=False,links=None,font_size=22):
        slides[-1]["items"].append(dict(kind="table",box=[x,y,sum(widths),rowh*len(values)],widths=widths,
            rowh=rowh,values=values,dark=dark,links=links or {},size=font_size,font=FONT))
    def heading(text,sub,dark=False):
        txt(60,41,1170,76,text,49,PALE if dark else INK,True)
        txt(64,129,1150,48,sub,25,SLATE if dark else MUTED)
    def footer(text,dark=False):
        txt(64,658,1160,34,text,19,SLATE if dark else MUTED)

    new(DARK,[PROJECT_URL,OFFICIAL])
    txt(65,68,658,51,"Reactive Omni Buildathon  /  Reactive Meets AI",24,MINT,True,NUM)
    txt(60,151,662,90,"Reactive PegPulse",52,PALE,True,NUM)
    txt(64,246,663,72,"一条报价，三链共证，人人可验。",42,PALE,True)
    txt(66,317,658,53,"One quote. Three chains. Anyone can verify.",26,MINT,False,NUM)
    txt(68,386,655,58,"1 USDC 换 0.9930 USDT，值得告警吗？",28,SLATE)
    txt(68,476,630,59,"Sunshine",36,LAV,True,NUM)
    txt(68,551,655,49,TEAM,24,PALE,False,NUM)
    pic(735,75,475,475,"avatar.jpg","根据讲者提供照片生成的蓝帽数字分身")
    footer("2026.11.29  ·  预录展示  ·  数字分身与合成旁白",True)

    new(CREAM,[SRC+"visual/threshold.py",SRC+"contracts/StablecoinAlerts.sol",urls[0]])
    heading("哪些报价会触发回调？","模拟 USDC/USDT 报价。一个基点等于 0.01%。")
    pic(59,189,728,411,"wanim-still.png","Wanim 运行画面，模拟报价跨越下边界")
    for k,(value,action,detail) in enumerate([
        ("0.9990","观察","公网对照报价 · 偏离 10 个基点"),
        ("0.9950","观察","动画边界示例 · 恰好 50 个基点"),
        ("0.9930","请求回调","公网触发报价 · 偏离 70 个基点")]):
        y=182+143*k
        txt(832,y,350,59,value,46,TEAL if k!=2 else "#943E27",True,NUM)
        txt(834,y+58,360,36,action,24,INK,True)
        txt(834,y+97,375,35,detail,19,MUTED)
    footer("Wanim 动画展示判断规则。公开运行通过指定报价合约发布 0.9990 和 0.9930。")

    new(DARK,[*urls,REACTIVE_DOC,SRC+"evidence/public-run.json"])
    heading("三份回执，对上同一条源事件","Sepolia 发出报价 → Lasna 调用 react() → Base 写入告警   ·   区块时间为 UTC",True)
    tbl(62,204,[238,158,290],61,[
        ["网络","区块时间","链上事件"],
        ["Ethereum Sepolia","13:38:12","PriceObserved"],
        ["Reactive Lasna","13:38:12","QuoteRouted"],
        ["Base Sepolia","13:38:14","PriceDeviation"]],True,
        {f"{i+1},2":v for i,v in enumerate(urls)},22)
    txt(65,472,220,94,"2 秒",67,MINT,True)
    txt(231,503,520,54,"这一次，首尾区块时间戳之差",25,PALE)
    pic(805,188,403,351,"trace.png","复核器核对同一来源的三条公开交易")
    txt(806,552,402,41,"项目复核器的实际画面",20,SLATE)
    footer("2026.11.27 · 源日志序号 2。点击表中事件名，可打开三笔交易。",True)

    new(CREAM,[SRC+"model/MODEL_CARD.md",SRC+"evidence/public-run.json",ORACLES])
    heading("一次报价偏离，够不够升级复核？","模型需要报价历史及两项独立美元参考价。公网演示使用模拟的 USDC/USDT 报价。")
    txt(62,208,650,54,"公开运行的决定",34,TEAL,True)
    txt(64,284,661,75,"证据不足，暂缓评分。",44,INK,True)
    txt(64,371,640,47,"链上告警保留，等待补充同期市场证据。",25,MUTED)
    pic(63,459,600,121,"decision.png","真实复核器的输出，公开运行没有评分")
    txt(740,210,479,57,"同一告警的合成对照",31,INK,True)
    txt(740,293,464,53,"USDC 参考价 $0.9904",29,TEAL,True)
    txt(740,352,466,47,"走势也持续走弱，升级复核。",23,MUTED)
    txt(740,432,464,53,"USDC 参考价 $0.9999",29,TEAL,True)
    txt(740,491,470,78,"两项参考价都接近平价，继续观察。",23,MUTED)
    footer("两个对照场景均为合成输入。USDT 在两种情形中的参考价均为 $1.0001。")

    new(DARK,[SRC+"tests/StablecoinGuards.t.sol",SRC+"evidence/forge-guards.txt",SRC+"README.md#出问题怎么办"])
    heading("自动化最多能花多少钱？","项目只记录告警，动用的 USDC 和 USDT 本金均为零。",True)
    tbl(62,224,[225,231,248],66,[
        ["付款合约","单次服务费上限","累计服务费上限"],
        ["ReactiveAlert","0.05 lREACT","0.30 lREACT"],
        ["AlertSink","0.00025 ETH","0.002 ETH"]],True,font_size=21)
    txt(65,480,695,45,"同一日志只请求一次，同一回调只写入一次。",25,PALE,True)
    txt(65,546,685,40,"余额耗尽时暂停，充值不增加剩余累计额度。",22,SLATE)
    txt(827,242,360,98,"15/15",77,MINT,True,NUM)
    txt(832,368,342,52,"Foundry 测试通过",29,PALE,True)
    txt(833,439,364,54,"0 项失败  ·  0 项跳过",23,SLATE)
    footer("金额上限已在新版合约本地验证。公开运行使用加设上限前的版本。",True)

    new(CREAM,[PROJECT_URL,*urls,SDG10,SDG16])
    txt(63,57,805,49,"Reactive PegPulse  /  Web3 Commons",26,TEAL,True,NUM)
    txt(60,125,811,82,"没有钱包，也能核验吗？",53,INK,True)
    txt(65,244,770,54,"SDG 10.2 · 包容参与",31,TEAL,True,link=SDG10)
    txt(65,302,778,65,"志愿者打开浏览器即可读回执，配有双语文字稿。",26,INK)
    txt(65,392,770,54,"SDG 16.6 · 透明问责",31,TEAL,True,link=SDG16)
    txt(65,453,771,64,"公开源日志和模型所缺证据，社区可自行核查。",26,INK)
    txt(65,541,783,57,"下一步将实测社区成员独立核验的完成率。",23,MUTED)
    pic(873,141,340,340,"avatar.jpg","Sunshine 的蓝帽数字分身")
    txt(874,503,343,60,"Sunshine  /  3S Lab",23,MUTED,True,NUM)
    footer("两项 SDG 是设计目标。用户实测将检验这些做法是否降低核验门槛。")

    qa=[
      ("Execution","如何确认目标链真的执行了？","查 Base 接收合约的 PriceDeviation 事件。","对照源交易哈希、源日志序号 2 和事件 ID。","打开目标链回执",urls[2]),
      ("Integration","有了价格预言机，Reactive 做什么？","预言机可提供美元参考价。","Lasna 的 react() 核对来源、阈值及重复事件，再向 Base 请求回调。此次测试使用模拟报价。","打开 Lasna 执行交易",urls[1]),
      ("Usefulness","一个池子下跌就等于脱锚吗？","单池偏离足以启动调查。","判定复核优先级还需要历史走势和两个独立美元参考价。","打开模型卡",SRC+"model/MODEL_CARD.md"),
      ("Craft","回调失败或重放怎么办？","失败回调不会增加目标链告警数。","核对余额、欠费和事件；授权重投同一日志最多记录一次。","打开失败处理说明",SRC+"README.md#出问题怎么办")
    ]
    for i,(label,question,answer,detail,link,url) in enumerate(qa):
        new(DARK,[url,OFFICIAL]+([REACTIVE_DOC,ORACLES] if label=="Integration" else []))
        txt(64,49,1164,63,"预录模拟问答  /  "+label,35,MINT,True)
        pic(65,157,318,318,"avatar.jpg","预录模拟问答中的数字讲者")
        txt(67,507,345,44,"Sunshine  /  3S Lab",23,SLATE,False,NUM)
        txt(434,159,783,86,question,41,PALE,True)
        txt(437,297,758,89,answer,31,LAV,True)
        txt(437,400,740,89,detail.replace("；","。"),25,SLATE)
        txt(438,544,650,50,link,23,MINT,True,link=url)
        footer("预设问题由数字分身朗读。现场追问可由主持人记录，讲者会后书面回复。",True)
    return slides


def write_pptx(slides,out):
    from pptx import Presentation
    from pptx.util import Pt,Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN,MSO_ANCHOR,MSO_AUTO_SIZE
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.oxml.ns import qn
    prs=Presentation()
    px=lambda v:Emu(round(v*9525))
    rgb=lambda v: RGBColor.from_string(v.lstrip("#"))
    prs.slide_width,prs.slide_height=px(1280),px(720)
    def write(frame,text,size,color,bold=False,font=FONT,link=None):
        frame.clear();frame.word_wrap=True;frame.auto_size=MSO_AUTO_SIZE.NONE
        frame.margin_left=frame.margin_right=frame.margin_top=frame.margin_bottom=0
        frame.vertical_anchor=MSO_ANCHOR.TOP
        for ix,line in enumerate(text.split("\n")):
            para=frame.paragraphs[0] if ix==0 else frame.add_paragraph()
            para.alignment=PP_ALIGN.LEFT;para.space_before=para.space_after=Pt(0)
            run=para.add_run();run.text=line
            if link:run.hyperlink.address=link
            run.font.name=font;run.font.size=Pt(size*.75);run.font.bold=bold;run.font.color.rgb=rgb(color)
            rpr=run._r.get_or_add_rPr()
            for tag in ("ea","cs"):
                node=rpr.find(qn("a:"+tag))
                if node is None:node=OxmlElement("a:"+tag);rpr.append(node)
                node.set("typeface",font)
    for s in slides:
        slide=prs.slides.add_slide(prs.slide_layouts[6]);bg=slide.background.fill;bg.solid();bg.fore_color.rgb=rgb(s["bg"])
        for item in s["items"]:
            x,y,w,h=map(px,item["box"])
            if item["kind"]=="text":
                sh=slide.shapes.add_textbox(x,y,w,h)
                write(sh.text_frame,item["text"],item["size"],item["colour"],item["bold"],item["font"])
                if item.get("link"):sh.click_action.hyperlink.address=item["link"]
            elif item["kind"]=="image":
                shape=slide.shapes.add_picture(str(HERE.parent/"media"/item["file"]),x,y,w,h)
                shape._element.nvPicPr.cNvPr.set("descr",item["alt"])
            else:
                vals=item["values"];table=slide.shapes.add_table(len(vals),len(vals[0]),x,y,w,h).table
                for j,width in enumerate(item["widths"]):table.columns[j].width=px(width)
                for i,row in enumerate(vals):
                    table.rows[i].height=px(item["rowh"])
                    for j,value in enumerate(row):
                        cell=table.cell(i,j);cell.fill.solid();cell.fill.fore_color.rgb=rgb("#263648" if i==0 else DARK)
                        ln=item["links"].get(f"{i},{j}")
                        write(cell.text_frame,value,item["size"],MINT if i==0 or ln else PALE,i==0,FONT)
                        cell.margin_left=px(8);cell.margin_right=px(5);cell.margin_top=px(6);cell.margin_bottom=0
                        cell.vertical_anchor=MSO_ANCHOR.MIDDLE
                        if ln:
                            hit=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,x+px(sum(item["widths"][:j])),
                                y+px(item["rowh"]*i),px(item["widths"][j]),px(item["rowh"]))
                            hit.fill.background();hit.line.fill.background()
                            hit.click_action.hyperlink.address=ln;hit.name=value+" · block explorer"
        slide.notes_slide.notes_text_frame.text=s["notes"]
    props = prs.core_properties
    props.title = TITLE
    props.author = props.last_modified_by = "Sunshine"
    props.subject = TEAM + " · Reactive Meets AI · Reactive Builder Camp Demo Day"
    props.comments = "Bilingual prerecorded presentation and simulated Q&A."
    prs.save(out)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("output",type=Path);a=p.parse_args()
    slides=make_spec()
    if a.output.suffix==".json":a.output.write_text(json.dumps(slides,ensure_ascii=False)+"\n")
    else:write_pptx(slides,a.output)
