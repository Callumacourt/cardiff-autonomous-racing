import wx
# import wx.lib.agw.aui as aui
# import wx.lib.mixins.inspection as wit
import matplotlib as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.collections import LineCollection


class WorldView(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):         #sets default values for the world view
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = plt.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = FigureCanvas(self, -1, self.figure)
        # self.toolbar = NavigationToolbar(self.canvas)
        # self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)                            #sets default size of canvas
        sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND)
        # sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizerAndFit(sizer)

        self.h_traj_best = None
        self.ax = self.figure.gca()

    # @profile
    def draw(self, traj_best, traj_all):                       #draws the scenery? 
        ax = self.ax
        # lc_traj = LineCollection(traj_all, colors='k')
        # lc_b = LineCollection(lines_b, colors='b')
        if self.h_traj_best is None:                           #if no best trajectory then displays ???
            ax.grid(True, linestyle='--')                                                          
            self.h_traj_all = ax.plot(traj_all[:, 0], traj_all[:, 1], 'k.', markersize=1)[0]
            self.h_traj_best = ax.plot(traj_best[:, 0], traj_best[:, 1], 'r')[0]
            # self.h_edges_y = ax.add_collection(lc_y)
            # self.h_edges_b = ax.add_collection(lc_b)
            # self.h_plan_y = ax.plot(plan_y[:, 0], plan_y[:, 1], 'yo')[0]
            # self.h_plan_b = ax.plot(plan_b[:, 0], plan_b[:, 1], 'bo')[0]
            # self.h_target = ax.plot(target[0], target[1], 'r*')[0]
            # self.h_ctr = ax.plot(ctr[:, 0], ctr[:, 1], 'r', lw=4.0)[0]
            # self.h_ctr_i = ax.plot(ctr_i[:, 0], ctr_i[:, 1], 'g')[0]
            # self.h_pred = ax.plot(pred[:, 0], pred[:, 1], 'k')[0]

            ax.set_xlim(xmin=-100, xmax=100)
            ax.set_ylim(ymin=-100, ymax=100)
        else:                                                             #if best trajectory found, then display it
            self.h_traj_all.set_data(traj_all[:, 1], traj_all[:, 0])
            # self.h_edges_b.set_segments(lines_b)
            # self.h_plan_y.set_data(plan_y[:, 0], plan_y[:, 1])
            # self.h_plan_b.set_data(plan_b[:, 0], plan_b[:, 1])
            # self.h_target.set_data(target[0], target[1])
            # self.h_ctr.set_data(ctr[:, 0], ctr[:, 1])
            # self.h_ctr_i.set_data(ctr_i[:, 0], ctr_i[:, 1])
            # self.h_pred.set_data(pred[:, 0], pred[:, 1])
            
            

