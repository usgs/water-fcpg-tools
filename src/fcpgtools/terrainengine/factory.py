import importlib
import os
import sys
import importlib.util
from typing import Any, Callable

engines : dict[str,Callable] = {}

def register(engine_name:str, engine_initializer:Callable):
    """Register a new engine to the system"""
    engines[engine_name.lower()] = engine_initializer

def unregister(engine_name:str): 
    """Deregister the engine from the system"""
    engines.pop(engine_name.lower())

def create(arguments: dict[str, Any]):
    args_copy = arguments.copy()
    engine_name = args_copy.pop('engine')
    try:
        engine = engines[engine_name.lower()]
        return engine(**args_copy)
    except KeyError:
        raise ValueError(f'Unknown engine type "{engine_name}" requested. Are you missing a plugin?')

def loader() -> None:
    """Loads all plugin engines in the engine directory"""
    #reference: https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    import fcpgtools.terrainengine.engines as engines
    for name in os.listdir(engines.__path__[0]):
        if name.startswith('__'): continue
        #TODO raise warning/exception that this is not a valid plugin? 
        #'initalize' not in dir(plugin):
        #'engine_name' not in dir(plugin):

        spec = importlib.util.spec_from_file_location(name,f'{engines.__path__[0]}/{name}')
        module = importlib.util.module_from_spec(spec)
        name = name.strip('.py')
        sys.modules[name] = module
        spec.loader.exec_module(module)
        register(module.engine_name, module.initialize)
                
if not engines:
    loader()