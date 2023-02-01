import functools
from fcpgtools.terrainengine import factory

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

        @functools.wraps(func)
        def valid_func(*args, **kwargs) -> callable:
            engine = kwargs['engine']
            if isinstance(engine, str):
                kwargs['engine'] = factory.create(kwargs)
            if not isinstance(kwargs['engine'], protocol):
                raise TypeError(f'Invalid engine provided, {func.__name__}'
                                f' requires engine implementing {protocol.__name__} protocol')
            return func(*args, **kwargs)
        return valid_func
    return validator
