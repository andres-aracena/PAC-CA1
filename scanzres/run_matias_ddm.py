import matplotlib.pyplot as plt
import numpy as np
from netpyne import sim
from scipy import signal
from cfg_matias import cfg
from netParams_matias import netParams
import os

# =============================================================================
# 1. CONFIGURACIÓN Y PARÁMETROS
# =============================================================================
print(">>> INICIALIZANDO CONFIGURACIÓN...")

# Parámetros del Experimento
N_TRIALS = 10            
TARGET_SIDE = 'A'       
LTP_RATE = 0.032        
LTD_RATE = 0.023        

# Ajustes de Simulación (Overrides)
cfg.dt = 0.1
cfg.verbose = False
print(f"   > Paso de tiempo (dt): {cfg.dt} ms")

# --- ACTIVACIÓN DE GRABACIÓN DE TRAZAS (CRÍTICO) ---
# Necesario para Trazas_Separadas, Trazas_Juntas, Analisis_Espectral y model_output_traces
cfg.recordTraces = {'V_soma': {'sec':'soma_0', 'loc':0.5, 'var':'v'}}

# Configuración para gráficos automáticos de NetPyNE (model_output_...)
cfg.analysis['plotTraces'] = {
    'include': [0, 40],       # GID 0 (PYR_A) y GID 40 (PYR_B)
    'saveFig': True, 
    'showFig': False,
    'oneFigPer': 'trace',     # Un archivo por célula (model_output_traces__gid_0.png)
    'overlay': False
}
cfg.analysis['plotRaster'] = {
    'include': ['PYR_A', 'PYR_B'], 
    'saveFig': True,          # Genera model_output_raster.png
    'showFig': False
}

# Inicialización de Variables de Estado
current_weight_A = cfg.sc_wei_left  
current_weight_B = cfg.sc_wei_right

# Historiales
history_weights_A = []
history_weights_B = []
history_choice = []     

# Memoria para trayectorias DDM (Racing Model)
full_trace_A = []
full_trace_B = []
experiment_decision_points = [] 

# =============================================================================
# 2. BUCLE DE SIMULACIÓN (APRENDIZAJE)
# =============================================================================
print(f"\n>>> INICIANDO EXPERIMENTO: {N_TRIALS} Trials")

for trial in range(N_TRIALS):
    print(f"\n--- TRIAL {trial + 1}/{N_TRIALS} ---")
    
    # A. Actualizar Pesos
    netParams.stimTargetParams['Input->PYR_A']['weight'] = current_weight_A
    netParams.stimTargetParams['Input->PYR_B']['weight'] = current_weight_B
    history_weights_A.append(current_weight_A)
    history_weights_B.append(current_weight_B)
    
    # B. Ejecutar Simulación
    sim.initialize()
    sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg)
    
    # C. Extraer Espigas
    all_spikes_time = np.array(sim.allSimData['spkt'])
    all_spikes_gid = np.array(sim.allSimData['spkid'])
    gids_A = np.array(sim.net.pops['PYR_A'].cellGids)
    gids_B = np.array(sim.net.pops['PYR_B'].cellGids)
    spikes_A = all_spikes_time[np.isin(all_spikes_gid, gids_A)]
    spikes_B = all_spikes_time[np.isin(all_spikes_gid, gids_B)]
    
    # D. Gráfico: Raster_Split (Por Trial)
    print(f"   > Generando Raster_Split del Trial {trial+1}...")
    spikes_gids_A = all_spikes_gid[np.isin(all_spikes_gid, gids_A)]
    spikes_gids_B = all_spikes_gid[np.isin(all_spikes_gid, gids_B)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax1.scatter(spikes_A, spikes_gids_A, s=10, c='green', marker='|')
    ax1.set_title(f'Trial {trial+1}: PYR_A (Correcta) - W={current_weight_A:.4f}')
    ax1.set_ylabel('GID')
    ax2.scatter(spikes_B, spikes_gids_B, s=10, c='red', marker='|')
    ax2.set_title(f'Trial {trial+1}: PYR_B (Incorrecta) - W={current_weight_B:.4f}')
    ax2.set_xlabel('Tiempo (ms)')
    ax2.set_ylabel('GID')
    plt.tight_layout()
    plt.savefig(f'Raster_Split_Trial_{trial+1}.png')
    plt.close()

    # E. Cálculo DDM / Racing Model
    dt_decision = 10.0
    time_bins = np.arange(0, cfg.duration, dt_decision)
    
    # 1. Calcular Tasas Instantáneas
    rate_A, rate_B = [], []
    for t in time_bins:
        t_end = t + dt_decision
        hz_A = (np.sum((spikes_A >= t) & (spikes_A < t_end)) / cfg.popA_size) * (1000/dt_decision)
        hz_B = (np.sum((spikes_B >= t) & (spikes_B < t_end)) / cfg.popB_size) * (1000/dt_decision)
        rate_A.append(float(hz_A))
        rate_B.append(float(hz_B))

    # 2. Simular Acumulación (Carrera)
    decision_threshold = 30.0 
    x_A, x_B = 0.0, 0.0
    alpha = 0.10
    
    trace_A_trial, trace_B_trial = [0.0], [0.0]
    winner = 'NONE'
    rt = cfg.duration
    
    for i, t in enumerate(time_bins):
        # Ecuación de acumulación con ruido y leak
        x_A += (alpha * rate_A[i]) + np.random.normal(0, 0.1) - (0.01 * x_A)
        x_B += (alpha * rate_B[i]) + np.random.normal(0, 0.1) - (0.01 * x_B)
        
        # Limpieza de datos (float y no negativo)
        x_A = float(max(0, x_A))
        x_B = float(max(0, x_B))
        
        trace_A_trial.append(x_A)
        trace_B_trial.append(x_B)
        
        if x_A >= decision_threshold: winner = 'A'; rt = t; break
        elif x_B >= decision_threshold: winner = 'B'; rt = t; break
            
    # F. Guardar Trayectorias
    full_trace_A.extend(trace_A_trial)
    full_trace_B.extend(trace_B_trial)
    
    # Relleno visual
    remaining = int((cfg.duration - rt) / dt_decision)
    if remaining > 0:
        full_trace_A.extend([float(x_A)] * remaining)
        full_trace_B.extend([float(x_B)] * remaining)
    
    experiment_decision_points.append(len(full_trace_A))
    
    # G. Aprendizaje
    # Fallback si nadie cruza el umbral
    if winner == 'NONE':
        winner = 'A' if len(spikes_A) > len(spikes_B) else 'B'
        
    is_correct = (winner == TARGET_SIDE)
    history_choice.append(1 if is_correct else 0)
    print(f"   > Resultado: {winner} ({'ACIERTO' if is_correct else 'FALLO'})")
    
    if is_correct:
        current_weight_A += (current_weight_A * LTP_RATE)
        current_weight_B -= (current_weight_B * LTD_RATE)
    else:
        current_weight_B -= (current_weight_B * LTD_RATE)
        
    current_weight_A = np.clip(current_weight_A, 0.001, 1.0)
    current_weight_B = np.clip(current_weight_B, 0.001, 1.0)

# =============================================================================
# 3. GENERACIÓN DE GRÁFICOS FINALES
# =============================================================================
print("\n>>> GENERANDO GRÁFICOS FINALES...")

# --- A. Final_Learning_Results (Pesos y Desempeño) ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
ax1.plot(history_weights_A, 'g-o', label='Peso A (Correcto)')
ax1.plot(history_weights_B, 'r-x', label='Peso B (Incorrecto)')
ax1.set_title('Evolución de Pesos')
ax1.legend()
ax1.grid(True)

ax2.plot(history_choice, 'b-s')
ax2.set_title('Historial de Aciertos (1=Acierto, 0=Fallo)')
ax2.set_xlabel('Trial')
ax2.set_yticks([0, 1])
ax2.grid(True)
plt.tight_layout()
plt.savefig('Final_Learning_Results.png')
print("   > Guardado: Final_Learning_Results.png")

# --- B. DDM_Trajectory_Full_Sequence (Historial Completo A vs B) ---
if len(full_trace_A) > 0:
    fig_seq, ax_seq = plt.subplots(figsize=(12, 6))
    dt_plot = 10.0 
    t_vec = np.arange(0, len(full_trace_A) * dt_plot, dt_plot)
    
    ax_seq.plot(t_vec, full_trace_A, color='green', lw=2, label='Acumulación A')
    ax_seq.plot(t_vec, full_trace_B, color='red', lw=2, label='Acumulación B')
    
    # Líneas verticales
    for idx in experiment_decision_points:
        ax_seq.axvline(x=idx*dt_plot, color='gray', linestyle=':', alpha=0.5)

    ax_seq.axhline(y=decision_threshold, color='black', ls='--', label='Umbral')
    ax_seq.set_title('Evolución de la Competencia (Secuencia Completa)')
    ax_seq.set_xlabel('Tiempo Total (ms)')
    ax_seq.legend()
    plt.savefig('DDM_Trajectory_Full_Sequence.png')
    print("   > Guardado: DDM_Trajectory_Full_Sequence.png")

# --- C. DDM_Trajectory (Solo el último trial) ---
# Usamos los datos guardados en trace_A_trial (que corresponden al último bucle)
if len(trace_A_trial) > 0:
    fig_last, ax_last = plt.subplots(figsize=(10, 6))
    t_last = np.arange(0, len(trace_A_trial) * dt_decision, dt_decision)
    
    ax_last.plot(t_last, trace_A_trial, color='green', lw=2, label='Acumulación A')
    ax_last.plot(t_last, trace_B_trial, color='red', lw=2, label='Acumulación B')
    ax_last.axhline(y=decision_threshold, color='black', ls='--')
    
    ax_last.set_title(f'Trayectoria de Decisión (Último Trial: {winner})')
    ax_last.set_xlabel('Tiempo (ms)')
    ax_last.legend()
    plt.savefig('DDM_Trajectory.png')
    print("   > Guardado: DDM_Trajectory.png")

# --- D. Gráficos de Voltaje (Trazas Separadas y Juntas) ---
if 'V_soma' in sim.allSimData:
    time_vec = np.array(sim.allSimData['t'])
    trace_0 = np.array(sim.allSimData['V_soma'].get('cell_0', []))
    trace_40 = np.array(sim.allSimData['V_soma'].get('cell_40', []))
    
    if len(trace_0) > 0 and len(trace_40) > 0:
        # Trazas Juntas
        plt.figure(figsize=(10, 6))
        plt.plot(time_vec, trace_0, 'g', label='PYR_A (Correcta)', alpha=0.8)
        plt.plot(time_vec, trace_40, 'r', label='PYR_B (Incorrecta)', alpha=0.8)
        plt.title('Voltaje Soma: Competencia A vs B (Último Trial)')
        plt.legend()
        plt.savefig('Trazas_Juntas.png')
        print("   > Guardado: Trazas_Juntas.png")
        
        # Trazas Separadas
        fig_sep, (ax_s1, ax_s2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        ax_s1.plot(time_vec, trace_0, 'g')
        ax_s1.set_title('PYR_A (Correcta)')
        ax_s2.plot(time_vec, trace_40, 'r')
        ax_s2.set_title('PYR_B (Incorrecta)')
        plt.savefig('Trazas_Separadas.png')
        print("   > Guardado: Trazas_Separadas.png")
    else:
        print("WARN: No se encontraron datos para cell_0 o cell_40.")

# --- E. Analisis_Espectral_PAC ---
if 'V_soma' in sim.allSimData:
    dt = cfg.dt
    fs = 1000.0 / dt
    all_traces = [np.array(t) for t in sim.allSimData['V_soma'].values()]
    
    if len(all_traces) > 0:
        lfp = np.mean(all_traces, axis=0)
        lfp = lfp - np.mean(lfp)

        fig_spec = plt.figure(figsize=(10, 8))
        gs = fig_spec.add_gridspec(3, 1, height_ratios=[1, 1, 1.5], hspace=0.4)

        # Señal
        ax0 = fig_spec.add_subplot(gs[0])
        ax0.plot(np.linspace(0, cfg.duration, len(lfp)), lfp, 'k', lw=1)
        ax0.set_title('Pseudo-LFP (Promedio Poblacional)')
        
        # PSD
        ax1 = fig_spec.add_subplot(gs[1])
        f, Pxx = signal.welch(lfp, fs, nperseg=min(len(lfp), 1024))
        ax1.semilogy(f, Pxx)
        ax1.set_xlim([0, 100])
        ax1.axvspan(4, 12, color='green', alpha=0.2, label='Theta')
        ax1.axvspan(30, 80, color='red', alpha=0.2, label='Gamma')
        ax1.legend()
        ax1.set_title('Densidad Espectral (PSD)')

        # Espectrograma
        ax2 = fig_spec.add_subplot(gs[2])
        f_s, t_s, Sxx = signal.spectrogram(lfp, fs, nperseg=128, noverlap=100)
        c = ax2.pcolormesh(t_s*1000, f_s, 10 * np.log10(Sxx + 1e-10), shading='gouraud', cmap='jet')
        ax2.set_ylim([0, 100])
        ax2.set_ylabel('Hz'); ax2.set_xlabel('ms')
        ax2.set_title('Espectrograma')
        fig_spec.colorbar(c, ax=ax2, label='dB')
        
        plt.savefig('Analisis_Espectral_PAC.png')
        print("   > Guardado: Analisis_Espectral_PAC.png")

print(">>> PROCESO COMPLETADO EXITOSAMENTE.")
plt.show()