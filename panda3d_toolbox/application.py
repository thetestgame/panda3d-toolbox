"""
Application base class for creating standardized applications using the Panda3D game engine.
This module provides ApplicationBase and HeadlessApplication classes for creating applications. These 
are extensions of the ShowBase class provided by the Panda3D engine.
"""

import sys
import builtins
import traceback

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.ShowBase import ShowBase

from panda3d import core as p3d
from panda3d_toolbox import runtime, prc
import panda3d_vfs as vfs

class Application(ShowBase):
    """
    Custom ShowBase instance for creating standardized applications
    using the Panda3D game engine
    """ 

    def __init__(self, *args, **kwargs):
        """
        Initialize the ApplicationBase instance
        """

        self.load_runtime_configuration()
        ShowBase.__init__(self, *args, **kwargs)
        self.notify = directNotify.newCategory('showbase')
        self.exit_code = 0

        self.set_developer_flag()
        self.set_antialias(prc.get_prc_bool('render-antialias', True))
        self.__showing_frame_rate = prc.get_prc_bool('show-frame-rate-meter', False)

        runtime.base = self
        runtime.task_mgr = self.taskMgr
        runtime.loader = self.loader
        runtime.cam = self.cam
        runtime.camera = self.camera

        self.configure_virtual_file_system()
    
    def load_runtime_configuration(self) -> None:
        """
        Loads the runtime configuration for the application.
        This is intended to be overridden by subclasses if desired.

        Preferably runtime configuration would be set prior to the instantiation
        of the ApplicationBase instance in the main entry point of the application.
        """
    
    def set_developer_flag(self) -> None:
        """
        Sets the developer flag for the application based on PRC configuration
        and the current compiled state of the application.
        """

        is_compiled = runtime.is_built_executable()
        want_dev = prc.get_prc_bool('want-dev', is_compiled)
        builtins.__dev__ = want_dev

    def configure_virtual_file_system(self) -> None:
        """
        Configures the virtual file system for the application
        """
    
        if not runtime.is_built_executable():
            vfs.vfs_mount_directory('.', 'assets')
        else:
            multifiles = prc.get_prc_list('vfs-multifile')
            for multifile in multifiles:
                vfs.vfs_mount_multifile('.', multifile)

        vfs.switch_file_functions_to_vfs()
        vfs.switch_io_functions_to_vfs()

    def set_window_title(self, window_title: str) -> None:
        """
        Sets the primary window's title
        """

        # Verify we have a window instance
        if not self.win:
            return

        props = p3d.WindowProperties()
        props.set_title(window_title)
        self.win.request_properties(props)

    def set_window_dimensions(self, origin: tuple, size: tuple) -> None:
        """
        Sets the current window dimensions
        """

        if not self.win:
            return

        props = p3d.WindowProperties()
        props.set_origin(*origin)
        props.set_size(*size)
        self.win.request_properties(props)

    def get_window_dimensions(self) -> tuple:
        """
        Returns the current windows dimensions
        """

        origin = (-1, -1)
        size = (-1, -1)

        if not self.win:
            return (origin, size)

        props = self.win.get_properties()
        if sys.platform == 'darwin':
            origin = (25, 50)
        elif props.has_origin():
            origin = (props.get_x_origin(), props.get_y_origin())
        
        if props.has_size():
            size = (props.get_x_size(), props.get_y_size())

        return (origin, size)

    def set_clear_color(self, clear_color: object) -> None:
        """
        Sets the primary window's clear color
        """

        # Verify we have a window instance
        if not self.win:
            return

        self.win.set_clear_color(clear_color)

    def set_antialias(self, antialias: bool) -> None:
        """
        Sets the graphics library based antialiasing state
        """

        if not prc.get_prc_bool('framebuffer-mutlisample', False):
            prc.set_prc_value('framebuffer-multisample', True)

        if prc.get_prc_int('multisamples', 0) < 2:
            self.notify.warning('Multisamples not set. Defaulting to a value of 2')
            prc.set_prc_value('multisamples', 2)

        if antialias:
            self.render.set_antialias(p3d.AntialiasAttrib.MAuto)
        else:
            self.render.clear_antialias()

    def post_window_setup(self) -> None:
        """
        Performs setup operations after the window has succesfully
        opened
        """

    def open_default_window(self) -> object:
        """
        Opens a window with the default configuration
        options
        """

        props = p3d.WindowProperties.get_default()
        return self.openMainWindow(props = props)

    def openMainWindow(self, *args, **kwargs) -> object:
        """
        Custom override of the ShowBase openMainWindow function
        for handling runtime registering
        """

        result = ShowBase.openMainWindow(self, *args, **kwargs)

        if result:
            runtime.window = self.win
            runtime.render = self.render

            self.post_window_setup()

        return self.win

    def toggle_frame_rate(self) -> None:
        """
        Toggles the application's frame rate meter
        """

        self.__showing_frame_rate = not self.__showing_frame_rate
        self.set_frame_rate_meter(self.__showing_frame_rate)

    def is_oobe(self) -> bool:
        """
        Returns true if the ShowBase instance is in oobe mode
        """

        if not hasattr(self, 'oobeMode'):
            return False

        return self.oobeMode

    def set_exit_callback(self, func: object) -> None:
        """
        Sets the showbase's shutdown callback
        """

        assert func != None
        assert callable(func)

        self.exitFunc = func

    def set_exit_code(self, code: int) -> None:
        """
        Sets the exit code for the application
        """

        # if the exit code provided is an enum get the value
        if hasattr(code, 'value'):
            code = code.value

        # set the exit code
        self.exit_code = code

    def execute(self) -> int:
        """
        Calls the Panda3D ShowBase run() method with automatic
        error handling and exit code return.
        """

        try:
            self.run()
        except Exception as e:
            self.notify.error('An error occurred during execution: %s' % e)
            self.notify.error(traceback.format_exc())

            self.exit_code = 1

        return self.exit_code

class HeadlessApplication(Application):
    """
    Headless varient of the ApplicationBase object. Creates
    without a primary window instance
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the HeadlessApplication instance
        """

        prc.load_headless_prc_data()
        super().__init__(*args, **kwargs)