"""
Überprüft und installiert benötigte Pakete.
"""
import sys
import subprocess
import logging
import pkg_resources
from typing import Dict, List

logger = logging.getLogger(__name__)

class RequirementsChecker:
    """Klasse zum Überprüfen und Installieren von Python-Paketen."""
    
    def __init__(self, requirements_file: str):
        """Initialisiert den RequirementsChecker.
        
        Args:
            requirements_file: Pfad zur requirements.txt
        """
        self.requirements_file = requirements_file
        self.logger = logging.getLogger(__name__)
    
    def _parse_requirements(self) -> Dict[str, str]:
        """Liest die requirements.txt und gibt ein Dictionary mit Paket-Versionen zurück."""
        requirements = {}
        try:
            with open(self.requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Entferne eventuelle Kommentare am Ende der Zeile
                        line = line.split('#')[0].strip()
                        if '>=' in line:
                            package, version = line.split('>=')
                            requirements[package.strip()] = f">={version.strip()}"
                        elif '==' in line:
                            package, version = line.split('==')
                            requirements[package.strip()] = f"=={version.strip()}"
                        else:
                            requirements[line] = ""
        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der requirements.txt: {e}")
            return {}
        return requirements
    
    def check_and_install(self) -> bool:
        """Überprüft und installiert fehlende Pakete."""
        try:
            # Hole installierte Pakete
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
            required = self._parse_requirements()
            missing: List[str] = []
            
            # Prüfe jedes benötigte Paket
            for package, version in required.items():
                package_lower = package.lower()
                if package_lower not in installed:
                    missing.append(f"{package}{version}")
                    
            # Installiere fehlende Pakete
            if missing:
                self.logger.info(f"Installiere benötigte Pakete: {', '.join(pkg.split('>=')[0] for pkg in missing)}")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
                    self.logger.info("Pakete erfolgreich installiert")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Fehler beim Installieren der Pakete: {e}")
                    return False
            else:
                self.logger.info("Alle benötigten Pakete sind bereits installiert")
            
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
