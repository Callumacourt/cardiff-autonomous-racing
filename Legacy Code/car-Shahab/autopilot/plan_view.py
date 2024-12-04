import wx
# import wx.lib.agw.aui as aui
# import wx.lib.mixins.inspection as wit
import matplotlib as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.collections import LineCollection


class PlanView(wx.Panel):                                             #https://wxpython.org/Phoenix/docs/html/wx.Panel.html
    def __init__(self, parent, id=-1, dpi=None, **kwargs):            #creating figure based on coordinates
        wx.Panel.__init__(self, parent, id=id, **kwargs) 
        self.figure = plt.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = FigureCanvas(self, -1, self.figure)
        # self.toolbar = NavigationToolbar(self.canvas)
        # self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND)
        # sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizerAndFit(sizer)

        self.h_plan_y = None          # Default function for draw function        
        self.h_plan_b = None
        self.h_tri = None
        self.h_ctr = None
        self.h_ctr_i = None
        # self.h_plan_prev = None
        self.h_e_y = None
        self.ax = self.figure.gca()

    # @profile
    def draw(self, plan_y, plan_b, plan_all, tri, ctr, ctr_i, lines_y, lines_b, X, V, traj_best, traj_all, frame):
        ax = self.ax
        # ax.clear()
        lc_y = LineCollection(lines_y, colors='y')                           # Plotting yellow line
        lc_b = LineCollection(lines_b, colors='b')                           # Plotting blue line
        if self.h_plan_y is None:                                            # Defining parameters in there is no input
            ax.grid(True, linestyle='--')
            self.h_field = ax.quiver(X[:, 0], X[:, 1], V[:, 0], V[:, 1], color='c', scale=200)
            self.h_edges_y = ax.add_collection(lc_y)
            self.h_edges_b = ax.add_collection(lc_b)
            self.h_plan_y = ax.plot(plan_y[:, 0], plan_y[:, 1], 'yo')[0]
            self.h_plan_b = ax.plot(plan_b[:, 0], plan_b[:, 1], 'bo')[0]
            # self.h_target = ax.plot(target[0], target[1], 'r*')[0]
            self.h_ctr = ax.plot(ctr[:, 0], ctr[:, 1], 'r.', lw=4.0, markersize=8)[0]
            # if len(ctr_i) > 0:
            self.h_ctr_i = ax.plot(ctr_i[:, 0], ctr_i[:, 1], 'g')[0]
            # self.h_pred = ax.plot(pred[:, 0], pred[:, 1], 'k')[0]
            # self.h_traj_best = ax.plot(traj_best[:, 1], traj_best[:, 0], 'r')[0]
            self.h_traj_all = ax.plot(traj_all[:, 1], traj_all[:, 0], 'k.', markersize=1)[0]
            ax.set_xlim(xmin=-10, xmax=10)
            ax.set_ylim(ymin=0.0, ymax=20.0)
        else:                                                                # Defining parameters with the inputed variables
            self.h_edges_y.set_segments(lines_y)
            self.h_edges_b.set_segments(lines_b)
            self.h_plan_y.set_data(plan_y[:, 0], plan_y[:, 1])
            self.h_plan_b.set_data(plan_b[:, 0], plan_b[:, 1])
            # self.h_target.set_data(target[0], target[1])
            self.h_ctr.set_data(ctr[:, 0], ctr[:, 1])
            if len(ctr_i) > 0:
                self.h_ctr_i.set_data(ctr_i[:, 0], ctr_i[:, 1])
            # self.h_pred.set_data(pred[:, 0], pred[:, 1])
            self.h_field.set_UVC(V[:, 0], V[:, 1])
            # self.h_traj_best.set_data(traj_best[:, 1], traj_best[:, 0])
            self.h_traj_all.set_data(traj_all[:, 1], traj_all[:, 0])
            
        if tri.shape[0] > 0:                                                 # If variable 'tri' value has more than zero dimensions 
            tri_x = [plan_all[tri[:, 0], 0],                                 # Defining x-axis 'tri'
                     plan_all[tri[:, 1], 0],
                     plan_all[tri[:, 2], 0],
                     plan_all[tri[:, 0], 0]]
            tri_y = [plan_all[tri[:, 0], 1],                                 # defining y-axis 'tri'
                     plan_all[tri[:, 1], 1],
                     plan_all[tri[:, 2], 1],
                     plan_all[tri[:, 0], 1]]
            if self.h_tri is not None:                                       # Defining y and x axis parameters when there is no variable input                    
                try:
                    ax.lines.remove(self.h_tri[0])
                    ax.lines.remove(self.h_tri[1])
                except:
                    pass
            self.h_tri = ax.triplot(plan_all[:, 0], plan_all[:, 1], tri, 'k:')    #Defining variable for ploting tri 
        else:                                                                # If variable 'tri' has zero dimensions 
            if self.h_tri is not None:                                       # Defining y and x axis parameters when there is no variable input 
                try:
                    ax.lines.remove(self.h_tri[0])
                    ax.lines.remove(self.h_tri[1])
                except:
                    pass

        # self.figure.savefig("out_mppi/%06d.png" % frame)

