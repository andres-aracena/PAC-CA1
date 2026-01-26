from netpyne import specs

cfg = specs.SimConfig()

# =============================================================================
# CONFIGURACIÓN DE SIMULACIÓN (Optimizada para velocidad)
# =============================================================================
cfg.duration = 600.0           # 500 ms por trial es suficiente para ver quién gana
cfg.dt = 0.1                   # Paso de tiempo estándar (rápido)
cfg.verbose = False
cfg.recordStep = 1.0
cfg.hParams = {'v_init': -65, 'celsius': 34}
cfg.seeds = {'conn': 42, 'stim': 42, 'loc': 42}

# Desactivar guardado en disco para maximizar rendimiento
cfg.saveJson = False
cfg.savePickle = False
cfg.saveMat = False

# =============================================================================
# TAMAÑOS DE POBLACIONES (Arquitectura Competitiva)
# =============================================================================
cfg.popA_size = 40    # PYR_A (Grupo Opción Correcta)
cfg.popB_size = 40    # PYR_B (Grupo Opción Incorrecta)
cfg.olm_size = 10     # OLM (Inhibición Global)

# =============================================================================
# PARÁMETROS DE APRENDIZAJE INICIALES (Variables requeridas por netParams)
# =============================================================================
cfg.sc_wei_left = 0.5   # Peso inicial para la opción A (Correcta)
cfg.sc_wei_right = 0.5 # Peso inicial para la opción B (Incorrecta)

# =============================================================================
# ANÁLISIS
# =============================================================================
# Solo graficamos raster para verificar actividad visualmente si es necesario
cfg.analysis['plotRaster'] = {
    'include': ['PYR_A', 'PYR_B', 'OLM'], 
    'saveFig': True, 
    'showFig': False,
    'markerSize': 5
}

cfg.recordTraces = {'V_soma': {'sec':'soma_0', 'loc':0.5, 'var':'v'}}   # Con trazas de voltaje para velocidad
cfg.analysis['plotTraces'] = {'include': [0, 40], 'saveFig': True} # Graficar la célula 0