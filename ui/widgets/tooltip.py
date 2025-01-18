from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen

class CustomTooltip(QWidget):
    """Angepasster Tooltip mit modernem Design."""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Label für Text
        self.label = QLabel()
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.label)
        
        # Timer für automatisches Ausblenden
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        
    def show_tooltip(self, text: str, pos: QPoint, duration: int = 3000):
        """Zeigt den Tooltip an der angegebenen Position.
        
        Args:
            text: Anzuzeigender Text
            pos: Position (global)
            duration: Anzeigedauer in ms
        """
        # Setze Text
        self.label.setText(text)
        
        # Berechne optimale Größe
        self.adjustSize()
        
        # Stelle sicher, dass Tooltip im sichtbaren Bereich bleibt
        screen = QApplication.screenAt(pos)
        if screen:
            screen_geo = screen.geometry()
            tooltip_geo = QRect(pos, self.size())
            
            # Prüfe ob Tooltip außerhalb des Bildschirms wäre
            if tooltip_geo.right() > screen_geo.right():
                pos.setX(screen_geo.right() - tooltip_geo.width())
            if tooltip_geo.bottom() > screen_geo.bottom():
                pos.setY(screen_geo.bottom() - tooltip_geo.height())
                
        # Positioniere und zeige Tooltip
        self.move(pos)
        self.show()
        
        # Starte Timer
        self.hide_timer.start(duration)
        
    def paintEvent(self, event):
        """Zeichnet den Tooltip mit abgerundeten Ecken und Schatten."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Erstelle Pfad für abgerundete Ecken
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 6, 6)
        
        # Zeichne Schatten
        painter.setPen(Qt.NoPen)
        for i in range(5):
            painter.setBrush(QColor(0, 0, 0, 50 - i * 10))
            painter.drawPath(path.translated(0, i))
            
        # Zeichne Hintergrund
        painter.setBrush(QColor(64, 64, 64))
        painter.setPen(QPen(QColor(96, 96, 96), 1))
        painter.drawPath(path)
        
class TooltipManager:
    """Verwaltet Tooltips für die Anwendung."""
    
    def __init__(self):
        self.tooltips = {}
        
    def show_tooltip(self, widget: QWidget, text: str, duration: int = 3000):
        """Zeigt einen Tooltip für ein Widget.
        
        Args:
            widget: Widget, für das der Tooltip angezeigt werden soll
            text: Tooltip-Text
            duration: Anzeigedauer in ms
        """
        # Erstelle Tooltip wenn nötig
        if widget not in self.tooltips:
            self.tooltips[widget] = CustomTooltip()
            
        tooltip = self.tooltips[widget]
        
        # Berechne Position (mittig unter dem Widget)
        pos = widget.mapToGlobal(QPoint(0, widget.height()))
        pos.setX(pos.x() + widget.width() // 2)
        
        # Zeige Tooltip
        tooltip.show_tooltip(text, pos, duration)
        
    def hide_tooltip(self, widget: QWidget):
        """Versteckt den Tooltip eines Widgets."""
        if widget in self.tooltips:
            self.tooltips[widget].hide()
