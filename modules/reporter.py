#!/usr/bin/env python3
"""
Reporter minimaliste
"""

from colorama import Fore

class WiFiReporter:
    def __init__(self, scan_data=None):
        self.scan_data = scan_data
    
    def generate_text_report(self, filename='report.txt'):
        """Génère un rapport texte simple"""
        with open(filename, 'w') as f:
            f.write("=== RAPPORT WIFI ===\n\n")
            if self.scan_data:
                for net in self.scan_data.get('networks', []):
                    f.write(f"Réseau {net.get('num')}: {net.get('essid')}\n")
        print(f"{Fore.GREEN}[✓] Rapport texte généré: {filename}")
    
    def generate_html_report(self, filename='report.html'):
        """Génère un rapport HTML simple"""
        with open(filename, 'w') as f:
            f.write("<html><body><h1>Rapport WiFi</h1></body></html>")
        print(f"{Fore.GREEN}[✓] Rapport HTML généré: {filename}")
    
    def generate_csv_report(self, filename='report.csv'):
        """Génère un rapport CSV simple"""
        with open(filename, 'w') as f:
            f.write("ESSID,BSSID,Sécurité\n")
            if self.scan_data:
                for net in self.scan_data.get('networks', []):
                    f.write(f"{net.get('essid')},{net.get('bssid')},{net.get('security')}\n")
        print(f"{Fore.GREEN}[✓] Rapport CSV généré: {filename}")
