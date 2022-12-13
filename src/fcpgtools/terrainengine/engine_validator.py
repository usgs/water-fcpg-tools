from fcpgtools import custom_types


def validate_engine(protocol):
    """decorator verify `engine` argument of function matches required protocol

        Validation is performed at runtime. In the `engine` argument does not match the 
        protocol specified, the decorator will raise a TypeError indicting the required
        engine type for the original function.

        Example usage:

            @validator(SupportsFACtoFDR)
            def my_func(engine:SupportsFACtoFDR):
                ...
    """

    def validator(func, *args, **kwargs) -> callable:
        # TODO: make it so engine is founds off kwarg not position, and always returned as the class if input was str
        def valid_func(engine, *args, **kwargs):
            if isinstance(engine, str):
                engine = custom_types.NameToTerrainEngineDict[engine.lower()]
            if not isinstance(engine, protocol):
                raise TypeError(f'Invalid engine provided, {func.__name__}'
                                f'requires engine implementing {protocol.__name__} protocol')
            func(engine, *args, **kwargs)
        return valid_func
    return validator
