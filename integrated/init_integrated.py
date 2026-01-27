#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inicialización para Modelo Integrado
Compatible con ejecución directa y batch processing
"""

from neuron import h
h.nrnmpi_init()

from netpyne import sim

# Leer configuración de línea de comandos si está disponible
simConfig, netParams = sim.readCmdLineArgs(
    simConfigDefault='cfg_integrated.py',
    netParamsDefault='netParams_integrated.py'
)

# Crear y ejecutar simulación
sim.createSimulateAnalyze(netParams=netParams, simConfig=simConfig)

# Finalización limpia
if sim.rank == 0:
    print("\n" + "="*60)
    print("Simulación finalizada con éxito.")
    print("="*60)

sim.pc.done()
h.quit()
