"""
PlantDiscoverySimulator v3.0
Advanced anomaly detection and scientific discovery from plant bioelectric signals.
Detects inter-species communication, geological anomalies, and novel phenomena.
"""

import numpy as np
import json
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import List, Dict, Optional


class DiscoveryType(IntEnum):
    """Classification of discovery phenomena."""
    BASE_METABOLISM = 0       # Standard behavior (No discovery)
    BIO_COMMUNICATION = 1     # Novel correlation: Accelerated inter-species communication
    GEO_ANOMALY = 2           # Environmental anomaly: Detection of rare deposits or pollutants


@dataclass
class DiscoveryEvent:
    """Represents a single discovery event with metadata."""
    timestamp: str
    signal_pattern_hash: str
    fluorescence_shift_nm: float
    detected_phenomenon: DiscoveryType
    confidence_score: float
    action_required: str


class PlantDiscoverySimulator:
    """Core engine for plant bioelectric signal analysis and scientific discovery."""

    def __init__(self):
        """
        Initialize the discovery simulator with ternary state matrix.
        State matrix represents 3D phase space for:
        - Electrical signal vectors
        - VOC emission vectors
        - Near-infrared fluorescence vectors
        """
        # 3D state matrix (QCSA) - represents structured phase space
        self.state_matrix = np.array([
            [1, 0, -1],   # Electric signal phase vectors
            [0, 1,  1],   # VOC emission phase vectors
            [-1, 1, 0]    # nIR fluorescence phase vectors
        ], dtype=np.float32)
        
        self.discovery_history: List[DiscoveryEvent] = []
        self.threshold_config = {
            'elec_variance_high': 15.0,
            'elec_variance_low': -15.0,
            'voc_trend_threshold': 2.0,
            'nir_shift_high': 25.0,
            'nir_shift_low': -5.0,
            'magnitude_geo_threshold': 2.5,
            'magnitude_bio_threshold': 1.5,
        }

    def analyze_anomalous_stream(self, elec_variance: float, voc_trend: float, nir_shift: float) -> DiscoveryEvent:
        """
        Analyze bioelectric data stream for anomalies indicating scientific discoveries.
        Deviations from homeostasis suggest novel phenomena.
        
        Args:
            elec_variance: Electrical signal variance (mV)
            voc_trend: Volatile organic compound trend (ppm/min)
            nir_shift: Near-infrared fluorescence shift (nm)
            
        Returns:
            DiscoveryEvent containing classification and confidence metrics
        """
        # Discrete evaluation through assertive ternary logic thresholds
        sig_elec = 1 if elec_variance > self.threshold_config['elec_variance_high'] \
                   else (-1 if elec_variance < self.threshold_config['elec_variance_low'] else 0)
        
        sig_voc = 1 if voc_trend > self.threshold_config['voc_trend_threshold'] else 0
        
        sig_nir = 1 if nir_shift > self.threshold_config['nir_shift_high'] \
                  else (-1 if nir_shift < self.threshold_config['nir_shift_low'] else 0)
        
        input_vector = np.array([sig_elec, sig_voc, sig_nir], dtype=np.float32)
        
        # Project signal vector onto QCSA state matrix structure
        projection = np.dot(input_vector, self.state_matrix)
        magnitude = float(np.linalg.norm(projection))
        
        # Classify discovery based on phase deviation magnitude
        if magnitude > self.threshold_config['magnitude_geo_threshold'] and sig_nir == 1:
            discovery = DiscoveryType.GEO_ANOMALY
            desc = "DISCOVERY: Groundwater detection with heavy metal / rare mineral fingerprint."
            action = "Initiate geological mapping through bionic mesh network. Save XYZ coordinates."
        
        elif magnitude > self.threshold_config['magnitude_bio_threshold'] and sig_elec == -1:
            discovery = DiscoveryType.BIO_COMMUNICATION
            desc = "DISCOVERY: Alarm signal detection inter-species (Xylem synchronization with external trees)."
            action = "Record wave pattern in 'The Spark'. Propagate optical fortification stimulus."
        
        else:
            discovery = DiscoveryType.BASE_METABOLISM
            desc = "Basal metabolism stable. Homeostatic parameters optimal."
            action = "Maintain passive equanimity margin."

        # Calculate confidence score (0-100%)
        confidence_score = round(min(100.0, magnitude * 35.0), 2)
        
        # Generate pattern hash from signal vector
        signal_hash = f"PH-{''.join(str(int(x)) for x in input_vector.tolist())}"
        
        event = DiscoveryEvent(
            timestamp=datetime.now().isoformat(),
            signal_pattern_hash=signal_hash,
            fluorescence_shift_nm=nir_shift,
            detected_phenomenon=discovery,
            confidence_score=confidence_score,
            action_required=desc + " | " + action
        )
        
        self.discovery_history.append(event)
        return event

    def batch_analyze(self, scenarios: List[Dict[str, float]]) -> List[DiscoveryEvent]:
        """
        Analyze multiple sensor scenarios in batch mode.
        
        Args:
            scenarios: List of dictionaries with 'elec', 'voc', 'nir' keys
            
        Returns:
            List of DiscoveryEvent results
        """
        results = []
        for scenario in scenarios:
            event = self.analyze_anomalous_stream(
                scenario.get('elec', 0.0),
                scenario.get('voc', 0.0),
                scenario.get('nir', 0.0)
            )
            results.append(event)
        return results

    def get_discovery_summary(self) -> Dict[str, int]:
        """
        Generate summary statistics of discoveries.
        
        Returns:
            Dictionary with counts by discovery type
        """
        summary = {
            'total': len(self.discovery_history),
            'base_metabolism': 0,
            'bio_communication': 0,
            'geo_anomaly': 0,
            'avg_confidence': 0.0
        }
        
        if self.discovery_history:
            for event in self.discovery_history:
                if event.detected_phenomenon == DiscoveryType.BASE_METABOLISM:
                    summary['base_metabolism'] += 1
                elif event.detected_phenomenon == DiscoveryType.BIO_COMMUNICATION:
                    summary['bio_communication'] += 1
                elif event.detected_phenomenon == DiscoveryType.GEO_ANOMALY:
                    summary['geo_anomaly'] += 1
            
            avg_conf = sum(e.confidence_score for e in self.discovery_history) / len(self.discovery_history)
            summary['avg_confidence'] = round(avg_conf, 2)
        
        return summary

    def save_discoveries(self, filepath: str = "the_spark_discoveries.json") -> None:
        """
        Persist all discovered events to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = [
            {
                "timestamp": e.timestamp,
                "pattern_id": e.signal_pattern_hash,
                "nir_shift_nm": e.fluorescence_shift_nm,
                "type": e.detected_phenomenon.name,
                "confidence": f"{e.confidence_score}%",
                "log_summary": e.action_required
            } for e in self.discovery_history
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[Deep Storage] All discovery possibilities archived in '{filepath}'.")

    def load_discoveries(self, filepath: str) -> List[DiscoveryEvent]:
        """
        Load previously saved discoveries from JSON file.
        
        Args:
            filepath: Input file path
            
        Returns:
            List of loaded DiscoveryEvent objects
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            loaded_events = []
            for item in data:
                event = DiscoveryEvent(
                    timestamp=item['timestamp'],
                    signal_pattern_hash=item['pattern_id'],
                    fluorescence_shift_nm=item['nir_shift_nm'],
                    detected_phenomenon=DiscoveryType[item['type']],
                    confidence_score=float(item['confidence'].rstrip('%')),
                    action_required=item['log_summary']
                )
                loaded_events.append(event)
                self.discovery_history.append(event)
            
            print(f"\n[Load Complete] {len(loaded_events)} discoveries loaded from '{filepath}'.")
            return loaded_events
        
        except FileNotFoundError:
            print(f"[Error] File not found: {filepath}")
            return []

    def print_discovery_report(self) -> None:
        """
        Print formatted discovery report to console.
        """
        summary = self.get_discovery_summary()
        
        print("\n" + "="*70)
        print("              PLANT DISCOVERY ANALYSIS REPORT")
        print("="*70)
        print(f"\nTotal Events Analyzed: {summary['total']}")
        print(f"Average Confidence: {summary['avg_confidence']}%")
        print(f"\nDiscovery Breakdown:")
        print(f"  🔵 Base Metabolism: {summary['base_metabolism']} events")
        print(f"  🟢 Bio-Communication: {summary['bio_communication']} events")
        print(f"  🟠 Geological Anomalies: {summary['geo_anomaly']} events")
        print(f"\nRecent Events:")
        
        for i, event in enumerate(self.discovery_history[-5:], 1):
            print(f"\n  [{i}] {event.timestamp}")
            print(f"      Type: {event.detected_phenomenon.name}")
            print(f"      Confidence: {event.confidence_score}%")
            print(f"      Pattern: {event.signal_pattern_hash}")
            print(f"      Action: {event.action_required[:60]}...")
        
        print("\n" + "="*70)


# =====================================================================
# RESEARCH TEST BENCH (FRONTIER SCENARIOS)
# =====================================================================
if __name__ == "__main__":
    simulator = PlantDiscoverySimulator()
    
    # Simulate 3 scenarios collected from bionic mesh network field research
    research_scenarios = [
        {
            "name": "Scenario 1: Standard electrical signals in greenhouse",
            "elec": 2.0,
            "voc": 0.1,
            "nir": 0.0
        },
        {
            "name": "Scenario 2: Massive spontaneous synchronization (Network electrical wave)",
            "elec": -18.5,
            "voc": 2.5,
            "nir": 2.0
        },
        {
            "name": "Scenario 3: Massive nIR fluorescence shift (Soil compound absorption)",
            "elec": 5.0,
            "voc": 2.8,
            "nir": 32.4
        }
    ]
    
    print("\n" + "="*70)
    print("      LOGOALGORITHM ADVANCED DISCOVERY SIMULATOR")
    print("="*70)
    
    for scenario in research_scenarios:
        print(f"\n[Analysis] {scenario['name']}")
        result = simulator.analyze_anomalous_stream(
            scenario["elec"],
            scenario["voc"],
            scenario["nir"]
        )
        print(f"  → Signal Pattern Hash: {result.signal_pattern_hash}")
        print(f"  → Confidence Score: {result.confidence_score}%")
        print(f"  → Discovery Type: {result.detected_phenomenon.name}")
        print(f"  → Result: {result.action_required}")
        print("-" * 70)
    
    # Generate report and save
    simulator.print_discovery_report()
    simulator.save_discoveries()
