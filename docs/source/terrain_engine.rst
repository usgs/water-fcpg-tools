Terrain Engine Reference
=======================
Note: This is for reference only, all terrain engine functionality should be accessed 
via the user facing tools.


fcpgtools.terrainengine.protocols module
----------------------------------------
Python protocols defining the input/output signature of terrain engine functions.

This module stores abstract methods for all tools.py functions that require 
a terrain engine. Nesting these methods in @runtime_checkable classes that 
inherit from typing. Protocols allows function signatures to be verified via our 
engine_validator.validate_engine decorator.

For more information on Python Protocols see: https://peps.python.org/pep-0544/

.. automodule:: fcpgtools.terrainengine.protocols
   :members:
   :undoc-members:
   :show-inheritance:

fcpgtools.terrainengine.engine\_validator module
------------------------------------------------

.. automodule:: fcpgtools.terrainengine.engine_validator
   :members:
   :undoc-members:
   :show-inheritance:

fcpgtools.terrainengine.pysheds\_engine module
----------------------------------------------
PySheds terrain engine implementation.

class:PyShedsEngine stores concrete implementation of some terrain engine 
protocols, PySheds specific helper functions, the engines required D8 format,
and a dictionary with valid function kwargs.

For more information on PySheds see the projects documentation: http://mattbartos.com/pysheds/

.. automodule:: fcpgtools.terrainengine.pysheds_engine
   :members:
   :undoc-members:
   :show-inheritance:

fcpgtools.terrainengine.taudem\_engine module
---------------------------------------------
TauDEM terrain engine implementation.

class:TauDEMEngine stores concrete implementation of some terrain engine 
protocols, TauDEM specific helper functions, the engines required D8 format,
and a dictionary with valid function kwargs.

Note that when using the TauDEM terrain engine temporary files will be saved 
to the current working directory. Additionally, in HPC environments one may 
need to pass in kwargs={'mpiCall': 'alternative command line call'} if 
'mpiexec' (default) is not a valid command line term.

For more information on TauDEM see the projects documentation: https://hydrology.usu.edu/taudem/taudem5/

.. automodule:: fcpgtools.terrainengine.taudem_engine
   :members:
   :undoc-members:
   :show-inheritance:

