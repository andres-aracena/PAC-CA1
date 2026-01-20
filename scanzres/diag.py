import pickle
import json
import numpy as np

# Intenta cargar el archivo .pkl
try:
    with open('model_output_data.pkl', 'rb') as f:
        data = pickle.load(f)
    print("=== ESTRUCTURA DEL ARCHIVO PKL ===")
    
    # Función para explorar estructura
    def explore(obj, indent=0, max_depth=3, current_depth=0):
        if current_depth > max_depth:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                print("  " * indent + f"'{key}': {type(value)}")
                if current_depth < max_depth:
                    explore(value, indent+1, max_depth, current_depth+1)
        elif isinstance(obj, (list, np.ndarray)):
            print("  " * indent + f"Tamaño: {len(obj)}")
            if len(obj) > 0 and current_depth < max_depth:
                explore(obj[0], indent+1, max_depth, current_depth+1)
    
    explore(data, max_depth=2)
    
    # Buscar spikes específicamente
    print("\n=== BUSCANDO SPIKES ===")
    def find_spikes(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if 'spk' in key.lower():
                    print(f"Encontrado en {path}.{key}: {type(value)}")
                    if isinstance(value, (list, np.ndarray)):
                        print(f"  Tamaño: {len(value)}")
                        if len(value) > 0:
                            print(f"  Primeros 5 valores: {value[:5] if len(value) > 5 else value}")
                find_spikes(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, (list, np.ndarray)) and len(obj) > 0:
            find_spikes(obj[0], path + "[0]")
    
    find_spikes(data)
    
except Exception as e:
    print(f"Error cargando .pkl: {e}")

# También revisa el archivo JSON
try:
    with open('model_output_data.json', 'r') as f:
        data_json = json.load(f)
    print("\n=== ESTRUCTURA DEL ARCHIVO JSON ===")
    
    # Versión simplificada para JSON
    def explore_json(obj, indent=0, max_depth=2, current_depth=0):
        if current_depth > max_depth:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                if 'spk' in key.lower():
                    print("  " * indent + f"'{key}': {type(value)} - tamaño: {len(value) if isinstance(value, list) else 'N/A'}")
                    if isinstance(value, list) and len(value) > 0 and current_depth < max_depth:
                        print("  " * (indent+1) + f"Primeros 3: {value[:3]}")
                elif current_depth < max_depth:
                    print("  " * indent + f"'{key}': {type(value)}")
                    explore_json(value, indent+1, max_depth, current_depth+1)
    
    explore_json(data_json, max_depth=2)
    
except Exception as e:
    print(f"Error cargando .json: {e}")
    