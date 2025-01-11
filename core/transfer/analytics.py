"""
Analyse und Statistik für Dateiübertragungen.
"""

import logging
import threading
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class TransferAnalytics:
    """Verwaltet Statistiken und Analysen für Dateiübertragungen."""
    
    def __init__(self):
        self._transfer_history = []
        self._error_history = []
        self._history_lock = threading.Lock()
        self._max_history_size = 1000
        
    def record_transfer(self, transfer_data: Dict):
        """Zeichnet eine Übertragung auf."""
        with self._history_lock:
            # Füge Zeitstempel hinzu
            transfer_data['timestamp'] = datetime.now().isoformat()
            
            # Füge zur Historie hinzu
            self._transfer_history.append(transfer_data)
            
            # Begrenze Größe der Historie
            if len(self._transfer_history) > self._max_history_size:
                self._transfer_history = self._transfer_history[-self._max_history_size:]
                
    def record_error(self, error_data: Dict):
        """Zeichnet einen Fehler auf."""
        with self._history_lock:
            # Füge Zeitstempel hinzu
            error_data['timestamp'] = datetime.now().isoformat()
            
            # Füge zur Historie hinzu
            self._error_history.append(error_data)
            
            # Begrenze Größe der Historie
            if len(self._error_history) > self._max_history_size:
                self._error_history = self._error_history[-self._max_history_size:]
                
    def get_transfer_stats(self, time_window: Optional[timedelta] = None) -> Dict:
        """Berechnet Übertragungsstatistiken für ein Zeitfenster."""
        with self._history_lock:
            if not self._transfer_history:
                return {}
                
            # Filtere nach Zeitfenster
            transfers = self._transfer_history
            if time_window:
                cutoff = datetime.now() - time_window
                transfers = [
                    t for t in transfers 
                    if datetime.fromisoformat(t['timestamp']) > cutoff
                ]
                
            if not transfers:
                return {}
                
            # Berechne Statistiken
            total_bytes = sum(t['size'] for t in transfers)
            total_time = sum(t['duration'] for t in transfers)
            avg_speed = total_bytes / total_time if total_time > 0 else 0
            
            return {
                'total_transfers': len(transfers),
                'total_bytes': total_bytes,
                'total_time': total_time,
                'avg_speed': avg_speed,
                'success_rate': sum(
                    1 for t in transfers if t['status'] == 'completed'
                ) / len(transfers),
                'error_rate': sum(
                    1 for t in transfers if t['status'] == 'failed'
                ) / len(transfers)
            }
            
    def get_error_analysis(self, time_window: Optional[timedelta] = None) -> Dict:
        """Analysiert aufgetretene Fehler."""
        with self._history_lock:
            if not self._error_history:
                return {}
                
            # Filtere nach Zeitfenster
            errors = self._error_history
            if time_window:
                cutoff = datetime.now() - time_window
                errors = [
                    e for e in errors 
                    if datetime.fromisoformat(e['timestamp']) > cutoff
                ]
                
            if not errors:
                return {}
                
            # Gruppiere Fehler
            error_types = defaultdict(int)
            error_paths = defaultdict(int)
            
            for error in errors:
                error_types[error['type']] += 1
                error_paths[error['path']] += 1
                
            return {
                'total_errors': len(errors),
                'error_types': dict(error_types),
                'error_paths': dict(error_paths),
                'error_rate_over_time': self._calculate_error_rate_over_time(errors)
            }
            
    def get_performance_report(self) -> Dict:
        """Erstellt einen detaillierten Performance-Bericht."""
        with self._history_lock:
            if not self._transfer_history:
                return {}
                
            # Analysiere Stoßzeiten
            peak_times = self._analyze_peak_times()
            
            # Analysiere Pfadnutzung
            path_usage = self._analyze_path_usage()
            
            # Analysiere Größenverteilung
            size_distribution = self._analyze_size_distribution()
            
            # Analysiere Performance-Trends
            performance_trends = self._analyze_performance_trends()
            
            return {
                'peak_times': peak_times,
                'path_usage': path_usage,
                'size_distribution': size_distribution,
                'performance_trends': performance_trends
            }
            
    def _calculate_error_rate_over_time(
        self, errors: List[Dict], interval: timedelta = timedelta(hours=1)
    ) -> Dict:
        """Berechnet die Fehlerrate über Zeit."""
        if not errors:
            return {}
            
        # Gruppiere Fehler nach Zeitintervallen
        error_counts = defaultdict(int)
        
        for error in errors:
            timestamp = datetime.fromisoformat(error['timestamp'])
            interval_start = timestamp.replace(
                minute=0, second=0, microsecond=0
            )
            error_counts[interval_start.isoformat()] += 1
            
        return dict(error_counts)
        
    def _analyze_peak_times(self) -> Dict:
        """Analysiert Stoßzeiten der Übertragungen."""
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for transfer in self._transfer_history:
            timestamp = datetime.fromisoformat(transfer['timestamp'])
            hour_counts[timestamp.hour] += 1
            day_counts[timestamp.strftime('%A')] += 1
            
        return {
            'hourly': dict(hour_counts),
            'daily': dict(day_counts)
        }
        
    def _analyze_path_usage(self) -> Dict:
        """Analysiert die Nutzung verschiedener Pfade."""
        source_paths = defaultdict(int)
        dest_paths = defaultdict(int)
        
        for transfer in self._transfer_history:
            source_paths[transfer['source']] += 1
            dest_paths[transfer['destination']] += 1
            
        return {
            'source_paths': dict(source_paths),
            'destination_paths': dict(dest_paths)
        }
        
    def _analyze_size_distribution(self) -> Dict:
        """Analysiert die Größenverteilung der übertragenen Dateien."""
        size_ranges = {
            'small': (0, 1024 * 1024),  # 0-1MB
            'medium': (1024 * 1024, 100 * 1024 * 1024),  # 1-100MB
            'large': (100 * 1024 * 1024, float('inf'))  # >100MB
        }
        
        distribution = defaultdict(int)
        
        for transfer in self._transfer_history:
            size = transfer['size']
            for range_name, (min_size, max_size) in size_ranges.items():
                if min_size <= size < max_size:
                    distribution[range_name] += 1
                    break
                    
        return dict(distribution)
        
    def _analyze_performance_trends(self) -> Dict:
        """Analysiert Performance-Trends über Zeit."""
        if not self._transfer_history:
            return {}
            
        # Gruppiere nach Tagen
        daily_stats = defaultdict(lambda: {'bytes': 0, 'time': 0, 'count': 0})
        
        for transfer in self._transfer_history:
            timestamp = datetime.fromisoformat(transfer['timestamp'])
            day = timestamp.date().isoformat()
            
            daily_stats[day]['bytes'] += transfer['size']
            daily_stats[day]['time'] += transfer['duration']
            daily_stats[day]['count'] += 1
            
        # Berechne tägliche Durchschnitte
        trends = {}
        for day, stats in daily_stats.items():
            trends[day] = {
                'avg_speed': stats['bytes'] / stats['time'] if stats['time'] > 0 else 0,
                'total_transfers': stats['count'],
                'total_bytes': stats['bytes']
            }
            
        return trends
        
    def export_analytics(self, filepath: str) -> bool:
        """Exportiert alle Analytics-Daten in eine JSON-Datei."""
        try:
            data = {
                'transfer_history': self._transfer_history,
                'error_history': self._error_history,
                'stats': self.get_transfer_stats(),
                'error_analysis': self.get_error_analysis(),
                'performance_report': self.get_performance_report()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Exportieren der Analytics: {e}")
            return False
            
    def import_analytics(self, filepath: str) -> bool:
        """Importiert Analytics-Daten aus einer JSON-Datei."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            with self._history_lock:
                self._transfer_history = data['transfer_history']
                self._error_history = data['error_history']
                
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Importieren der Analytics: {e}")
            return False
