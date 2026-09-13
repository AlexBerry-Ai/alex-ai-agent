"""
test_discovery_suite.py
Comprehensive test suite for all discovery modules.
Includes unit tests, integration tests, performance tests, and fixtures.
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
import numpy as np
from typing import List

from plant_discovery_simulator import (
    PlantDiscoverySimulator, DiscoveryType, DiscoveryEvent
)
from discovery_database import DiscoveryDatabase, DatabaseBackend
from discovery_dashboard import DiscoveryDashboard
from realtime_discovery_streamer import RealTimeDiscoveryStreamer, EventBuffer, PerformanceMetrics


class TestDiscoverySimulator(unittest.TestCase):
    """Unit tests for PlantDiscoverySimulator."""
    
    def setUp(self):
        self.simulator = PlantDiscoverySimulator()
    
    def test_initialization(self):
        """Test simulator initialization."""
        self.assertIsNotNone(self.simulator.state_matrix)
        self.assertEqual(self.simulator.state_matrix.shape, (3, 3))
        self.assertEqual(len(self.simulator.discovery_history), 0)
    
    def test_base_metabolism_detection(self):
        """Test detection of base metabolism (no discovery)."""
        event = self.simulator.analyze_anomalous_stream(2.0, 0.1, 0.0)
        self.assertEqual(event.detected_phenomenon, DiscoveryType.BASE_METABOLISM)
        self.assertLess(event.confidence_score, 50)
    
    def test_bio_communication_detection(self):
        """Test detection of bio-communication anomaly."""
        event = self.simulator.analyze_anomalous_stream(-18.5, 2.5, 2.0)
        self.assertEqual(event.detected_phenomenon, DiscoveryType.BIO_COMMUNICATION)
        self.assertGreater(event.confidence_score, 50)
    
    def test_geo_anomaly_detection(self):
        """Test detection of geological anomaly."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        self.assertEqual(event.detected_phenomenon, DiscoveryType.GEO_ANOMALY)
        self.assertGreater(event.confidence_score, 50)
    
    def test_batch_analysis(self):
        """Test batch analysis of multiple scenarios."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        results = self.simulator.batch_analyze(scenarios)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(self.simulator.discovery_history), 3)
    
    def test_confidence_scoring(self):
        """Test confidence score calculation."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        self.assertGreaterEqual(event.confidence_score, 0)
        self.assertLessEqual(event.confidence_score, 100)
    
    def test_signal_pattern_hash(self):
        """Test signal pattern hash generation."""
        event = self.simulator.analyze_anomalous_stream(2.0, 0.1, 0.0)
        self.assertIsNotNone(event.signal_pattern_hash)
        self.assertTrue(event.signal_pattern_hash.startswith("PH-"))
    
    def test_threshold_boundaries(self):
        """Test threshold boundary conditions."""
        # Just below high threshold
        event1 = self.simulator.analyze_anomalous_stream(14.9, 0.1, 0.0)
        self.assertEqual(event1.detected_phenomenon, DiscoveryType.BASE_METABOLISM)
        
        # Just above high threshold
        event2 = self.simulator.analyze_anomalous_stream(15.1, 0.1, 0.0)
        # Should trigger signal change
        self.assertNotEqual(event1.signal_pattern_hash, event2.signal_pattern_hash)
    
    def test_discovery_history_growth(self):
        """Test that discovery history grows correctly."""
        initial_count = len(self.simulator.discovery_history)
        self.simulator.analyze_anomalous_stream(2.0, 0.1, 0.0)
        self.assertEqual(len(self.simulator.discovery_history), initial_count + 1)
    
    def test_get_discovery_summary(self):
        """Test summary statistics generation."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        self.simulator.batch_analyze(scenarios)
        summary = self.simulator.get_discovery_summary()
        
        self.assertEqual(summary['total'], 3)
        self.assertGreater(summary['avg_confidence'], 0)
        self.assertIn('base_metabolism', summary)
        self.assertIn('bio_communication', summary)
        self.assertIn('geo_anomaly', summary)


class TestDiscoveryDatabase(unittest.TestCase):
    """Unit tests for DiscoveryDatabase."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.db = DiscoveryDatabase(DatabaseBackend.SQLITE, self.db_path)
        self.simulator = PlantDiscoverySimulator()
    
    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test database schema creation."""
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cursor)
    
    def test_insert_single_event(self):
        """Test inserting a single event."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        event_id = self.db.insert_event(event)
        self.assertIsNotNone(event_id)
        self.assertGreater(event_id, 0)
    
    def test_insert_batch_events(self):
        """Test batch insertion of events."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        events = self.simulator.batch_analyze(scenarios)
        ids = self.db.insert_batch(events)
        self.assertEqual(len(ids), 3)
    
    def test_get_event_by_id(self):
        """Test retrieving event by ID."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        event_id = self.db.insert_event(event)
        retrieved = self.db.get_event(event_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.fluorescence_shift_nm, event.fluorescence_shift_nm)
        self.assertEqual(retrieved.confidence_score, event.confidence_score)
    
    def test_get_by_type(self):
        """Test retrieving events by type."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},      # Base
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},    # Bio
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},     # Geo
        ]
        events = self.simulator.batch_analyze(scenarios)
        self.db.insert_batch(events)
        
        geo_events = self.db.get_by_type(DiscoveryType.GEO_ANOMALY)
        self.assertGreater(len(geo_events), 0)
    
    def test_get_by_confidence_range(self):
        """Test retrieving events by confidence range."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        events = self.simulator.batch_analyze(scenarios)
        self.db.insert_batch(events)
        
        high_conf = self.db.get_by_confidence_range(50.0, 100.0)
        self.assertGreater(len(high_conf), 0)
        
        for event in high_conf:
            self.assertGreaterEqual(event.confidence_score, 50.0)
            self.assertLessEqual(event.confidence_score, 100.0)
    
    def test_get_statistics(self):
        """Test statistics generation."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        events = self.simulator.batch_analyze(scenarios)
        self.db.insert_batch(events)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_events'], 3)
        self.assertIsNotNone(stats['avg_confidence'])
        self.assertIsNotNone(stats['min_confidence'])
        self.assertIsNotNone(stats['max_confidence'])
    
    def test_export_to_json(self):
        """Test exporting events to JSON."""
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
        ]
        events = self.simulator.batch_analyze(scenarios)
        self.db.insert_batch(events)
        
        export_path = tempfile.mktemp(suffix='.json')
        self.db.export_to_json(export_path)
        
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
        
        os.unlink(export_path)
    
    def test_backup(self):
        """Test database backup."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        self.db.insert_event(event)
        
        backup_path = tempfile.mktemp(suffix='.db')
        self.db.backup(backup_path)
        
        self.assertTrue(os.path.exists(backup_path))
        os.unlink(backup_path)


class TestEventBuffer(unittest.TestCase):
    """Unit tests for EventBuffer."""
    
    def setUp(self):
        self.buffer = EventBuffer(max_size=10)
        self.simulator = PlantDiscoverySimulator()
    
    def test_buffer_initialization(self):
        """Test buffer initialization."""
        self.assertEqual(len(self.buffer.buffer), 0)
    
    def test_add_event(self):
        """Test adding event to buffer."""
        event = self.simulator.analyze_anomalous_stream(5.0, 2.8, 32.4)
        self.buffer.add_event(event)
        self.assertEqual(len(self.buffer.buffer), 1)
    
    def test_buffer_max_size(self):
        """Test buffer max size enforcement."""
        small_buffer = EventBuffer(max_size=3)
        simulator = PlantDiscoverySimulator()
        
        for i in range(5):
            event = simulator.analyze_anomalous_stream(2.0 + i, 0.1, 0.0)
            small_buffer.add_event(event)
        
        self.assertEqual(len(small_buffer.buffer), 3)
    
    def test_get_batch(self):
        """Test batch retrieval."""
        events = [self.simulator.analyze_anomalous_stream(2.0 + i, 0.1, 0.0) for i in range(3)]
        for event in events:
            self.buffer.add_event(event)
        
        batch = self.buffer.get_batch(timeout=0.05)
        self.assertEqual(len(batch), 3)


class TestPerformanceMetrics(unittest.TestCase):
    """Unit tests for PerformanceMetrics."""
    
    def setUp(self):
        self.metrics = PerformanceMetrics(window_size=10)
    
    def test_fps_calculation(self):
        """Test FPS calculation."""
        for _ in range(3):
            self.metrics.record_frame(1)
            time.sleep(0.01)
        
        fps = self.metrics.get_fps()
        self.assertGreater(fps, 0)
    
    def test_get_summary(self):
        """Test metrics summary."""
        for i in range(5):
            self.metrics.record_frame(i + 1)
        
        summary = self.metrics.get_summary()
        self.assertIn('fps', summary)
        self.assertIn('avg_events_per_frame', summary)
        self.assertIn('total_frames', summary)
        self.assertIn('runtime_seconds', summary)


class TestIntegration(unittest.TestCase):
    """Integration tests across modules."""
    
    def setUp(self):
        self.simulator = PlantDiscoverySimulator()
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.db = DiscoveryDatabase(DatabaseBackend.SQLITE, self.db_path)
    
    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_simulator_to_database_pipeline(self):
        """Test full pipeline: simulate -> store -> retrieve."""
        # Generate events
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
            {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        ]
        events = self.simulator.batch_analyze(scenarios)
        
        # Store events
        ids = self.db.insert_batch(events)
        self.assertEqual(len(ids), 3)
        
        # Retrieve and verify
        all_events = self.db.get_all_events()
        self.assertEqual(len(all_events), 3)
        
        # Verify data integrity
        for original, retrieved in zip(events, all_events):
            self.assertEqual(original.confidence_score, retrieved.confidence_score)
            self.assertEqual(original.detected_phenomenon, retrieved.detected_phenomenon)
    
    def test_simulator_to_streamer_pipeline(self):
        """Test integration of simulator and streamer."""
        streamer = RealTimeDiscoveryStreamer(self.simulator, history_size=10)
        
        # Generate and buffer events
        scenarios = [
            {"elec": 2.0, "voc": 0.1, "nir": 0.0},
            {"elec": -18.5, "voc": 2.5, "nir": 2.0},
        ]
        events = self.simulator.batch_analyze(scenarios)
        
        for event in events:
            streamer.event_buffer.add_event(event)
        
        # Retrieve from buffer
        batch = streamer.event_buffer.get_batch(timeout=0.05)
        self.assertEqual(len(batch), 2)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.simulator = PlantDiscoverySimulator()
    
    def test_extreme_values(self):
        """Test with extreme input values."""
        event = self.simulator.analyze_anomalous_stream(-1000.0, 1000.0, 1000.0)
        self.assertIsNotNone(event)
        self.assertGreaterEqual(event.confidence_score, 0)
        self.assertLessEqual(event.confidence_score, 100)
    
    def test_zero_values(self):
        """Test with zero input values."""
        event = self.simulator.analyze_anomalous_stream(0.0, 0.0, 0.0)
        self.assertIsNotNone(event)
        self.assertEqual(event.detected_phenomenon, DiscoveryType.BASE_METABOLISM)
    
    def test_boundary_values(self):
        """Test at exact threshold boundaries."""
        # Exactly at high threshold
        event = self.simulator.analyze_anomalous_stream(15.0, 2.0, 25.0)
        self.assertIsNotNone(event)
    
    def test_negative_confidence(self):
        """Ensure confidence is never negative."""
        for _ in range(10):
            event = self.simulator.analyze_anomalous_stream(-100.0, -100.0, -100.0)
            self.assertGreaterEqual(event.confidence_score, 0)


class TestPerformance(unittest.TestCase):
    """Performance and load testing."""
    
    def setUp(self):
        self.simulator = PlantDiscoverySimulator()
    
    def test_batch_processing_performance(self):
        """Test performance of batch processing."""
        scenarios = [{"elec": 2.0 + i % 3, "voc": 0.1, "nir": 0.0} for i in range(100)]
        
        start_time = time.time()
        self.simulator.batch_analyze(scenarios)
        elapsed = time.time() - start_time
        
        # Should process 100 events in less than 1 second
        self.assertLess(elapsed, 1.0)
        print(f"Processed 100 events in {elapsed:.3f}s")
    
    def test_database_query_performance(self):
        """Test database query performance."""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_db.name
        temp_db.close()
        
        try:
            db = DiscoveryDatabase(DatabaseBackend.SQLITE, db_path)
            
            # Insert 100 events
            scenarios = [{"elec": 2.0 + i % 3, "voc": 0.1, "nir": 0.0} for i in range(100)]
            events = self.simulator.batch_analyze(scenarios)
            db.insert_batch(events)
            
            # Time a query
            start_time = time.time()
            db.get_all_events()
            elapsed = time.time() - start_time
            
            # Should query 100 events in less than 0.1 seconds
            self.assertLess(elapsed, 0.1)
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
