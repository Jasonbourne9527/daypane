"""V1 output, calendar edge cases, and footer exit lifecycle."""
import importlib.util
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from PIL import ImageFont
import kindle_plugin_test as harness

spec = importlib.util.spec_from_file_location('daypane', Path(__file__).parents[1] / 'tools/daypane_v1.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class DaypaneTests(unittest.TestCase):
    def test_seasons_leap_day_and_six_week_calendar(self):
        font = lambda size: ImageFont.load_default(size=size)
        for month,day in [(2,29),(3,31),(6,30),(9,30),(12,31)]:
            with self.subTest(month=month), tempfile.TemporaryDirectory() as tmp:
                im = r.render_daypane({'weather': {'ok': False}}, tmp+'/screen.png', font,
                                      datetime(2024,month,day,23,59))
                self.assertEqual(im.size,(1448,1072))
                self.assertEqual(im.mode,'1')

    def test_footer_exit_only_on_landscape_button(self):
        harness.lua.execute('''
        package.preload['ui/event']=function() return {new=function(_,name) return {name=name} end} end
        local count=0
        function UI:broadcastEvent(event) assert(event.name=='Exit');count=count+1 end
        local d=Plugin:new{}
        d.releaseNetwork=function() end
        d.holdScreen=function() end
        d.armAutoRefresh=function() end
        local screen=d:buildScreen('unused',1448,1072)
        screen:onTapScroll(nil,{pos={x=100,y=700}})
        assert(count==0)
        screen:onTapScroll(nil,{pos={x=100,y=990}})
        assert(count==1 and d.dash_widget==nil and d._busy==false)
        local portrait=d:buildScreen('unused',1072,1448)
        portrait:onTapScroll(nil,{pos={x=100,y=1400}})
        assert(count==1)
        portrait:onTapScroll(nil,{pos={x=100,y=10}})
        assert(count==1)
        ''')

    def test_landscape_rotation_fullscreen_and_restore(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            Image.new('1',(1448,1072),1).save(tmp+'/landscape.png')
            Image.new('1',(1072,1448),1).save(tmp+'/portrait.png')
            harness.lua.globals().IMAGE_DIR=tmp
            harness.lua.execute('''
            local screen=require('device').screen
            local old_w,old_h=screen.getWidth,screen.getHeight
            local old_get,old_set=screen.getRotationMode,screen.setRotationMode
            local mode=0
            function screen:getRotationMode() return mode end
            function screen:setRotationMode(value) mode=value end
            function screen:getWidth() return mode%2==0 and 1072 or 1448 end
            function screen:getHeight() return mode%2==0 and 1448 or 1072 end
            for _,initial in ipairs({0,2,1,3}) do
                mode=initial
                local d=Plugin:new{}
                d.option=function() return false end
                d.holdScreen=function() end
                d.releaseNetwork=function() end
                d.armAutoRefresh=function() end
                d.record=function() end
                assert(d:showDashboard(IMAGE_DIR..'/landscape.png'))
                local widget=d.dash_widget
                assert(widget.fullscreen and widget.covers_fullscreen)
                assert(widget.dimen.w==1448 and widget.dimen.h==1072)
                local filled=false
                widget:paintTo({paintRect=function(_,x,y,w,h,color)
                    assert(x==0 and y==0 and w==1448 and h==1072 and color==255)
                    filled=true
                end},0,0)
                assert(filled)
                -- Refresh must not replace the original rotation with landscape.
                assert(d:showDashboard(IMAGE_DIR..'/landscape.png'))
                d.dash_widget:onBack()
                assert(mode==initial and d._dashboard_rotation==nil)
            end
            mode=0
            local d=Plugin:new{}
            d.record=function() end
            d.buildScreen=function() error('decode failed') end
            assert(not d:showDashboard(IMAGE_DIR..'/landscape.png'))
            assert(mode==0 and d._dashboard_rotation==nil)
            d:prepareDashboardRotation(IMAGE_DIR..'/portrait.png')
            assert(mode==0)
            screen.getWidth,screen.getHeight=old_w,old_h
            screen.getRotationMode,screen.setRotationMode=old_get,old_set
            ''')

    def test_local_minute_clock_without_network_and_timer_cleanup(self):
        harness.lua.execute('''
        local old_time=os.time
        local now=1793289605 -- UTC midnight at China time 08:00:05
        os.time=function() return now end
        local d=Plugin:new{}
        d.option=function(_,_,default) return default end
        local widget=d:buildScreen('unused',1448,1072)
        d.dash_widget=widget
        local redraws=0
        local old_dirty=UI.setDirty
        function UI:setDirty(target,kind,rect)
            assert(target==widget and kind=='partial' and rect==widget.clock_rect)
            redraws=redraws+1
        end
        widget:armClock()
        assert(UI.queue[widget._clock_tick]==55)
        widget:paintTo({paintRect=function() end},0,0)
        assert(DRAWN_TIME==os.date('!%H:%M',now+8*3600))
        now=now+55
        widget._clock_tick()
        assert(redraws==1 and UI.queue[widget._clock_tick]==60)
        widget:paintTo({paintRect=function() end},0,0)
        assert(DRAWN_TIME==os.date('!%H:%M',now+8*3600))
        widget:stopClock()
        assert(UI.queue[widget._clock_tick]==nil)
        d._suspended=true;widget:armClock()
        assert(UI.queue[widget._clock_tick]==nil)
        d._suspended=false;widget:armClock()
        assert(UI.queue[widget._clock_tick]==60)
        widget:onCloseWidget()
        assert(UI.queue[widget._clock_tick]==nil)
        UI.setDirty=old_dirty
        os.time=old_time
        ''')

    def test_startup_uses_cache_and_respects_opt_out(self):
        harness.lua.execute('''
        local d=Plugin:new{}
        d.option=function(_,_,default) return default end
        d.cacheImg=function() return 'cached.png' end
        d.fileExists=function() return true end
        local calls={}
        d.showDashboard=function(_,path,offline)
            assert(path=='cached.png' and offline);table.insert(calls,'cache')
        end
        d.requestRefresh=function(_,silent,manual)
            assert(silent and not manual);table.insert(calls,'refresh')
        end
        d:scheduleStartup()
        assert(UI.queue[d._startup_tick]==1)
        d._startup_tick()
        assert(calls[1]=='cache' and calls[2]=='refresh' and d._startup_tick==nil)
        d.option=function() return false end
        d:scheduleStartup();assert(d._startup_tick==nil)
        ''')

    def test_weather_icons_follow_wmo_codes(self):
        from PIL import Image, ImageDraw
        groups = {
            'sun': [0], 'partly_cloudy': [1, 2], 'cloud': [3], 'fog': [45, 48],
            'rain': [51,53,55,56,57,61,63,65,66,67,80,81,82],
            'snow': [71,73,75,77,85,86], 'thunder': [95,96,99],
            'unknown': [None, -1, 999],
        }
        for kind,codes in groups.items():
            for code in codes:
                self.assertEqual(r.weather_icon_kind(code),kind)
                im=Image.new('L',(110,110),255)
                r.draw_weather_icon(ImageDraw.Draw(im),code,0,0)
                self.assertLess(min(im.getdata()),255)
