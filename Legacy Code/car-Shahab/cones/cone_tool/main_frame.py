import wx
import wx.aui
import platform
import cv2
from console import Console
from image_editor import ImageEditor
from image_list import ImageList
from util import read_text, write_text
from log import log

LAST_IMAGE_FN = 'last_image.txt'


class MainFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='Cone Annotation Tool',
                 pos=wx.Point(100, 200), size=(1024, 768),
                 style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # self.create_menu()
        self.CreateStatusBar(2)
        self.load_cursors()

        self.manager = wx.aui.AuiManager(self)

        self.console = Console(self)
        self.editor = ImageEditor(self)
        self.image_list = ImageList(self)
        # self.letters_list = LettersList(self)
        # self.text_view = TextView(self)

        # Add the panes to the manager
        self.manager.AddPane(self.editor, wx.CENTER)
        self.manager.AddPane(self.image_list, wx.aui.AuiPaneInfo(
        ).Left().Caption('List').CloseButton(False).Layer(0))
        # self.manager.AddPane(self.letters_list, wx.aui.AuiPaneInfo().Right().Caption('Letters').CloseButton(False).Layer(1))
        # self.manager.AddPane(self.text_view, wx.BOTTOM, 'Text')
        self.manager.AddPane(self.console, wx.BOTTOM, 'Console')
        # Tell the manager to 'commit' all the changes just made
        self.manager.Update()

        self.image_list.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListSelect)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # self.Maximize(True)
        wx.CallAfter(self.after_init)

    def select_last_annotated_image(self):
        try:
            fn = read_text(LAST_IMAGE_FN).rstrip()
            idx = (idx for idx, x in enumerate(
                self.image_list.fns) if fn in x).__next__()
            print(idx)
        except:
            idx = 0
        self.image_list.list.Select(idx)
        self.image_list.list.EnsureVisible(idx)

    def after_init(self):
        wx.SafeYield()
        self.manager.Update()
        self.Refresh()
        self.SetFocus()
        self.display_help()
        self.editor.OnDraw()
        # self.editor.Resize()
        # self.editor.SetFocus()
        # self.editor.OnDraw()
        self.image_list.scan_images()
        self.select_last_annotated_image()
        self.editor.auto_zoom()
        # self.editor.OnDraw()

    def OnKey(self, event):
        focused = wx.Window.FindFocus()
        if isinstance(focused, wx.TextCtrl):
            event.Skip()
            return
        code = event.GetKeyCode()
        if code == ord('D'):
            self.editor.delete()
            self.editor.OnDraw()
        # Selecting different labels
        elif code == ord('1'):
            self.editor.set_label(1)
        elif code == ord('Y'):
            self.editor.set_label(1)
        elif code == ord('2'):
            self.editor.set_label(2)
        elif code == ord('B'):
            self.editor.set_label(2)
        elif code == ord('3'):
            self.editor.set_label(3)
        elif code == ord('S'):
            self.editor.set_label(3)
        elif code == ord('G'):
            self.editor.set_label(3)
        elif code == ord('S'):
            self.editor.set_label(3)
        elif code == ord('4'):
            self.editor.set_label(4)
        elif code == ord('R'):
            self.editor.set_label(4)
        elif code == ord('Z'):
            if wx.GetKeyState(wx.WXK_CONTROL):
                self.editor.undo()
        elif code == ord('Q'):
            if wx.GetKeyState(wx.WXK_CONTROL):
                self.Close()
        elif code == ord('C'):
            self.editor.auto_zoom()
            self.editor.OnDraw()
        elif code == ord('A') or code == wx.WXK_F5:
            self.editor.auto_annotate()
        elif code == wx.WXK_DOWN:
            self.image_list.select_next_image()
        elif code == wx.WXK_PAGEDOWN:
            self.image_list.select_next_image_page()
        elif code == wx.WXK_UP:
            self.image_list.select_prev_image()
        elif code == wx.WXK_PAGEUP:
            self.image_list.select_prev_image_page()
        elif code == wx.WXK_HOME:
            self.image_list.select_first_image()
        elif code == wx.WXK_END:
            self.image_list.select_last_image()
        else:
            event.Skip()

    def OnListSelect(self, event):
        # print(len(self.image_list.fns), event.GetIndex())
        fn = self.image_list.fns[event.GetIndex()]
        write_text(LAST_IMAGE_FN, fn)
        self.editor.load_image(fn)
        self.editor.OnDraw()

    def OnUndo(self, event):
        self.editor.undo()

    def OnQuit(self, event):
        self.Close()

    def OnClose(self, event):
        # del cone_tool.font
        # deinitialize the frame manager
        self.manager.UnInit()
        # delete the frame
        self.Destroy()

    def load_cursors(self):
        pass
        # self.cursor_pencil = wx.Cursor('resources/Cursor.Pencil.png', wx.BITMAP_TYPE_PNG, 7, 24)
        # self.cursor_fill = wx.Cursor('resources/Cursor.PaintBucket.png', wx.BITMAP_TYPE_PNG, 21, 21)

    # def create_menu(self):
    #     menubar = wx.MenuBar()
    #     file = wx.Menu()
    #     edit = wx.Menu()
    #     help = wx.Menu()
    #     # file.Append(wx.ID_OPEN, '&Open', 'Open a new document')
    #     # file.Append(wx.ID_SAVE, '&Save', 'Save the document')
    #     file.AppendSeparator()
    #     quit = wx.MenuItem(file, wx.ID_EXIT, '&Quit\tCtrl+Q', 'Quit the Application')
    #     # quit.SetBitmap(wx.Image('stock_exit-16.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    #     file.AppendItem(quit)

    #     undo = wx.MenuItem(edit, wx.ID_UNDO, '&Undo\tCtrl-Z', 'Undo the last action')
    #     # fill = wx.MenuItem(edit, wx.NewId(), '&Fill\tF', 'Fill')
    #     edit.AppendItem(undo)
    #     # edit.AppendItem(fill)
    #     menubar.Append(file, '&File')
    #     menubar.Append(edit, '&Edit')
    #     # menubar.Append(help, '&Help')

    #     self.Bind(wx.EVT_MENU, self.OnUndo, undo)
    #     self.Bind(wx.EVT_MENU, self.OnQuit, quit)
    #     # self.Bind(wx.EVT_MENU, self.OnFill, fill)

    #     self.SetMenuBar(menubar)

    def display_help(self):
        # return
        log('Cone Annotation Tool. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2018--2019')
        log('')
        log('USAGE:')
        log('Left Click + Drag: Create a new or adjust an existing bounding box. Right Click + Drag: Drag the image around. Mouse Wheel: Zoom in and out.')
        log('C: Auto zoom and center the image. D or DEL: Delete bounding box under cursor. Ctrl-Z: Undo the last action.')
        log('1/2/3/4 or Y/B/G/R: Change label. PgUp/PgDown/Up/Down/Home/End: select images.')
        log('')
        log('OpenCV version:    ' + cv2.__version__)
        log('wxWidgets version: ' + wx.version())
        log('Python version:    ' + platform.python_version())
        log('Running on:        ' + platform.platform())

        # log('A or F5: Automatically annotate image.')
        # log('Ctrl-D: Delete all bounding boxes.')
