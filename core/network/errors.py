"""
Fehlerdefinitionen für Netzwerkoperationen.
"""

class NetworkError(Exception):
    """Basisklasse für Netzwerkfehler."""
    pass

class ConnectionError(NetworkError):
    """Wird bei Verbindungsfehlern ausgelöst."""
    pass

class TransferError(NetworkError):
    """Wird bei Übertragungsfehlern ausgelöst."""
    pass

class CopyAborted(NetworkError):
    """Wird ausgelöst, wenn Kopiervorgang abgebrochen wird."""
    pass

class CopyVerificationError(NetworkError):
    """Wird ausgelöst, wenn Kopierverifizierung fehlschlägt."""
    pass
