from typing import Any, Callable
from engine import TerrainEngine

engines : dict[str,Callable] = {}

def register(engine_name:str, engine_class:Callable):
    """Register a new engine to the system"""
    engines[engine_name.lower()] = engine_class

def unregister(engine_name:str, engine_class:Callable): 
    """Deregister the engine from the system"""
    engines.pop(engine_name.lower())

def create(arguments: dict[str, Any]) -> TerrainEngine:
    
    args_copy = arguments.copy()
    engine_name = args_copy.pop('engine')
    try:
        engine = engines[engine_name.lower()]
        return engine(**args_copy)
    except KeyError:
        raise ValueError(f'Unknown engine type "{engine_name}" requested. Are you missing a plugin?')
