"""Static vector-like line art composed in Pillow; no generative service."""
import calendar
import sys
import math
from PIL import Image, ImageDraw, ImageOps
from pathlib import Path

def weather_icon_kind(code):
    if code == 0: return 'sun'
    if code in (1, 2): return 'partly_cloudy'
    if code == 3: return 'cloud'
    if code in (45, 48): return 'fog'
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82): return 'rain'
    if code in (71, 73, 75, 77, 85, 86): return 'snow'
    if code in (95, 96, 99): return 'thunder'
    return 'unknown'


def draw_weather_icon(draw, code, x=700, y=397):
    """WMO codes from the same payload as the temperature and weather label."""
    kind = weather_icon_kind(code)
    def line(points, width=3):
        draw.line([(x+a,y+b) for a,b in points], fill=0, width=width, joint='curve')
    def sun(cx,cy,r):
        draw.ellipse((x+cx-r,y+cy-r,x+cx+r,y+cy+r),outline=0,width=3)
        for angle in range(0,360,45):
            a=math.radians(angle)
            line([(cx+(r+7)*math.cos(a),cy+(r+7)*math.sin(a)),
                  (cx+(r+16)*math.cos(a),cy+(r+16)*math.sin(a))])
    if kind == 'unknown':
        draw.text((x+30,y+15),'?',fill=0)
        return
    if kind == 'sun':
        sun(48,44,20)
        return
    if kind == 'partly_cloudy': sun(66,26,14)
    # Continuous cloud silhouette, without seams between overlapping circles.
    cloud=[(13,59),(8,57),(5,52),(5,46),(8,41),(14,38),(21,39),
           (22,30),(26,23),(33,20),(41,21),(48,25),(52,33),
           (60,31),(68,33),(74,39),(76,44),(84,44),(91,48),
           (94,54),(93,60),(89,65),(82,67),(15,67),(10,64),(13,59)]
    draw.polygon([(x+a,y+b) for a,b in cloud],fill=255)
    line(cloud)
    if kind == 'rain':
        for a in (26,49,72): line([(a,76),(a-6,88)])
    elif kind == 'snow':
        for a in (27,52,77):
            line([(a-5,81),(a+5,81)],2)
            line([(a,76),(a,86)],2)
            line([(a-4,77),(a+4,85)],2)
            line([(a-4,85),(a+4,77)],2)
    elif kind == 'thunder':
        line([(50,73),(39,85),(51,85),(44,97)],4)
    elif kind == 'fog':
        line([(12,77),(85,77)])
        line([(21,88),(76,88)])


def render_daypane(data, path, font, now):
    from lunar_python import Solar
    im = Image.new('L', (1448, 1072), 255)
    d = ImageDraw.Draw(im)
    def text(x,y,s,size=30):
        d.text((x,y),str(s),font=font(size),fill=0)
    text(64,40,'D A Y P A N E   /   日 常',26)
    d.line((64,100,1384,100),fill=0,width=2)
    text(64,120,now.strftime('%H:%M'),168)
    text(72,330,f'{now.year} 年 {now.month} 月 {now.day} 日   星期'+ '一二三四五六日'[now.weekday()],35)
    w=data.get('weather') or {}
    text(72,405,f"{w.get('city','')}   {w.get('temp','—')}°C   {w.get('text','')}" if w.get('ok') else '天气暂不可用',38)
    if w.get('ok'):
        draw_weather_icon(d, w.get('code'))
    # A single generated asset, reused on every cloud run (no image API calls).
    with Image.open(Path(__file__).parent / 'golden-retriever.png') as asset:
        dog = ImageOps.contain(asset.convert('L'), (444, 330), Image.Resampling.LANCZOS)
        dog = dog.point(lambda value: 0 if value < 215 else 255)
        im.paste(dog, (940 + (444 - dog.width) // 2, 170 + (330 - dog.height) // 2))
    season=((now.month % 12)//3 + 3) % 4
    for x,y in [(1280,140),(1330,175),(1300,100)]:
        if season==3:  # winter snowflakes
            for dx,dy in [(13,0),(0,13),(9,9),(9,-9)]:
                d.line((x-dx,y-dy,x+dx,y+dy),fill=0,width=2)
        elif season==0:  # spring blossoms
            for dx,dy in [(0,-9),(9,0),(0,9),(-9,0)]:
                d.ellipse((x+dx-6,y+dy-6,x+dx+6,y+dy+6),outline=0,width=2)
        elif season==1:  # summer leaves
            d.ellipse((x-8,y-14,x+8,y+14),outline=0,width=2)
            d.line((x,y-10,x,y+18),fill=0,width=2)
        else:  # autumn fallen leaves
            d.polygon([(x,y-14),(x+12,y),(x,y+14),(x-8,y)],outline=0,width=2)
            d.line((x,y-10,x-5,y+20),fill=0,width=2)
    d.line((64,560,1384,560),fill=0,width=2)
    text(72,590,f'{now.month:02d} / 月历',32)
    for j,s in enumerate('一二三四五六日'): text(74+j*65,650,s,24)
    for i,week in enumerate(calendar.monthcalendar(now.year,now.month)):
        for j,day in enumerate(week):
            if day:
                x,y=74+j*65,690+i*36
                if day==now.day: d.ellipse((x-5,y,x+35,y+35),outline=0,width=2)
                text(x,y,day,24)
    lunar=Solar.fromYmd(now.year,now.month,now.day).getLunar()
    text(650,590,'今日黄历',32)
    text(650,652,f'农历 {lunar.getMonthInChinese()}月{lunar.getDayInChinese()}',32)
    eight=lunar
    for y,label,items in [(720,'宜',eight.getDayYi()),(798,'忌',eight.getDayJi())]:
        text(650,y,label,30)
        text(715,y,' · '.join(items[:4]),27)
    text(650,865,'传统民俗参考',21)
    d.rectangle((64,958,1384,1032),outline=0,width=2)
    text(100,970,'打开 Kindle 原生界面  →',34)
    text(970,984,'退出 KOReader 后选书阅读',23)
    im=im.convert('1')
    im.save(path if path else sys.stdout.buffer,format='PNG')
    return im
