#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 14:41:05 2021

@author: adam
"""

from netpyne import specs

## Population parameters
cfg = specs.SimConfig()					# object of class SimConfig to store simulation configuration

# CAMBIO 1: Duración de simulación 6.3 segundos (6300 ms)
cfg.duration = 6300  # Cambiado de 600 a 6300 ms (6.3 segundos)
cfg.starttime = 300
cfg.seedval = 42

# CAMBIO 2: Poblaciones según modelo simplificado

cfg.pyrpopsize = 60    # 120 grupos de células PYR (en lugar de 480 grupos)
cfg.pcscalenum = 1      # 4 células por grupo PYR (total: 120×4 = 480 células)
cfg.pvbcpopsize = 0     # ELIMINADO: No hay células PVBC en el modelo simplificado
cfg.pvscalenum = 1      # Irrelevante porque pvbcpopsize=0
cfg.olmpopsize = 5     # 10 grupos de células OLM (en lugar de 20 grupos)
cfg.olmscalenum = 1     # 2 células por grupo OLM (total: 10×2 = 20 células)

# CAMBIO 3: Solo conexiones feedforward PYR→OLM y feedback OLM→PYR
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
# CAMBIO 4: GABA decay time constante reducido a 11.8 ms para SM base
cfg.olm_pc_gaba_tau = 11.8      # Cambiado de 18 a 11.8 ms (valor del paper [74])
# CAMBIO 5: STP eliminado en sinapsis OLM→PYR (F y D = 0)
cfg.olm2pcDep = 0               # Cambiado de 1770 a 0 (parámetro D de depression)
cfg.olm2pcFac = 0               # Cambiado de 6 a 0 (parámetro F de facilitation)
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

# MEJORA 1: Aumentar fuerza sináptica OLM→PYR para más actividad de feedback
cfg.olm_pc_synfact  = 1.5      # Incrementado de 1 a 1.5 (50% más fuerte)

cfg.pv_pc_conprob = 1
cfg.pv_pc_synfact = 1
cfg.pvbc_pvbc_conprob = 1
cfg.pvbc_pvbc_synfact = 1

cfg.pc_olm_hibound = 0.7 
cfg.pc_olm_lowbound = 0.5 
cfg.pc_olm_wei = 0.5

cfg.pc_pv_wei = 1

# MEJORA 2: Aumentar peso sináptico OLM→PYR para mayor inhibición
cfg.olm_pc_wei = 0.35          # Incrementado de 0.25 a 0.35
cfg.olm_pc_lobound = 4.1
cfg.olm_pc_hibound = 5.5

cfg.pv_pc_wei = 1

#############################

    
cfg.doAlvstim = True

# MEJORA 3: Aumentar estimulación alvear para más activación
cfg.alv_olm_synfact = 200      # Incrementado de 138 a 200
cfg.alv_pv_synfact = 100       # Incrementado de 80 a 100

cfg.doAlvPYRclamp = True

# MEJORA 4: Ajustar clamp para mayor excitación
cfg.alvsomaclampamp = 0.6      # Incrementado de 0.5 a 0.6 nA
cfg.alvclamptarg = 'PYR'

# MEJORA 5: Más estímulos alveares para actividad sostenida
cfg.scanz_stimtotnum = 30      # Incrementado de 3 a 30 estímulos
cfg.scanz_fval = 50            # Cambiado de 10 a 50 ms (20 Hz - frecuencia theta)



############################

cfg.artifperpyr = 100

cfg.artifpyrpars = {}
cfg.artifpyrpars['doartif'] = False
cfg.artifpyrpars['namestr'] = '_pyrart'
cfg.artifpyrpars['artif_starttime'] = 0
cfg.artifpyrpars['artif_duration'] = cfg.duration
cfg.artifpyrpars['pyrpopsize'] = cfg.pyrpopsize

cfg.artifpyrpars['artifpyrat'] =  int(cfg.artifperpyr/2)        
cfg.artifpyrpars['inp_uptime_start'] = 60000
cfg.artifpyrpars['inp_downtime_start'] = 60000
cfg.artifpyrpars['artifperpyr'] = cfg.artifperpyr

cfg.artifpyrpars['gshape'] = 1

meanCA3isi = 688
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




#############################

cfg.cvode_active = False
cfg.dt = 0.025
cfg.hParams = {'v_init': -65, 'celsius': 34} #, 'clamp_resist': 0.001}
cfg.verbose = False

cfg.distributeSynsUniformly = False
cfg.connRandomSecFromList = False

cfg.recordStep = 1 			# Step size in ms to save data (eg. V traces, LFP, etc)

# MEJORA 6: Guardar datos en pickle para análisis posterior
cfg.savePickle = True 		# Cambiado de False a True
cfg.saveJson = True
cfg.saveFileStep = 1000     # step size in ms to save data to disk

# MEJORA 7: Configurar análisis mejorado
cfg.analysis = {}

# MEJORA 8: Raster plot mejorado - SOLUCIÓN SIMPLIFICADA
cfg.analysis['plotRaster'] = {
    'include': ['PYR_pop', 'OLM_pop'],
    'saveFig': True, 
    'showFig': False
}

# SOLUCIÓN: Configuración de grabación CORREGIDA
cfg.recordStim = False
cfg.recordTime = True  

# SOLUCIÓN: Grabar solo voltajes básicos sin condiciones complejas
cfg.recordTraces = {'V_soma': {'sec':'soma_0','loc':0.5,'var':'v'}}

# SOLUCIÓN: Análisis de trazas simplificado
cfg.analysis['plotTraces'] = {'include': [0], 'saveFig': False, 'showFig': False}

# SOLUCIÓN: Análisis de tasa básico
cfg.analysis['plotRate'] = {'saveFig': False, 'showFig': False}

# Configuración de seeds
cfg.seeds = {'conn': cfg.seedval + 7515, 'stim': cfg.seedval + 84331, 'loc': cfg.seedval + 943}