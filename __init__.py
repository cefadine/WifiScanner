"""
WiFiScanner Pro - Outil complet d'audit WiFi
"""

# Version globale
__version__ = "1.0.0"
__author__ = "Votre Nom"
__description__ = "Outil d'audit WiFi éthique avec interface interactive"
__license__ = "MIT"

# Importations principales
try:
    from modules.scanner import NetworkScanner
    from modules.deauth import DeauthAttack
    from modules.handshake import HandshakeCapture
    from modules.reporter import WiFiReporter
    
    __all__ = [
        'NetworkScanner',
        'DeauthAttack', 
        'HandshakeCapture',
        'WiFiReporter'
    ]
    
except ImportError as e:
    print(f"⚠️  Erreur d'importation: {e}")
    __all__ = []

# Banner ASCII
BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║    ██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗   ║
║    ██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║   ║
║    ██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║   ║
║    ██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║   ║
║    ╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║   ║
║     ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝   ║
║                                                                          ║
║                         WiFiScanner Pro v{version}                        ║
║               Pour audit éthique uniquement - Labo personnel             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""".format(version=__version__)

def show_banner():
    """Affiche la bannière du programme"""
    print(BANNER)

def get_version():
    """Retourne la version du programme"""
    return __version__

def get_author():
    """Retourne l'auteur du programme"""
    return __author__

def check_dependencies():
    """Vérifie les dépendances nécessaires"""
    import subprocess
    import sys
    
    dependencies = [
        ('aircrack-ng', 'aircrack-ng'),
        ('airodump-ng', 'aircrack-ng'),
        ('aireplay-ng', 'aircrack-ng'),
        ('python3', 'python3'),
        ('pip3', 'python3-pip')
    ]
    
    missing = []
    for cmd, package in dependencies:
        try:
            subprocess.run([cmd, '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            missing.append((cmd, package))
    
    if missing:
        print("⚠️  Dépendances manquantes:")
        for cmd, package in missing:
            print(f"   - {cmd} (installez: sudo apt install {package})")
        return False
    
    return True

# Initialisation
if __name__ == "__main__":
    show_banner()
    print(f"\nVersion: {__version__}")
    print(f"Auteur: {__author__}")
    print(f"Description: {__description__}")
    print(f"Licence: {__license__}")
    
    if check_dependencies():
        print("\n✅ Toutes les dépendances sont satisfaites")
    else:
        print("\n❌ Certaines dépendances sont manquantes")
