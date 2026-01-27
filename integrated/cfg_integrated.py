#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración Integrada: Modelo CA1 + Toma de Decisiones Competitiva
Combina la biofísica del modelo original (t42) con la arquitectura de aprendizaje
"""

from netpyne import specs

cfg = specs.SimConfig()

# =============================================================================
# PARÁMETROS DE SIMULACIÓN (del modelo original)
# =============================================================================
cfg.duration = 1300.0           # Duración por trial (ms)
cfg.starttime = 300             # Sin offset temporal
cfg.dt = 0.1                    # Paso de tiempo (más rápido que original 0.025)
cfg.verbose = False

cfg.cvode_active = False
cfg.hParams = {'v_init': -65, 'celsius': 34}
cfg.recordStep = 1.0

# Seeds
cfg.seedval = 42
cfg.seeds = {
    'conn': cfg.seedval + 7515, 
    'stim': cfg.seedval + 84331, 
    'loc': cfg.seedval + 943
}

# =============================================================================
# ARQUITECTURA DE POBLACIONES (Estructura Competitiva)
# =============================================================================
# Dos poblaciones piramidales competitivas + una población OLM compartida
cfg.popA_size = 60             # PYR_A (Opción Correcta)
cfg.popB_size = 60             # PYR_B (Opción Incorrecta)
cfg.olm_size = 10              # OLM (Inhibición Global)

# Factores de escala (del modelo original)
cfg.pcscalenum = 4             # Factor de escala para sinapsis PYR
cfg.olmscalenum = 2            # Factor de escala para sinapsis OLM

# Poblaciones desactivadas del modelo original
cfg.pvbcpopsize = 0            # Sin PVBC en este modelo
cfg.pvscalenum = 1

# =============================================================================
# CONECTIVIDAD (Circuito PYR→OLM→PYR)
# =============================================================================
# Activar solo las conexiones necesarias para el feedback competitivo
cfg.connectPCOLM = True        # PYR → OLM (feedforward excitatorio)
cfg.connectOLMPC = True        # OLM → PYR (feedback inhibitorio)

# Desactivar conexiones no usadas
cfg.connectPC2PC = False       # Sin recurrencia PYR→PYR
cfg.connectPCPVBC = False      # Sin PVBC
cfg.connectPVBCPC = False
cfg.connectPVBC2PVBC = False

# =============================================================================
# PARÁMETROS SINÁPTICOS PYR→OLM (del modelo original)
# =============================================================================
cfg.pc_olm_use = 0.07          # Utilization parameter
cfg.olmdepfact = 38            # Depression
cfg.olmfacfact = 470           # Facilitation

# Conductancias sinápticas PYR→OLM
cfg.pc_olm_lowbound = 0.275      # nS (rango actualizado del modelo simplificado)
cfg.pc_olm_hibound = 0.325       # nS
cfg.pc_olm_wei = 1.0           # Multiplicador

# Conectividad PYR→OLM
cfg.pc_olm_conprob = 1.0       # Probabilidad de conexión
cfg.pc_olm_synfact = 1.0       # Factor para número de sinapsis
cfg.pc_olm_sec = 'basal'       # Sección target en OLM

# =============================================================================
# PARÁMETROS SINÁPTICOS OLM→PYR (del modelo original)
# =============================================================================
# CRÍTICO: Estos parámetros determinan la fuerza de la inhibición competitiva
cfg.olm_pc_gaba_tau = 11.8     # Decay time GABAA (ms) - Modelo Simplificado

# STP removido (Modelo Simplificado)
cfg.olm2pcDep = 0.0            # Sin depresión
cfg.olm2pcFac = 0.0            # Sin facilitación

# Conductancias sinápticas OLM→PYR
cfg.olm_pc_lobound = 4.1       # nS
cfg.olm_pc_hibound = 5.5       # nS
cfg.olm_pc_wei = 0.25          # Multiplicador (puede ajustarse para competencia)

# MEJORA: Aumentar para más inhibición competitiva
cfg.olm_pc_synfact = 1.5       # Factor de sinapsis (incrementado)

# Conectividad OLM→PYR
cfg.olm_pc_conprob = 1.0       # Probabilidad de conexión

# Distancias para targeting dendrítico
cfg.OLMsomaDist = 250          # Distancia mínima del soma para conexiones OLM (μm)
cfg.PVBCsomaDist = 50          # No usado (sin PVBC)

# =============================================================================
# PARÁMETROS NO USADOS (Mantenidos por compatibilidad)
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
# ENTRADA SCHAFFER COLLATERAL (Estímulo de Aprendizaje)
# =============================================================================
# Desactivar entrada artificial del modelo original
cfg.artifpyrpars = {}
cfg.artifpyrpars['doartif'] = False  # Usaremos NetStim en su lugar

# PARÁMETROS DE APRENDIZAJE (Controlados por el script de simulación)
cfg.sc_wei_left = 0.5          # Peso inicial para PYR_A (Correcta)
cfg.sc_wei_right = 0.5         # Peso inicial para PYR_B (Incorrecta)
cfg.sc_input_rate = 20         # Hz - Frecuencia del estímulo NetStim
cfg.sc_input_noise = 0.5       # Nivel de ruido Poisson

# =============================================================================
# ESTIMULACIÓN ALVEAR (Desactivada - No usada en este modelo)
# =============================================================================
cfg.doAlvstim = False
cfg.doAlvPYRclamp = False
cfg.alv_olm_synfact = 200
cfg.alv_pv_synfact = 100
cfg.alvsomaclampamp = 0.6
cfg.alvclamptarg = 'PYR'
cfg.scanz_stimtotnum = 30
cfg.scanz_fval = 50

# =============================================================================
# GRABACIÓN Y ANÁLISIS
# =============================================================================
cfg.distributeSynsUniformly = False
cfg.connRandomSecFromList = False

# Grabación de trazas (CRÍTICO para análisis DDM)
cfg.recordTraces = {
    'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}
}

cfg.recordStim = False
cfg.recordTime = True

# Guardado de datos
cfg.savePickle = True
cfg.saveJson = False
cfg.saveMat = False
cfg.saveFileStep = 1000

# Análisis automático
cfg.analysis = {}

cfg.analysis['plotRaster'] = {
    'include': ['PYR_A', 'PYR_B', 'OLM'],
    'saveFig': True,
    'showFig': False,
    'markerSize': 5,
    'orderBy': 'pop'
}

cfg.analysis['plotTraces'] = {
    'include': [0, 40],        # GID 0 (PYR_A) y GID 40 (PYR_B)
    'saveFig': True,
    'showFig': False,
    'oneFigPer': 'trace',
    'overlay': False,
    'timeRange': [0, cfg.duration]
}

cfg.analysis['plotRate'] = {
    'include': ['PYR_A', 'PYR_B', 'OLM'],
    'saveFig': True,
    'showFig': False
}
