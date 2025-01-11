from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget

def create_progress_layout(parent: QWidget) -> QVBoxLayout:
    """Erstellt das Layout für die Fortschrittsanzeige.
    
    Args:
        parent: Das übergeordnete Widget
        
    Returns:
        QVBoxLayout mit der Fortschrittsanzeige
    """
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    
    return layout
