#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba Rápida - Verificación de Actividad Neuronal
Versión simplificada para confirmar que las células disparan
"""

import sys
from netpyne import sim

# =============================================================================
# CONFIGURACIÓN RÁPIDA
# =============================================================================
print("="*80)
print("PRUEBA RÁPIDA: Verificación de Actividad")
print("="*80)

try:
    from cfg_integrated import cfg
    from netParams_integrated import netParams
except ImportError as e:
    print(f"ERROR: No se pueden importar configuraciones: {e}")
    sys.exit(1)

# CONFIGURACIÓN PARA PRUEBA RÁPIDA
cfg.duration = 500.0        # 500 ms (prueba corta)
cfg.popA_size = 20          # Poblaciones pequeñas
cfg.popB_size = 20
cfg.olm_size = 5

# DESACTIVAR ANÁLISIS AUTOMÁTICO (para velocidad)
cfg.analysis = {}

# ASEGURAR PESOS FUERTES
cfg.sc_wei_left = 3.0       # Peso fuerte garantizado
cfg.sc_wei_right = 3.0
cfg.sc_input_rate = 60      # Frecuencia alta

# Actualizar netParams
netParams.sc_wei_A = cfg.sc_wei_left
netParams.sc_wei_B = cfg.sc_wei_right

print(f"\nConfiguración de Prueba:")
print(f"  - Duración: {cfg.duration} ms")
print(f"  - Poblaciones: PYR_A={cfg.popA_size}, PYR_B={cfg.popB_size}, OLM={cfg.olm_size}")
print(f"  - Pesos: A={cfg.sc_wei_left:.1f}, B={cfg.sc_wei_right:.1f} nS")
print(f"  - Frecuencia estímulo: {cfg.sc_input_rate} Hz")
print(f"  - Sinapsis por conexión: 10 (fijo en netParams)")

print("\n" + "-"*80)
print("Ejecutando simulación...")
print("-"*80 + "\n")

# =============================================================================
# EJECUTAR SIMULACIÓN
# =============================================================================
sim.initialize()
sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg)

# =============================================================================
# ANÁLISIS DE RESULTADOS
# =============================================================================
print("\n" + "="*80)
print("RESULTADOS DE LA PRUEBA")
print("="*80)

import numpy as np

# Extraer espigas
all_spikes_time = np.array(sim.allSimData['spkt']) if 'spkt' in sim.allSimData else np.array([])
all_spikes_gid = np.array(sim.allSimData['spkid']) if 'spkid' in sim.allSimData else np.array([])

total_spikes = len(all_spikes_time)

# Espigas por población
if total_spikes > 0:
    pop_gids_A = np.array(sim.net.pops['PYR_A'].cellGids)
    pop_gids_B = np.array(sim.net.pops['PYR_B'].cellGids)
    pop_gids_OLM = np.array(sim.net.pops['OLM'].cellGids)
    
    spikes_A = all_spikes_time[np.isin(all_spikes_gid, pop_gids_A)]
    spikes_B = all_spikes_time[np.isin(all_spikes_gid, pop_gids_B)]
    spikes_OLM = all_spikes_time[np.isin(all_spikes_gid, pop_gids_OLM)]
    
    print(f"\n✅ ÉXITO: Se generaron espigas")
    print(f"\nEstadísticas:")
    print(f"  - Total de espigas: {total_spikes}")
    print(f"  - PYR_A: {len(spikes_A)} espigas ({len(spikes_A)/cfg.popA_size:.1f} por célula)")
    print(f"  - PYR_B: {len(spikes_B)} espigas ({len(spikes_B)/cfg.popB_size:.1f} por célula)")
    print(f"  - OLM: {len(spikes_OLM)} espigas ({len(spikes_OLM)/cfg.olm_size:.1f} por célula)")
    
    # Tasa de disparo promedio
    duration_sec = cfg.duration / 1000.0
    rate_A = len(spikes_A) / (cfg.popA_size * duration_sec)
    rate_B = len(spikes_B) / (cfg.popB_size * duration_sec)
    rate_OLM = len(spikes_OLM) / (cfg.olm_size * duration_sec)
    
    print(f"\nTasas de disparo promedio:")
    print(f"  - PYR_A: {rate_A:.2f} Hz")
    print(f"  - PYR_B: {rate_B:.2f} Hz")
    print(f"  - OLM: {rate_OLM:.2f} Hz")
    
    # Evaluación
    print(f"\nEvaluación:")
    if rate_A > 0.5 and rate_B > 0.5:
        print(f"  ✅ Actividad adecuada en ambas poblaciones PYR")
    elif rate_A > 0.1 or rate_B > 0.1:
        print(f"  ⚠️  Actividad baja pero presente - considera aumentar pesos")
    else:
        print(f"  ❌ Actividad muy baja - aumenta pesos o frecuencia")
    
    if rate_OLM > 0.5:
        print(f"  ✅ OLMs respondiendo correctamente")
    else:
        print(f"  ⚠️  OLMs poco activas - esto es normal si PYRs disparan poco")
    
    # Recomendaciones
    print(f"\nRecomendaciones para simulación completa:")
    if rate_A < 1.0:
        rec_weight = cfg.sc_wei_left * 1.5
        print(f"  - Aumentar pesos a {rec_weight:.1f} nS")
    if rate_A > 5.0:
        rec_weight = cfg.sc_wei_left * 0.7
        print(f"  - Reducir pesos a {rec_weight:.1f} nS (demasiada actividad)")
    if 1.0 <= rate_A <= 5.0:
        print(f"  - Configuración actual es óptima para experimento completo")
    
else:
    print(f"\n❌ PROBLEMA: No se generaron espigas")
    print(f"\nSoluciones sugeridas:")
    print(f"  1. Aumentar peso sináptico:")
    print(f"     cfg.sc_wei_left = 5.0")
    print(f"     cfg.sc_wei_right = 5.0")
    print(f"  2. Aumentar frecuencia de estímulo:")
    print(f"     cfg.sc_input_rate = 80")
    print(f"  3. Verificar que synsPerConn = 10 en netParams")
    print(f"  4. Verificar mecanismos NMODL compilados (carpeta x86_64/)")

print("\n" + "="*80)
print("PRUEBA COMPLETADA")
print("="*80)

# Guardar datos para inspección
if total_spikes > 0:
    print(f"\nDatos guardados en: model_output_data.pkl")
    print(f"Puedes cargarlos con: data = pickle.load(open('model_output_data.pkl', 'rb'))")

print(f"\nSi la prueba fue exitosa, ejecuta el experimento completo:")
print(f"  mpiexec -n 4 python run_integrated_ddm.py")