import pickle
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos
with open('model_output_data.pkl', 'rb') as f:
    data = pickle.load(f)

spike_times = np.array(data['simData']['spkt'])
spike_ids = np.array(data['simData']['spkid'])

print("=== DIAGNÓSTICO RÁPIDO ===")
print(f"Spikes totales: {len(spike_times)}")
print(f"Tiempo simulación: {data['simConfig']['duration']} ms")
print(f"Primer spike: {spike_times.min():.3f} ms")
print(f"Último spike: {spike_times.max():.3f} ms")

# Separar por población
pyr_ids = data['net']['pops']['PYR_pop']['cellGids']
olm_ids = data['net']['pops']['OLM_pop']['cellGids']
artif_ids = data['net']['pops']['artif_pyr']['cellGids']

pyr_mask = np.isin(spike_ids, pyr_ids)
olm_mask = np.isin(spike_ids, olm_ids)
artif_mask = np.isin(spike_ids, artif_ids)

print(f"\n=== SPIKES POR POBLACIÓN ===")
print(f"PYR: {np.sum(pyr_mask)} spikes")
print(f"OLM: {np.sum(olm_mask)} spikes")  
print(f"artif: {np.sum(artif_mask)} spikes")

# 1. Distribución temporal
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Raster total
axes[0, 0].scatter(spike_times[:5000], spike_ids[:5000], s=1, alpha=0.3)
axes[0, 0].set_xlabel('Time (ms)')
axes[0, 0].set_ylabel('Cell ID')
axes[0, 0].set_title('Raster (primeros 5000 spikes)')

# Primeros 100ms
axes[0, 1].scatter(spike_times[spike_times < 100], 
                   spike_ids[spike_times < 100], s=2, alpha=0.5)
axes[0, 1].set_xlabel('Time (ms)')
axes[0, 1].set_ylabel('Cell ID')
axes[0, 1].set_title('Primeros 100ms')

# Histograma de tiempos
axes[0, 2].hist(spike_times, bins=100)
axes[0, 2].set_xlabel('Time (ms)')
axes[0, 2].set_ylabel('Spike count')
axes[0, 2].set_yscale('log')
axes[0, 2].set_title('Distribución de spikes')

# Tasa de disparo por ventana
axes[1, 0].hist(spike_times[pyr_mask], bins=50, alpha=0.5, label='PYR')
axes[1, 0].hist(spike_times[olm_mask], bins=50, alpha=0.5, label='OLM')
axes[1, 0].set_xlabel('Time (ms)')
axes[1, 0].set_ylabel('Spike count')
axes[1, 0].set_title('Spikes por población')
axes[1, 0].legend()

# ISI distribution
for mask, label, color in [(pyr_mask, 'PYR', 'blue'), 
                          (olm_mask, 'OLM', 'red'),
                          (artif_mask, 'artif', 'green')]:
    if np.sum(mask) > 10:
        cell_spikes = spike_times[mask]
        cell_ids = spike_ids[mask]
        # Para cada célula en esta población
        for cell_id in np.unique(cell_ids)[:5]:  # Primeras 5 células
            cell_times = cell_spikes[cell_ids == cell_id]
            if len(cell_times) > 5:
                isi = np.diff(cell_times)
                axes[1, 1].hist(isi[isi < 100], bins=20, alpha=0.3, 
                               label=f'{label}_{int(cell_id)}', color=color)
axes[1, 1].set_xlabel('ISI (ms)')
axes[1, 1].set_ylabel('Count')
axes[1, 1].set_title('ISI (primeras 5 células por población)')
axes[1, 1].set_yscale('log')

# Firing rate instantáneo
window = 10  # ms
times = np.arange(0, 1300, window)
rates = []
for t in times:
    spikes_in_window = np.sum((spike_times >= t) & (spike_times < t + window))
    rate = spikes_in_window / (window/1000) / 370  # Hz por célula
    rates.append(rate)
    
axes[1, 2].plot(times, rates)
axes[1, 2].set_xlabel('Time (ms)')
axes[1, 2].set_ylabel('Firing rate (Hz/célula)')
axes[1, 2].set_title('Tasa instantánea de disparo')
axes[1, 2].axhline(y=20, color='r', linestyle='--', label='Límite normal (20 Hz)')
axes[1, 2].legend()

plt.tight_layout()
plt.savefig('quick_diagnosis.png', dpi=150)
plt.show()

# Análisis de explosividad
print(f"\n=== ANÁLISIS DE EXPLOSIVIDAD ===")
print(f"Spikes en primeros 10ms: {np.sum(spike_times < 10)}")
print(f"Spikes en primeros 50ms: {np.sum(spike_times < 50)}")
print(f"Spikes en primeros 100ms: {np.sum(spike_times < 100)}")

# Bursts (ISI < 10ms)
isi_all = np.diff(np.sort(spike_times))
burst_ratio = np.sum(isi_all < 10) / len(isi_all) * 100
print(f"Bursts (ISI < 10ms): {burst_ratio:.1f}% de todos los ISIs")