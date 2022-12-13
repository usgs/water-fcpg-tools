from fcpgtools.terrainengine.taudem_engine import TauDEMEngine
from fcpgtools.terrainengine.pysheds_engine import PyShedsEngine

NameToTerrainEngineDict = {
    'taudem': TauDEMEngine,
    'pysheds': PyShedsEngine,
}


def validate_engine(protocol):
    """decorator verify `engine` argument of function matches required protocol

        Validation is performed at runtime. In the `engine` argument does not match the 
        protocol specified, the decorator will raise a TypeError indicting the required
        engine type for the original function.

        Example usage:

            @validate_engine(SupportsFACtoFDR)
            def my_func(engine:SupportsFACtoFDR):
                ...
    """

    def validator(func, *args, **kwargs) -> callable:
        def valid_func(*args, **kwargs):
            engine = kwargs['engine']
            if isinstance(engine, str):
                try:
                    kwargs['engine'] = NameToTerrainEngineDict[engine.lower()]
                except KeyError:
                    raise TypeError(
                        f'{engine} is not a recognized engine.')
            if not isinstance(kwargs['engine'], protocol):
                raise TypeError(f'Invalid engine provided, {func.__name__}'
                                f' requires engine implementing {protocol.__name__} protocol')
            return func(*args, **kwargs)
        return valid_func
    return validator
