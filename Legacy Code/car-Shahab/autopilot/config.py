import configparser
import ast
import wx


CONFIG_FN = 'autopilot.cfg'


class Config(object):
    def __init__(self):
        # Initialise default values first
        self.auto_save = False
        self.init_defaults()
        # Load saved values from the persistent config
        self.load()
        self.auto_save = True
        self.listeners = {}

    def init_defaults(self):
        """Initialise default values"""
        # Cascade detector options
        self.CD_ENABLE = True
        self.CD_INITIAL_SCALE = 1
        self.CD_SCALE_FACTOR = 1.5
        self.CD_PYRAMID_LEVELS = 5
        # File name of the cascade detector model.
        self.CD_FILENAME = 'cnn/net-8-6-6-6-4-do00-bn.mat'
        self.CD_USE_ROI = False
        self.CD_ROI_TOP = 20
        self.CD_ROI_BOTTOM = 20
        self.CD_ABS_THRESHOLD = 1.5

        # Video source options
        self.VIDEO_SOURCE = 0
        self.STEREO = True

        # Visualisation
        self.SHOW_CENTRES = True
        self.HIDPI = True

        # Miscellaneous options

        # In which colour to draw the bounding boxes.
        self.LABEL_COLOURS = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.0], [
            0.0, 0.5, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]

        # In which colour to draw the bounding boxes when they are selected.
        self.LABEL_COLOURS_SELECTED = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.5], [
            0.5, 0.5, 1.0], [0.5, 1.0, 0.5], [1.0, 0.5, 0.5]]

        # Extensions of recognised image file
        self.IMAGE_EXT = ['*.png', '*.jpg', '*.jpeg']

    def add_listener(self, name, listener):
        if name in self.listeners:
            self.listeners[name].append(listener)
        else:
            self.listeners[name] = listener

    def load(self):
        """Load config from file"""
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FN)
        default = self.config['DEFAULT']
        for key in default:
            k = key.upper()
            if hasattr(self, k):
                try:
                    val = ast.literal_eval(default[key])
                except:
                    val = default[key]
                setattr(self, k, val)

    def save(self):
        """Save config to file"""
        if hasattr(self, 'config'):
            with open(CONFIG_FN, 'w') as file:
                self.config.write(file)

    def __setattr__(self, name, value):
        """Automatically save config and execute actions when properties change"""
        super(Config, self).__setattr__(name, value)
        if not(name == "auto_save") and self.auto_save and hasattr(self, 'config'):
            self.config['DEFAULT'][name.lower()] = str(value)
            self.save()

        # Execute actions
        if hasattr(self, 'listeners') and name in self.listeners:
            self.listeners[name]()


config = Config()
