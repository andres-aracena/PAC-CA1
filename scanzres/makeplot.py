import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal, stats

# Cargar datos de manera robusta
try:
    with open('model_output_data.pkl', 'rb') as f:
        data = pickle.load(f)
    
    # Estrategia 1: Buscar datos en estructura común de NetPyNE
    simData = None
    cfg = None
    
    # Buscar simData
    if 'simData' in data:
        simData = data['simData']
    elif 'sim_data' in data:
        simData = data['sim_data']
    elif isinstance(data, dict) and any('spk' in key for key in data.keys()):
        simData = data
    
    # Buscar cfg
    if 'cfg' in data:
        cfg = data['cfg']
    elif 'config' in data:
        cfg = data['config']
    elif 'simConfig' in data:
        cfg = data['simConfig']
    
    # Estrategia 2: Si no encontramos simData, asumimos que data ES simData
    if simData is None:
        simData = data
    
    print("=== INFORMACIÓN DE LA SIMULACIÓN ===")
    if cfg:
        print(f"Duración: {cfg.get('duration', 'No encontrado')} ms")
        print(f"Poblaciones configuradas: {cfg.get('pyrpopsize', 'N/A')} PYR, {cfg.get('olmpopsize', 'N/A')} OLM")
    else:
        print("Configuración no encontrada en los datos")
    
    # Buscar spikes de diferentes maneras
    spike_times = None
    spike_ids = None
    
    # Posibles nombres de claves
    spike_keys = ['spkt', 'spikeTimes', 'spike_times', 't', 'times']
    id_keys = ['spkid', 'spikeIds', 'spike_ids', 'gids', 'cells']
    
    for t_key in spike_keys:
        for id_key in id_keys:
            if t_key in simData and id_key in simData:
                spike_times = np.array(simData[t_key])
                spike_ids = np.array(simData[id_key])
                print(f"Spikes encontrados en claves: '{t_key}' y '{id_key}'")
                break
        if spike_times is not None:
            break
    
    if spike_times is None:
        # Último intento: buscar arrays con la forma correcta
        for key, value in simData.items():
            if isinstance(value, (list, np.ndarray)) and len(value) > 100:
                print(f"Array encontrado en '{key}': tamaño {len(value)}")
                # Asumir que el primer array largo es spike_times
                if spike_times is None and len(value) == len(spike_ids or []):
                    spike_times = np.array(value)
                elif spike_ids is None and len(value) == len(spike_times or []):
                    spike_ids = np.array(value)
    
    if spike_times is not None and spike_ids is not None:
        print(f"\n=== ANÁLISIS DE SPIKES ===")
        print(f"Total de spikes: {len(spike_times)}")
        print(f"Tiempos de spike: {spike_times[:5]} ... {spike_times[-5:]}")
        print(f"IDs de spike: {spike_ids[:5]} ... {spike_ids[-5:]}")
        
        # Cálculos básicos
        total_time = 6300  # Asumiendo duración de tu simulación
        avg_rate = len(spike_times) / (total_time / 1000)  # Hz
        print(f"Tasa promedio: {avg_rate:.2f} Hz")
        
        # Histograma simple
        plt.figure(figsize=(10, 5))
        plt.hist(spike_times, bins=100)
        plt.xlabel('Tiempo (ms)')
        plt.ylabel('Número de spikes')
        plt.title(f'Distribución de spikes ({len(spike_times)} total)')
        plt.savefig('spikes_histogram.png', dpi=150)
        plt.show()
        
        # Análisis temporal
        bin_size = 50  # ms
        time_bins = np.arange(0, total_time, bin_size)
        spike_hist, _ = np.histogram(spike_times, bins=time_bins)
        
        # Espectro
        fs = 1000 / bin_size
        if len(spike_hist) > 10:
            frequencies, power = signal.welch(spike_hist, fs, nperseg=min(256, len(spike_hist)))
            
            plt.figure(figsize=(12, 4))
            plt.subplot(121)
            plt.plot(time_bins[:-1], spike_hist)
            plt.xlabel('Tiempo (ms)')
            plt.ylabel('Spikes por bin')
            
            plt.subplot(122)
            plt.semilogy(frequencies, power)
            plt.xlabel('Frecuencia (Hz)')
            plt.ylabel('Potencia')
            plt.xlim(0, 100)
            plt.axvline(x=10, color='r', linestyle='--', alpha=0.5, label='Theta')
            plt.axvline(x=40, color='g', linestyle='--', alpha=0.5, label='Gamma')
            plt.legend()
            plt.tight_layout()
            plt.savefig('network_activity.png', dpi=150)
            plt.show()
            
            # Buscar picos en el espectro
            peaks, properties = signal.find_peaks(power, height=np.percentile(power, 75))
            if len(peaks) > 0:
                print("\n=== PICOS EN EL ESPECTRO ===")
                for peak in peaks[:5]:  # Mostrar solo los 5 principales
                    freq = frequencies[peak]
                    if freq > 1:  # Ignorar frecuencia 0
                        print(f"  {freq:.1f} Hz: potencia {power[peak]:.2e}")
    
    else:
        print("ERROR: No se pudieron encontrar spikes en los datos")
        print("Claves disponibles:", list(simData.keys()) if isinstance(simData, dict) else "N/A")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Último recurso: intenta cargar como numpy array directamente
    try:
        # Buscar cualquier archivo .npy o .dat
        import os
        for file in os.listdir('.'):
            if file.endswith('.npy'):
                print(f"\nIntentando cargar {file}...")
                array_data = np.load(file)
                print(f"Cargado: forma {array_data.shape}")
    except:
        pass