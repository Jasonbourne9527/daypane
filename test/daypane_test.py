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
