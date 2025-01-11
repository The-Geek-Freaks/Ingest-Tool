"""
Status-Definitionen für Laufwerke.
"""

class DriveStatus:
    """Status eines Laufwerks."""
    BEREIT = "ready"
    KOPIEREN = "copying"
    FEHLER = "error"
    GETRENNT = "disconnected"
