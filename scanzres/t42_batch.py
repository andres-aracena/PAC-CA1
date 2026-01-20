#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  2 14:34:42 2021

@author: adam
"""
from netpyne import specs
from netpyne.batch import Batch

from neuron import h
h.nrnmpi_init()

def batchTauWeight():

    params = specs.ODict()
    
    seedbase = 576667
    
    params['seedval'] = list(range(0 + seedbase, 100 + seedbase, 100)) 
    
    b = Batch(params=params, cfgFile='t42_cfg.py', netParamsFile='t42_netParams.py',)

 
    b.batchLabel = 't42'
    b.saveFolder = 't42_data'
    b.method = 'grid'
    
    
    numcores = 8
    doslurm = False
    if doslurm:
    
        b.runCfg = {    'type': 'hpc_slurm',
                        #'type': 'mpi_bulletin',
                            'mpiCommand': 'srun',
                            'custom': '#SBATCH --constraint=mc\n#SBATCH --partition=normal',
                            'allocation': '***',
                            'nodes': 2,
                            'coresPerNode': 35,
                            'script': 't42_init.py',
                            'walltime': '1:00:00',
                            'skip': True}
    else:
        # Configuración específica para Windows y Anaconda
        # Poner en Terminal: set PYTHONHOME=C:\Users\Andres\anaconda3\envs\lasconx
        import sys
        python_exe = sys.executable 
        
        b.runCfg = {
            'type': 'mpi_direct',
            'numprocs': 8,
            'mpiCommand': 'mpiexec', # Ponemos el comando base
            'script': 't42_init.py',
            'skip': True
        }

    # --- EL TRUCO PARA WINDOWS ---
    # Sobreescribimos manualmente el comando que NetPyNE construyó mal
    # Esto obliga a usar tus 8 núcleos y tu python de anaconda
    import os
    b.run()
# Main code
if __name__ == '__main__':
    batchTauWeight()
    import sys
    sys.exit()
