"""
RealTimeDiscoveryStreamer v1.0
Live streaming and animation of plant discovery events.
Real-time visualization with animated updates and data buffering.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
import numpy as np
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional, Callable, Tuple
import threading
import time
from queue import Queue, Empty

from plant_discovery_simulator import PlantDiscoverySimulator, DiscoveryType, DiscoveryEvent


class EventBuffer:
    """Thread-safe buffer for incoming discovery events."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize event buffer.
        
        Args:
            max_size: Maximum number of events to buffer
        """
        self.buffer = deque(maxlen=max_size)
        self.queue = Queue()
        self.lock = threading.Lock()
    
    def add_event(self, event: DiscoveryEvent) -> None:
        """Add event to buffer and queue."""
        with self.lock:
            self.buffer.append(event)
            self.queue.put(event)
    
    def get_batch(self, timeout: float = 0.1) -> List[DiscoveryEvent]:
        """Get all queued events (non-blocking)."""
        batch = []
        while True:
            try:
                event = self.queue.get(timeout=timeout)
                batch.append(event)
            except Empty:
                break
        return batch
    
    def get_recent(self, count: int) -> List[DiscoveryEvent]:
        """Get most recent N events."""
        with self.lock:
            return list(self.buffer)[-count:]
    
    def clear(self) -> None:
        """Clear all buffers."""
        with self.lock:
            self.buffer.clear()
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    break


class PerformanceMetrics:
    """Track streaming performance metrics."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics tracker.
        
        Args:
            window_size: Number of frames to average over
        """
        self.frame_times = deque(maxlen=window_size)
        self.event_counts = deque(maxlen=window_size)
        self.start_time = time.time()
    
    def record_frame(self, events_processed: int) -> None:
        """Record frame timing and event count."""
        current_time = time.time()
        frame_time = current_time - (self.start_time if not self.frame_times else self.start_time)
        self.frame_times.append(frame_time)
        self.event_counts.append(events_processed)
        self.start_time = current_time
    
    def get_fps(self) -> float:
        """Calculate frames per second."""
        if not self.frame_times:
            return 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_avg_events_per_frame(self) -> float:
        """Get average events processed per frame."""
        if not self.event_counts:
            return 0.0
        return sum(self.event_counts) / len(self.event_counts)
    
    def get_summary(self) -> Dict[str, float]:
        """Get metrics summary."""
        return {
            'fps': self.get_fps(),
            'avg_events_per_frame': self.get_avg_events_per_frame(),
            'total_frames': len(self.frame_times),
            'runtime_seconds': time.time() - self.start_time
        }


class RealTimeDiscoveryStreamer:
    """Real-time streaming and animation of discovery events."""
    
    def __init__(self, simulator: PlantDiscoverySimulator, history_size: int = 50):
        """
        Initialize the real-time streamer.
        
        Args:
            simulator: PlantDiscoverySimulator instance
            history_size: Number of recent events to keep in rolling window
        """
        self.simulator = simulator
        self.history_size = history_size
        self.event_buffer = EventBuffer(max_size=1000)
        self.metrics = PerformanceMetrics()
        self.running = False
        self.animation = None
        
        # Data tracking
        self.event_history = deque(maxlen=history_size)
        self.timestamp_history = deque(maxlen=history_size)
        self.confidence_history = deque(maxlen=history_size)
        self.type_history = deque(maxlen=history_size)
        self.signal_history = deque(maxlen=history_size)
        
        # Color mapping
        self.type_colors = {
            DiscoveryType.BASE_METABOLISM: '#3498db',
            DiscoveryType.BIO_COMMUNICATION: '#2ecc71',
            DiscoveryType.GEO_ANOMALY: '#e67e22'
        }
        
        self.type_labels = {
            DiscoveryType.BASE_METABOLISM: '🔵 Base',
            DiscoveryType.BIO_COMMUNICATION: '🟢 Bio-Comm',
            DiscoveryType.GEO_ANOMALY: '🟠 Geo'
        }

    def stream_events(self, event_generator: Callable, interval_ms: int = 1000) -> None:
        """
        Stream events from generator at specified intervals.
        
        Args:
            event_generator: Function that yields DiscoveryEvent objects
            interval_ms: Milliseconds between event generation
        """
        def generator_thread():
            try:
                for event in event_generator():
                    if not self.running:
                        break
                    self.event_buffer.add_event(event)
                    time.sleep(interval_ms / 1000.0)
            except Exception as e:
                print(f"[Error] Event generator failed: {e}")
        
        thread = threading.Thread(target=generator_thread, daemon=True)
        thread.start()

    def create_animated_dashboard(self, output_path: Optional[str] = None, 
                                 interval_ms: int = 500, num_frames: int = 100) -> None:
        """
        Create animated dashboard with real-time updates.
        
        Args:
            output_path: Optional path to save animation as MP4
            interval_ms: Update interval in milliseconds
            num_frames: Number of animation frames to generate
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('LOGOALGORITHM Real-Time Discovery Stream', fontsize=16, fontweight='bold')
        
        # Panel 1: Timeline
        ax_timeline = axes[0, 0]
        
        # Panel 2: Confidence Timeline
        ax_confidence = axes[0, 1]
        
        # Panel 3: Signal Pattern
        ax_signal = axes[1, 0]
        
        # Panel 4: Metrics
        ax_metrics = axes[1, 1]
        ax_metrics.axis('off')
        
        # Initialize plot elements
        scatter_timeline = ax_timeline.scatter([], [], s=100, alpha=0.6, edgecolors='black', linewidth=1)
        line_confidence, = ax_confidence.plot([], [], lw=2, color='#9b59b6')
        heatmap_data = np.zeros((3, self.history_size))
        im_signal = ax_signal.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
        
        # Setup axes
        ax_timeline.set_xlabel('Event Index', fontweight='bold')
        ax_timeline.set_ylabel('Discovery Type', fontweight='bold')
        ax_timeline.set_yticks([0, 1, 2])
        ax_timeline.set_yticklabels(['Base', 'Bio-Comm', 'Geo'])
        ax_timeline.set_ylim(-0.5, 2.5)
        ax_timeline.set_xlim(-1, self.history_size)
        ax_timeline.grid(True, alpha=0.3)
        
        ax_confidence.set_xlabel('Event Index', fontweight='bold')
        ax_confidence.set_ylabel('Confidence Score (%)', fontweight='bold')
        ax_confidence.set_ylim(0, 105)
        ax_confidence.set_xlim(-1, self.history_size)
        ax_confidence.grid(True, alpha=0.3)
        ax_confidence.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Threshold')
        ax_confidence.legend()
        
        ax_signal.set_xlabel('Event Index', fontweight='bold')
        ax_signal.set_ylabel('Signal Component', fontweight='bold')
        ax_signal.set_yticklabels(['Electric', 'VOC', 'nIR'])
        
        # Initialize text elements
        text_status = ax_metrics.text(0.05, 0.95, '', transform=ax_metrics.transAxes,
                                     fontsize=10, verticalalignment='top', fontfamily='monospace',
                                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        def update_animation(frame):
            """Update animation frame."""
            self.running = True
            
            # Get new events from buffer
            new_events = self.event_buffer.get_batch()
            
            # Add events to history
            for event in new_events:
                self.event_history.append(event)
                self.timestamp_history.append(event.timestamp)
                self.confidence_history.append(event.confidence_score)
                self.type_history.append(event.detected_phenomenon)
                signal_vec = self._parse_signal_hash(event.signal_pattern_hash)
                self.signal_history.append(signal_vec)
            
            # Record metrics
            self.metrics.record_frame(len(new_events))
            
            # Update Timeline (Panel 1)
            if self.event_history:
                event_indices = list(range(len(self.event_history)))
                type_indices = [0 if t == DiscoveryType.BASE_METABOLISM else
                               1 if t == DiscoveryType.BIO_COMMUNICATION else 2
                               for t in self.type_history]
                colors = [self.type_colors[t] for t in self.type_history]
                
                ax_timeline.clear()
                ax_timeline.scatter(event_indices, type_indices, s=100, c=colors, alpha=0.6, 
                                   edgecolors='black', linewidth=1)
                ax_timeline.set_xlabel('Event Index', fontweight='bold')
                ax_timeline.set_ylabel('Discovery Type', fontweight='bold')
                ax_timeline.set_yticks([0, 1, 2])
                ax_timeline.set_yticklabels(['Base', 'Bio-Comm', 'Geo'])
                ax_timeline.set_ylim(-0.5, 2.5)
                ax_timeline.set_xlim(-1, max(len(self.event_history), 10))
                ax_timeline.grid(True, alpha=0.3)
                ax_timeline.set_title(f'Timeline ({len(self.event_history)} events)', fontweight='bold')
            
            # Update Confidence (Panel 2)
            if self.confidence_history:
                event_indices = list(range(len(self.confidence_history)))
                ax_confidence.clear()
                ax_confidence.plot(event_indices, list(self.confidence_history), lw=2, 
                                  color='#9b59b6', marker='o', markersize=6)
                ax_confidence.axhline(y=50, color='red', linestyle='--', alpha=0.5, linewidth=1)
                ax_confidence.fill_between(event_indices, 50, 105, alpha=0.1, color='red')
                ax_confidence.set_xlabel('Event Index', fontweight='bold')
                ax_confidence.set_ylabel('Confidence Score (%)', fontweight='bold')
                ax_confidence.set_ylim(0, 105)
                ax_confidence.set_xlim(-1, max(len(self.confidence_history), 10))
                ax_confidence.grid(True, alpha=0.3)
                ax_confidence.set_title(f'Confidence Trend (Avg: {np.mean(list(self.confidence_history)):.1f}%)', 
                                      fontweight='bold')
            
            # Update Signal Heatmap (Panel 3)
            if self.signal_history:
                heatmap = np.zeros((3, len(self.signal_history)))
                for j, signal in enumerate(self.signal_history):
                    heatmap[:, j] = signal
                
                ax_signal.clear()
                ax_signal.imshow(heatmap, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
                ax_signal.set_xlabel('Event Index', fontweight='bold')
                ax_signal.set_ylabel('Signal Component', fontweight='bold')
                ax_signal.set_yticklabels(['Electric', 'VOC', 'nIR'])
                ax_signal.set_title(f'Signal Heatmap ({len(self.signal_history)} events)', fontweight='bold')
            
            # Update Metrics (Panel 4)
            metrics = self.metrics.get_summary()
            status_text = f"""
STREAMING METRICS
{'='*35}
FPS: {metrics['fps']:.1f}
Events/Frame: {metrics['avg_events_per_frame']:.2f}
Total Frames: {int(metrics['total_frames'])}
Runtime: {metrics['runtime_seconds']:.1f}s

DISCOVERY STATUS
{'='*35}
Events Buffered: {len(self.event_history)}
Avg Confidence: {np.mean(list(self.confidence_history)):.1f}% if self.confidence_history else 0
Last Event: {self.event_history[-1].detected_phenomenon.name if self.event_history else 'None'}

STREAM STATE
{'='*35}
Status: {'🟢 LIVE' if self.running else '🔴 STOPPED'}
Buffer Fill: {len(self.event_history)}/{self.history_size}
"""
            text_status.set_text(status_text)
            
            return []
        
        # Create animation
        self.animation = animation.FuncAnimation(
            fig, update_animation, frames=num_frames,
            interval=interval_ms, blit=False, repeat=True
        )
        
        plt.tight_layout()
        
        if output_path:
            try:
                self.animation.save(output_path, writer='ffmpeg', fps=30)
                print(f"✅ Animation saved to: {output_path}")
            except Exception as e:
                print(f"⚠️ Could not save animation: {e}")
        
        plt.show()

    def start_live_feed(self, update_interval_ms: int = 500) -> None:
        """
        Start live streaming feed with console output.
        
        Args:
            update_interval_ms: Interval between feed updates
        """
        print("\n" + "="*80)
        print(" "*20 + "LOGOALGORITHM LIVE DISCOVERY FEED")
        print("="*80)
        print("\n[Stream Starting] Press Ctrl+C to stop\n")
        
        self.running = True
        frame_count = 0
        
        try:
            while self.running:
                # Get new events
                new_events = self.event_buffer.get_batch()
                
                if new_events:
                    frame_count += 1
                    
                    for event in new_events:
                        self.event_history.append(event)
                        self.confidence_history.append(event.confidence_score)
                        self.type_history.append(event.detected_phenomenon)
                    
                    self.metrics.record_frame(len(new_events))
                    
                    # Print feed
                    print(f"\n[Frame {frame_count}] {datetime.now().strftime('%H:%M:%S')} | "
                          f"FPS: {self.metrics.get_fps():.1f}")
                    
                    for event in new_events:
                        emoji = self.type_labels[event.detected_phenomenon]
                        print(f"  → {emoji} | Conf: {event.confidence_score:>6.2f}% | "
                              f"nIR: {event.fluorescence_shift_nm:>7.2f}nm | "
                              f"{event.timestamp}")
                    
                    # Print summary every 5 events
                    if len(self.event_history) % 5 == 0:
                        print(f"\n  Summary: {len(self.event_history)} events | "
                              f"Avg Confidence: {np.mean(list(self.confidence_history)):.1f}% | "
                              f"Events/sec: {self.metrics.get_avg_events_per_frame():.2f}")
                
                time.sleep(update_interval_ms / 1000.0)
        
        except KeyboardInterrupt:
            print("\n\n[Stream Stopped] Finalizing...\n")
            self.running = False
            self._print_final_summary()

    def _print_final_summary(self) -> None:
        """Print final summary statistics."""
        if not self.event_history:
            return
        
        summary = {
            'base': sum(1 for t in self.type_history if t == DiscoveryType.BASE_METABOLISM),
            'bio': sum(1 for t in self.type_history if t == DiscoveryType.BIO_COMMUNICATION),
            'geo': sum(1 for t in self.type_history if t == DiscoveryType.GEO_ANOMALY),
        }
        
        print("="*80)
        print(" "*25 + "STREAM SESSION SUMMARY")
        print("="*80)
        print(f"\nTotal Events Processed: {len(self.event_history)}")
        print(f"Average Confidence: {np.mean(list(self.confidence_history)):.2f}%")
        print(f"\nDiscovery Breakdown:")
        print(f"  🔵 Base Metabolism: {summary['base']} ({summary['base']/len(self.event_history)*100:.1f}%)")
        print(f"  🟢 Bio-Communication: {summary['bio']} ({summary['bio']/len(self.event_history)*100:.1f}%)")
        print(f"  🟠 Geological Anomalies: {summary['geo']} ({summary['geo']/len(self.event_history)*100:.1f}%)")
        
        metrics = self.metrics.get_summary()
        print(f"\nPerformance Metrics:")
        print(f"  Average FPS: {metrics['fps']:.2f}")
        print(f"  Events per Frame: {metrics['avg_events_per_frame']:.2f}")
        print(f"  Total Frames: {int(metrics['total_frames'])}")
        print(f"  Total Runtime: {metrics['runtime_seconds']:.2f}s")
        print("\n" + "="*80 + "\n")

    def _parse_signal_hash(self, signal_hash: str) -> List[int]:
        """Parse signal hash to vector."""
        try:
            values_str = signal_hash.replace("PH-", "")
            return [int(v) if v in '-01' else 0 for v in values_str]
        except:
            return [0, 0, 0]


# =====================================================================
# EXAMPLE USAGE
# =====================================================================
if __name__ == "__main__":
    import random
    
    # Create simulator
    simulator = PlantDiscoverySimulator()
    
    # Create streamer
    streamer = RealTimeDiscoveryStreamer(simulator, history_size=50)
    
    # Define event generator
    def event_generator():
        """Generate simulated discovery events."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
            {"elec": 1.5, "voc": 0.05, "nir": -1.0},
            {"elec": -20.0, "voc": 3.0, "nir": 5.0},
            {"elec": 3.5, "voc": 1.2, "nir": 10.0},
        ]
        
        for i in range(20):  # Generate 20 events
            scenario = random.choice(scenarios)
            event = simulator.analyze_anomalous_stream(
                scenario["elec"], scenario["voc"], scenario["nir"]
            )
            yield event
    
    # Start streaming
    print("🔴 Starting real-time discovery stream...\n")
    
    # Option 1: Live console feed
    streamer.stream_events(event_generator, interval_ms=800)
    streamer.start_live_feed(update_interval_ms=1000)
    
    # Option 2: Animated dashboard (uncomment to use)
    # streamer.create_animated_dashboard(
    #     output_path="discovery_stream_animation.mp4",
    #     interval_ms=500,
    #     num_frames=100
    # )
