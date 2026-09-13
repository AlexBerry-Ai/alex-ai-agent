"""
Plant Mesh Network Module v3.0
Biosymbiotic monitoring and distributed control for agricultural systems.
"""

import numpy as np
from datetime import datetime
from typing import Dict, List


class PlantMeshNode:
    """Reprezintă un nod individual (o plantă monitorizată) din rețeaua mesh."""
    def __init__(self, node_id: str, zone: str):
        self.node_id = node_id
        self.zone = zone
        self.weights = np.array([1, 2]) # [Electric, Chimic]
        self.bias = 0
        self.current_state = 0 # Neutru inițial
        
    def evaluate_sensors(self, voltage_mv: float, voc_ppm: float) -> int:
        """Calculează starea ternară locală a nodului vegetal."""
        sig_electric = -1 if voltage_mv < -10.0 else (1 if voltage_mv > 0.0 else 0)
        sig_chemical = -1 if voc_ppm > 150.0 else 0
        
        raw_score = int(np.dot(np.array([sig_electric, sig_chemical]), self.weights) + self.bias)
        
        if raw_score < -1:
            self.current_state = -1 # STRES CRITIC
        elif raw_score > 0:
            self.current_state = 1  # FOTOSINTEZĂ OPTIMĂ
        else:
            self.current_state = 0  # ECUANIMITATE
            
        return self.current_state


class PlantMeshNetworkController:
    """Controlerul central care orchestrează comunicarea și acțiunile de urgență în rețeaua mesh."""
    def __init__(self):
        self.nodes: Dict[str, PlantMeshNode] = {}
        
    def register_node(self, node: PlantMeshNode):
        self.nodes[node.node_id] = node
        
    def process_network_sync(self, sensor_data: Dict[str, dict]):
        print(f"\n🌐 [MESH SYNC - {datetime.now().strftime('%H:%M:%S')}] Corelarea datelor biosimbiotice...")
        
        alerts_triggered = False
        stressed_zones = []
        
        # Pasul 1: Evaluăm starea fiecărui nod în mod independent
        for node_id, data in sensor_data.items():
            node = self.nodes[node_id]
            state = node.evaluate_sensors(data["voltage"], data["voc"])
            
            if state == -1:
                alerts_triggered = True
                stressed_zones.append(node.zone)
                print(f" 🔴 [NOD {node_id} - Zona {node.zone}]: Raportează STRES CRITIC! (Senzori: {data['voltage']}mV, {data['voc']}ppm)")
            else:
                status_name = "OPTIM" if state == 1 else "STABIL"
                print(f" 🟢 [NOD {node_id} - Zona {node.zone}]: Stare {status_name}.")
                
        # Pasul 2: Comunicarea sistemică (Dacă o zonă suferă, trimitem comenzi preventive vecinilor)
        if alerts_triggered:
            print(f"\n📢 [MECANISM SIMBIOTIC DECLANȘAT]: Răspuns automat la nivel de rețea:")
            for node_id, node in self.nodes.items():
                if node.zone not in stressed_zones:
                    # Tritem stimul optic preventiv nodurilor sănătoase din rețea pentru a le fortifica
                    print(f"  ⚡ -> Stimulare preventivă pe NOD {node_id} (Zona {node.zone}): Activare spectru UV-B / Roșu pentru imunitate.")
        else:
            print("\n✔️ [STATUS REȚEA]: Toate nodurile vegetale cooperează în stare de echilibru perfect.")
        print("="*75)
