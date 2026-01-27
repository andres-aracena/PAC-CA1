#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Principal Integrado: Simulación DDM con Modelo CA1 Biofísico
Versión MPI corregida - Estructura simplificada
"""

import sys
import os

# =============================================================================
# CONFIGURACIÓN MPI
# =============================================================================
# Para evitar problemas, configuramos esto al inicio
if 'mpi4py' in sys.modules:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    nhosts = comm.Get_size()
    USE_MPI = True
else:
    # Intentar importar mpi4py
    try:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        nhosts = comm.Get_size()
        USE_MPI = True
    except:
        rank = 0
        nhosts = 1
        USE_MPI = False

# =============================================================================
# CONFIGURACIÓN DE MATPLOTLIB (antes de cualquier import)
# =============================================================================
# Solo el proceso maestro necesita matplotlib
if rank == 0:
    import matplotlib
    matplotlib.use('Agg')  # Backend no interactivo

# =============================================================================
# IMPORTS COMUNES A TODOS LOS PROCESOS
# =============================================================================
from netpyne import sim

try:
    from cfg_integrated import cfg
    from netParams_integrated import netParams
except ImportError as e:
    if rank == 0:
        print(f"ERROR: No se pueden importar configuraciones: {e}")
    sys.exit(1)

# =============================================================================
# PARÁMETROS GLOBALES (definidos para todos los procesos)
# =============================================================================
N_TRIALS = 5  # Reducido para pruebas, puedes cambiarlo después
TARGET_SIDE = 'A'
LTP_RATE = 0.032
LTD_RATE = 0.023

# =============================================================================
# VARIABLES GLOBALES
# =============================================================================
current_weight_A = cfg.sc_wei_left
current_weight_B = cfg.sc_wei_right

# =============================================================================
# BLOQUE DEL PROCESO MAESTRO (rank 0)
# =============================================================================
if rank == 0:
    print("=" * 80)
    print("SIMULACIÓN INTEGRADA: CA1 + TOMA DE DECISIONES")
    print("=" * 80)
    print(f"MPI: Proceso {rank} de {nhosts} (MAESTRO)")
    print("\n>>> INICIALIZANDO CONFIGURACIÓN...")
    
    # Importar módulos específicos del maestro
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import signal
    
    print(f"   > Paso de tiempo (dt): {cfg.dt} ms")
    print(f"   > Duración por trial: {cfg.duration} ms")
    print(f"   > Poblaciones: PYR_A={cfg.popA_size}, PYR_B={cfg.popB_size}, OLM={cfg.olm_size}")
    
    # Historiales (solo en maestro)
    history_weights_A = []
    history_weights_B = []
    history_choice = []
    
    # Memoria para trayectorias DDM
    full_trace_A = []
    full_trace_B = []
    experiment_decision_points = []
    
    print(f"\n>>> INICIANDO EXPERIMENTO: {N_TRIALS} Trials")
    print("-" * 80)
    
    # =========================================================================
    # FUNCIONES AUXILIARES (definidas solo en rank 0)
    # =========================================================================
    def extract_spikes_by_population(sim_data, pop_name):
        """Extrae tiempos de espigas para una población específica"""
        all_spikes_time = np.array(sim_data['spkt'])
        all_spikes_gid = np.array(sim_data['spkid'])
        pop_gids = np.array(sim.net.pops[pop_name].cellGids)
        mask = np.isin(all_spikes_gid, pop_gids)
        return all_spikes_time[mask], all_spikes_gid[mask], pop_gids
    
    def compute_firing_rate_time_series(spike_times, pop_size, duration, dt_bin):
        """Calcula serie temporal de tasa de disparo con ventana deslizante"""
        time_bins = np.arange(0, duration, dt_bin)
        rates = []
        
        for t in time_bins:
            t_end = t + dt_bin
            spike_count = np.sum((spike_times >= t) & (spike_times < t_end))
            rate_hz = (spike_count / pop_size) * (1000.0 / dt_bin)
            rates.append(float(rate_hz))
        
        return time_bins, np.array(rates)
    
    def simulate_ddm_race(rate_A, rate_B, time_bins, threshold=30.0, alpha=0.10, 
                          noise_std=0.1, leak=0.01):
        """Simula modelo de carrera (Racing DDM)"""
        x_A, x_B = 0.0, 0.0
        trace_A, trace_B = [0.0], [0.0]
        winner = 'NONE'
        rt = time_bins[-1] if len(time_bins) > 0 else 0
        
        for i, t in enumerate(time_bins):
            # Ecuación de acumulación: dx = alpha*rate + noise - leak*x
            x_A += (alpha * rate_A[i]) + np.random.normal(0, noise_std) - (leak * x_A)
            x_B += (alpha * rate_B[i]) + np.random.normal(0, noise_std) - (leak * x_B)
            
            # No negativos
            x_A = float(max(0, x_A))
            x_B = float(max(0, x_B))
            
            trace_A.append(x_A)
            trace_B.append(x_B)
            
            # Detección de umbral
            if x_A >= threshold:
                winner = 'A'
                rt = t
                break
            elif x_B >= threshold:
                winner = 'B'
                rt = t
                break
        
        return trace_A, trace_B, winner, rt
    
    def plot_raster_split(trial_num, spikes_A, gids_A, spikes_B, gids_B, 
                          weight_A, weight_B, duration):
        """Genera raster plot dividido por población"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        
        ax1.scatter(spikes_A, gids_A, s=10, c='green', marker='|', alpha=0.6)
        ax1.set_title(f'Trial {trial_num}: PYR_A (Correcta) - W={weight_A:.4f}')
        ax1.set_ylabel('GID')
        ax1.set_xlim([0, duration])
        ax1.grid(True, alpha=0.3)
        
        ax2.scatter(spikes_B, gids_B, s=10, c='red', marker='|', alpha=0.6)
        ax2.set_title(f'Trial {trial_num}: PYR_B (Incorrecta) - W={weight_B:.4f}')
        ax2.set_xlabel('Tiempo (ms)')
        ax2.set_ylabel('GID')
        ax2.set_xlim([0, duration])
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'Raster_Split_Trial_{trial_num}.png', dpi=150)
        plt.close()

# =============================================================================
# BLOQUE DE PROCESOS ESCLAVOS (rank > 0)
# =============================================================================
else:
    if USE_MPI:
        print(f"MPI: Proceso {rank} de {nhosts} (ESCLAVO)")

# =============================================================================
# BUCLE PRINCIPAL DE SIMULACIÓN
# =============================================================================
for trial in range(N_TRIALS):
    # -------------------------------------------------------------------------
    # A. SINCRONIZAR PESOS ENTRE PROCESOS
    # -------------------------------------------------------------------------
    if rank == 0:
        print(f"\n--- TRIAL {trial + 1}/{N_TRIALS} ---")
        
        # Guardar historial de pesos
        history_weights_A.append(current_weight_A)
        history_weights_B.append(current_weight_B)
        
        # Actualizar netParams
        netParams.sc_wei_A = current_weight_A
        netParams.sc_wei_B = current_weight_B
        
        print(f"   > Pesos: A={current_weight_A:.4f}, B={current_weight_B:.4f}")
        
        # Enviar pesos a procesos esclavos si usamos MPI
        if USE_MPI:
            # Crear array con los pesos
            weight_data = [current_weight_A, current_weight_B]
            comm.bcast(weight_data, root=0)
    
    else:
        # Procesos esclavos: recibir pesos del maestro
        if USE_MPI:
            weight_data = comm.bcast(None, root=0)
            current_weight_A, current_weight_B = weight_data
            netParams.sc_wei_A = current_weight_A
            netParams.sc_wei_B = current_weight_B
    
    # -------------------------------------------------------------------------
    # B. EJECUTAR SIMULACIÓN
    # -------------------------------------------------------------------------
    # Configurar MPI para NetPyNE
    if USE_MPI:
        cfg.useMPI = True
        cfg.comm = comm
        cfg.rank = rank
        cfg.nhosts = nhosts
    else:
        cfg.useMPI = False
    
    # Reiniciar y ejecutar simulación
    sim.initialize()
    sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg)
    
    # -------------------------------------------------------------------------
    # C. PROCESAMIENTO DE RESULTADOS (solo rank 0)
    # -------------------------------------------------------------------------
    if rank == 0:
        # Extraer datos de espigas
        spikes_A, gids_A_spikes, pop_gids_A = extract_spikes_by_population(
            sim.allSimData, 'PYR_A'
        )
        spikes_B, gids_B_spikes, pop_gids_B = extract_spikes_by_population(
            sim.allSimData, 'PYR_B'
        )
        
        print(f"   > Espigas: A={len(spikes_A)}, B={len(spikes_B)}")
        
        # Gráfico: Raster Split
        plot_raster_split(
            trial + 1, spikes_A, gids_A_spikes, spikes_B, gids_B_spikes,
            current_weight_A, current_weight_B, cfg.duration
        )
        print(f"   > Guardado: Raster_Split_Trial_{trial+1}.png")
        
        # ---------------------------------------------------------------------
        # D. Cálculo DDM / Racing Model
        # ---------------------------------------------------------------------
        dt_decision = 10.0  # ms por bin
        
        # Calcular tasas de disparo
        time_bins_A, rate_A = compute_firing_rate_time_series(
            spikes_A, cfg.popA_size, cfg.duration, dt_decision
        )
        time_bins_B, rate_B = compute_firing_rate_time_series(
            spikes_B, cfg.popB_size, cfg.duration, dt_decision
        )
        
        # Simular acumulación (carrera)
        trace_A_trial, trace_B_trial, winner, rt = simulate_ddm_race(
            rate_A, rate_B, time_bins_A,
            threshold=30.0, alpha=0.10, noise_std=0.1, leak=0.01
        )
        
        # ---------------------------------------------------------------------
        # E. Guardar Trayectorias
        # ---------------------------------------------------------------------
        full_trace_A.extend(trace_A_trial)
        full_trace_B.extend(trace_B_trial)
        
        # Relleno visual
        remaining = int((cfg.duration - rt) / dt_decision)
        if remaining > 0 and len(trace_A_trial) > 0:
            final_A = trace_A_trial[-1]
            final_B = trace_B_trial[-1]
            full_trace_A.extend([final_A] * remaining)
            full_trace_B.extend([final_B] * remaining)
        
        experiment_decision_points.append(len(full_trace_A))
        
        # ---------------------------------------------------------------------
        # F. Aprendizaje (Actualización de Pesos)
        # ---------------------------------------------------------------------
        # Fallback si no hay decisión
        if winner == 'NONE':
            winner = 'A' if len(spikes_A) > len(spikes_B) else 'B'
            print(f"   > Sin cruce de umbral. Decisión por conteo: {winner}")
        
        is_correct = (winner == TARGET_SIDE)
        history_choice.append(1 if is_correct else 0)
        
        print(f"   > Resultado: {winner} ({'ACIERTO' if is_correct else 'FALLO'}) | RT={rt:.1f} ms")
        
        # Regla de aprendizaje
        if is_correct:
            # Potenciar la respuesta correcta y debilitar la incorrecta
            current_weight_A += (current_weight_A * LTP_RATE)
            current_weight_B -= (current_weight_B * LTD_RATE)
        else:
            # Solo debilitar la respuesta incorrecta
            current_weight_B -= (current_weight_B * LTD_RATE)
        
        # Limitar pesos
        current_weight_A = np.clip(current_weight_A, 0.001, 1.0)
        current_weight_B = np.clip(current_weight_B, 0.001, 1.0)
    
    # Sincronizar procesos antes del próximo trial
    if USE_MPI:
        comm.Barrier()

# =============================================================================
# GENERACIÓN DE GRÁFICOS FINALES (solo rank 0)
# =============================================================================
if rank == 0:
    print("\n" + "=" * 80)
    print(">>> GENERANDO GRÁFICOS FINALES...")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # A. Final_Learning_Results (Evolución de Pesos y Desempeño)
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    ax1.plot(history_weights_A, 'g-o', label='Peso A (Correcto)', linewidth=2)
    ax1.plot(history_weights_B, 'r-x', label='Peso B (Incorrecto)', linewidth=2)
    ax1.set_title('Evolución de Pesos Sinápticos', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Peso Sináptico', fontsize=12)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(history_choice, 'b-s', linewidth=2, markersize=8)
    ax2.set_title('Historial de Aciertos', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Trial', fontsize=12)
    ax2.set_ylabel('Resultado (1=Acierto, 0=Fallo)', fontsize=12)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['Fallo', 'Acierto'])
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('Final_Learning_Results.png', dpi=150)
    plt.close()
    print("   > Guardado: Final_Learning_Results.png")
    
    # Estadísticas
    accuracy = np.mean(history_choice) * 100
    print(f"\n   ESTADÍSTICAS FINALES:")
    print(f"   - Precisión: {accuracy:.1f}%")
    print(f"   - Peso Final A: {current_weight_A:.4f}")
    print(f"   - Peso Final B: {current_weight_B:.4f}")
    print(f"   - Ratio A/B: {current_weight_A/current_weight_B:.2f}")
    
    # -------------------------------------------------------------------------
    # B. DDM_Trajectory_Full_Sequence (Historial Completo)
    # -------------------------------------------------------------------------
    if len(full_trace_A) > 0:
        fig_seq, ax_seq = plt.subplots(figsize=(14, 6))
        dt_plot = 10.0
        t_vec = np.arange(0, len(full_trace_A) * dt_plot, dt_plot)
        
        ax_seq.plot(t_vec, full_trace_A, color='green', lw=2, label='Acumulación A', alpha=0.8)
        ax_seq.plot(t_vec, full_trace_B, color='red', lw=2, label='Acumulación B', alpha=0.8)
        
        # Líneas verticales para separar trials
        for idx in experiment_decision_points[:-1]:  # Excluir el último
            ax_seq.axvline(x=idx*dt_plot, color='gray', linestyle=':', alpha=0.4)
        
        ax_seq.axhline(y=30.0, color='black', ls='--', lw=2, label='Umbral')
        ax_seq.set_title('Evolución Completa de la Competencia (Todos los Trials)', 
                         fontsize=14, fontweight='bold')
        ax_seq.set_xlabel('Tiempo Total (ms)', fontsize=12)
        ax_seq.set_ylabel('Acumulación', fontsize=12)
        ax_seq.legend(fontsize=11)
        ax_seq.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('DDM_Trajectory_Full_Sequence.png', dpi=150)
        plt.close()
        print("   > Guardado: DDM_Trajectory_Full_Sequence.png")
    
    # -------------------------------------------------------------------------
    # C. DDM_Trajectory (Solo el último trial)
    # -------------------------------------------------------------------------
    if 'trace_A_trial' in locals() and len(trace_A_trial) > 0:
        fig_last, ax_last = plt.subplots(figsize=(10, 6))
        t_last = np.arange(0, len(trace_A_trial) * dt_decision, dt_decision)
        
        ax_last.plot(t_last, trace_A_trial, color='green', lw=3, 
                    label='Acumulación A', alpha=0.8)
        ax_last.plot(t_last, trace_B_trial, color='red', lw=3, 
                    label='Acumulación B', alpha=0.8)
        ax_last.axhline(y=30.0, color='black', ls='--', lw=2, label='Umbral')
        
        # Marcar punto de decisión
        if winner != 'NONE':
            ax_last.scatter([rt], [30.0], s=200, c='gold', marker='*', 
                           edgecolors='black', linewidths=2, 
                           label=f'Decisión: {winner}', zorder=5)
        
        ax_last.set_title(f'Trayectoria de Decisión (Último Trial: {winner})', 
                         fontsize=14, fontweight='bold')
        ax_last.set_xlabel('Tiempo (ms)', fontsize=12)
        ax_last.set_ylabel('Acumulación', fontsize=12)
        ax_last.legend(fontsize=11)
        ax_last.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('DDM_Trajectory.png', dpi=150)
        plt.close()
        print("   > Guardado: DDM_Trajectory.png")
    
    # -------------------------------------------------------------------------
    # D. Gráficos de Voltaje (Trazas de Soma)
    # -------------------------------------------------------------------------
    if 'V_soma' in sim.allSimData and len(sim.allSimData['V_soma']) > 0:
        time_vec = np.array(sim.allSimData['t'])
        
        # Intentar extraer trazas de células representativas
        trace_0 = sim.allSimData['V_soma'].get('cell_0', [])
        trace_40 = sim.allSimData['V_soma'].get('cell_40', [])
        
        if len(trace_0) > 0 and len(trace_40) > 0:
            trace_0 = np.array(trace_0)
            trace_40 = np.array(trace_40)
            
            # Trazas Juntas
            plt.figure(figsize=(12, 6))
            plt.plot(time_vec, trace_0, 'g', label='PYR_A (Correcta)', 
                    alpha=0.8, linewidth=1.5)
            plt.plot(time_vec, trace_40, 'r', label='PYR_B (Incorrecta)', 
                    alpha=0.8, linewidth=1.5)
            plt.title('Voltaje de Soma: Competencia A vs B (Último Trial)', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Tiempo (ms)', fontsize=12)
            plt.ylabel('Voltaje (mV)', fontsize=12)
            plt.legend(fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('Trazas_Juntas.png', dpi=150)
            plt.close()
            print("   > Guardado: Trazas_Juntas.png")
            
            # Trazas Separadas
            fig_sep, (ax_s1, ax_s2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            ax_s1.plot(time_vec, trace_0, 'g', linewidth=1.5)
            ax_s1.set_title('PYR_A (Correcta)', fontsize=13, fontweight='bold')
            ax_s1.set_ylabel('Voltaje (mV)', fontsize=11)
            ax_s1.grid(True, alpha=0.3)
            
            ax_s2.plot(time_vec, trace_40, 'r', linewidth=1.5)
            ax_s2.set_title('PYR_B (Incorrecta)', fontsize=13, fontweight='bold')
            ax_s2.set_xlabel('Tiempo (ms)', fontsize=11)
            ax_s2.set_ylabel('Voltaje (mV)', fontsize=11)
            ax_s2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('Trazas_Separadas.png', dpi=150)
            plt.close()
            print("   > Guardado: Trazas_Separadas.png")
        else:
            print("   WARN: No se encontraron trazas de voltaje completas.")
    
    print("\n" + "=" * 80)
    print(">>> PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 80)

# =============================================================================
# FINALIZAR MPI
# =============================================================================
if USE_MPI:
    if rank == 0:
        print(">>> Simulación completada. Cerrando procesos MPI...")
    comm.Barrier()
    MPI.Finalize()