"""Static vector-like line art composed in Pillow; no generative service."""
import calendar
import sys
from PIL import Image, ImageDraw

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
    # One fixed dog, with sparse seasonal decoration.
    d.ellipse((1060,250,1300,390),outline=0,width=5)
    d.ellipse((1000,140,1190,315),fill=255,outline=0,width=5)
    d.ellipse((985,169,1027,267),fill=255,outline=0,width=5)
    d.ellipse((1165,169,1207,267),fill=255,outline=0,width=5)
    for x in (1050,1134): d.ellipse((x,210,x+9,219),fill=0)
    d.ellipse((1087,241,1104,253),fill=0)
    d.arc((1073,245,1117,279),0,180,fill=0,width=3)
    for x in (1100,1240): d.line((x,365,x,422,x+35,422),fill=0,width=5)
    d.arc((1270,210,1350,330),230,80,fill=0,width=5)
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
