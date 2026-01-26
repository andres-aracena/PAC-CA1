from netpyne import specs
from cfg_matias import cfg
import numpy as np

netParams = specs.NetParams()

# =============================================================================
# PASO 1: DEFINICIÓN DE CÉLULAS (Importadas de HOC)
# =============================================================================
# Regla para Células Piramidales (Se usará para PYR_A y PYR_B)
netParams.importCellParams(
    label='PYR_rule', 
    conds={'cellType': 'PYR', 'cellModel': 'PYR'},
    fileName='pyr.hoc', 
    cellName='CA1_PC_cAC_sig', 
    somaAtOrigin=True
)

# Regla para Células OLM
netParams.importCellParams(
    label='OLM_rule', 
    conds={'cellType': 'OLM', 'cellModel': 'OLM'},
    fileName='olm.hoc', 
    cellName='INT_cAC_noljp', 
    somaAtOrigin=True
)

# =============================================================================
# PASO 2: CREACIÓN DE POBLACIONES (Estructura Competitiva)
# =============================================================================

# POBLACIÓN A (La respuesta "Correcta" o Izquierda)
# Usamos cellType='PYR' para que coincida con la regla de célula importada arriba,
# pero le damos un 'popLabel' distinto implícito al usar la llave 'PYR_A'.
netParams.popParams['PYR_A'] = {
    'cellType': 'PYR',      # Usa la biofísica de PYR
    'numCells': cfg.popA_size,
    'cellModel': 'PYR'
}

# POBLACIÓN B (La respuesta "Incorrecta" o Derecha)
netParams.popParams['PYR_B'] = {
    'cellType': 'PYR',      # Usa la misma biofísica de PYR
    'numCells': cfg.popB_size,
    'cellModel': 'PYR'
}

# POBLACIÓN OLM (Inhibición Lateral Compartida)
netParams.popParams['OLM'] = {
    'cellType': 'OLM',
    'numCells': cfg.olm_size,
    'cellModel': 'OLM'
}

# =============================================================================
# 3. MECANISMOS SINÁPTICOS (VERSIÓN ROBUSTA: Exp2Syn)
# =============================================================================
# Usamos mecanismos estándar de NEURON para evitar errores de 'NoneType' si faltan los MODs

# Excitatorio Estándar (Reemplaza a DetAMPANMDA para debug)
netParams.synMechParams['Exc_Standard'] = {
    'mod': 'Exp2Syn', 
    'tau1': 0.1, 
    'tau2': 5.0, 
    'e': 0
}

# Inhibitorio Estándar (Reemplaza a DetGABAAB para debug)
netParams.synMechParams['Inh_Standard'] = {
    'mod': 'Exp2Syn', 
    'tau1': 0.1, 
    'tau2': 10.0, 
    'e': -80 # Potencial de reversión inhibitorio
}

# =============================================================================
# 4. CONECTIVIDAD (CIRCUITO COMPETITIVO)
# =============================================================================

# A) PYR -> OLM (Excitación)
# --------------------------
netParams.connParams['PYR_A->OLM'] = {
    'preConds': {'pop': 'PYR_A'}, 'postConds': {'pop': 'OLM'},
    'synMech': 'Exc_Standard',  # <--- Usamos el mecanismo seguro
    'probability': 0.35, 
    'weight': 0.05, 
    'delay': 1.0,
    'sec': 'dend_0' # Conectamos en dendrita genérica
}

netParams.connParams['PYR_B->OLM'] = {
    'preConds': {'pop': 'PYR_B'}, 'postConds': {'pop': 'OLM'},
    'synMech': 'Exc_Standard',
    'probability': 0.35, 
    'weight': 0.05, 
    'delay': 1.0,
    'sec': 'dend_0'
}

# B) OLM -> PYR (Inhibición Lateral / Feedback)
# ---------------------------------------------
# Conectamos al soma para máxima inhibición efectiva en esta prueba
netParams.connParams['OLM->PYR_A'] = {
    'preConds': {'pop': 'OLM'}, 'postConds': {'pop': 'PYR_A'},
    'synMech': 'Inh_Standard',  # <--- Usamos el mecanismo seguro
    'probability': 1.0, 
    'weight': 0.1, # Inhibición fuerte
    'delay': 1.0,
    'sec': 'soma_0' 
}

netParams.connParams['OLM->PYR_B'] = {
    'preConds': {'pop': 'OLM'}, 'postConds': {'pop': 'PYR_B'},
    'synMech': 'Inh_Standard',
    'probability': 1.0, 
    'weight': 0.1, 
    'delay': 1.0,
    'sec': 'soma_0'
}

# =============================================================================
# 5. ESTÍMULO EXTERNO (APRENDIZAJE)
# =============================================================================
netParams.stimSourceParams['Task_Input'] = {
    'type': 'NetStim', 
    'rate': 20, 
    'noise': 0.5 
}

# Conexión A (Correcta)
netParams.stimTargetParams['Input->PYR_A'] = {
    'source': 'Task_Input', 
    'conds': {'pop': 'PYR_A'},
    'synMech': 'Exc_Standard',
    'weight': cfg.sc_wei_left,  # Variable controlada por run_matias_ddm.py
    'delay': 1.0,
    'sec': 'soma_0' # Directo al soma para asegurar disparo
}

# Conexión B (Incorrecta)
netParams.stimTargetParams['Input->PYR_B'] = {
    'source': 'Task_Input', 
    'conds': {'pop': 'PYR_B'},
    'synMech': 'Exc_Standard',
    'weight': cfg.sc_wei_right, # Variable controlada por run_matias_ddm.py
    'delay': 1.0,
    'sec': 'soma_0'
}

""" 
# =============================================================================
# PREPARACIÓN: Identificar Secciones Dendríticas (Para OLM)
# =============================================================================
# Necesitamos saber qué secciones están lejos del soma (>250um) para que las OLM
# se conecten allí, imitando la biología real.
OLMsecList = []
OLMsomaDist = 250

if 'PYR_rule' in netParams.cellParams:
    for secName, sec in netParams.cellParams['PYR_rule'].secs.items():
        if 'pt3d' in sec['geom']:
            pt3d = sec['geom']['pt3d']
            mid = int(len(pt3d)/2)
            # Calculamos distancia euclidiana al origen (0,0,0) asumiendo soma allí
            distSec = np.linalg.norm(np.array(pt3d[mid][0:3]))
            
            if secName.startswith('apic') and distSec > OLMsomaDist:
                OLMsecList.append(secName)


# =============================================================================
# PASO 3: MECANISMOS SINÁPTICOS Y CONECTIVIDAD (El Circuito)
# =============================================================================

# 1. Definir Mecanismos Sinápticos
# --------------------------------
# Excitatorio (AMPA/NMDA) para PYR -> OLM y para el Estímulo
# netParams.synMechParams['Exc_AMPA_NMDA'] = {
#    'mod': 'DetAMPANMDA', 
#    'tau_d_AMPA': 1.7, 'tau_d_NMDA': 148.5, 
#    'Use': 0.07, 'Dep': 38, 'Fac': 470, 'NMDA_ratio': 0.28
# }

netParams.synMechParams['Exc_Standard'] = {
    'mod': 'Exp2Syn', 
    'tau1': 0.1, 'tau2': 5.0, 'e': 0.0} 

# Inhibitorio (GABA) para OLM -> PYR
netParams.synMechParams['Inh_GABA'] = {
    'mod': 'DetGABAAB',
    'tau_d_GABAA': 11.8, # Decaimiento rápido (Modelo Simplificado)
    'Use': 0.3, 'Dep': 0, 'Fac': 0
}

# 2. Conectividad Excitatoria (Feedforward: PYR -> OLM)
# -----------------------------------------------------
# Las células PYR (tanto A como B) excitan a las OLM
netParams.connParams['PYR_A->OLM'] = {
    'preConds': {'pop': 'PYR_A'}, 'postConds': {'pop': 'OLM'},
    'synMech': 'Exc_AMPA_NMDA',
    'probability': 0.35, 'weight': 0.1, 'delay': 1.0,
    'sec': 'basal' # Conectan en dendritas basales
}

netParams.connParams['PYR_B->OLM'] = {
    'preConds': {'pop': 'PYR_B'}, 'postConds': {'pop': 'OLM'},
    'synMech': 'Exc_AMPA_NMDA',
    'probability': 0.35, 'weight': 0.1, 'delay': 1.0,
    'sec': 'basal'
}

# 3. Conectividad Inhibitoria (Feedback: OLM -> PYR)
# --------------------------------------------------
# La OLM inhibe a AMBAS poblaciones. Esto crea la competencia.
netParams.connParams['OLM->PYR_A'] = {
    'preConds': {'pop': 'OLM'}, 'postConds': {'pop': 'PYR_A'},
    'synMech': 'Inh_GABA',
    'probability': 1.0, 'weight': 0.5, 'delay': 1.0,
    'sec': OLMsecList # Conectan solo en dendritas distales
}

netParams.connParams['OLM->PYR_B'] = {
    'preConds': {'pop': 'OLM'}, 'postConds': {'pop': 'PYR_B'},
    'synMech': 'Inh_GABA',
    'probability': 1.0, 'weight': 0.5, 'delay': 1.0,
    'sec': OLMsecList
}
 """

""" 
# =============================================================================
# PASO 4: ESTÍMULO EXTERNO (La "Entrada" que aprenderemos)
# =============================================================================
# Creamos un generador de espigas (Ruido de fondo / Estímulo de la tarea)
netParams.stimSourceParams['Task_Input'] = {
    'type': 'NetStim', 
    'rate': 20,         # 20 Hz (Frecuencia de disparo)
    'noise': 0.5        # Ruido Poisson (0=rítmico, 1=totalmente aleatorio)
}

# CONEXIÓN APRENDIBLE 1: Estímulo -> PYR_A (Respuesta Correcta)
# El peso 'cfg.sc_wei_left' se actualizará en el bucle de aprendizaje
netParams.stimTargetParams['Input->PYR_A'] = {
    'source': 'Task_Input', 
    'conds': {'pop': 'PYR_A'},
    'synMech': 'Exc_Standard',
    'weight': cfg.sc_wei_left,  # <--- VARIABLE CLAVE
    'delay': 1.0,
    'sec': 'soma' # El estímulo llega al soma
}

# CONEXIÓN APRENDIBLE 2: Estímulo -> PYR_B (Respuesta Incorrecta)
# El peso 'cfg.sc_wei_right' disminuirá si el agente se equivoca
netParams.stimTargetParams['Input->PYR_B'] = {
    'source': 'Task_Input', 
    'conds': {'pop': 'PYR_B'},
    'synMech': 'Exc_Standard',
    'weight': cfg.sc_wei_right, # <--- VARIABLE CLAVE
    'delay': 1.0,
    'sec': 'soma'
} """