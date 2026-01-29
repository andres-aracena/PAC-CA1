#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PKL Data Analyzer - Windows Compatible (No Unicode)
Analyzes simulation data saved in model_output_data.pkl
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt

def load_pkl_data(filename='model_output_data.pkl'):
    """Load simulation data from PKL file"""
    print(f"Loading data from {filename}...")
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    print("[OK] Data loaded successfully\n")
    return data

def analyze_simulation_data(data):
    """Analyze and print simulation statistics"""
    print("=" * 80)
    print("SIMULATION DATA ANALYSIS")
    print("=" * 80)
    
    # Basic info
    print("\n1. SIMULATION CONFIGURATION")
    print("-" * 80)
    if 'simConfig' in data:
        cfg = data['simConfig']
        print(f"  Duration: {cfg.get('duration', 'N/A')} ms")
        print(f"  dt: {cfg.get('dt', 'N/A')} ms")
        print(f"  Seeds: {cfg.get('seeds', 'N/A')}")
    
    # Network structure
    print("\n2. NETWORK STRUCTURE")
    print("-" * 80)
    if 'net' in data and 'pops' in data['net']:
        for pop_name, pop_data in data['net']['pops'].items():
            cell_gids = pop_data.get('cellGids', [])
            print(f"  {pop_name}: {len(cell_gids)} cells (GIDs: {min(cell_gids)}-{max(cell_gids)})")
    
    # Spike statistics
    print("\n3. SPIKE STATISTICS")
    print("-" * 80)
    if 'simData' in data:
        sim_data = data['simData']
        
        if 'spkt' in sim_data and 'spkid' in sim_data:
            spkt = np.array(sim_data['spkt'])
            spkid = np.array(sim_data['spkid'])
            
            print(f"  Total spikes: {len(spkt)}")
            print(f"  Average rate: {len(spkt) / (data['simConfig']['duration'] / 1000):.2f} Hz")
            
            # Per population
            if 'net' in data and 'pops' in data['net']:
                print("\n  Per population:")
                for pop_name, pop_data in data['net']['pops'].items():
                    gids = pop_data.get('cellGids', [])
                    mask = np.isin(spkid, gids)
                    pop_spikes = np.sum(mask)
                    avg_per_cell = pop_spikes / len(gids) if len(gids) > 0 else 0
                    print(f"    {pop_name}: {pop_spikes} spikes | {avg_per_cell:.1f} spikes/cell")
    
    # Connectivity
    print("\n4. CONNECTIVITY")
    print("-" * 80)
    if 'net' in data and 'params' in data['net']:
        params = data['net']['params']
        if 'connParams' in params:
            for conn_name, conn_data in params['connParams'].items():
                print(f"  {conn_name}:")
                print(f"    Synapse: {conn_data.get('synMech', 'N/A')}")
                print(f"    Weight: {conn_data.get('weight', 'N/A')}")
                print(f"    Delay: {conn_data.get('delay', 'N/A')}")
    
    # Recorded traces
    print("\n5. RECORDED TRACES")
    print("-" * 80)
    if 'simData' in data and 'V_soma' in data['simData']:
        traces = data['simData']['V_soma']
        print(f"  Voltage traces recorded: {len(traces)} cells")
        if len(traces) > 0:
            first_trace = list(traces.values())[0]
            print(f"  Time points per trace: {len(first_trace)}")
    
    return data

def plot_raster_from_pkl(data, save_filename='PKL_Raster_Analysis.png'):
    """Generate raster plot from PKL data"""
    print("\n6. GENERATING RASTER PLOT FROM PKL")
    print("-" * 80)
    
    if 'simData' not in data:
        print("  [WARN] No simData in PKL file")
        return
    
    sim_data = data['simData']
    
    if 'spkt' not in sim_data or 'spkid' not in sim_data:
        print("  [WARN] No spike data in PKL file")
        return
    
    spkt = np.array(sim_data['spkt'])
    spkid = np.array(sim_data['spkid'])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Color by population if available
    if 'net' in data and 'pops' in data['net']:
        colors = {'PYR_A': 'green', 'PYR_B': 'red', 'OLM': 'blue'}
        
        for pop_name, pop_data in data['net']['pops'].items():
            gids = pop_data.get('cellGids', [])
            mask = np.isin(spkid, gids)
            
            if np.sum(mask) > 0:
                ax.scatter(spkt[mask], spkid[mask], s=8, c=colors.get(pop_name, 'black'), 
                          marker='|', alpha=0.6, label=pop_name)
    else:
        ax.scatter(spkt, spkid, s=8, c='black', marker='|', alpha=0.6)
    
    ax.set_xlabel('Time (ms)', fontsize=12)
    ax.set_ylabel('Cell GID', fontsize=12)
    ax.set_title('Raster Plot from PKL Data', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(save_filename, dpi=150)
    plt.close()
    print(f"  [OK] Saved: {save_filename}")

def plot_firing_rates_from_pkl(data, save_filename='PKL_Firing_Rates.png'):
    """Plot population firing rates over time"""
    print("\n7. GENERATING FIRING RATE PLOT FROM PKL")
    print("-" * 80)
    
    if 'simData' not in data or 'net' not in data:
        print("  [WARN] Insufficient data")
        return
    
    sim_data = data['simData']
    spkt = np.array(sim_data['spkt'])
    spkid = np.array(sim_data['spkid'])
    duration = data['simConfig']['duration']
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    dt_bin = 50.0  # 50 ms bins
    time_bins = np.arange(0, duration, dt_bin)
    
    colors = {'PYR_A': 'green', 'PYR_B': 'red', 'OLM': 'blue'}
    
    for pop_name, pop_data in data['net']['pops'].items():
        gids = pop_data.get('cellGids', [])
        mask = np.isin(spkid, gids)
        pop_spikes = spkt[mask]
        
        rates = []
        for t in time_bins:
            t_end = t + dt_bin
            count = np.sum((pop_spikes >= t) & (pop_spikes < t_end))
            rate_hz = (count / len(gids)) * (1000.0 / dt_bin) if len(gids) > 0 else 0
            rates.append(rate_hz)
        
        ax.plot(time_bins, rates, color=colors.get(pop_name, 'black'), 
               lw=2, label=pop_name, alpha=0.8)
    
    ax.set_xlabel('Time (ms)', fontsize=12)
    ax.set_ylabel('Firing Rate (Hz)', fontsize=12)
    ax.set_title('Population Firing Rates Over Time', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_filename, dpi=150)
    plt.close()
    print(f"  [OK] Saved: {save_filename}")

def plot_voltage_traces_from_pkl(data, save_filename='PKL_Voltage_Traces.png'):
    """Plot voltage traces from PKL data"""
    print("\n8. GENERATING VOLTAGE TRACE PLOT FROM PKL")
    print("-" * 80)
    
    if 'simData' not in data:
        print("  [WARN] No simData in PKL file")
        return
    
    sim_data = data['simData']
    
    if 'V_soma' not in sim_data or 't' not in sim_data:
        print("  [WARN] No voltage traces in PKL file")
        return
    
    time_vec = np.array(sim_data['t'])
    traces = sim_data['V_soma']
    
    if len(traces) == 0:
        print("  [WARN] No voltage traces recorded")
        return
    
    fig, axes = plt.subplots(min(3, len(traces)), 1, figsize=(14, 8), sharex=True)
    
    if not isinstance(axes, np.ndarray):
        axes = [axes]
    
    colors = ['green', 'red', 'blue']
    cell_names = list(traces.keys())[:min(3, len(traces))]
    
    for i, cell_name in enumerate(cell_names):
        trace = traces[cell_name]
        axes[i].plot(time_vec, trace, color=colors[i], lw=0.8)
        axes[i].set_ylabel('Voltage (mV)')
        axes[i].set_title(f'Cell {cell_name}', fontsize=11)
        axes[i].grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Time (ms)')
    fig.suptitle('Somatic Voltage Traces', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_filename, dpi=150)
    plt.close()
    print(f"  [OK] Saved: {save_filename}")

def export_spike_data_to_csv(data, save_filename='spike_data.csv'):
    """Export spike data to CSV"""
    print("\n9. EXPORTING SPIKE DATA TO CSV")
    print("-" * 80)
    
    if 'simData' not in data:
        print("  [WARN] No simData in PKL file")
        return
    
    sim_data = data['simData']
    
    if 'spkt' not in sim_data or 'spkid' not in sim_data:
        print("  [WARN] No spike data")
        return
    
    spkt = np.array(sim_data['spkt'])
    spkid = np.array(sim_data['spkid'])
    
    # Add population labels
    pop_labels = np.empty(len(spkid), dtype='U10')
    
    if 'net' in data and 'pops' in data['net']:
        for pop_name, pop_data in data['net']['pops'].items():
            gids = pop_data.get('cellGids', [])
            mask = np.isin(spkid, gids)
            pop_labels[mask] = pop_name
    
    # Save to CSV
    import csv
    with open(save_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time_ms', 'GID', 'Population'])
        for t, gid, pop in zip(spkt, spkid, pop_labels):
            writer.writerow([t, int(gid), pop])
    
    print(f"  [OK] Saved: {save_filename} ({len(spkt)} spikes)")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("PKL DATA ANALYZER")
    print("=" * 80 + "\n")
    
    try:
        # Load data
        data = load_pkl_data('model_output_data.pkl')
        
        # Analyze
        analyze_simulation_data(data)
        
        # Generate plots
        plot_raster_from_pkl(data)
        plot_firing_rates_from_pkl(data)
        plot_voltage_traces_from_pkl(data)
        
        # Export
        export_spike_data_to_csv(data)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80 + "\n")
        
    except FileNotFoundError:
        print("[ERROR] model_output_data.pkl not found")
        print("  Make sure to run the simulation first to generate the PKL file")
    except Exception as e:
        print(f"[ERROR] Error during analysis: {e}")
        import traceback
        traceback.print_exc()