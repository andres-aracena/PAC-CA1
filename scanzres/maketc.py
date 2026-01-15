import os.path
import json
import matplotlib.pyplot as plt
import numpy as np

filename1 = 'model_output_data.json'
dirs1 = 't42_data'
starttime = 300
ndends = 1 + 20
apicnum = 6 

if os.path.isfile(filename1):
    print(f"Archivo encontrado: {filename1}. Procesando...")
    with open(filename1) as f:
        data = json.load(f)
    
    # --- DIAGNÓSTICO DE CÉLULAS DISPONIBLES ---
    # Miramos qué celdas realmente tienen datos en V_soma
    available_cells = list(data['simData']['V_soma'].keys())
    print(f"Células con trazas de voltaje encontradas: {available_cells}")

    if not available_cells:
        print("ERROR: No hay datos de voltaje en 'V_soma'. Revisa cfg.recordTraces en tu simulación.")
    else:
        # En lugar de buscar 'PYR_pop', usamos la primera célula que tenga datos
        target_cell_key = available_cells[0] # Ejemplo: 'cell_0' o 'cell_11'
        print(f"Graficando datos para: {target_cell_key}")

        # Extraer el voltaje del soma
        x1 = np.array(data['simData']['V_soma'][target_cell_key])
        
        # Preparar matriz para todas las dendritas
        x1all = np.zeros((x1.shape[0], ndends))
        x1all[:, 0] = x1
        
        # Buscar todas las apicales grabadas para ESA misma célula
        l1 = [key for key, val in data['simData'].items() 
              if (key.startswith('V_apic') and target_cell_key in val)]
        
        print(f"Secciones apicales encontradas para esta célula: {len(l1)}")

        for x, xval1 in enumerate(l1):
            if x + 1 < ndends: # Evitar desborde de índice
                x1_dend = np.array(data['simData'][xval1][target_cell_key])
                x1all[:, x + 1] = x1_dend

        # --- PROCESAMIENTO Y GRÁFICO ---
        # Restar el valor inicial (baseline)
        baseline_idx = int(starttime - 1)
        if baseline_idx < len(x1all):
            x1all = x1all - x1all[baseline_idx, :]

            plt.figure('traces2', figsize=(10, 6))
            time_axis = np.arange(len(x1all)) # Asumiendo dt=1 o similar para el eje X
            
            # Graficar Soma
            plt.plot(x1all[int(starttime-20):, 0], 'k', linewidth=2, label='Soma')
            
            # Graficar Apical (si existe el índice)
            if apicnum < x1all.shape[1]:
                plt.plot(x1all[int(starttime-20):, apicnum], 'deepskyblue', linewidth=2, label=f'Apical {apicnum}')

            plt.grid(True, which='both', linestyle='--', alpha=0.5)
            plt.ylabel('Membrane Potential Change (mV)')
            plt.xlabel('Time Points')
            plt.legend()
            
            plt.savefig('traces2.png', transparent=True)
            print("Gráfico guardado exitosamente como 'traces2.png'")
        else:
            print(f"ERROR: El tiempo de simulación es menor que el starttime ({len(x1all)} < {starttime})")

else:
    print(f"ERROR: No se encontró el archivo {filename1}")