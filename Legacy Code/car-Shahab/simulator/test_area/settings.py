import collections.abc
import wx
import wx.propgrid as wxpg
import wx.lib.agw.floatspin as fs
from log import log
from config import config

class Settings(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id, pos, size, style)

        pg = wxpg.PropertyGridManager(
            self,
            wx.ID_ANY,
            style= wxpg.PG_SPLITTER_AUTO_CENTER |
            wxpg.PG_TOOLBAR |
            # wxpg.PG_DESCRIPTION |
            wxpg.PGMAN_DEFAULT_STYLE
        )

            
        # page = pg.AddPage("First Page")
        pg.Append(wxpg.PropertyCategory("Car"))
        # self.append_bool_property(pg, "Do cone detection", "CD_ENABLE", config.CD_ENABLE)
        # pg.Append(wxpg.FileProperty("Cascade detector model", "CD_FILENAME", value=config.CD_FILENAME))
        pg.Append(wxpg.FloatProperty("Scale factor", name="CD_SCALE_FACTOR", value=config.CD_SCALE_FACTOR))
        # pg.Append(wxpg.IntProperty("Merge threshold", name="CD_MERGE_THRESHOLD", value=config.CD_MERGE_THRESHOLD))
        # pg.Append(SizeProperty("Min size", "CD_MIN_SIZE", value=config.CD_MIN_SIZE))
        # pg.Append(SizeProperty("Max size", "CD_MAX_SIZE", value=config.CD_MAX_SIZE))
        # self.append_bool_property(pg, "Use region of interest", "CD_USE_ROI", config.CD_USE_ROI)
        # pg.Append(wxpg.FloatProperty("ROI truncate top, %", name="CD_ROI_TOP", value=config.CD_ROI_TOP))
        # pg.Append(wxpg.FloatProperty("ROI truncate bottom, %", name="CD_ROI_BOTTOM", value=config.CD_ROI_BOTTOM))

        # pg.Append(wxpg.PropertyCategory("Appearance Model"))
        # pg.Append(wxpg.DirProperty("AM folder", value="../models/am_svm"))
        # self.append_bool_property(pg, "Filter detections", "AM_FILTER_DETECTIONS", config.AM_FILTER_DETECTIONS)
        # self.append_bool_property(pg, "Refine detections", "AM_REFINE_DETECTIONS", config.AM_REFINE_DETECTIONS)
        # pg.Append(wxpg.FloatProperty("AM variance threshold", value=3.5))
        # pg.Append(wxpg.FloatProperty("Absolute SVM threshold", "AM_ABS_THRESHOLD", value=config.AM_ABS_THRESHOLD))
        # pg.Append(wxpg.FloatProperty("Refinement precision", value=0.5))

        # pg.Append(wxpg.PropertyCategory("Video Source"))
        # pg.Append(wxpg.EnumProperty("Video source", labels=['Camera', 'Image folder'], values=[0, 1], value=1))
        # pg.Append(wxpg.DirProperty("Image folder", value="../../data/cones/amz/every10"))
        # pg.Append(wxpg.IntProperty("Left camera device ID", value=0))
        # pg.Append(wxpg.IntProperty("Right camera device ID", value=1))
        # self.append_bool_property(pg, "Stereo", "STEREO", config.STEREO)

        pg.Append(wxpg.PropertyCategory("Visualisation"))
        self.append_bool_property(pg, "High DPI display fix", "HIDPI", True)
        # self.append_bool_property(pg, "Show original detections", "SHOW_ORIGINAL_DETECTIONS", True)
        # self.append_bool_property(pg, "Show refined detections", "SHOW_REFINED_DETECTIONS", True)
        # self.append_bool_property(pg, "Show centres", "SHOW_CENTRES", config.SHOW_CENTRES)
        # self.append_bool_property(pg, "Show epipolar lines", "SHOW_EPIPOLAR", True)
        # self.append_bool_property(pg, "Show reprojections", "SHOW_REPROJECTIONS", True)
        # self.append_bool_property(pg, "Show 3D coordinates", "SHOW_3D_COORDINATES", True)

        # pg.Append(wxpg.PropertyCategory("3D Reconstruction"))
        # pg.Append(wxpg.FileProperty("Stereo calibration parameters", value="../../data/local/calib/stereoParams.mat"))
        # self.append_bool_property(pg, "Do stereo reconstruction", "DO_STEREO", True)

        pg.Bind(wxpg.EVT_PG_CHANGED, self.OnChange)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(pg, 1, wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(box)


    def append_bool_property(self, pg, label, name, val):
        prop = wxpg.BoolProperty(label, name, value=val)
        pg.SetPropertyAttribute(prop, "UseCheckbox", True)
        pg.Append(prop)

        
    def OnChange(self, event):
        p = event.GetProperty()
        name = p.GetName()
        if p:
            log('%s changed to "%s"\n' % (name, p.GetValueAsString()))

        if hasattr(config, name):
            log('INFO: Config has attribute %s.' % name)
            log('INFO: Previous value: %s' % str(getattr(config, name)))
            setattr(config, name, p.GetValue())
        else:
            log('WARNING: Config does not have attribute %s.' % name)



class SizeProperty(wxpg.PGProperty):
    def __init__(self, label, name = "Size", value=wx.Size(0, 0)):
        wxpg.PGProperty.__init__(self, label, name)

        value = self._ConvertValue(value)

        self.AddPrivateChild(wxpg.IntProperty("H", value=value.x))
        self.AddPrivateChild(wxpg.IntProperty("W", value=value.y))

        self.m_value = value

        
    def GetClassName(self):
        return self.__class__.__name__

    
    def GetEditor(self):
        return "TextCtrl"

    
    def RefreshChildren(self):
        size = self.m_value
        self.Item(0).SetValue( size.x )
        self.Item(1).SetValue( size.y )

        
    def _ConvertValue(self, value):
        # from operator import isSequenceType
        if isinstance(value, wx.Point):
            value = wx.Size(value.x, value.y)
        elif isinstance(value, collections.abc.Sequence):
            value = wx.Size(*value)
        return value

    
    def ChildChanged(self, thisValue, childIndex, childValue):
        # FIXME: This does not work yet. ChildChanged needs be fixed "for"
        #        wxPython in wxWidgets SVN trunk, and that has to wait for
        #        2.9.1, as wxPython 2.9.0 uses WX_2_9_0_BRANCH.
        size = self._ConvertValue(self.m_value)
        if childIndex == 0:
            size.x = childValue
        elif childIndex == 1:
            size.y = childValue
        else:
            raise AssertionError

        return size
