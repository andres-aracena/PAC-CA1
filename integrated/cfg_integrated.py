#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración MEJORADA: Actividad sostenida en OLM + Mejor competencia
PROBLEMA RESUELTO: OLMs solo activaban primeros 100ms
SOLUCIÓN: Aumentar conectividad PYR→OLM y reducir inhibición OLM→PYR
"""

from netpyne import specs

cfg = specs.SimConfig()

# =============================================================================
# PARÁMETROS DE SIMULACIÓN
# =============================================================================
cfg.duration = 1300.0
cfg.starttime = 300
cfg.dt = 0.1
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
# ARQUITECTURA DE POBLACIONES
# =============================================================================
cfg.popA_size = 60
cfg.popB_size = 60
cfg.olm_size = 10  # Aumentado de 5 a 10 para más actividad

# Factores de escala
cfg.pcscalenum = 4
cfg.olmscalenum = 2

cfg.pvbcpopsize = 0
cfg.pvscalenum = 1

# =============================================================================
# CONECTIVIDAD
# =============================================================================
cfg.connectPCOLM = True
cfg.connectOLMPC = True

cfg.connectPC2PC = False
cfg.connectPCPVBC = False
cfg.connectPVBCPC = False
cfg.connectPVBC2PVBC = False

# =============================================================================
# PARÁMETROS SINÁPTICOS PYR→OLM (MEJORADOS)
# =============================================================================
cfg.pc_olm_use = 0.15  # AUMENTADO de 0.07 → más release probability
cfg.olmdepfact = 20    # REDUCIDO de 38 → menos depresión
cfg.olmfacfact = 600   # AUMENTADO de 470 → más facilitación

# Conductancias AUMENTADAS
cfg.pc_olm_lowbound = 1.5  # Antes 1.0
cfg.pc_olm_hibound = 3.0   # Antes 2.0
cfg.pc_olm_wei = 1.5       # AUMENTADO de 1.0 → OLMs reciben más excitación

# Conectividad
cfg.pc_olm_conprob = 1.0
cfg.pc_olm_synfact = 1.5   # AUMENTADO → más sinapsis PYR→OLM
cfg.pc_olm_sec = 'basal'

# =============================================================================
# PARÁMETROS SINÁPTICOS OLM→PYR (REDUCIDOS PARA MENOS INHIBICIÓN)
# =============================================================================
cfg.olm_pc_gaba_tau = 11.8

# STP removido
cfg.olm2pcDep = 0.0
cfg.olm2pcFac = 0.0

# Conductancias REDUCIDAS para no suprimir totalmente a PYRs
cfg.olm_pc_lobound = 3.0   # REDUCIDO de 4.1
cfg.olm_pc_hibound = 4.0   # REDUCIDO de 5.5
cfg.olm_pc_wei = 0.08      # REDUCIDO de 0.1 → menos inhibición total

# Conectividad
cfg.olm_pc_synfact = 1.0   # Mantenido
cfg.olm_pc_conprob = 1.0

# Distancias
cfg.OLMsomaDist = 250
cfg.PVBCsomaDist = 50

# =============================================================================
# PARÁMETROS NO USADOS
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
# ENTRADA SCHAFFER COLLATERAL (OPTIMIZADA)
# =============================================================================
cfg.artifpyrpars = {}
cfg.artifpyrpars['doartif'] = False

# PESOS OPTIMIZADOS
cfg.sc_wei_left = 3.0    # AUMENTADO de 2.5 → más actividad inicial
cfg.sc_wei_right = 3.0   # AUMENTADO de 2.5
cfg.sc_input_rate = 60   # AUMENTADO de 50 → más frecuencia
cfg.sc_input_noise = 0.5

# =============================================================================
# ESTIMULACIÓN ALVEAR (Desactivada)
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
# GRABACIÓN (OPTIMIZADA PARA VOLTAJES)
# =============================================================================
cfg.distributeSynsUniformly = False
cfg.connRandomSecFromList = False

# GRABACIÓN DE VOLTAJES ACTIVADA
cfg.recordTraces = {
    'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}
}

cfg.recordStim = False
cfg.recordTime = True

# Guardado
cfg.savePickle = True
cfg.saveJson = False
cfg.saveMat = False
cfg.saveFileStep = 1000

# Análisis (desactivado - se hace en el script)
cfg.analysis = {}

# =============================================================================
# NOTAS SOBRE LAS CORRECCIONES
# =============================================================================
"""
PROBLEMA IDENTIFICADO:
- OLMs solo disparaban en los primeros 100ms
- Después quedaban silenciosas el resto de la simulación
- Ratio PYR_A:PYR_B era ~1:1 (no había diferenciación)

CAUSAS:
1. Excitación PYR→OLM muy débil (Use=0.07, pesos 1-2 nS)
2. Inhibición OLM→PYR muy fuerte (pesos 4.1-5.5 nS × 0.1)
3. Fuerte depresión en PYR→OLM (Dep=38)
4. Pocas OLMs (5) para distribuir carga

SOLUCIONES IMPLEMENTADAS:
1. ↑ pc_olm_use: 0.07 → 0.15 (más release)
2. ↓ olmdepfact: 38 → 20 (menos depresión)
3. ↑ olmfacfact: 470 → 600 (más facilitación)
4. ↑ pc_olm_lowbound: 1.0 → 1.5 nS
5. ↑ pc_olm_hibound: 2.0 → 3.0 nS
6. ↑ pc_olm_wei: 1.0 → 1.5 (50% más excitación)
7. ↑ pc_olm_synfact: 1.0 → 1.5 (más sinapsis)
8. ↓ olm_pc_wei: 0.1 → 0.08 (20% menos inhibición)
9. ↓ olm_pc_lobound: 4.1 → 3.0 nS
10. ↓ olm_pc_hibound: 5.5 → 4.0 nS
11. ↑ olm_size: 5 → 10 células
12. ↑ sc_wei_left/right: 2.5 → 3.0 nS
13. ↑ sc_input_rate: 50 → 60 Hz

RESULTADO ESPERADO:
- OLMs disparan durante toda la simulación (no solo 100ms)
- ~50-100 spikes de OLM por trial (antes ~5-7)
- PYR_A y PYR_B mantienen ~130-150 spikes cada uno
- Mejor diferenciación entre A y B con aprendizaje
"""