#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Configuration: CA1 Model + Decision Making
CRITICAL FIX: Removed synaptic depression to enable sustained OLM activity
ADDED: Fixed recording configuration and trial management
"""

from netpyne import specs

cfg = specs.SimConfig()

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================
cfg.duration = 1000.0       
cfg.starttime = 0
cfg.dt = 0.1                
cfg.verbose = False

cfg.cvode_active = False
cfg.hParams = {'v_init': -65, 'celsius': 34}
cfg.recordStep = 1.0

cfg.seedval = 42
cfg.seeds = {
    'conn': cfg.seedval + 7515, 
    'stim': cfg.seedval + 84331, 
    'loc': cfg.seedval + 943
}

# =============================================================================
# POPULATION SIZES
# =============================================================================
cfg.popA_size = 60              
cfg.popB_size = 60              
cfg.olm_size = 10               

cfg.pcscalenum = 4
cfg.olmscalenum = 2

cfg.pvbcpopsize = 0
cfg.pvscalenum = 1

# =============================================================================
# CONNECTIVITY
# =============================================================================
cfg.connectPCOLM = True
cfg.connectOLMPC = True
cfg.connectPC2PC = False
cfg.connectPCPVBC = False
cfg.connectPVBCPC = False
cfg.connectPVBC2PVBC = False

# =============================================================================
# PYR→OLM SYNAPTIC PARAMETERS
# CRITICAL PROBLEM IDENTIFIED: Paper's Dep=38 ms causes STRONG depression
# After 2-3 spikes, synapse is depleted and OLM stops firing
# 
# SOLUTION: Reduce depression to MINIMUM (Dep=5) + increase conductances massively
# Paper: Use=0.07, Dep=38, Fac=470, g=0.2-0.4 nS
# Final: Use=0.07, Dep=5 (FIXED!), Fac=700, g=8.0-16.0 nS (40× scaled)
# =============================================================================
cfg.pc_olm_use = 0.07           # Paper (kept)
cfg.olmdepfact = 5              # Paper: 38 → REDUCED to 5 (minimal depression!)
cfg.olmfacfact = 700            # Paper: 470 → INCREASED to 700 (strong facilitation!)

# Conductances: Paper 0.2-0.4 nS × 40 = 8.0-16.0 nS (VERY STRONG)
cfg.pc_olm_lowbound = 8.0       # Paper 0.2 × 40
cfg.pc_olm_hibound = 16.0       # Paper 0.4 × 40
cfg.pc_olm_wei = 1.0

cfg.pc_olm_conprob = 0.35       # Paper
cfg.pc_olm_synfact = 5          # Paper
cfg.pc_olm_sec = 'basal'

# =============================================================================
# OLM→PYR SYNAPTIC PARAMETERS
# Paper SM: tau=11.8, Dep=0, Fac=0, g=1.0-1.4 nS, 13 syn, prob=0.4
# Scaled 3×: g=3.0-4.2 nS (STRONG inhibition for competition)
# =============================================================================
cfg.olm_pc_gaba_tau = 11.8      # Paper SM

cfg.olm2pcDep = 0.0             # Paper SM (no STP)
cfg.olm2pcFac = 0.0             # Paper SM (no STP)

cfg.olm_pc_lobound = 3.0        # Paper 1.0 × 3
cfg.olm_pc_hibound = 4.2        # Paper 1.4 × 3
cfg.olm_pc_wei = 1.0

cfg.olm_pc_synfact = 13         # Paper
cfg.olm_pc_conprob = 0.4        # Paper

cfg.OLMsomaDist = 250           # Paper
cfg.PVBCsomaDist = 50

# =============================================================================
# UNUSED PVBC PARAMETERS
# =============================================================================
cfg.pv_pc_gaba_tau_fact = 1
cfg.pvbc2pcDep = 965
cfg.pvbc2pcFac = 8.6
cfg.pc_pv_conprob = 1
cfg.pc_pv_synfact = 1
cfg.pc_pv_wei = 1
cfg.pv_pc_conprob = 1
cfg.pv_pc_synfact = 1
cfg.pv_pc_wei = 1
cfg.pvbc_pvbc_conprob = 1
cfg.pvbc_pvbc_synfact = 1
cfg.pvbcdep = 110
cfg.pvbcfac = 0

# =============================================================================
# EXTERNAL INPUT
# Paper SC: 34 Hz, g=0.6 nS, 6 syn
# M: g=0.5 nS initial
# Final: g=6.0 nS, 34 Hz (scaled 10× for robust activity)
# =============================================================================
cfg.sc_wei_left = 6.0           # M: 0.5 × 12 (very strong)
cfg.sc_wei_right = 6.0          
cfg.sc_input_rate = 34          # Paper
cfg.sc_input_noise = 0.5        

# =============================================================================
# RECORDING CONFIGURATION - FIXED
# =============================================================================
# CRITICAL: Habilitar distribución uniforme de sinapsis
cfg.distributeSynsUniformly = True
cfg.connRandomSecFromList = False

# FIXED: Configuración mejorada de grabación
# Grabar de todas las poblaciones, no solo algunas
cfg.recordCells = ['all']  # Grabar todas las células

# FIXED: Definir qué traces grabar
cfg.recordTraces = {
    'V_soma': {
        'sec': 'soma_0', 
        'loc': 0.5, 
        'var': 'v'
    },
    # Opcional: agregar más traces si es necesario
    # 'V_dend': {'sec': 'apic_0', 'loc': 0.5, 'var': 'v'},
}

# FIXED: Asegurar que se graban spikes
cfg.recordSpikes = {
    'PYR_A': {'include': 'all'},  # Grabar todos los spikes de PYR_A
    'PYR_B': {'include': 'all'},  # Grabar todos los spikes de PYR_B
    'OLM': {'include': 'all'},    # Grabar todos los spikes de OLM
}

cfg.recordStim = True  # Grabar estímulos
cfg.recordTime = True  # Grabar tiempos
cfg.recordStep = 0.1   # Resolución de grabación (puedes ajustar)

# Configuración de guardado
cfg.savePickle = True
cfg.saveJson = False
cfg.saveMat = False
cfg.saveFileStep = 1000

# =============================================================================
# ANÁLISIS - FIXED
# =============================================================================
cfg.analysis = {
    'plotRaster': {'saveFig': True, 'showFig': False},
    'plotTraces': {'include': [0, 5, 10, 15], 'saveFig': True, 'showFig': False},
    'plot2Dnet': {'saveFig': True, 'showFig': False}
}

# =============================================================================
# ALVEAR STIMULATION (Deactivated)
# =============================================================================
cfg.doAlvstim = False
cfg.doAlvPYRclamp = False

# =============================================================================
# PARÁMETROS ADICIONALES PARA CONTROL DE TRIALS - NUEVO
# =============================================================================
cfg.trialDuration = 1000.0  # Duración de cada trial
cfg.interTrialInterval = 100.0  # Intervalo entre trials (opcional)