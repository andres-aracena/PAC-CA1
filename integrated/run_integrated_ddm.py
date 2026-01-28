#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Principal FINAL: Todos los gráficos + Configuración mejorada
Genera: DDM_Trajectory_Full, Learning_Result, Model_Output_Raster, 
Model_Output_Trace, Raster_Split (por trial)
"""

import sys
import os

# =============================================================================
# CONFIGURACIÓN MPI
# =============================================================================
if 'mpi4py' in sys.modules:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    nhosts = comm.Get_size()
    USE_MPI = True
else:
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
# CONFIGURACIÓN DE MATPLOTLIB
# =============================================================================
if rank == 0:
    import matplotlib
    matplotlib.use('Agg')

# =============================================================================
# IMPORTS
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
# PARÁMETROS GLOBALES
# =============================================================================
N_TRIALS = 5
TARGET_SIDE = 'A'
LTP_RATE = 0.05
LTD_RATE = 0.03

current_weight_A = cfg.sc_wei_left
current_weight_B = cfg.sc_wei_right

# =============================================================================
# BLOQUE DEL PROCESO MAESTRO
# =============================================================================
if rank == 0:
    print("=" * 80)
    print("SIMULACIÓN INTEGRADA: CA1 + TOMA DE DECISIONES")
    print("=" * 80)
    print(f"MPI: Proceso {rank} de {nhosts} (MAESTRO)")
    print("\n>>> INICIALIZANDO CONFIGURACIÓN...")
    
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import signal
    from matplotlib.lines import Line2D
    
    print(f"   > Paso de tiempo (dt): {cfg.dt} ms")
    print(f"   > Duración por trial: {cfg.duration} ms")
    print(f"   > Poblaciones: PYR_A={cfg.popA_size}, PYR_B={cfg.popB_size}, OLM={cfg.olm_size}")
    
    # Historiales
    history_weights_A = []
    history_weights_B = []
    history_choice = []
    history_spikes_A = []
    history_spikes_B = []
    history_spikes_OLM = []
    
    # Memoria DDM
    full_trace_A = []
    full_trace_B = []
    experiment_decision_points = []
    
    # Datos de trials
    all_trial_data = []
    
    print(f"\n>>> INICIANDO EXPERIMENTO: {N_TRIALS} Trials")
    print("-" * 80)
    
    # =========================================================================
    # FUNCIONES AUXILIARES
    # =========================================================================
    def extract_spikes_by_population(sim_data, pop_name):
        all_spikes_time = np.array(sim_data['spkt'])
        all_spikes_gid = np.array(sim_data['spkid'])
        pop_gids = np.array(sim.net.pops[pop_name].cellGids)
        mask = np.isin(all_spikes_gid, pop_gids)
        return all_spikes_time[mask], all_spikes_gid[mask], pop_gids
    
    def compute_firing_rate_time_series(spike_times, pop_size, duration, dt_bin):
        time_bins = np.arange(0, duration, dt_bin)
        rates = []
        for t in time_bins:
            t_end = t + dt_bin
            spike_count = np.sum((spike_times >= t) & (spike_times < t_end))
            rate_hz = (spike_count / pop_size) * (1000.0 / dt_bin)
            rates.append(float(rate_hz))
        return time_bins, np.array(rates)
    
    def simulate_ddm_race(rate_A, rate_B, time_bins, threshold=25.0, alpha=0.15, 
                          noise_std=0.2, leak=0.01):
        x_A, x_B = 0.0, 0.0
        trace_A, trace_B = [0.0], [0.0]
        winner = 'NONE'
        rt = time_bins[-1] if len(time_bins) > 0 else 0
        
        for i, t in enumerate(time_bins):
            x_A += (alpha * rate_A[i]) + np.random.normal(0, noise_std) - (leak * x_A)
            x_B += (alpha * rate_B[i]) + np.random.normal(0, noise_std) - (leak * x_B)
            x_A = float(max(0, x_A))
            x_B = float(max(0, x_B))
            trace_A.append(x_A)
            trace_B.append(x_B)
            
            if x_A >= threshold:
                winner = 'A'
                rt = t
                break
            elif x_B >= threshold:
                winner = 'B'
                rt = t
                break
        
        return trace_A, trace_B, winner, rt
    
    def plot_raster_split_trial(trial_num, spikes_A, gids_A, spikes_B, gids_B,
                                spikes_OLM, gids_OLM, weight_A, weight_B, duration):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
        
        if len(spikes_A) > 0:
            ax1.scatter(spikes_A, gids_A, s=12, c='green', marker='|', alpha=0.7)
        ax1.set_title(f'Trial {trial_num}: PYR_A (Correcta) - W={weight_A:.3f} nS', 
                     fontsize=12, fontweight='bold', color='green')
        ax1.set_ylabel('GID', fontsize=10)
        ax1.set_xlim([0, duration])
        ax1.grid(True, alpha=0.2, axis='x')
        
        if len(spikes_B) > 0:
            ax2.scatter(spikes_B, gids_B, s=12, c='red', marker='|', alpha=0.7)
        ax2.set_title(f'PYR_B (Incorrecta) - W={weight_B:.3f} nS', 
                     fontsize=12, fontweight='bold', color='red')
        ax2.set_ylabel('GID', fontsize=10)
        ax2.set_xlim([0, duration])
        ax2.grid(True, alpha=0.2, axis='x')
        
        if len(spikes_OLM) > 0:
            ax3.scatter(spikes_OLM, gids_OLM, s=12, c='blue', marker='|', alpha=0.7)
        ax3.set_title(f'OLM (Inhibición) - {len(spikes_OLM)} spikes', 
                     fontsize=12, fontweight='bold', color='blue')
        ax3.set_xlabel('Tiempo (ms)', fontsize=11)
        ax3.set_ylabel('GID', fontsize=10)
        ax3.set_xlim([0, duration])
        ax3.grid(True, alpha=0.2, axis='x')
        
        plt.tight_layout()
        plt.savefig(f'Raster_Split_Trial_{trial_num}.png', dpi=130)
        plt.close()

else:
    if USE_MPI:
        print(f"MPI: Proceso {rank} de {nhosts} (ESCLAVO)")

cfg.analysis = {}

# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================
for trial in range(N_TRIALS):
    if rank == 0:
        print(f"\n--- TRIAL {trial + 1}/{N_TRIALS} ---")
        history_weights_A.append(current_weight_A)
        history_weights_B.append(current_weight_B)
        netParams.sc_wei_A = current_weight_A
        netParams.sc_wei_B = current_weight_B
        print(f"   > Pesos: A={current_weight_A:.4f}, B={current_weight_B:.4f}")
        
        if USE_MPI:
            weight_data = [current_weight_A, current_weight_B]
            comm.bcast(weight_data, root=0)
    else:
        if USE_MPI:
            weight_data = comm.bcast(None, root=0)
            current_weight_A, current_weight_B = weight_data
            netParams.sc_wei_A = current_weight_A
            netParams.sc_wei_B = current_weight_B
    
    if USE_MPI:
        cfg.useMPI = True
        cfg.comm = comm
        cfg.rank = rank
        cfg.nhosts = nhosts
    else:
        cfg.useMPI = False
    
    sim.initialize()
    sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg)
    
    if rank == 0:
        spikes_A, gids_A_spikes, pop_gids_A = extract_spikes_by_population(sim.allSimData, 'PYR_A')
        spikes_B, gids_B_spikes, pop_gids_B = extract_spikes_by_population(sim.allSimData, 'PYR_B')
        spikes_OLM, gids_OLM_spikes, pop_gids_OLM = extract_spikes_by_population(sim.allSimData, 'OLM')
        
        history_spikes_A.append(len(spikes_A))
        history_spikes_B.append(len(spikes_B))
        history_spikes_OLM.append(len(spikes_OLM))
        
        print(f"   > Espigas: A={len(spikes_A)}, B={len(spikes_B)}, OLM={len(spikes_OLM)}")
        
        all_trial_data.append({
            'trial': trial + 1,
            'spikes_A': spikes_A.copy(),
            'gids_A': gids_A_spikes.copy(),
            'spikes_B': spikes_B.copy(),
            'gids_B': gids_B_spikes.copy(),
            'spikes_OLM': spikes_OLM.copy(),
            'gids_OLM': gids_OLM_spikes.copy(),
            'weight_A': current_weight_A,
            'weight_B': current_weight_B
        })
        
        plot_raster_split_trial(trial + 1, spikes_A, gids_A_spikes, spikes_B, gids_B_spikes,
                               spikes_OLM, gids_OLM_spikes, current_weight_A, current_weight_B, cfg.duration)
        print(f"   > Guardado: Raster_Split_Trial_{trial+1}.png")
        
        dt_decision = 10.0
        time_bins_A, rate_A = compute_firing_rate_time_series(spikes_A, cfg.popA_size, cfg.duration, dt_decision)
        time_bins_B, rate_B = compute_firing_rate_time_series(spikes_B, cfg.popB_size, cfg.duration, dt_decision)
        trace_A_trial, trace_B_trial, winner, rt = simulate_ddm_race(rate_A, rate_B, time_bins_A)
        
        full_trace_A.extend(trace_A_trial)
        full_trace_B.extend(trace_B_trial)
        
        remaining = int((cfg.duration - rt) / dt_decision)
        if remaining > 0 and len(trace_A_trial) > 0:
            full_trace_A.extend([trace_A_trial[-1]] * remaining)
            full_trace_B.extend([trace_B_trial[-1]] * remaining)
        
        experiment_decision_points.append(len(full_trace_A))
        
        if winner == 'NONE':
            winner = 'A' if len(spikes_A) > len(spikes_B) else 'B'
        
        is_correct = (winner == TARGET_SIDE)
        history_choice.append(1 if is_correct else 0)
        print(f"   > Resultado: {winner} ({'ACIERTO' if is_correct else 'FALLO'}) | RT={rt:.1f} ms")
        
        if is_correct:
            current_weight_A += (current_weight_A * LTP_RATE)
            current_weight_B -= (current_weight_B * LTD_RATE)
        else:
            current_weight_B -= (current_weight_B * LTD_RATE)
        
        current_weight_A = np.clip(current_weight_A, 0.01, 10.0)
        current_weight_B = np.clip(current_weight_B, 0.01, 10.0)
    
    if USE_MPI:
        comm.Barrier()

# =============================================================================
# GRÁFICOS FINALES
# =============================================================================
if rank == 0:
    print("\n" + "=" * 80)
    print(">>> GENERANDO GRÁFICOS FINALES...")
    print("=" * 80)
    
    # 1. LEARNING_RESULT
    fig_learn, axes_learn = plt.subplots(3, 1, figsize=(12, 10))
    trials_x = range(1, N_TRIALS + 1)
    
    axes_learn[0].plot(trials_x, history_weights_A, 'g-o', label='Peso A', lw=2.5, ms=8)
    axes_learn[0].plot(trials_x, history_weights_B, 'r-x', label='Peso B', lw=2.5, ms=8)
    axes_learn[0].set_title('Evolución de Pesos', fontsize=14, fontweight='bold')
    axes_learn[0].set_ylabel('Peso (nS)', fontsize=12)
    axes_learn[0].legend(fontsize=11)
    axes_learn[0].grid(True, alpha=0.3)
    
    axes_learn[1].plot(trials_x, history_choice, 'b-s', lw=2.5, ms=10)
    axes_learn[1].fill_between(trials_x, history_choice, alpha=0.3)
    axes_learn[1].set_title('Historial de Aciertos', fontsize=14, fontweight='bold')
    axes_learn[1].set_ylabel('Resultado', fontsize=12)
    axes_learn[1].set_yticks([0, 1])
    axes_learn[1].set_yticklabels(['Fallo', 'Acierto'])
    axes_learn[1].grid(True, alpha=0.3)
    
    axes_learn[2].plot(trials_x, history_spikes_A, 'g-o', label='PYR_A', lw=2, ms=7)
    axes_learn[2].plot(trials_x, history_spikes_B, 'r-x', label='PYR_B', lw=2, ms=7)
    axes_learn[2].plot(trials_x, history_spikes_OLM, 'b-^', label='OLM', lw=2, ms=7)
    axes_learn[2].set_title('Actividad por Trial', fontsize=14, fontweight='bold')
    axes_learn[2].set_xlabel('Trial', fontsize=12)
    axes_learn[2].set_ylabel('Número de Espigas', fontsize=12)
    axes_learn[2].legend(fontsize=11)
    axes_learn[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('Learning_Result.png', dpi=150)
    plt.close()
    print("   > Guardado: Learning_Result.png")
    
    # 2. DDM_TRAJECTORY_FULL
    fig_ddm, ax_ddm = plt.subplots(figsize=(16, 7))
    t_vec = np.arange(0, len(full_trace_A) * 10.0, 10.0)
    
    ax_ddm.plot(t_vec, full_trace_A, 'g', lw=2.5, label='Acumulación A', alpha=0.8)
    ax_ddm.plot(t_vec, full_trace_B, 'r', lw=2.5, label='Acumulación B', alpha=0.8)
    
    for idx in experiment_decision_points[:-1]:
        ax_ddm.axvline(x=idx*10.0, color='gray', ls=':', lw=1.5, alpha=0.6)
    
    ax_ddm.axhline(y=25.0, color='black', ls='--', lw=2, label='Umbral')
    ax_ddm.set_title(f'Trayectorias DDM ({N_TRIALS} Trials)', fontsize=15, fontweight='bold')
    ax_ddm.set_xlabel('Tiempo Total (ms)', fontsize=13)
    ax_ddm.set_ylabel('Acumulación', fontsize=13)
    ax_ddm.legend(fontsize=12)
    ax_ddm.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('DDM_Trajectory_Full.png', dpi=150)
    plt.close()
    print("   > Guardado: DDM_Trajectory_Full.png")
    
    # 3. MODEL_OUTPUT_RASTER
    fig_rast, ax_rast = plt.subplots(figsize=(16, 10))
    time_offset = 0
    
    for trial_data in all_trial_data:
        spikes_A_offset = trial_data['spikes_A'] + time_offset
        spikes_B_offset = trial_data['spikes_B'] + time_offset
        spikes_OLM_offset = trial_data['spikes_OLM'] + time_offset
        
        if len(spikes_A_offset) > 0:
            ax_rast.scatter(spikes_A_offset, trial_data['gids_A'] + 40, s=8, c='green', marker='|', alpha=0.6)
        if len(spikes_B_offset) > 0:
            ax_rast.scatter(spikes_B_offset, trial_data['gids_B'], s=8, c='red', marker='|', alpha=0.6)
        if len(spikes_OLM_offset) > 0:
            ax_rast.scatter(spikes_OLM_offset, trial_data['gids_OLM'] + 20, s=8, c='blue', marker='|', alpha=0.6)
        
        if trial_data['trial'] < N_TRIALS:
            ax_rast.axvline(x=time_offset + cfg.duration, color='black', ls='--', lw=1, alpha=0.4)
        
        time_offset += cfg.duration
    
    ax_rast.set_title(f'Raster Completo: {N_TRIALS} Trials', fontsize=15, fontweight='bold')
    ax_rast.set_xlabel('Tiempo (ms)', fontsize=13)
    ax_rast.set_ylabel('GID', fontsize=13)
    ax_rast.grid(True, alpha=0.2, axis='x')
    
    legend_elements = [
        Line2D([0], [0], marker='|', color='w', markerfacecolor='g', ms=10, label='PYR_A'),
        Line2D([0], [0], marker='|', color='w', markerfacecolor='b', ms=10, label='OLM'),
        Line2D([0], [0], marker='|', color='w', markerfacecolor='r', ms=10, label='PYR_B')
    ]
    ax_rast.legend(handles=legend_elements, fontsize=12)
    
    plt.tight_layout()
    plt.savefig('Model_Output_Raster.png', dpi=130)
    plt.close()
    print("   > Guardado: Model_Output_Raster.png")
    
    # 4. MODEL_OUTPUT_TRACE
    if 'V_soma' in sim.allSimData and len(sim.allSimData['V_soma']) > 0:
        time_vec = np.array(sim.allSimData['t'])
        trace_A = sim.allSimData['V_soma'].get('cell_0', [])
        trace_B = sim.allSimData['V_soma'].get(f'cell_{cfg.popA_size}', [])
        trace_OLM = sim.allSimData['V_soma'].get(f'cell_{cfg.popA_size + cfg.popB_size}', [])
        
        if len(trace_A) > 0 and len(trace_B) > 0:
            fig_trace, (ax_pyr, ax_olm) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
            
            ax_pyr.plot(time_vec, trace_A, 'g', label='PYR_A', alpha=0.8, lw=1.2)
            ax_pyr.plot(time_vec, trace_B, 'r', label='PYR_B', alpha=0.8, lw=1.2)
            ax_pyr.set_title('Voltaje: PYR_A y PYR_B', fontsize=14, fontweight='bold')
            ax_pyr.set_ylabel('Voltaje (mV)', fontsize=12)
            ax_pyr.legend(fontsize=11)
            ax_pyr.grid(True, alpha=0.3)
            
            if len(trace_OLM) > 0:
                ax_olm.plot(time_vec, trace_OLM, 'b', alpha=0.8, lw=1.2)
                ax_olm.set_title('Voltaje: OLM', fontsize=14, fontweight='bold', color='blue')
                ax_olm.set_xlabel('Tiempo (ms)', fontsize=12)
                ax_olm.set_ylabel('Voltaje (mV)', fontsize=12)
                ax_olm.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('Model_Output_Trace.png', dpi=150)
            plt.close()
            print("   > Guardado: Model_Output_Trace.png")
    
    # Estadísticas
    accuracy = np.mean(history_choice) * 100
    print(f"\n   ESTADÍSTICAS FINALES:")
    print(f"   - Precisión: {accuracy:.1f}%")
    print(f"   - Peso Final A: {current_weight_A:.4f} nS")
    print(f"   - Peso Final B: {current_weight_B:.4f} nS")
    print(f"   - Ratio A/B: {current_weight_A/current_weight_B:.2f}")

    print("\n" + "=" * 80)
    print(">>> PROCESO COMPLETADO")
    print("=" * 80)

if USE_MPI:
    if rank == 0:
        print("\n>>> Finalizando MPI...")
    comm.Barrier()
    MPI.Finalize()