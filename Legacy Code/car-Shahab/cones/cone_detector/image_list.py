import wx
import glob
import os
from util import glob_files, labels_fn, load_labels
from cone_detector import log
import config


class ImageList(wx.Panel):
    def __init__(self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size(300, 0), style = wx.TAB_TRAVERSAL):
        super(self.__class__, self).__init__(parent, id, pos, size, style)
        self.list = wx.ListCtrl(self, id = wx.ID_ANY,
                                pos = wx.DefaultPosition,
                                size = wx.Size(300, 0),
                                style = wx.LC_REPORT | wx.LC_SINGLE_SEL)

        self.list.InsertColumn(0, 'Name', width = 200)
        self.list.InsertColumn(1, 'Y', width = 25)
        self.list.InsertColumn(2, 'B', width = 25)
        self.list.InsertColumn(3, 'S', width = 25)
        self.list.InsertColumn(4, 'R', width = 25)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.list, 1, wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(box)

    def scan_images(self):
        # self.fns = sorted(glob.glob('./data/amz/*.png'))
        log('Scanning the data folder for images...')

        self.fns = sorted(glob_files(config.DATA_PREFIX, ['*.png', '*.jpg']))
        truncate = len(config.DATA_PREFIX) + 1
        total_count = [0] * 5

        for fn in self.fns:
            # name, ext = os.path.splitext(os.path.basename(fn))
            # self.InsertStringItem(self.GetItemCount(), name + ext)
            bboxes = load_labels(labels_fn(fn))
            count = [0] * 5
            for bb in bboxes:
                count[bb[4]] += 1
                total_count[bb[4]] += 1
            pos = self.list.InsertStringItem(self.list.GetItemCount(), fn[truncate:])
            self.set_bbox_count(count, pos)
        log('Found ' + str(total_count[1]) + ' yellow, ' +
            str(total_count[2]) + ' blue, ' +
            str(total_count[3]) + ' solid, ' +
            str(total_count[4]) + ' red cones (' +
            str(sum(total_count)) + ' in total) in ' + str(len(self.fns)) + ' images.')


    def set_bbox_count(self, count, pos = None):
        if pos is None:
            pos = self.selected_idx()
        if count[1] > 0:
            self.list.SetStringItem(pos, 1, str(count[1]))
        if count[2] > 0:
            self.list.SetStringItem(pos, 2, str(count[2]))
        if count[3] > 0:
            self.list.SetStringItem(pos, 3, str(count[3]))
        if count[4] > 0:
            self.list.SetStringItem(pos, 4, str(count[4]))

        
    def selected_idx(self):
        return self.list.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
        
    def select_next_image(self):
        idx = self.selected_idx()
        if idx < self.list.GetItemCount() - 1:
            self.list.Select(idx + 1)
            self.list.EnsureVisible(idx + 1)

    def select_next_image_page(self):
        idx = min(self.selected_idx() + 10, self.list.GetItemCount() - 1)
        self.list.Select(idx)
        self.list.EnsureVisible(idx)

    def select_prev_image(self):
        idx = self.selected_idx()
        if idx > 0:
            self.list.Select(idx - 1)
            self.list.EnsureVisible(idx - 1)

    def select_prev_image_page(self):
        idx = max(self.selected_idx() - 10, 01)
        self.list.Select(idx)
        self.list.EnsureVisible(idx)

    def select_first_image(self):
        self.list.Select(0)
        self.list.EnsureVisible(0)

    def select_last_image(self):
        N = self.list.GetItemCount()
        self.list.Select(N - 1)
        self.list.EnsureVisible(N - 1)
