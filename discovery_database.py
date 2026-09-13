"""
DiscoveryDatabase v1.0
Persistent storage and retrieval of plant discovery events.
Supports SQLite and PostgreSQL backends with query interface.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import asdict
from enum import Enum
import os

from plant_discovery_simulator import DiscoveryEvent, DiscoveryType


class DatabaseBackend(Enum):
    """Supported database backends."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DiscoveryDatabase:
    """Database abstraction for persistent discovery storage."""
    
    def __init__(self, backend: DatabaseBackend = DatabaseBackend.SQLITE, 
                 connection_string: str = "discoveries.db"):
        """
        Initialize database connection.
        
        Args:
            backend: Database backend type
            connection_string: SQLite path or PostgreSQL connection string
        """
        self.backend = backend
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
        
        self._connect()
        self._initialize_schema()
    
    def _connect(self) -> None:
        """Establish database connection."""
        if self.backend == DatabaseBackend.SQLITE:
            self.conn = sqlite3.connect(self.connection_string)
            self.cursor = self.conn.cursor()
        elif self.backend == DatabaseBackend.POSTGRESQL:
            try:
                import psycopg2
                self.conn = psycopg2.connect(self.connection_string)
                self.cursor = self.conn.cursor()
            except ImportError:
                raise ImportError("psycopg2 required for PostgreSQL support: pip install psycopg2-binary")
    
    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        if self.backend == DatabaseBackend.SQLITE:
            sql = """
            CREATE TABLE IF NOT EXISTS discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                signal_pattern_hash TEXT NOT NULL,
                fluorescence_shift_nm REAL NOT NULL,
                discovered_phenomenon INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                action_required TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_timestamp ON discoveries(timestamp);
            CREATE INDEX IF NOT EXISTS idx_phenomenon ON discoveries(discovered_phenomenon);
            CREATE INDEX IF NOT EXISTS idx_confidence ON discoveries(confidence_score);
            """
            for statement in sql.split(';'):
                if statement.strip():
                    self.cursor.execute(statement)
            self.conn.commit()
        
        elif self.backend == DatabaseBackend.POSTGRESQL:
            sql = """
            CREATE TABLE IF NOT EXISTS discoveries (
                id SERIAL PRIMARY KEY,
                timestamp TEXT NOT NULL,
                signal_pattern_hash TEXT NOT NULL,
                fluorescence_shift_nm REAL NOT NULL,
                discovered_phenomenon INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                action_required TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_timestamp ON discoveries(timestamp);
            CREATE INDEX IF NOT EXISTS idx_phenomenon ON discoveries(discovered_phenomenon);
            CREATE INDEX IF NOT EXISTS idx_confidence ON discoveries(confidence_score);
            """
            try:
                self.cursor.execute(sql)
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                # Table might already exist
                pass
    
    def insert_event(self, event: DiscoveryEvent) -> int:
        """
        Insert a discovery event into the database.
        
        Args:
            event: DiscoveryEvent to store
            
        Returns:
            ID of inserted record
        """
        sql = """
        INSERT INTO discoveries 
        (timestamp, signal_pattern_hash, fluorescence_shift_nm, 
         discovered_phenomenon, confidence_score, action_required)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        self.cursor.execute(sql, (
            event.timestamp,
            event.signal_pattern_hash,
            event.fluorescence_shift_nm,
            int(event.detected_phenomenon),
            event.confidence_score,
            event.action_required
        ))
        self.conn.commit()
        
        return self.cursor.lastrowid
    
    def insert_batch(self, events: List[DiscoveryEvent]) -> List[int]:
        """
        Insert multiple discovery events in batch.
        
        Args:
            events: List of DiscoveryEvent objects
            
        Returns:
            List of inserted record IDs
        """
        ids = []
        for event in events:
            ids.append(self.insert_event(event))
        return ids
    
    def get_event(self, event_id: int) -> Optional[DiscoveryEvent]:
        """
        Retrieve a single discovery event by ID.
        
        Args:
            event_id: ID of event to retrieve
            
        Returns:
            DiscoveryEvent or None if not found
        """
        sql = "SELECT * FROM discoveries WHERE id = ?"
        self.cursor.execute(sql, (event_id,))
        row = self.cursor.fetchone()
        
        if row:
            return self._row_to_event(row)
        return None
    
    def get_all_events(self, limit: Optional[int] = None) -> List[DiscoveryEvent]:
        """
        Retrieve all discovery events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of DiscoveryEvent objects
        """
        sql = "SELECT * FROM discoveries ORDER BY timestamp DESC"
        if limit:
            sql += f" LIMIT {limit}"
        
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [self._row_to_event(row) for row in rows]
    
    def get_by_type(self, phenomenon_type: DiscoveryType) -> List[DiscoveryEvent]:
        """
        Retrieve events by discovery type.
        
        Args:
            phenomenon_type: DiscoveryType to filter by
            
        Returns:
            List of matching DiscoveryEvent objects
        """
        sql = "SELECT * FROM discoveries WHERE discovered_phenomenon = ? ORDER BY timestamp DESC"
        self.cursor.execute(sql, (int(phenomenon_type),))
        rows = self.cursor.fetchall()
        return [self._row_to_event(row) for row in rows]
    
    def get_by_confidence_range(self, min_conf: float, max_conf: float) -> List[DiscoveryEvent]:
        """
        Retrieve events within confidence score range.
        
        Args:
            min_conf: Minimum confidence score
            max_conf: Maximum confidence score
            
        Returns:
            List of matching DiscoveryEvent objects
        """
        sql = """
        SELECT * FROM discoveries 
        WHERE confidence_score BETWEEN ? AND ?
        ORDER BY confidence_score DESC
        """
        self.cursor.execute(sql, (min_conf, max_conf))
        rows = self.cursor.fetchall()
        return [self._row_to_event(row) for row in rows]
    
    def get_by_time_range(self, start_time: str, end_time: str) -> List[DiscoveryEvent]:
        """
        Retrieve events within time range.
        
        Args:
            start_time: ISO format start timestamp
            end_time: ISO format end timestamp
            
        Returns:
            List of matching DiscoveryEvent objects
        """
        sql = """
        SELECT * FROM discoveries 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp DESC
        """
        self.cursor.execute(sql, (start_time, end_time))
        rows = self.cursor.fetchall()
        return [self._row_to_event(row) for row in rows]
    
    def get_recent(self, hours: int = 24) -> List[DiscoveryEvent]:
        """
        Retrieve events from the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent DiscoveryEvent objects
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff_time.isoformat()
        return self.get_by_time_range(cutoff_iso, datetime.now().isoformat())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        self.cursor.execute("SELECT COUNT(*) FROM discoveries")
        total = self.cursor.fetchone()[0]
        
        stats = {'total_events': total}
        
        # Count by type
        for discovery_type in DiscoveryType:
            sql = "SELECT COUNT(*) FROM discoveries WHERE discovered_phenomenon = ?"
            self.cursor.execute(sql, (int(discovery_type),))
            count = self.cursor.fetchone()[0]
            stats[discovery_type.name.lower()] = count
        
        # Confidence stats
        self.cursor.execute("SELECT AVG(confidence_score), MIN(confidence_score), MAX(confidence_score) FROM discoveries")
        avg, min_conf, max_conf = self.cursor.fetchone()
        stats['avg_confidence'] = avg
        stats['min_confidence'] = min_conf
        stats['max_confidence'] = max_conf
        
        return stats
    
    def export_to_json(self, filepath: str, **filters) -> None:
        """
        Export events to JSON file.
        
        Args:
            filepath: Output file path
            **filters: Optional filter criteria (type, confidence_min, confidence_max, hours)
        """
        if 'type' in filters:
            events = self.get_by_type(filters['type'])
        elif 'hours' in filters:
            events = self.get_recent(filters['hours'])
        elif 'confidence_min' in filters and 'confidence_max' in filters:
            events = self.get_by_confidence_range(filters['confidence_min'], filters['confidence_max'])
        else:
            events = self.get_all_events()
        
        data = [
            {
                'timestamp': e.timestamp,
                'pattern_id': e.signal_pattern_hash,
                'nir_shift_nm': e.fluorescence_shift_nm,
                'type': e.detected_phenomenon.name,
                'confidence': f"{e.confidence_score}%",
                'action': e.action_required
            } for e in events
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(events)} events to {filepath}")
    
    def import_from_json(self, filepath: str) -> int:
        """
        Import events from JSON file.
        
        Args:
            filepath: Input file path
            
        Returns:
            Number of events imported
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for item in data:
            event = DiscoveryEvent(
                timestamp=item['timestamp'],
                signal_pattern_hash=item['pattern_id'],
                fluorescence_shift_nm=item['nir_shift_nm'],
                detected_phenomenon=DiscoveryType[item['type']],
                confidence_score=float(item['confidence'].rstrip('%')),
                action_required=item['action']
            )
            self.insert_event(event)
            count += 1
        
        print(f"✅ Imported {count} events from {filepath}")
        return count
    
    def backup(self, backup_path: str) -> None:
        """
        Create database backup.
        
        Args:
            backup_path: Path for backup file
        """
        if self.backend == DatabaseBackend.SQLITE:
            import shutil
            shutil.copy(self.connection_string, backup_path)
            print(f"✅ Database backed up to {backup_path}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def _row_to_event(self, row: Tuple) -> DiscoveryEvent:
        """Convert database row to DiscoveryEvent."""
        return DiscoveryEvent(
            timestamp=row[1],
            signal_pattern_hash=row[2],
            fluorescence_shift_nm=row[3],
            detected_phenomenon=DiscoveryType(row[4]),
            confidence_score=row[5],
            action_required=row[6]
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =====================================================================
# EXAMPLE USAGE
# =====================================================================
if __name__ == "__main__":
    from plant_discovery_simulator import PlantDiscoverySimulator
    
    # Create simulator and generate events
    simulator = PlantDiscoverySimulator()
    scenarios = [
        {"elec": 2.0, "voc": 0.1, "nir": 0.0},
        {"elec": -18.5, "voc": 2.5, "nir": 2.0},
        {"elec": 5.0, "voc": 2.8, "nir": 32.4},
        {"elec": 1.5, "voc": 0.05, "nir": -1.0},
        {"elec": -20.0, "voc": 3.0, "nir": 5.0},
    ]
    
    results = simulator.batch_analyze(scenarios)
    
    # Use database
    print("📦 Testing DiscoveryDatabase...\n")
    
    with DiscoveryDatabase() as db:
        # Insert events
        print("➕ Inserting events...")
        db.insert_batch(results)
        
        # Get statistics
        stats = db.get_statistics()
        print(f"\n📊 Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Query by type
        print(f"\n🔍 Events by type:")
        for discovery_type in DiscoveryType:
            events = db.get_by_type(discovery_type)
            print(f"   {discovery_type.name}: {len(events)} events")
        
        # High confidence events
        high_conf = db.get_by_confidence_range(50.0, 100.0)
        print(f"\n⭐ High confidence events (>50%): {len(high_conf)}")
        for event in high_conf[:3]:
            print(f"   - {event.detected_phenomenon.name}: {event.confidence_score}%")
        
        # Export
        db.export_to_json("discoveries_export.json")
        
        # Backup
        db.backup("discoveries_backup.db")
