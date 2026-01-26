#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 14:41:05 2021

@author: adam
"""

from netpyne import specs

## Population parameters
cfg = specs.SimConfig()					# object of class SimConfig to store simulation configuration

# ================================================================
# CAMBIOS PARA EL MODELO SIMPLIFICADO (SM)
# ================================================================

# 1. DURACIÓN CORRECTA (ya está bien: 6300 ms = 6.3 segundos)
cfg.duration = 1300
cfg.starttime = 300
cfg.seedval = 42

# 2. POBLACIONES CORRECTAS (ya están bien)
cfg.pyrpopsize = 120    # SM = 240 | FM = 480 células
cfg.olmpopsize = 10     # SM = 10 | FM = 20 células
cfg.pvbcpopsize = 0     # Sin PVBC en el SM
cfg.pcscalenum = 4       # Factor de escala PYR
cfg.olmscalenum = 2      # Factor de escala OLM
cfg.pvscalenum = 1      # Irrelevante porque pvbcpopsize=0

# 3. CONEXIONES CORRECTAS (solo PYR→OLM y OLM→PYR)
cfg.connectPC2PC = False        # Sin conexiones recurrentes PYR→PYR
cfg.connectPVBC2PVBC = False    # Sin células PVBC
cfg.connectPVBCPC = False       # Sin conexiones PVBC→PYR
cfg.connectOLMPC = True         # CONEXIÓN ACTIVA: OLM→PYR (feedback)
cfg.connectPCPVBC = False       # Sin conexiones PYR→PVBC
cfg.connectPCOLM = True         # CONEXIÓN ACTIVA: PYR→OLM (feedforward)

cfg.PVBCsomaDist = 50           # Irrelevante (no hay PVBC)
cfg.OLMsomaDist = 250


cfg.pc_olm_use  = 0.07 
cfg.olmdepfact = 38
cfg.olmfacfact = 470
cfg.pvbcdep  = 110
cfg.pvbcfac = 0 

# 4. PARÁMETROS DE SINAPSIS ESPECÍFICOS DEL SM (Fig 5-7)
cfg.olm_pc_gaba_tau = 11.8      # GABA decay time constant reducido a 11.8 ms (de 18.0)
cfg.olm2pcDep = 0.0             # STP removed: D = 0 (depresión)
cfg.olm2pcFac = 0.0             # STP removed: F = 0 (facilitación)

cfg.pv_pc_gaba_tau_fact = 1
cfg.pvbc2pcDep = 965
cfg.pvbc2pcFac = 8.6
cfg.pc_olm_sec = 'basal'

cfg.pc_olm_conprob = 1
cfg.pc_olm_synfact = 1
cfg.pc_pc_conprob = 1
cfg.pc_pc_synfact = 1
cfg.pc_pv_conprob = 1
cfg.pc_pv_synfact  = 1
cfg.olm_pc_conprob = 1

# MEJORA: Aumentar fuerza sináptica OLM→PYR para más actividad de feedback
cfg.olm_pc_synfact  = 1.5      # Incrementado de 1 a 1.5 (50% más fuerte)

cfg.pv_pc_conprob = 1
cfg.pv_pc_synfact = 1
cfg.pvbc_pvbc_conprob = 1
cfg.pvbc_pvbc_synfact = 1

# 7. CONDUCTANCIAS SINÁPTICAS - RANGOS CORRECTOS
# PYR-OLM: [0.2, 0.4] nS (un poco menor que [0.275, 0.325] del paper)
cfg.pc_olm_lowbound = 1.0    # 1.0 nS (antes 0.2)
cfg.pc_olm_hibound = 2.0     # 2.0 nS (antes 0.4)
cfg.pc_olm_wei = 1.0            # Multiplicador = 1.0 para obtener rango directo
cfg.pc_pv_wei = 1

# 5. FUERZA SINÁPTICA OLM→PYR (sin triplicar - solo para variantes SM25/SM7)
cfg.olm_pc_wei = 0.25           # Valor normal del FM (no triplicado)
cfg.olm_pc_lobound = 4.1
cfg.olm_pc_hibound = 5.5

cfg.pv_pc_wei = 1

#############################

# 9. ESTIMULACIÓN ALVEAR - DESACTIVADA EN SM
cfg.doAlvstim = False           # El SM no usa estimulación alvear para OLM
cfg.doAlvPYRclamp = False       # Sin clamp

# MEJORA 3: Aumentar estimulación alvear para más activación
cfg.alv_olm_synfact = 200      # Incrementado de 138 a 200
cfg.alv_pv_synfact = 100       # Incrementado de 80 a 100


# MEJORA 4: Ajustar clamp para mayor excitación
cfg.alvsomaclampamp = 0.6      # Incrementado de 0.5 a 0.6 nA
cfg.alvclamptarg = 'PYR'

# MEJORA 5: Más estímulos alveares para actividad sostenida
cfg.scanz_stimtotnum = 30      # Incrementado de 3 a 30 estímulos
cfg.scanz_fval = 50            # Cambiado de 10 a 50 ms (20 Hz - frecuencia theta)



############################

# 6. ENTRADAS SCHAFFER COLLATERAL (SC) - NÚMERO CORRECTO
# Cada PYR debe recibir ~9 grupos (cada grupo = 20 procesos Poisson a 1.4 Hz = 34 Hz)
cfg.artifperpyr = 9             # Cambiado de 100 a 9 entradas por PYR

cfg.artifpyrpars = {}
cfg.artifpyrpars['doartif'] = True
cfg.artifpyrpars['namestr'] = '_pyrart'
cfg.artifpyrpars['artif_starttime'] = 0
cfg.artifpyrpars['artif_duration'] = cfg.duration
     
cfg.artifpyrpars['inp_uptime_start'] = 10000
cfg.artifpyrpars['inp_downtime_start'] = 0


# 12. ACTUALIZAR PARÁMETROS DEPENDIENTES
cfg.artifpyrpars['artifperpyr'] = cfg.artifperpyr  # 9 entradas por PYR
cfg.artifpyrpars['artifpyrat'] = int(cfg.artifperpyr / 2)  # 4 procesos agrupados
cfg.artifpyrpars['pyrpopsize'] = cfg.pyrpopsize
cfg.artifpyrpars['gshape'] = 1

# 11. PARÁMETROS DE GENERACIÓN DE SPIKE ARTIFICIAL
# Cada entrada SC = 34 Hz (grupo de 20 procesos a 1.4 Hz)
meanCA3isi = 1000.0 / 34.0      # Intervalo para 34 Hz
gscale = meanCA3isi/(cfg.artifpyrpars['gshape'])

cfg.artifpyrpars['lo_gscale_u'] = gscale
cfg.artifpyrpars['hi_gscale_u'] = gscale
cfg.artifpyrpars['lo_gscale_d'] = gscale
cfg.artifpyrpars['hi_gscale_d'] = gscale

cfg.artifpyrpars['scalesep'] = 0
cfg.artifpyrpars['grefract'] = 0
cfg.artifpyrpars['field_delay'] = 0
cfg.artifpyrpars['call_shift_fac'] = 0

cfg.artifpyrpars['npartifwei_low'] = 0.55
cfg.artifpyrpars['npartifwei_hi'] = 0.65
cfg.artifpyrpars['artifsynmech'] = 'PC-PCzero'
cfg.artifpyrpars['artifsynfact'] = 6

# 8. NÚMERO DE SINAPSIS POR CONEXIÓN (como en descripción)
# PYR-OLM: 5 sinapsis por conexión
# SC→PYR: 6 sinapsis por conexión (ya está en artifpyrpars['artifsynfact'] = 6)


#############################

cfg.cvode_active = False
cfg.dt = 0.025
cfg.hParams = {'v_init': -65, 'celsius': 34} #, 'clamp_resist': 0.001}
cfg.verbose = False

cfg.distributeSynsUniformly = False
cfg.connRandomSecFromList = False

cfg.recordStep = 1 			# Step size in ms to save data (eg. V traces, LFP, etc)

# MEJORA: Configuración de guardado para análisis posterior
cfg.savePickle = True           
cfg.saveJson = True
cfg.saveFileStep = 1000     # step size in ms to save data to disk

# MEJORA: Configurar análisis mejorado
cfg.analysis = {}

# MEJORA: Raster plot simplificado pero funcional
cfg.analysis['plotRaster'] = {
    'include': ['PYR_pop', 'OLM_pop'],
    'saveFig': True, 
    'showFig': False
}

# SOLUCIÓN CORREGIDA: Configuración de grabación sin conflictos
cfg.recordStim = False
cfg.recordTime = True  

# SOLUCIÓN: Configuración SEGURA - Solo grabar trazas básicas
# Opción A: Grabar solo 1 célula de cada tipo (más seguro)
cfg.recordTraces = {
    'V_soma_PYR0': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'},
    'V_soma_OLM0': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}
}

# SOLUCIÓN: Análisis de trazas corregido (usar índices existentes)
cfg.analysis['plotTraces'] = {
    'include': [0],  # Solo la primera célula para vista rápida
    'saveFig': False, 
    'showFig': False,
    'timeRange': [0, 500]  # Solo primeros 500 ms para prueba
}

# SOLUCIÓN: Análisis de tasa básico
cfg.analysis['plotRate'] = {
    'saveFig': False, 
    'showFig': False
}

# Configuración de seeds (sin cambios)
cfg.seeds = {'conn': cfg.seedval + 7515, 'stim': cfg.seedval + 84331, 'loc': cfg.seedval + 943}