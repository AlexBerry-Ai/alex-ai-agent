"""
Discovery Dashboard v1.0
Real-time visualization and monitoring of plant bioelectric discoveries.
Displays anomaly patterns, confidence scores, and network status.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from plant_discovery_simulator import PlantDiscoverySimulator, DiscoveryType, DiscoveryEvent


class DiscoveryDashboard:
    """Real-time visualization dashboard for plant discovery events."""

    def __init__(self, simulator: PlantDiscoverySimulator, window_size: int = 10):
        """
        Initialize the discovery dashboard.
        
        Args:
            simulator: PlantDiscoverySimulator instance to visualize
            window_size: Number of recent events to display
        """
        self.simulator = simulator
        self.window_size = window_size
        self.fig = None
        self.axes = {}

    def generate_static_report(self, output_path: str = "discovery_dashboard.png") -> None:
        """
        Generate a static multi-panel discovery report.
        
        Args:
            output_path: Path to save the figure
        """
        if not self.simulator.discovery_history:
            print("[Dashboard] No discovery data available to visualize.")
            return

        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.suptitle('LOGOALGORITHM Discovery Dashboard', fontsize=18, fontweight='bold', y=0.98)
        
        # Panel 1: Discovery Type Distribution (Pie Chart)
        ax1 = axes[0, 0]
        summary = self.simulator.get_discovery_summary()
        types = ['Base Metabolism', 'Bio-Communication', 'Geo-Anomaly']
        counts = [summary['base_metabolism'], summary['bio_communication'], summary['geo_anomaly']]
        colors = ['#3498db', '#2ecc71', '#e67e22']
        
        wedges, texts, autotexts = ax1.pie(
            counts, labels=types, autopct='%1.1f%%', colors=colors, startangle=90
        )
        ax1.set_title('Discovery Type Distribution', fontweight='bold', fontsize=12)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        # Panel 2: Confidence Score Timeline
        ax2 = axes[0, 1]
        recent_events = self.simulator.discovery_history[-self.window_size:]
        confidence_scores = [e.confidence_score for e in recent_events]
        event_indices = list(range(len(recent_events)))
        
        colors_by_type = [
            '#3498db' if e.detected_phenomenon == DiscoveryType.BASE_METABOLISM else
            '#2ecc71' if e.detected_phenomenon == DiscoveryType.BIO_COMMUNICATION else
            '#e67e22' for e in recent_events
        ]
        
        ax2.bar(event_indices, confidence_scores, color=colors_by_type, alpha=0.7, edgecolor='black')
        ax2.axhline(y=50, color='red', linestyle='--', linewidth=2, label='High Confidence Threshold')
        ax2.set_xlabel('Event Index', fontweight='bold')
        ax2.set_ylabel('Confidence Score (%)', fontweight='bold')
        ax2.set_title('Confidence Scores (Recent Events)', fontweight='bold', fontsize=12)
        ax2.set_ylim([0, 105])
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # Panel 3: Signal Pattern Heatmap
        ax3 = axes[0, 2]
        recent_patterns = [self._parse_signal_hash(e.signal_pattern_hash) for e in recent_events]
        if recent_patterns:
            pattern_matrix = np.array(recent_patterns).T
            im = ax3.imshow(pattern_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax3.set_xlabel('Event Index', fontweight='bold')
            ax3.set_ylabel('Signal Component', fontweight='bold')
            ax3.set_yticklabels(['Electric', 'VOC', 'nIR'])
            ax3.set_title('Signal Pattern Matrix', fontweight='bold', fontsize=12)
            plt.colorbar(im, ax=ax3, label='Signal Value')

        # Panel 4: Time Series - nIR Fluorescence Shift
        ax4 = axes[1, 0]
        nir_shifts = [e.fluorescence_shift_nm for e in recent_events]
        ax4.plot(event_indices, nir_shifts, marker='o', color='#9b59b6', linewidth=2, markersize=8)
        ax4.axhline(y=25, color='orange', linestyle='--', linewidth=2, label='Geo-Anomaly Threshold')
        ax4.axhline(y=-5, color='blue', linestyle='--', linewidth=2, label='Bio-Comm Threshold')
        ax4.fill_between(event_indices, -5, 25, alpha=0.1, color='gray')
        ax4.set_xlabel('Event Index', fontweight='bold')
        ax4.set_ylabel('nIR Fluorescence Shift (nm)', fontweight='bold')
        ax4.set_title('Fluorescence Dynamics', fontweight='bold', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # Panel 5: Cumulative Discovery Count
        ax5 = axes[1, 1]
        cumulative_base = []
        cumulative_bio = []
        cumulative_geo = []
        
        for i, event in enumerate(self.simulator.discovery_history):
            if event.detected_phenomenon == DiscoveryType.BASE_METABOLISM:
                cumulative_base.append(cumulative_base[-1] + 1 if cumulative_base else 1)
                cumulative_bio.append(cumulative_bio[-1] if cumulative_bio else 0)
                cumulative_geo.append(cumulative_geo[-1] if cumulative_geo else 0)
            elif event.detected_phenomenon == DiscoveryType.BIO_COMMUNICATION:
                cumulative_base.append(cumulative_base[-1] if cumulative_base else 0)
                cumulative_bio.append(cumulative_bio[-1] + 1 if cumulative_bio else 1)
                cumulative_geo.append(cumulative_geo[-1] if cumulative_geo else 0)
            else:
                cumulative_base.append(cumulative_base[-1] if cumulative_base else 0)
                cumulative_bio.append(cumulative_bio[-1] if cumulative_bio else 0)
                cumulative_geo.append(cumulative_geo[-1] + 1 if cumulative_geo else 1)
        
        event_range = list(range(len(self.simulator.discovery_history)))
        ax5.plot(event_range, cumulative_base, label='Base Metabolism', color='#3498db', linewidth=2)
        ax5.plot(event_range, cumulative_bio, label='Bio-Communication', color='#2ecc71', linewidth=2)
        ax5.plot(event_range, cumulative_geo, label='Geo-Anomaly', color='#e67e22', linewidth=2)
        ax5.set_xlabel('Event Timeline', fontweight='bold')
        ax5.set_ylabel('Cumulative Count', fontweight='bold')
        ax5.set_title('Discovery Accumulation Over Time', fontweight='bold', fontsize=12)
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # Panel 6: Summary Statistics Table
        ax6 = axes[1, 2]
        ax6.axis('off')
        
        summary_text = f"""
DISCOVERY SUMMARY
{'='*40}

Total Events: {summary['total']}
Avg Confidence: {summary['avg_confidence']}%

Discovery Breakdown:
  🔵 Base Metabolism: {summary['base_metabolism']}
  🟢 Bio-Communication: {summary['bio_communication']}
  🟠 Geological Anomalies: {summary['geo_anomaly']}

System Status: OPERATIONAL ✓
Last Event: {self.simulator.discovery_history[-1].timestamp}

Thresholds:
  • Electric Variance: ±15 mV
  • VOC Trend: 2.0 ppm/min
  • nIR Shift: ±25 nm
  • Geo Threshold: 2.5 mag
  • Bio Threshold: 1.5 mag
"""
        
        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Dashboard saved to: {output_path}")
        plt.close()

    def generate_discovery_timeline(self, output_path: str = "discovery_timeline.png") -> None:
        """
        Generate a detailed timeline visualization of discoveries.
        
        Args:
            output_path: Path to save the figure
        """
        if not self.simulator.discovery_history:
            print("[Dashboard] No discovery data available to visualize.")
            return

        fig, ax = plt.subplots(figsize=(16, 8))
        
        events = self.simulator.discovery_history
        y_positions = []
        colors = []
        labels = []
        sizes = []
        
        type_to_y = {
            DiscoveryType.BASE_METABOLISM: 0,
            DiscoveryType.BIO_COMMUNICATION: 1,
            DiscoveryType.GEO_ANOMALY: 2
        }
        
        type_colors = {
            DiscoveryType.BASE_METABOLISM: '#3498db',
            DiscoveryType.BIO_COMMUNICATION: '#2ecc71',
            DiscoveryType.GEO_ANOMALY: '#e67e22'
        }
        
        for i, event in enumerate(events):
            y_positions.append(type_to_y[event.detected_phenomenon])
            colors.append(type_colors[event.detected_phenomenon])
            sizes.append(event.confidence_score * 5)  # Scale for visibility
            
            # Add annotations for high-confidence events
            if event.confidence_score > 50:
                ax.annotate(
                    f"{event.confidence_score}%",
                    xy=(i, y_positions[-1]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    fontsize=8,
                    ha='center'
                )
        
        scatter = ax.scatter(range(len(events)), y_positions, s=sizes, c=colors, alpha=0.6, edgecolors='black', linewidth=1.5)
        
        ax.set_xlabel('Event Sequence', fontweight='bold', fontsize=12)
        ax.set_ylabel('Discovery Type', fontweight='bold', fontsize=12)
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(['Base Metabolism', 'Bio-Communication', 'Geo-Anomaly'])
        ax.set_title('LOGOALGORITHM Discovery Timeline', fontweight='bold', fontsize=14)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add legend
        blue_patch = mpatches.Patch(color='#3498db', label='Base Metabolism', alpha=0.6)
        green_patch = mpatches.Patch(color='#2ecc71', label='Bio-Communication', alpha=0.6)
        orange_patch = mpatches.Patch(color='#e67e22', label='Geo-Anomaly', alpha=0.6)
        ax.legend(handles=[blue_patch, green_patch, orange_patch], loc='upper right', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Timeline saved to: {output_path}")
        plt.close()

    def generate_signal_space_plot(self, output_path: str = "signal_space.png") -> None:
        """
        Generate 3D signal space visualization showing Electric, VOC, and nIR dimensions.
        
        Args:
            output_path: Path to save the figure
        """
        if not self.simulator.discovery_history:
            print("[Dashboard] No discovery data available to visualize.")
            return

        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        events = self.simulator.discovery_history
        
        # Extract signal components
        electric_signals = []
        voc_signals = []
        nir_signals = []
        colors = []
        
        type_colors = {
            DiscoveryType.BASE_METABOLISM: '#3498db',
            DiscoveryType.BIO_COMMUNICATION: '#2ecc71',
            DiscoveryType.GEO_ANOMALY: '#e67e22'
        }
        
        for event in events:
            signal_vector = self._parse_signal_hash(event.signal_pattern_hash)
            electric_signals.append(signal_vector[0])
            voc_signals.append(signal_vector[1])
            nir_signals.append(event.fluorescence_shift_nm / 10)  # Normalize
            colors.append(type_colors[event.detected_phenomenon])
        
        scatter = ax.scatter(
            electric_signals, voc_signals, nir_signals,
            c=colors, s=100, alpha=0.6, edgecolors='black', linewidth=1
        )
        
        ax.set_xlabel('Electric Signal (mV)', fontweight='bold')
        ax.set_ylabel('VOC Trend (ppm/min)', fontweight='bold')
        ax.set_zlabel('nIR Shift (nm/10)', fontweight='bold')
        ax.set_title('3D Signal Space (QCSA Projection)', fontweight='bold', fontsize=14)
        
        # Add legend
        blue_patch = mpatches.Patch(color='#3498db', label='Base Metabolism')
        green_patch = mpatches.Patch(color='#2ecc71', label='Bio-Communication')
        orange_patch = mpatches.Patch(color='#e67e22', label='Geo-Anomaly')
        ax.legend(handles=[blue_patch, green_patch, orange_patch], loc='upper left')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Signal space plot saved to: {output_path}")
        plt.close()

    def generate_confidence_heatmap(self, output_path: str = "confidence_heatmap.png") -> None:
        """
        Generate a heatmap showing confidence scores over time and discovery types.
        
        Args:
            output_path: Path to save the figure
        """
        if not self.simulator.discovery_history:
            print("[Dashboard] No discovery data available to visualize.")
            return

        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Create matrix: rows = discovery types, columns = events
        events = self.simulator.discovery_history
        types_order = [DiscoveryType.BASE_METABOLISM, DiscoveryType.BIO_COMMUNICATION, DiscoveryType.GEO_ANOMALY]
        type_names = ['Base Metabolism', 'Bio-Communication', 'Geo-Anomaly']
        
        heatmap_data = np.zeros((len(types_order), len(events)))
        
        for j, event in enumerate(events):
            i = types_order.index(event.detected_phenomenon)
            heatmap_data[i, j] = event.confidence_score
        
        im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto', vmin=0, vmax=100)
        
        ax.set_xlabel('Event Index', fontweight='bold', fontsize=12)
        ax.set_ylabel('Discovery Type', fontweight='bold', fontsize=12)
        ax.set_yticklabels(type_names)
        ax.set_title('Confidence Score Heatmap Over Discovery Events', fontweight='bold', fontsize=14)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Confidence (%)', fontweight='bold')
        
        # Add text annotations
        for i in range(len(types_order)):
            for j in range(len(events)):
                if heatmap_data[i, j] > 0:
                    text = ax.text(j, i, f'{int(heatmap_data[i, j])}',
                                  ha="center", va="center", color="black", fontsize=8)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Confidence heatmap saved to: {output_path}")
        plt.close()

    def print_dashboard_summary(self) -> None:
        """Print a text-based dashboard summary to console."""
        if not self.simulator.discovery_history:
            print("[Dashboard] No discovery data available.")
            return

        summary = self.simulator.get_discovery_summary()
        recent = self.simulator.discovery_history[-5:]
        
        print("\n" + "="*80)
        print(" "*20 + "LOGOALGORITHM DISCOVERY DASHBOARD")
        print("="*80)
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Events Processed: {summary['total']}")
        print(f"   Average Confidence: {summary['avg_confidence']}%")
        print(f"   System Status: OPERATIONAL ✓")
        
        print(f"\n🔍 DISCOVERY DISTRIBUTION:")
        print(f"   🔵 Base Metabolism Events: {summary['base_metabolism']} ({summary['base_metabolism']/summary['total']*100:.1f}%)")
        print(f"   🟢 Bio-Communication Events: {summary['bio_communication']} ({summary['bio_communication']/summary['total']*100:.1f}%)")
        print(f"   🟠 Geological Anomalies: {summary['geo_anomaly']} ({summary['geo_anomaly']/summary['total']*100:.1f}%)")
        
        print(f"\n📈 RECENT EVENTS:")
        for i, event in enumerate(recent, 1):
            emoji = "🔵" if event.detected_phenomenon == DiscoveryType.BASE_METABOLISM else \
                    "🟢" if event.detected_phenomenon == DiscoveryType.BIO_COMMUNICATION else "🟠"
            print(f"   [{i}] {emoji} {event.detected_phenomenon.name} | Confidence: {event.confidence_score}% | {event.timestamp}")
        
        print(f"\n⚙️ THRESHOLD CONFIGURATION:")
        config = self.simulator.threshold_config
        print(f"   Electric Variance: {config['elec_variance_low']} to {config['elec_variance_high']} mV")
        print(f"   VOC Trend: > {config['voc_trend_threshold']} ppm/min")
        print(f"   nIR Shift: {config['nir_shift_low']} to {config['nir_shift_high']} nm")
        print(f"   Geo-Anomaly Magnitude Threshold: > {config['magnitude_geo_threshold']}")
        print(f"   Bio-Communication Magnitude Threshold: > {config['magnitude_bio_threshold']}")
        
        print("\n" + "="*80 + "\n")

    def _parse_signal_hash(self, signal_hash: str) -> List[int]:
        """
        Parse signal pattern hash string back to signal vector.
        
        Args:
            signal_hash: Hash string in format "PH-ABC" where A, B, C are signal values
            
        Returns:
            List of signal values [electric, voc, nir]
        """
        try:
            # Remove "PH-" prefix and convert to integers
            values_str = signal_hash.replace("PH-", "")
            return [int(v) if v in '-01' else 0 for v in values_str]
        except:
            return [0, 0, 0]


# =====================================================================
# EXAMPLE USAGE
# =====================================================================
if __name__ == "__main__":
    from plant_discovery_simulator import PlantDiscoverySimulator
    
    # Create simulator and generate sample data
    simulator = PlantDiscoverySimulator()
    
    scenarios = [
        {"name": "Standard greenhouse signals", "elec": 2.0, "voc": 0.1, "nir": 0.0},
        {"name": "Network electrical wave", "elec": -18.5, "voc": 2.5, "nir": 2.0},
        {"name": "nIR fluorescence shift", "elec": 5.0, "voc": 2.8, "nir": 32.4},
        {"name": "Baseline 1", "elec": 1.5, "voc": 0.05, "nir": -1.0},
        {"name": "Bio-communication pulse", "elec": -20.0, "voc": 3.0, "nir": 5.0},
    ]
    
    print("🔬 Generating sample discovery data...\n")
    results = simulator.batch_analyze(scenarios)
    
    # Create dashboard
    dashboard = DiscoveryDashboard(simulator)
    
    # Generate all visualizations
    print("\n📊 Generating visualizations...\n")
    dashboard.generate_static_report("discovery_dashboard.png")
    dashboard.generate_discovery_timeline("discovery_timeline.png")
    dashboard.generate_signal_space_plot("signal_space_3d.png")
    dashboard.generate_confidence_heatmap("confidence_heatmap.png")
    
    # Print text summary
    dashboard.print_dashboard_summary()
    
    print("✅ All dashboard visualizations complete!")
