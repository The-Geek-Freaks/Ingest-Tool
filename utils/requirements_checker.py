"""
Überprüft und installiert benötigte Pakete.
"""
import sys
import subprocess
import logging
import pkg_resources

logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = {
    'PyQt5': '>=5.15.0',
    'wmi': '>=1.5.1'
}

class RequirementsChecker:
    """Klasse zum Überprüfen und Installieren von Python-Paketen."""
    
    def __init__(self, requirements_file: str):
        """Initialisiert den RequirementsChecker.
        
        Args:
            requirements_file: Pfad zur requirements.txt
        """
        self.requirements_file = requirements_file
        self.logger = logging.getLogger(__name__)
    
    def check_and_install(self) -> bool:
        """Überprüft und installiert fehlende Pakete."""
        try:
            # Hole installierte Pakete
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
            missing = []
            
            # Prüfe jedes benötigte Paket
            for package, version in REQUIRED_PACKAGES.items():
                if package.lower() not in installed:
                    missing.append(f"{package}{version}")
                    
            # Installiere fehlende Pakete
            if missing:
                self.logger.info(f"Installiere benötigte Pakete: {', '.join(pkg.split('>=')[0] for pkg in missing)}")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Fehler beim Installieren der Pakete: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Überprüfen/Installieren der Pakete: {e}")
            return False

def check_and_install_requirements():
    """Überprüft und installiert fehlende Pakete."""
    # Hole installierte Pakete
    installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    missing = []
    
    # Prüfe jedes benötigte Paket
    for package, version in REQUIRED_PACKAGES.items():
        if package.lower() not in installed:
            missing.append(f"{package}{version}")
            
    # Installiere fehlende Pakete
    if missing:
        logger.info(f"Installiere benötigte Pakete: {', '.join(pkg.split('>=')[0] for pkg in missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Installieren der Pakete: {e}")
            return False
    
    return True
