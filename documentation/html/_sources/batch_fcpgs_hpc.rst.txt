Batch FCPG Creation on a HPC
============================

This recipe provides an example of batch creating FCPG grids from a folder of parameter grids and a flow direction grid. This recipe requires two :code:`Python` scripts. The first script sorts through the parameter grids and submits a SLURM job for each one and the second script, :code:`makeFCPG.py`, creates the FCPG within the SLURM job.

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

