#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 13:22:12 2020

@author: adam
"""
import os.path
import json
import matplotlib.pyplot as plt
import numpy as np

dirs1 = 't42_data'

ndends = 1 + 20  # soma + apicales
apicnum = 6 
starttime = 300
asBatch = False

if asBatch:
   filename1 = dirs1 + '/t42_0' + '.json'
else:   
   filename1 = 'model_output_data.json'

if os.path.isfile(filename1):
    print(f"Archivo encontrado: {filename1}. Procesando...")
    with open(filename1) as f:
      data = json.load(f)
      
      # DIAGNÓSTICO: Ver qué células tienen trazas
      print("Claves en V_soma:", list(data['simData']['V_soma'].keys())[:5])
      
      # OPCIÓN A: Usar la primera célula que tenga trazas
      available_cells = list(data['simData']['V_soma'].keys())
      if not available_cells:
          print("ERROR: No hay trazas de V_soma registradas")
          exit()
      
      # Tomar la primera célula disponible
      cell_key = available_cells[0]  # Ej: 'cell_4'
      print(f"Usando célula: {cell_key}")
      
      # OPCIÓN B: Buscar una célula PYR específica (cambia el 4 por el índice que quieras)
      # cell_key = 'cell_4'  # Directamente usar célula 4
      
      # Obtener traza de soma
      x1 = np.array(data['simData']['V_soma'][cell_key])
      
      # Inicializar matriz para todas las trazas
      x1all = np.zeros((x1.shape[0], ndends))
      x1all[:,0] = x1
      
      # Buscar trazas apicales para la MISMA célula
      apical_traces = []
      for key in data['simData']:
          if key.startswith('V_apic') and cell_key in data['simData'][key]:
              apical_traces.append(key)
      
      # Ordenar numéricamente: V_apic_0, V_apic_1, etc.
      apical_traces.sort(key=lambda x: int(x.split('_')[2]) if x.split('_')[2].isdigit() else 0)
      
      print(f"Encontradas {len(apical_traces)} trazas apicales")
      
      # Llenar matriz con trazas apicales
      for i, apic_key in enumerate(apical_traces[:ndends-1]):
          x1all[:, i+1] = np.array(data['simData'][apic_key][cell_key])
      
      # Normalizar: restar valor en starttime
      x1all = x1all - x1all[int(starttime-1), :]
      
      # Graficar
      plt.figure('traces2', figsize=(12, 6))
      plt.xlim(0, 200)
      plt.plot(x1all[int(starttime-20):, 0], 'k', linewidth=2, label='soma')
      plt.plot(x1all[int(starttime-20):, apicnum], 'xkcd:light blue', linewidth=2, label=f'apic_{apicnum-1}')
      
      plt.grid(True, which='both', alpha=0.3)
      plt.minorticks_on()
      plt.ylabel('membrane potential (mV)')
      plt.xlabel('time (ms)')
      plt.legend()
      plt.tight_layout()
      
      if asBatch:
         plt.savefig(dirs1 + '/traces2.png', dpi=150, transparent=True)
      else:
         plt.savefig('traces2.png', dpi=150, transparent=True)
      
      plt.show()
      
else:
    print(f"ERROR: No se encontró el archivo {filename1}")
    print(f"Archivos en directorio actual: {os.listdir('.')}")