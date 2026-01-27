#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetParams Integrado: Modelo CA1 + Toma de Decisiones Competitiva
Mantiene la biofísica del modelo original con arquitectura de dos poblaciones PYR
"""

from netpyne import specs
import numpy as np
import random

try:
    from __main__ import cfg
except:
    from cfg_integrated import cfg

netParams = specs.NetParams()

# =============================================================================
# INICIALIZACIÓN DE SEMILLAS
# =============================================================================
np.random.seed(cfg.seedval)
random.seed(cfg.seedval)

somator = True

# =============================================================================
# PASO 1: IMPORTAR CÉLULAS BIOFÍSICAS (del modelo original)
# =============================================================================

# Célula Piramidal (se usará para PYR_A y PYR_B)
netParams.importCellParams(
    label='PYR_rule',
    conds={'cellType': 'PYR', 'cellModel': 'PYR'},
    fileName='pyr.hoc',
    cellName='CA1_PC_cAC_sig',
    somaAtOrigin=somator
)

# Célula OLM (inhibición compartida)
if cfg.olm_size > 0:
    netParams.importCellParams(
        label='OLM_rule',
        conds={'cellType': 'OLM', 'cellModel': 'OLM'},
        fileName='olm.hoc',
        cellName='INT_cAC_noljp',
        somaAtOrigin=somator
    )
    
    # Construir lista de secciones basales para OLM
    OLMbasalSecList = []
    for secName, sec in netParams.cellParams['OLM_rule'].secs.items():
        if 'basal' in secName:
            OLMbasalSecList.append(secName)
    
    if not OLMbasalSecList:
        OLMbasalSecList = ['soma_0']

# =============================================================================
# PASO 2: CREAR POBLACIONES (Arquitectura Competitiva)
# =============================================================================

# POBLACIÓN A (Respuesta Correcta / Izquierda)
netParams.popParams['PYR_A'] = {
    'cellType': 'PYR',
    'numCells': cfg.popA_size,
    'cellModel': 'PYR'
}

# POBLACIÓN B (Respuesta Incorrecta / Derecha)
netParams.popParams['PYR_B'] = {
    'cellType': 'PYR',
    'numCells': cfg.popB_size,
    'cellModel': 'PYR'
}

# POBLACIÓN OLM (Inhibición Global Compartida)
if cfg.olm_size > 0:
    netParams.popParams['OLM'] = {
        'cellType': 'OLM',
        'numCells': cfg.olm_size,
        'cellModel': 'OLM'
    }

# =============================================================================
# PASO 3: IDENTIFICAR SECCIONES DENDRÍTICAS (del modelo original)
# =============================================================================

# Listas para targeting sináptico específico
SCsecList = []        # Schaffer Collaterals (100-350 μm del soma)
OLMsecList = []       # Dendritas apicales distales (>250 μm)
PVBCsecList = []      # Cerca del soma (<50 μm) - No usado

SCsomaDist = [100, 350]
OLMsomaDist = cfg.OLMsomaDist
PVBCsomaDist = cfg.PVBCsomaDist

for secName, sec in netParams.cellParams['PYR_rule'].secs.items():
    if 'pt3d' in sec['geom']:
        pt3d = sec['geom']['pt3d']
        midpoint = int(len(pt3d)/2)
        x, y, z = pt3d[midpoint][0:3]
        distSec = np.linalg.norm(np.array([x, y, z]))
        
        if secName[0:4] == 'apic':
            # Schaffer Collaterals (zona media de apical)
            if (distSec >= SCsomaDist[0] and distSec <= SCsomaDist[1] 
                and sec['geom']['diam'] < 2):
                SCsecList.append(secName)
            
            # OLM targets (dendritas apicales distales)
            if distSec > OLMsomaDist:
                OLMsecList.append(secName)
        
        if secName[0:4] == 'dend' or secName[0:4] == 'soma':
            if distSec < PVBCsomaDist:
                PVBCsecList.append(secName)

# =============================================================================
# PASO 4: MECANISMOS SINÁPTICOS (del modelo original)
# =============================================================================

# Excitatorio PYR→OLM (AMPA/NMDA con STP)
netParams.synMechParams['PC-OLM'] = {
    'mod': 'DetAMPANMDA',
    'tau_d_AMPA': 1.7,
    'tau_d_NMDA': 148.5,
    'Use': cfg.pc_olm_use,
    'Dep': cfg.olmdepfact,
    'Fac': cfg.olmfacfact,
    'NMDA_ratio': 0.28
}

# Inhibitorio OLM→PYR (GABAA con parámetros del Modelo Simplificado)
netParams.synMechParams['OLM-PC'] = {
    'mod': 'DetGABAAB',
    'tau_d_GABAA': cfg.olm_pc_gaba_tau,
    'Use': 0.3,
    'Dep': cfg.olm2pcDep,  # 0 en Modelo Simplificado
    'Fac': cfg.olm2pcFac   # 0 en Modelo Simplificado
}

# Excitatorio para Schaffer Collateral (input externo)
# Sin STP para estímulo externo
netParams.synMechParams['SC-PC'] = {
    'mod': 'DetAMPANMDA',
    'tau_d_AMPA': 3.0,
    'tau_d_NMDA': 148.5,
    'Use': 0.5,
    'Dep': 0,              # Sin depresión para input externo
    'Fac': 0,              # Sin facilitación
    'NMDA_ratio': 1.22
}

# =============================================================================
# PASO 5: PARÁMETROS DE CONECTIVIDAD (Preparación)
# =============================================================================

# Asignar variables a netParams para uso en fórmulas de conectividad
netParams.np_pc_olm_hibound = cfg.pc_olm_hibound
netParams.np_pc_olm_lowbound = cfg.pc_olm_lowbound
netParams.np_pc_olm_wei = cfg.pc_olm_wei
netParams.pc_olm_conprob = cfg.pc_olm_conprob
netParams.pc_olm_synfact = cfg.pc_olm_synfact

netParams.np_olm_pc_wei = cfg.olm_pc_wei
netParams.olm_pc_synfact = cfg.olm_pc_synfact
netParams.olm_pc_conprob = cfg.olm_pc_conprob
netParams.np_olm_pc_lobound = cfg.olm_pc_lobound
netParams.np_olm_pc_hibound = cfg.olm_pc_hibound

netParams.olmscalenum = cfg.olmscalenum
netParams.pcscalenum = cfg.pcscalenum

# =============================================================================
# PASO 6: CONECTIVIDAD FEEDFORWARD (PYR → OLM)
# =============================================================================

if cfg.connectPCOLM and cfg.olm_size > 0:
    # PYR_A → OLM
    netParams.connParams['PYR_A->OLM'] = {
        'preConds': {'pop': 'PYR_A'},
        'postConds': {'pop': 'OLM'},
        'synMech': 'PC-OLM',
        'synsPerConn': 'int(binomial(int(pcscalenum*5*pc_olm_synfact), pc_olm_conprob))',
        'weight': 'uniform(np_pc_olm_lowbound, np_pc_olm_hibound) * np_pc_olm_wei',
        'delay': 'uniform(0.5, 2)',
        'sec': OLMbasalSecList,
        'connRandomSecFromList': True
    }
    
    # PYR_B → OLM
    netParams.connParams['PYR_B->OLM'] = {
        'preConds': {'pop': 'PYR_B'},
        'postConds': {'pop': 'OLM'},
        'synMech': 'PC-OLM',
        'synsPerConn': 'int(binomial(int(pcscalenum*5*pc_olm_synfact), pc_olm_conprob))',
        'weight': 'uniform(np_pc_olm_lowbound, np_pc_olm_hibound) * np_pc_olm_wei',
        'delay': 'uniform(0.5, 2)',
        'sec': OLMbasalSecList,
        'connRandomSecFromList': True
    }

# =============================================================================
# PASO 7: CONECTIVIDAD FEEDBACK (OLM → PYR) - CRÍTICO PARA COMPETENCIA
# =============================================================================

if cfg.connectOLMPC and cfg.olm_size > 0:
    # OLM → PYR_A (Inhibición competitiva)
    netParams.connParams['OLM->PYR_A'] = {
        'preConds': {'pop': 'OLM'},
        'postConds': {'pop': 'PYR_A'},
        'synMech': 'OLM-PC',
        'synsPerConn': 'int(binomial(int(olmscalenum*13*olm_pc_synfact), olm_pc_conprob))',
        'weight': 'uniform(np_olm_pc_lobound, np_olm_pc_hibound) * np_olm_pc_wei',
        'delay': 'uniform(0.5, 1)',
        'sec': OLMsecList,
        'connRandomSecFromList': True
    }
    
    # OLM → PYR_B (Inhibición competitiva)
    netParams.connParams['OLM->PYR_B'] = {
        'preConds': {'pop': 'OLM'},
        'postConds': {'pop': 'PYR_B'},
        'synMech': 'OLM-PC',
        'synsPerConn': 'int(binomial(int(olmscalenum*13*olm_pc_synfact), olm_pc_conprob))',
        'weight': 'uniform(np_olm_pc_lobound, np_olm_pc_hibound) * np_olm_pc_wei',
        'delay': 'uniform(0.5, 1)',
        'sec': OLMsecList,
        'connRandomSecFromList': True
    }

# =============================================================================
# PASO 8: ESTÍMULO EXTERNO (Entrada de Aprendizaje)
# =============================================================================

# Fuente de estímulo (compartida para ambas poblaciones)
netParams.stimSourceParams['Task_Input'] = {
    'type': 'NetStim',
    'rate': cfg.sc_input_rate,    # Hz
    'noise': cfg.sc_input_noise   # Ruido Poisson
}

# Parámetros para pesos uniformes
netParams.sc_wei_A = cfg.sc_wei_left   # Será actualizado por el script principal
netParams.sc_wei_B = cfg.sc_wei_right  # Será actualizado por el script principal

# Conexión Task_Input → PYR_A (Opción Correcta)
netParams.stimTargetParams['Input->PYR_A'] = {
    'source': 'Task_Input',
    'conds': {'pop': 'PYR_A'},
    'synMech': 'SC-PC',
    'weight': 'sc_wei_A',  # Variable controlada externamente
    'delay': 'uniform(0.5, 2)',
    'sec': SCsecList if len(SCsecList) > 0 else ['soma_0']
}

# Conexión Task_Input → PYR_B (Opción Incorrecta)
netParams.stimTargetParams['Input->PYR_B'] = {
    'source': 'Task_Input',
    'conds': {'pop': 'PYR_B'},
    'synMech': 'SC-PC',
    'weight': 'sc_wei_B',  # Variable controlada externamente
    'delay': 'uniform(0.5, 2)',
    'sec': SCsecList if len(SCsecList) > 0 else ['soma_0']
}

# =============================================================================
# NOTA FINAL
# =============================================================================
# Este netParams mantiene:
# 1. Células biofísicas del modelo original (pyr.hoc, olm.hoc)
# 2. Mecanismos sinápticos realistas (DetAMPANMDA, DetGABAAB)
# 3. Targeting dendrítico específico (OLMsecList, SCsecList)
# 4. Arquitectura competitiva con dos poblaciones PYR
# 5. Circuito PYR→OLM→PYR para competencia mediada por inhibición
