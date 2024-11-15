import builtins
import sys as __sys
import os as __os

#----------------------------------------------------------------------------------------------------------------------------------#

def __get_base_executable_name() -> str:
    """
    Returns the base executable name
    """

    basename = __os.path.basename(__sys.argv[0])
    if basename == '-m':
        basename = __os.environ.get('APP_NAME', 'panda3d')

    basename = __os.path.splitext(basename)[0]
    return basename

executable_name = __get_base_executable_name()

def is_venv() -> bool:
    """
    Returns true if the application is being run inside
    a virtual environment
    """

    real_prefix = hasattr(__sys, 'real_prefix')
    base_prefix = hasattr(__sys, 'base_prefix') and __sys.base_prefix != __sys.prefix

    return real_prefix or base_prefix

def is_frozen() -> bool:
    """
    Returns true if the application is being run from within
    a frozen Python environment
    """

    import importlib
    spec = importlib.util.find_spec(__name__)
    return spec is not None and spec.origin is not None

def is_interactive() -> bool:
    """
    Returns true if the application is being run from an
    interactive command prompt
    """

    import sys
    return hasattr(sys, 'ps1') and hasattr(sys, 'ps2')

def is_developer_build() -> bool:
    """
    Returns true if the application is currently
    running as a developer build
    """
    
    return (builtins.__dev__ or is_interactive()) and not is_frozen()

def is_production_build() -> bool:
    """
    Returns true if the application is currently
    running as a production build
    """

    return not is_developer_build()

def get_repository() -> object:
    """
    Returns the Client repository object or AI repository object
    if either exist. Otherwise returning NoneType
    """

    module = __get_module()
    if not module.has_base():
        return None
    
    base = module.get_base()
    if hasattr(base, 'air'):
        return base.air
    elif hasattr(base, 'cr'):
        return base.cr
    else:
        raise AttributeError('base has no repository object')

def is_panda3d_build() -> bool:
    """
    Returns true if the application is currently
    running as a Panda3d build
    """

    return is_frozen()

def is_built_executable() -> bool:
    """
    Returns true if the application is currently
    running as a built executable
    """

    compiled = is_panda3d_build()

    return compiled

#----------------------------------------------------------------------------------------------------------------------------------#

def __get_module() -> object:
    """
    Returns the runtime module's object instance
    """

    return __sys.modules[__name__]

def __has_variable(variable_name: str) -> bool:
    """
    Returns true if the runtime module has the requested variable name defined.
    Is served out via the custom __getattr__ function as has_x() method names
    """

    module = __get_module()
    defined = hasattr(module, variable_name)
    found = False

    if defined:
        attr = getattr(module, variable_name)
        found = attr != None

    return found

def __get_variable(variable_name: str) -> object:
    """
    Returns the requested variable from the runtime module if it exists.
    Otherwise returning NoneType
    """

    if not __has_variable(variable_name):
        return None

    module = __get_module()
    return getattr(module, variable_name)

def __set_variable(variable_name: str, value: object) -> None:
    """
    Sets the requested variable in the runtime module
    """

    module = __get_module()
    setattr(module, variable_name, value)

def __getattr__(key: str) -> object:
    """
    Custom get attribute handler for allowing access to the has_x method names
    of the engine runtime module. Also exposes the builtins module
    for the legacy Panda3d builtins provided by the ShowBase instance
    """

    result = None
    is_has_method = key.startswith('has_')
    is_get_method = key.startswith('get_')
    is_set_method = key.startswith('set_')

    if len(key) > 4:
        variable_name = key[4:]
    else:
        variable_name = key

    if is_has_method:
        result = lambda: __has_variable(variable_name)
    elif is_get_method:
        result = lambda: __get_variable(variable_name)
    elif is_set_method:
        result = lambda value: __set_variable(variable_name, value)
    elif hasattr(builtins, key):
        result = getattr(builtins, key)

    if not result:
        raise AttributeError('runtime module has no attribute: %s' % key)

    return result

#----------------------------------------------------------------------------------------------------------------------------------#