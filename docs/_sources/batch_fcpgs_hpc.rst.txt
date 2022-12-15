Batch FCPG Creation on an HPC
=============================

This is an example of batch creating FCPG grids from a folder of parameter (precipitation, air temperature, land cover, etc.) grids and a flow direction grid. This example uses two Python scripts. The first script sorts through the parameter grids and submits a Slurm job for each one and the second script, :code:`makeFCPG.py`, creates the FCPG within the Slurm job. For more information on the Slurm workload manager, see https://slurm.schedmd.com/overview.html.

Parse parameter grids and submit SLURM jobs
-------------------------------------------
.. literalinclude:: ../scripts/batchFCPGs.py
	:language: Python
	:linenos:

Generate a FCPG given a parameter and FDR grid
----------------------------------------------
:code:`makeFCPG.py`

.. literalinclude:: ../scripts/makeFCPG.py
	:language: Python
	:linenos:

