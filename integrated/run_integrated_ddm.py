#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated DDM Simulation: CA1 Model + Decision Making
CRITICAL FIXES:
1. Variable seeds per trial (creates firing variability)
2. No Unicode characters (Windows-compatible)
3. Reduced synaptic depression (enables sustained OLM activity)
"""

import sys
import os

# =============================================================================
# MPI CONFIGURATION
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
# MATPLOTLIB BACKEND
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
        print(f"ERROR: Cannot import configurations: {e}")
    sys.exit(1)

# =============================================================================
# PARAMETERS (M: Learning framework)
# =============================================================================
N_TRIALS = 10
TARGET_SIDE = 'A'
LTP_RATE = 0.032            # M
LTD_RATE = 0.023            # M

current_weight_A = cfg.sc_wei_left
current_weight_B = cfg.sc_wei_right

# =============================================================================
# MASTER PROCESS INITIALIZATION
# =============================================================================
if rank == 0:
    print("\n" + "=" * 80)
    print("CA1 INTEGRATED SIMULATION - Robust OLM Activity")
    print("=" * 80)
    print(f"MPI: {nhosts} processes")
    print(f"Config: {cfg.popA_size}+{cfg.popB_size}+{cfg.olm_size} cells | {cfg.duration:.0f}ms | dt={cfg.dt}ms")
    print(f"Learning: LTP={LTP_RATE}, LTD={LTD_RATE}")
    print(f"CRITICAL FIX: Dep={cfg.olmdepfact} (Paper: 38, reduced for sustained OLM)")
    print("=" * 80 + "\n")
    
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import signal
    from scipy.signal import butter, filtfilt
    
    # Histories
    history_weights_A = []
    history_weights_B = []
    history_choice = []
    history_spikes_A = []
    history_spikes_B = []
    history_spikes_OLM = []
    
    # DDM traces
    full_trace_A = []
    full_trace_B = []
    experiment_decision_points = []
    
    # Trial data
    all_trial_data = []
    all_lfp_trials = []
    
    print("Trial | Weights (nS) |     Spikes      | Decision | Accuracy")
    print("      |   A  :   B   |  A  :  B : OLM  |  (RT ms) |    (%)  ")
    print("-" * 80)
    
    # Helper functions
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
    
    def plot_raster_trial(trial_num, spikes_A, gids_A, spikes_B, gids_B,
                         spikes_OLM, gids_OLM, weight_A, weight_B, duration):
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        
        # Offsets: PYR_A top, OLM middle, PYR_B bottom
        if len(gids_OLM) > 0 and len(gids_A) > 0 and len(gids_B) > 0:
            offset_A = max(gids_OLM) - min(gids_A) + 5
            offset_B = min(gids_OLM) - max(gids_B) - 5
        else:
            offset_A = 0
            offset_B = 0
        
        if len(spikes_A) > 0:
            ax.scatter(spikes_A, gids_A + offset_A, s=10, c='green', 
                      marker='|', alpha=0.7, label='PYR_A')
        
        if len(spikes_OLM) > 0:
            ax.scatter(spikes_OLM, gids_OLM, s=10, c='blue', 
                      marker='|', alpha=0.7, label='OLM')
        
        if len(spikes_B) > 0:
            ax.scatter(spikes_B, gids_B + offset_B, s=10, c='red', 
                      marker='|', alpha=0.7, label='PYR_B')
        
        if len(gids_OLM) > 0:
            ax.axhline(y=max(gids_OLM) + 2, color='gray', ls='--', lw=0.5, alpha=0.5)
            ax.axhline(y=min(gids_OLM) - 2, color='gray', ls='--', lw=0.5, alpha=0.5)
        
        ax.set_title(f'Trial {trial_num} | W_A={weight_A:.2f}, W_B={weight_B:.2f} nS',
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('Time (ms)', fontsize=11)
        ax.set_ylabel('Cells', fontsize=11)
        ax.set_xlim([0, duration])
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(f'Raster_Trial_{trial_num}.png', dpi=120)
        plt.close()

else:
    pass  # Silent slaves

# Disable NetPyNE verbose
cfg.analysis = {}
cfg.verbose = False

# =============================================================================
# MAIN SIMULATION LOOP
# =============================================================================
for trial in range(N_TRIALS):
    
    # UPDATE SEED FOR EACH TRIAL (creates variability in firing patterns)
    trial_seed = cfg.seedval + (trial * 1000)
    cfg.seeds = {
        'conn': trial_seed + 7515,
        'stim': trial_seed + 84331,
        'loc': trial_seed + 943
    }
    
    # Synchronize weights
    if rank == 0:
        history_weights_A.append(current_weight_A)
        history_weights_B.append(current_weight_B)
        
        netParams.sc_wei_A = current_weight_A
        netParams.sc_wei_B = current_weight_B
        
        if USE_MPI:
            weight_data = [current_weight_A, current_weight_B, trial_seed]
            comm.bcast(weight_data, root=0)
    else:
        if USE_MPI:
            weight_data = comm.bcast(None, root=0)
            current_weight_A, current_weight_B, trial_seed = weight_data
            netParams.sc_wei_A = current_weight_A
            netParams.sc_wei_B = current_weight_B
            # Update seeds on slaves too
            cfg.seeds = {
                'conn': trial_seed + 7515,
                'stim': trial_seed + 84331,
                'loc': trial_seed + 943
            }
    
    # Run simulation
    if USE_MPI:
        cfg.useMPI = True
        cfg.comm = comm
        cfg.rank = rank
        cfg.nhosts = nhosts
    else:
        cfg.useMPI = False
    
    sim.initialize()
    sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg)
    
    # Post-processing (Master only)
    if rank == 0:
        
        # Extract spikes
        spikes_A, gids_A_spikes, pop_gids_A = extract_spikes_by_population(sim.allSimData, 'PYR_A')
        spikes_B, gids_B_spikes, pop_gids_B = extract_spikes_by_population(sim.allSimData, 'PYR_B')
        spikes_OLM, gids_OLM_spikes, pop_gids_OLM = extract_spikes_by_population(sim.allSimData, 'OLM')
        
        # Store counts
        history_spikes_A.append(len(spikes_A))
        history_spikes_B.append(len(spikes_B))
        history_spikes_OLM.append(len(spikes_OLM))
        
        # Store trial data
        all_trial_data.append({
            'trial': trial + 1,
            'spikes_A': spikes_A.copy(),
            'gids_A': gids_A_spikes.copy(),
            'spikes_B': spikes_B.copy(),
            'gids_B': gids_B_spikes.copy(),
            'spikes_OLM': spikes_OLM.copy(),
            'gids_OLM': gids_OLM_spikes.copy(),
            'weight_A': current_weight_A,
            'weight_B': current_weight_B,
            'seed': trial_seed
        })
        
        # Generate raster
        plot_raster_trial(trial + 1, spikes_A, gids_A_spikes, spikes_B, gids_B_spikes,
                         spikes_OLM, gids_OLM_spikes, current_weight_A, current_weight_B, cfg.duration)
        
        # DDM computation
        dt_decision = 10.0
        time_bins_A, rate_A = compute_firing_rate_time_series(spikes_A, cfg.popA_size, cfg.duration, dt_decision)
        time_bins_B, rate_B = compute_firing_rate_time_series(spikes_B, cfg.popB_size, cfg.duration, dt_decision)
        
        trace_A_trial, trace_B_trial, winner, rt = simulate_ddm_race(rate_A, rate_B, time_bins_A)
        
        # Store DDM traces
        full_trace_A.extend(trace_A_trial)
        full_trace_B.extend(trace_B_trial)
        
        remaining = int((cfg.duration - rt) / dt_decision)
        if remaining > 0 and len(trace_A_trial) > 0:
            full_trace_A.extend([trace_A_trial[-1]] * remaining)
            full_trace_B.extend([trace_B_trial[-1]] * remaining)
        
        experiment_decision_points.append(len(full_trace_A))
        
        # Learning
        if winner == 'NONE':
            winner = 'A' if len(spikes_A) > len(spikes_B) else 'B'
        
        is_correct = (winner == TARGET_SIDE)
        history_choice.append(1 if is_correct else 0)
        
        # Output (Windows-compatible, no Unicode)
        accuracy_so_far = (sum(history_choice) / len(history_choice)) * 100
        check = "OK" if is_correct else "ER"
        
        print(f"  {trial+1:2d}  | {current_weight_A:4.2f} : {current_weight_B:4.2f} | {len(spikes_A):3d} : {len(spikes_B):3d} : {len(spikes_OLM):3d} | {winner} {check} ({rt:4.0f}) | {accuracy_so_far:6.1f}")
        
        # Apply learning (M framework)
        if is_correct:
            current_weight_A += (current_weight_A * LTP_RATE)
            current_weight_B -= (current_weight_B * LTD_RATE)
        else:
            current_weight_B -= (current_weight_B * LTD_RATE)
        
        current_weight_A = np.clip(current_weight_A, 0.01, 10.0)
        current_weight_B = np.clip(current_weight_B, 0.01, 10.0)
        
        # Store LFP
        if 'V_soma' in sim.allSimData and len(sim.allSimData['V_soma']) > 0:
            all_traces = [np.array(t) for t in sim.allSimData['V_soma'].values()]
            if len(all_traces) > 0:
                lfp_trial = np.mean(all_traces, axis=0)
                lfp_trial = lfp_trial - np.mean(lfp_trial)
                all_lfp_trials.append(lfp_trial)
    
    # Synchronize
    if USE_MPI:
        comm.Barrier()

# =============================================================================
# FINAL PLOTS (Master only)
# =============================================================================
if rank == 0:
    print("\n" + "=" * 80)
    print("GENERATING PLOTS...")
    print("=" * 80)
    
    # Plot 1: Learning_Result
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    trials_x = range(1, N_TRIALS + 1)
    
    axes[0].plot(trials_x, history_weights_A, 'g-o', label='Weight A', lw=2.5, ms=8)
    axes[0].plot(trials_x, history_weights_B, 'r-x', label='Weight B', lw=2.5, ms=8)
    axes[0].set_title('Weight Evolution', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Weight (nS)', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(trials_x, history_choice, 'b-s', lw=2.5, ms=10)
    axes[1].fill_between(trials_x, history_choice, alpha=0.3)
    axes[1].set_title('Choice History', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Outcome', fontsize=12)
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(['Error', 'Correct'])
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(trials_x, history_spikes_A, 'g-o', label='PYR_A', lw=2, ms=7)
    axes[2].plot(trials_x, history_spikes_B, 'r-x', label='PYR_B', lw=2, ms=7)
    axes[2].plot(trials_x, history_spikes_OLM, 'b-^', label='OLM', lw=2, ms=7)
    axes[2].set_title('Neural Activity', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Trial', fontsize=12)
    axes[2].set_ylabel('Spikes', fontsize=12)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('Learning_Result.png', dpi=150)
    plt.close()
    print("[OK] Learning_Result.png")
    
    # Plot 2: DDM_Trajectory_Full
    fig, ax = plt.subplots(figsize=(16, 7))
    t_vec = np.arange(0, len(full_trace_A) * 10.0, 10.0)
    
    ax.plot(t_vec, full_trace_A, 'g', lw=2.5, label='Accumulation A', alpha=0.8)
    ax.plot(t_vec, full_trace_B, 'r', lw=2.5, label='Accumulation B', alpha=0.8)
    
    for idx in experiment_decision_points[:-1]:
        ax.axvline(x=idx*10.0, color='gray', ls=':', lw=1.5, alpha=0.6)
    
    ax.axhline(y=25.0, color='black', ls='--', lw=2, label='Threshold')
    ax.set_title(f'DDM Trajectories ({N_TRIALS} Trials)', fontsize=15, fontweight='bold')
    ax.set_xlabel('Time (ms)', fontsize=13)
    ax.set_ylabel('Accumulation', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('DDM_Trajectory_Full.png', dpi=150)
    plt.close()
    print("[OK] DDM_Trajectory_Full.png")
    
    # Plot 3: Model_Output_Trace
    if 'V_soma' in sim.allSimData and len(sim.allSimData['V_soma']) > 0:
        time_vec = np.array(sim.allSimData['t'])
        trace_A = sim.allSimData['V_soma'].get('cell_0', [])
        trace_B = sim.allSimData['V_soma'].get(f'cell_{cfg.popA_size}', [])
        trace_OLM = sim.allSimData['V_soma'].get(f'cell_{cfg.popA_size + cfg.popB_size}', [])
        
        if len(trace_A) > 0 and len(trace_B) > 0 and len(trace_OLM) > 0:
            fig, ax = plt.subplots(figsize=(14, 6))
            
            ax.plot(time_vec, trace_A, 'g', label='PYR_A', alpha=0.7, lw=1.0)
            ax.plot(time_vec, trace_B, 'r', label='PYR_B', alpha=0.7, lw=1.0)
            ax.plot(time_vec, trace_OLM, 'b', label='OLM', alpha=0.7, lw=1.0)
            
            ax.set_title('Voltage Traces (Last Trial)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Time (ms)', fontsize=12)
            ax.set_ylabel('Voltage (mV)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('Model_Output_Trace.png', dpi=150)
            plt.close()
            print("[OK] Model_Output_Trace.png")
        else:
            print("[WARN] Model_Output_Trace.png - No valid traces")
    else:
        print("[WARN] Model_Output_Trace.png - No voltage data")
    
    # Plot 4: Spectral_Analysis_PAC
    if len(all_lfp_trials) > 0:
        try:
            lfp = all_lfp_trials[-1]
            dt = cfg.dt
            fs = 1000.0 / dt
            
            if len(lfp) > 100:
                fig = plt.figure(figsize=(14, 10))
                gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1.5, 1], 
                                     width_ratios=[1, 1], hspace=0.4, wspace=0.3)
                
                # Panel 1: LFP
                ax0 = fig.add_subplot(gs[0, :])
                t_lfp = np.linspace(0, cfg.duration, len(lfp))
                ax0.plot(t_lfp, lfp, 'k', lw=0.8)
                ax0.set_title('LFP (Population Average)', fontsize=13, fontweight='bold')
                ax0.set_xlabel('Time (ms)')
                ax0.set_ylabel('Amplitude (mV)')
                ax0.grid(True, alpha=0.2)
                
                # Panel 2: PSD
                ax1 = fig.add_subplot(gs[1, :])
                f, Pxx = signal.welch(lfp, fs, nperseg=min(len(lfp), 1024))
                ax1.semilogy(f, Pxx, 'b', lw=1.5)
                ax1.set_xlim([0, 100])
                ax1.axvspan(4, 12, color='green', alpha=0.2, label='Theta')
                ax1.axvspan(30, 80, color='orange', alpha=0.2, label='Gamma')
                ax1.legend()
                ax1.set_title('Power Spectral Density', fontsize=13, fontweight='bold')
                ax1.set_xlabel('Frequency (Hz)')
                ax1.set_ylabel('Power')
                ax1.grid(True, alpha=0.2)
                
                # Panel 3: Spectrogram
                ax2 = fig.add_subplot(gs[2, :])
                f_s, t_s, Sxx = signal.spectrogram(lfp, fs, nperseg=min(128, len(lfp)//4), 
                                                   noverlap=min(100, len(lfp)//8))
                c = ax2.pcolormesh(t_s * 1000, f_s, 10 * np.log10(Sxx + 1e-12), 
                                  shading='gouraud', cmap='jet', vmin=-40, vmax=20)
                ax2.set_ylim([0, 100])
                ax2.set_ylabel('Frequency (Hz)')
                ax2.set_xlabel('Time (ms)')
                ax2.set_title('Spectrogram', fontsize=13, fontweight='bold')
                fig.colorbar(c, ax=ax2, label='Power (dB)')
                
                # Panel 4: Band power
                ax3 = fig.add_subplot(gs[3, 0])
                theta_power = []
                gamma_power = []
                
                for lfp_trial in all_lfp_trials:
                    if len(lfp_trial) > 100:
                        f_trial, Pxx_trial = signal.welch(lfp_trial, fs, nperseg=min(len(lfp_trial), 512))
                        
                        theta_idx = np.where((f_trial >= 4) & (f_trial <= 12))[0]
                        theta_power.append(np.mean(Pxx_trial[theta_idx]) if len(theta_idx) > 0 else 0)
                        
                        gamma_idx = np.where((f_trial >= 30) & (f_trial <= 80))[0]
                        gamma_power.append(np.mean(Pxx_trial[gamma_idx]) if len(gamma_idx) > 0 else 0)
                
                if len(theta_power) > 0:
                    ax3.plot(range(1, len(theta_power) + 1), theta_power, 'g-o', label='Theta', lw=2, ms=6)
                    ax3.plot(range(1, len(gamma_power) + 1), gamma_power, 'orange', marker='s', label='Gamma', lw=2, ms=6)
                    ax3.set_title('Band Power Evolution', fontsize=12, fontweight='bold')
                    ax3.set_xlabel('Trial')
                    ax3.set_ylabel('Mean Power')
                    ax3.legend()
                    ax3.grid(True, alpha=0.2)
                
                # Panel 5: PAC
                ax4 = fig.add_subplot(gs[3, 1])
                
                def bandpass_filter(data, lowcut, highcut, fs, order=4):
                    nyq = 0.5 * fs
                    low = lowcut / nyq
                    high = highcut / nyq
                    b, a = butter(order, [low, high], btype='band')
                    return filtfilt(b, a, data)
                
                try:
                    theta_filtered = bandpass_filter(lfp, 4, 12, fs)
                    gamma_filtered = bandpass_filter(lfp, 30, 80, fs)
                    
                    theta_analytic = signal.hilbert(theta_filtered)
                    gamma_analytic = signal.hilbert(gamma_filtered)
                    
                    theta_phase = np.angle(theta_analytic)
                    gamma_amplitude = np.abs(gamma_analytic)
                    
                    phase_bins = np.linspace(-np.pi, np.pi, 18)
                    mean_amp_per_bin = []
                    
                    for i in range(len(phase_bins) - 1):
                        bin_mask = (theta_phase >= phase_bins[i]) & (theta_phase < phase_bins[i + 1])
                        if np.sum(bin_mask) > 0:
                            mean_amp_per_bin.append(np.mean(gamma_amplitude[bin_mask]))
                        else:
                            mean_amp_per_bin.append(0)
                    
                    phase_bin_centers = (phase_bins[:-1] + phase_bins[1:]) / 2
                    ax4.plot(phase_bin_centers * 180 / np.pi, mean_amp_per_bin, 'purple', lw=2, marker='o')
                    ax4.fill_between(phase_bin_centers * 180 / np.pi, mean_amp_per_bin, alpha=0.3, color='purple')
                    ax4.set_title('Phase-Amplitude Coupling', fontsize=12, fontweight='bold')
                    ax4.set_xlabel('Theta Phase (deg)')
                    ax4.set_ylabel('Gamma Amplitude')
                    ax4.set_xlim([-180, 180])
                    ax4.set_xticks([-180, -90, 0, 90, 180])
                    ax4.grid(True, alpha=0.2)
                except:
                    pass
                
                plt.savefig('Spectral_Analysis_PAC.png', dpi=150)
                plt.close()
                print("[OK] Spectral_Analysis_PAC.png")
            else:
                print("[WARN] Spectral_Analysis_PAC.png - Insufficient data")
        except Exception as e:
            print(f"[WARN] Spectral_Analysis_PAC.png - Error: {e}")
    else:
        print("[WARN] Spectral_Analysis_PAC.png - No LFP data")
    
    # Statistics
    accuracy = np.mean(history_choice) * 100
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    print(f"Accuracy:   {accuracy:5.1f}%")
    print(f"Weight A:   {current_weight_A:4.2f} nS (final) | Ratio A/B: {current_weight_A/current_weight_B:4.2f}")
    print(f"Weight B:   {current_weight_B:4.2f} nS (final)")
    print(f"Avg spikes: A={np.mean(history_spikes_A):5.1f}, B={np.mean(history_spikes_B):5.1f}, OLM={np.mean(history_spikes_OLM):4.1f}")
    print("=" * 80 + "\n")

# MPI Finalization
if USE_MPI:
    comm.Barrier()
    MPI.Finalize()