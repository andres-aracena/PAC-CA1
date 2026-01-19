# Script rápido para analizar oscilaciones
import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Cargar datos
with open('model_output_data.pkl', 'rb') as f:
    data = pickle.load(f)

spike_times = data['simData']['spkt']
spike_ids = data['simData']['spkid']

# 1. Crear PSTH (histograma de spikes)
bin_size = 10  # ms
time_bins = np.arange(0, 6300, bin_size)
spike_hist, _ = np.histogram(spike_times, bins=time_bins)

# 2. Análisis espectral
fs = 1000/bin_size  # Frecuencia de muestreo en Hz
frequencies, power = signal.welch(spike_hist, fs, nperseg=1024)

plt.figure(figsize=(12, 4))
plt.subplot(121)
plt.plot(time_bins[:-1], spike_hist)
plt.xlabel('Time (ms)')
plt.ylabel('Spike count per bin')
plt.title('Network Activity')

plt.subplot(122)
plt.semilogy(frequencies, power)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power')
plt.title('Power Spectrum')
plt.xlim(0, 100)
plt.axvline(x=10, color='r', linestyle='--', alpha=0.5, label='Theta')
plt.axvline(x=40, color='g', linestyle='--', alpha=0.5, label='Gamma')
plt.legend()
plt.tight_layout()
plt.show()