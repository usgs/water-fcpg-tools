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
        def valid_func(engine, *args, **kwargs): 
            if not isinstance(engine, protocol):
                raise TypeError(f'Invalid engine provided, {func.__name__} requires engine implementing {protocol.__name__} protocol')
            func(engine, *args, **kwargs)
        return valid_func
    return validato