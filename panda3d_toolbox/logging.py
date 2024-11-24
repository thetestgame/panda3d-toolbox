"""
Utility functions for logging messages to the Panda3D logging system. Also provides
utility methods for merging with the native Python logging module and optional
support for Sentry monitoring.
"""

import os
import sys
import time
import logging
from io import open as io_open
from logging import StreamHandler

from panda3d.core import Filename, MultiplexStream, Notify
from panda3d_toolbox import runtime, prc

# -----------------------------------------------------------------------------------------------

def get_notify_categories() -> object:
    """
    Retrieves all Panda3D notifier categories
    """

    from direct.directnotify.DirectNotifyGlobal import directNotify
    return directNotify.getCategories()

def get_notify_category(name: str, create: bool = True) -> object:
    """
    Returns the requested Panda3D notifier category. Creating a new
    one if create is set to True
    """

    assert name != None
    assert name != ''

    from direct.directnotify.DirectNotifyGlobal import directNotify

    category = None
    if create:
        category = directNotify.newCategory(name)
    else:
        category = directNotify.getCategory(name)
    return category

def log(message: str, name: str = 'global', type: str = 'info') -> None:
    """
    Writes a message to the requested logger name
    """

    category = get_notify_category(name)
    assert hasattr(category, type)
    getattr(category, type)(message)

def log_error(message: str, name: str = 'global') -> None:
    """
    Writes an error message to the requested logger name
    """

    log(name, message, 'error')

def log_warn(message: str, name: str = 'global') -> None:
    """
    Writes an warn message to the requested logger name
    """

    log(name, message, 'warn')

def log_info(message: str, name: str = 'global') -> None:
    """
    Writes an info message to the requested logger name
    """

    log(name, message, 'info')

def log_debug(message: str, name: str = 'global') -> None:
    """
    Writes an debug message to the requested logger name
    """

    log(name, message, 'debug')

def condition_error(logger: object, condition: bool, message: str) -> None:
    """
    Writes a error message to the logging object if the provided
    condition is true
    """

    condition_log(logger, condition, message, 'error')

def condition_warn(logger: object, condition: bool, message: str) -> None:
    """
    Writes a warning message to the logging object if the provided
    condition is true
    """

    condition_log(logger, condition, message, 'warning')

def condition_info(logger: object, condition: bool, message: str) -> None:
    """
    Writes a info message to the logging object if the provided
    condition is true
    """

    condition_log(logger, condition, message, 'info')

def condition_debug(logger: object, condition: bool, message: str) -> None:
    """
    Writes a debug message to the logging object if the provided
    condition is true
    """

    condition_log(logger, condition, message, 'debug')

def condition_log(logger: object, condition: bool, message: str, type: str = 'info') -> None:
    """
    Writes a message to the logging object if the provided
    condition is true using the supplied type attribute function name
    """

    assert hasattr(logger, type)
    if condition:
        getattr(logger, type)(message)

def get_log_directory() -> str:
    """
    Returns this applications log directory
    based on the PRC configuration
    """

    default = '.%slogs' % os.sep
    return prc.get_prc_string('app-log-directory', default)

class PythonLogHandler:
    """
    Redirects native Python logs to a log file
    """

    def __init__(self, original: object, log_stream: object):
        """
        Initializes the PythonLogHandler instance
        """

        self.original = original
        self.log_stream = log_stream

    def write(self, message: str) -> None:
        """
        Writes a message to the log file
        """

        self.log_stream.write(message)
        self.log_stream.flush()

        self.original.write(message)
        self.original.flush()

    def flush(self) -> None:
        """
        Flushes the log stream
        """

        self.original.flush()
        self.log_stream.flush()

def configure_log_file() -> None:
    """
    Configures the application's log file based on the PRC configuration
    """

    # Create a timestamped log file name based on the executable name. This will allow
    # us to have multiple log files for different application sessions. The resulting
    # filename should be in the format of '{executable}_YYYY-MM-DD_HH-MM-SS.{ext}'
    local_time = time.localtime()
    log_prefix = runtime.executable_name.lower()
    log_suffix = time.strftime('%Y-%m-%d_%H-%M-%S', local_time)

    log_ext = prc.get_prc_string('app-log-ext', 'txt')
    log_filename = f"{log_prefix}_{log_suffix}.{log_ext}"

    # Open a new log file stream for appending. 
    # Make sure to use the 'a' mode (appending) because both Python and Panda3D
    # open this same filename to write to. Append mode has the nice property of seeking to the end of
    # the output stream before actually writing to the file. 'w' mode does not do this, so you will see Panda3D's
    # output and Python's output not interlace properly.
    log_file_path = os.path.join(get_log_directory(), log_filename)
    log_stream = io_open(log_file_path, 'a')

    # Create new Python log handlers for stdout and stderr and redirect
    # stdout and stderr to these handlers
    log_output = PythonLogHandler(sys.stdout, log_stream)
    log_error = PythonLogHandler(sys.stderr, log_stream)

    sys.stdout = log_output
    sys.stderr = log_error

    # Configture Panda3D to use the same log file
    nout = MultiplexStream()
    Notify.ptr().set_ostream_ptr(nout, 0)

    nout.add_file(Filename(log_file_path))
    nout.add_standard_output()
    nout.add_system_debug()

    # Write our log file header with useful information should we ever end up with
    # a log file that needs to be analyzed.
    print("\n\nStarting application...")
    print(f"Current time: {time.asctime(time.localtime(time.time()))}")
    print(f"sys.path = ", sys.path)
    print(f"sys.argv = ", sys.argv)
    print(f"os.environ = ", os.environ)

# ----------------------------------------------------------------------------------------------- 


class NotifyHandler(StreamHandler):
    """
    Custom logging module StreamHandler for pipeing lodding module based messages to a Panda3D
    notifier category
    """

    def __init__(self, name: str = 'global'):
        """
        Initializes the NotifyHandler instance
        """

        StreamHandler.__init__(self)

        self.name = name
        self.notify = get_notify_category(name)

    def emite(self, record: object) -> None:
        """
        Processes the incoming record from the logging module
        """

        message_parts = self.format(record).split('||')
        level = message_parts[0].lower()
        message = message_parts[1]
        
        if hasattr(self.notify, level):
            func = getattr(self.notify, level)
        else:
            func = self.notify.info
        
        func.info(message)

def configure_logging_module() -> None:
    """
    Initializes the Python logging module to pipe through the Panda3D notifier
    """

    level_map = {
        'spam': logging.DEBUG,
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARN,
        'error': logging.ERROR
    }

    level = level_map.get(prc.get_prc_string('notify-level-python', ''), logging.INFO)
    formatter = '%(levelname)s||%(message)s'
    logging.basicConfig(format=formatter, level=level, handlers=[NotifyHandler()])   


# ----------------------------------------------------------------------------------------------- 

def configure_sentry_monitoring() -> None:
    """
    Configures the Sentry SDK for use by the application
    """

    sentry_dsn = prc.get_prc_string('sentry-dsn', '')
    sentry_trace_rate = prc.get_prc_double('sentry-trace-rate', 1.0)

    assert sentry_dsn != ''

    import sentry_sdk
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=sentry_trace_rate
    )

# -----------------------------------------------------------------------------------------------