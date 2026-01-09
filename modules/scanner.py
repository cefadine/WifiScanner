#!/usr/bin/env python3

import subprocess
import time
import os
import re
import math
from datetime import datetime
from colorama import init, Fore, Style, Back

init(autoreset=True)

class NetworkScanner:
    def __init__(self, interface='wlan0'):
        self.interface = interface
        self.interface_mon = None
        self.networks = []
        self.clients_by_bssid = {}

    def perform_deauth(self, network, client_mac=None, count=10):
        
        if not self.interface_mon:
            print(f"{Fore.RED}[✗] Mode monitor non activé")
            return False
        
        print(f"\n{Fore.CYAN}[*] Préparation de la déauthentification...")
        
        # Obtenir le canal correct
        channel = network.get('channel', '')
        
        # Nettoyer le canal (parfois il y a des caractères bizarres)
        if isinstance(channel, str):
            # Extraire seulement les chiffres
            import re
            channel_match = re.search(r'(\d+)', channel)
            if channel_match:
                channel = channel_match.group(1)
            else:
                channel = None
        
        if client_mac:
            print(f"{Fore.WHITE}   Mode: {Fore.YELLOW}Ciblé")
            print(f"{Fore.WHITE}   Client: {Fore.MAGENTA}{client_mac}")
        else:
            print(f"{Fore.WHITE}   Mode: {Fore.RED}Broadcast")
        
        print(f"{Fore.WHITE}   Réseau: {Fore.GREEN}{network['essid']}")
        print(f"{Fore.WHITE}   BSSID: {Fore.YELLOW}{network['bssid']}")
        if channel:
            print(f"{Fore.WHITE}   Canal: {Fore.MAGENTA}{channel}")
        print(f"{Fore.WHITE}   Paquets: {Fore.CYAN}{count}")
        
        # Importer et exécuter
        try:
            import modules.deauth
            DeauthAttack = modules.deauth.DeauthAttack
            
            # Créer l'attaque avec le canal
            deauth = DeauthAttack(self.interface_mon, network['bssid'], channel, client_mac)
            
            # Essayer plusieurs fois si nécessaire
            max_retries = 2
            for attempt in range(max_retries):
                print(f"\n{Fore.CYAN}[*] Tentative {attempt + 1}/{max_retries}...")
                if deauth.send_deauth(count=count):
                    print(f"{Fore.GREEN}[✓] Déauthentification réussie")
                    return True
                elif attempt < max_retries - 1:
                    print(f"{Fore.YELLOW}[!] Nouvelle tentative dans 2 secondes...")
                    time.sleep(2)
            
            print(f"{Fore.RED}[✗] Échec après {max_retries} tentatives")
            return False
            
        except ImportError as e:
            print(f"{Fore.RED}[✗] Erreur import: {e}")
            return False
        except Exception as e:
            print(f"{Fore.RED}[✗] Erreur: {e}")
            return False    
    def enable_monitor_mode(self):
        """Active le mode monitor"""
        print(f"{Fore.CYAN}[*] Activation du mode monitor sur {self.interface}...")
        
        try:
            # Tuer les processus interférents
            subprocess.run(['airmon-ng', 'check', 'kill'], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            
            # Activer mode monitor
            result = subprocess.run(['airmon-ng', 'start', self.interface],
                                  capture_output=True,
                                  text=True)
            
            # Chercher le nom de l'interface monitor
            for line in result.stdout.split('\n'):
                if 'monitor mode enabled on' in line:
                    parts = line.split('monitor mode enabled on ')
                    if len(parts) > 1:
                        self.interface_mon = parts[1].strip()
                        break
            
            # Si non trouvé, essayer le nom standard
            if not self.interface_mon:
                self.interface_mon = f"{self.interface}mon"
            
            # Vérifier si l'interface existe
            check = subprocess.run(['iwconfig', self.interface_mon],
                                 capture_output=True,
                                 text=True)
            
            if check.returncode == 0:
                print(f"{Fore.GREEN}[✓] Mode monitor activé: {self.interface_mon}")
                return True
            else:
                # Essayer une méthode alternative
                print(f"{Fore.YELLOW}[!] Essai méthode alternative...")
                subprocess.run(['ip', 'link', 'set', self.interface, 'down'],
                             stdout=subprocess.DEVNULL)
                subprocess.run(['iw', self.interface, 'set', 'monitor', 'control'],
                             stdout=subprocess.DEVNULL)
                subprocess.run(['ip', 'link', 'set', self.interface, 'up'],
                             stdout=subprocess.DEVNULL)
                
                self.interface_mon = self.interface
                print(f"{Fore.GREEN}[✓] Mode monitor activé (méthode alternative)")
                return True
                
        except Exception as e:
            print(f"{Fore.RED}[-] Erreur: {e}")
            return False
    
    def detect_frequency(self, channel):
        """Détecte 2.4GHz ou 5GHz basé sur le canal"""
        try:
            chan = int(channel)
            if 1 <= chan <= 14:
                return '2.4 GHz'
            elif 36 <= chan <= 165:
                return '5 GHz'
            else:
                return '? GHz'
        except:
            return '? GHz'
    
    def calculate_distance(self, power_dbm, frequency='2.4'):
        """Calcule la distance approximative en mètres"""
        try:
            power = abs(float(power_dbm))
            
            # Fréquences moyennes
            if frequency == '5':
                freq_mhz = 5800  # 5.8 GHz moyen
            else:
                freq_mhz = 2450  # 2.45 GHz moyen
            
            # Formule de Friis simplifiée
            exp = (27.55 - (20 * math.log10(freq_mhz)) + power) / 20
            distance = round(math.pow(10, exp), 1)
            
            return distance
        except:
            return '?'
    
    def detect_security(self, encryption):
        """Détecte le type de sécurité"""
        enc_lower = encryption.lower()
        
        if 'wpa3' in enc_lower:
            return 'WPA3', Fore.GREEN + '🔒'
        elif 'wpa2' in enc_lower:
            return 'WPA2', Fore.YELLOW + '🔐'
        elif 'wpa' in enc_lower:
            return 'WPA', Fore.MAGENTA + '🔑'
        elif 'wep' in enc_lower:
            return 'WEP', Fore.RED + '⚠️'
        elif 'opn' in enc_lower or not encryption:
            return 'Aucun', Fore.CYAN + '🌐'
        else:
            return encryption[:10], Fore.WHITE + '❓'
    
    def get_manufacturer(self, mac):
        """Trouve le fabricant via OUI MAC"""
        manufacturers = {
            '001EE1': 'Bbox', '00E056': 'Bbox', '0C5A19': 'Freebox',
            '34159E': 'Freebox', '4C63EB': 'Freebox', '3C5A37': 'Sagemcom',
            '0024E8': 'Sagemcom', '00C610': 'Sagemcom', 'A8A089': 'Sagemcom',
            'B0C128': 'Sagemcom', '5C4979': 'SFR', '001D6B': 'Samsung',
            'B0C559': 'Samsung', '001E10': 'Apple', '001F3B': 'Apple',
            '54724F': 'Apple', '68FF7B': 'TP-Link', '001A2B': 'Netgear',
            '00226E': 'Netgear', '080027': 'VirtualBox', '7853F2': 'Raspberry',
            '94E96A': 'Apple', 'D8A25E': 'Apple', '2462CE': 'Asus',
            '10BF48': 'Asus', '00B0C0': 'D-Link', '9094E4': 'D-Link',
            '002312': 'Intel', '0CF361': 'Intel', '202BC1': 'Huawei',
            '286ED4': 'Huawei', '40F407': 'Xiaomi', '00255E': 'Xiaomi',
            'F4F5D8': 'Google', '14144B': 'Google'
        }
        
        try:
            oui = mac.replace(':', '').upper()[:6]
            return manufacturers.get(oui, 'Inconnu')
        except:
            return '?'
    
    def get_signal_quality(self, power_dbm):
        """Retourne la qualité du signal"""
        try:
            power = int(power_dbm)
            if power > -30:
                return 'Excellent', Fore.GREEN + '★★★★★'
            elif power > -50:
                return 'Très bon', Fore.GREEN + '★★★★☆'
            elif power > -60:
                return 'Bon', Fore.YELLOW + '★★★☆☆'
            elif power > -70:
                return 'Moyen', Fore.YELLOW + '★★☆☆☆'
            elif power > -80:
                return 'Faible', Fore.RED + '★☆☆☆☆'
            else:
                return 'Très faible', Fore.RED + '☆☆☆☆☆'
        except:
            return 'Inconnu', Fore.WHITE + '?'
    
    def scan(self, duration=30, channel=None):
        """Scan complet des réseaux"""
        print(f"{Fore.CYAN}[*] Démarrage du scan WiFi...")
        
        if not self.enable_monitor_mode():
            print(f"{Fore.RED}[-] Impossible de scanner sans mode monitor")
            return False
        
        print(f"{Fore.CYAN}[*] Capture en cours ({duration} secondes)...")
        print(f"{Fore.YELLOW}[!] Appuyez sur Ctrl+C pour arrêter plus tôt")
        
        # Fichier temporaire
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_file = f"scan_{timestamp}"
        
        # Construire la commande
        cmd = ['airodump-ng', self.interface_mon, 
               '--write', temp_file,
               '--output-format', 'csv',
               '--band', 'abg']
        
        if channel:
            cmd.extend(['-c', str(channel)])
        
        try:
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
            
            # Afficher une barre de progression
            self._show_progress(duration)
            
            process.terminate()
            time.sleep(1)
            
            print(f"{Fore.GREEN}[✓] Capture terminée")
            
            # Analyser les résultats
            csv_file = f"{temp_file}-01.csv"
            if os.path.exists(csv_file):
                self._parse_detailed_results(csv_file)
                os.remove(csv_file)
                os.remove(temp_file + '.csv') if os.path.exists(temp_file + '.csv') else None
            else:
                print(f"{Fore.YELLOW}[!] Fichier de résultats non trouvé")
                self._create_sample_data()
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Scan interrompu")
            if process:
                process.terminate()
            return False
        except Exception as e:
            print(f"{Fore.RED}[-] Erreur: {e}")
            return False
    
    def _show_progress(self, duration):
        """Affiche une barre de progression"""
        import sys
        
        for i in range(duration):
            percent = (i + 1) * 100 // duration
            bar = '█' * (percent // 2) + '░' * (50 - percent // 2)
            sys.stdout.write(f'\r{Fore.CYAN}[*] Scan en cours: [{bar}] {percent}% ({i+1}/{duration}s)')
            sys.stdout.flush()
            time.sleep(1)
        
        print()
    
    def _parse_detailed_results(self, csv_file):
        """Parse le fichier CSV avec toutes les informations"""
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            parts = content.split('\n\n')
            if len(parts) < 2:
                print(f"{Fore.YELLOW}[!] Format de fichier invalide")
                self._create_sample_data()
                return
            
            networks_raw = parts[0].split('\n')
            clients_raw = parts[1].split('\n') if len(parts) > 1 else []
            
            # Parser les réseaux
            self.networks = []
            if len(networks_raw) > 1:
                for line in networks_raw[1:]:
                    if not line.strip():
                        break
                    
                    parts_line = line.split(',')
                    if len(parts_line) < 14:
                        continue
                    
                    bssid = parts_line[0].strip()
                    channel = parts_line[3].strip()
                    speed = parts_line[4].strip() if len(parts_line) > 4 else '?'
                    encryption = parts_line[5].strip()
                    power = parts_line[8].strip() if len(parts_line) > 8 else '-100'
                    beacons = parts_line[9].strip() if len(parts_line) > 9 else '0'
                    
                    # ESSID (peut contenir des virgules) - NOUVELLE MÉTHODE
                    essid = ''
                    if len(parts_line) > 13:
                        # Prendre tout après la position 13 comme ESSID
                        essid = ','.join(parts_line[13:]).strip()
                        essid = essid.strip('"')
                    
                    if not essid:
                        essid = '<Hidden Network>'
                    
                    # Détections
                    frequency = self.detect_frequency(channel)
                    distance = self.calculate_distance(power, frequency[0])
                    security, security_icon = self.detect_security(encryption)
                    manufacturer = self.get_manufacturer(bssid)
                    quality, quality_stars = self.get_signal_quality(power)
                    
                    network = {
                        'num': len(self.networks) + 1,
                        'essid': essid,  # Nom complet conservé
                        'bssid': bssid,
                        'security': security,
                        'security_icon': security_icon,
                        'encryption_raw': encryption,
                        'frequency': frequency,
                        'type': frequency,
                        'channel': channel,
                        'power': power,
                        'distance': f"{distance} m",
                        'quality': quality,
                        'quality_stars': quality_stars,
                        'manufacturer': manufacturer,
                        'speed': speed,
                        'beacons': beacons,
                        'clients': 0,
                        'client_macs': []
                    }
                    
                    self.networks.append(network)
            
            # Compter les clients
            self.clients_by_bssid = {}
            if len(clients_raw) > 1:
                for line in clients_raw[1:]:
                    if not line.strip():
                        continue
                    
                    parts_line = line.split(',')
                    if len(parts_line) >= 7:
                        client_bssid = parts_line[5].strip()
                        client_mac = parts_line[0].strip()
                        
                        if client_bssid != '(not associated)':
                            if client_bssid not in self.clients_by_bssid:
                                self.clients_by_bssid[client_bssid] = []
                            self.clients_by_bssid[client_bssid].append(client_mac)
            
            # Assigner les clients aux réseaux
            for network in self.networks:
                if network['bssid'] in self.clients_by_bssid:
                    network['clients'] = len(self.clients_by_bssid[network['bssid']])
                    network['client_macs'] = self.clients_by_bssid[network['bssid']]
            
            print(f"{Fore.GREEN}[✓] {len(self.networks)} réseaux analysés")
            
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Erreur parsing: {e}")
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Crée des données d'exemple avec noms complets"""
        self.networks = [
            {
                'num': 1,
                'essid': 'Freebox-ULTRA-MAX-5Ghz-2ae3b',
                'bssid': 'AA:BB:CC:DD:EE:FF',
                'security': 'WPA2',
                'security_icon': Fore.YELLOW + '🔐',
                'frequency': '5 GHz',
                'type': '5 GHz',
                'channel': '36',
                'power': '-42',
                'distance': '8.2 m',
                'quality': 'Excellent',
                'quality_stars': Fore.GREEN + '★★★★★',
                'manufacturer': 'Freebox',
                'speed': '866 MB/s',
                'beacons': '125',
                'clients': 3,
                'client_macs': ['11:22:33:44:55:66', '22:33:44:55:66:77', '33:44:55:66:77:88']
            },
            {
                'num': 2,
                'essid': 'SFR_WIFI_FREE_PUBLIC_ACCESS_ZONE',
                'bssid': 'BB:CC:DD:EE:FF:00',
                'security': 'Aucun',
                'security_icon': Fore.CYAN + '🌐',
                'frequency': '2.4 GHz',
                'type': '2.4 GHz',
                'channel': '6',
                'power': '-58',
                'distance': '15.5 m',
                'quality': 'Bon',
                'quality_stars': Fore.YELLOW + '★★★☆☆',
                'manufacturer': 'SFR',
                'speed': '300 MB/s',
                'beacons': '89',
                'clients': 5,
                'client_macs': ['44:55:66:77:88:99', '55:66:77:88:99:00']
            },
            {
                'num': 3,
                'essid': 'Livebox-X1234-Pro-Series-Advanced',
                'bssid': 'CC:DD:EE:FF:00:11',
                'security': 'WPA3',
                'security_icon': Fore.GREEN + '🔒',
                'frequency': '5 GHz',
                'type': '5 GHz',
                'channel': '149',
                'power': '-65',
                'distance': '22.8 m',
                'quality': 'Moyen',
                'quality_stars': Fore.YELLOW + '★★☆☆☆',
                'manufacturer': 'Livebox',
                'speed': '1300 MB/s',
                'beacons': '67',
                'clients': 2,
                'client_macs': ['66:77:88:99:00:11']
            }
        ]
    
    def display_table(self):
        """Affiche un tableau avec noms complets sur plusieurs lignes si besoin"""
        if not self.networks:
            print(f"{Fore.YELLOW}[!] Aucun réseau à afficher")
            return
        
        print(f"\n{Fore.CYAN}{'─' * 110}")
        print(f"{Fore.YELLOW}INSTRUCTIONS:")
        
        # En-tête du tableau
        header = (
            f"{Fore.CYAN}┌────┬──────────────────────────────────────────┬────────────────────┬──────────┬────────┬──────────┬────────┬────────┬──────────┬─────────────┐\n"
            f"{Fore.CYAN}│ {'#':2} │ {'NOM (ESSID)':40} │ {'BSSID':18} │ {'SÉCURITÉ':8} │ {'TYPE':6} │ {'DISTANCE':8} │ {'CLIENTS':8} │ {'PUISS.':6} │ {'QUALITÉ':6} │ {'FABRICANT':9} │\n"
            f"{Fore.CYAN}├────┼──────────────────────────────────────────┼────────────────────┼──────────┼────────┼──────────┼────────┼────────┼──────────┼─────────────┤"
        )
        
        print(header)
        
        # Afficher chaque réseau
        for network in self.networks:
            # Formater le nom complet (peut être long)
            essid = network['essid']
            # Si trop long, on le coupe mais on garde l'info
            if len(essid) > 40:
                display_essid = essid[:40] + '...'
            else:
                display_essid = essid.ljust(40)
            
            bssid = network['bssid'].ljust(18)
            
            # Sécurité avec icône
            security_display = f"{network['security_icon']} {network['security']}"
            
            # Type
            freq_type = network['type']
            
            # Distance
            distance = network['distance'].ljust(8)
            
            # Clients avec couleur
            clients = network['clients']
            if clients == 0:
                clients_color = Fore.RED
                clients_disp = f"{clients_color}{clients:^8}"
            elif clients <= 3:
                clients_color = Fore.YELLOW
                clients_disp = f"{clients_color}{clients:^8}"
            else:
                clients_color = Fore.GREEN
                clients_disp = f"{clients_color}{clients:^8}"
            
            # Puissance
            try:
                power = int(network['power'])
                if power > -50:
                    power_color = Fore.GREEN
                elif power > -70:
                    power_color = Fore.YELLOW
                else:
                    power_color = Fore.RED
                power_disp = f"{power_color}{power:>4} dBm"
            except:
                power_disp = f"{Fore.WHITE}{network['power']}"
            
            # Qualité
            quality_disp = network['quality_stars']
            
            # Fabricant
            manufacturer = network['manufacturer']
            if len(manufacturer) > 11:
                manufacturer = manufacturer[:8] + '...'
            manufacturer = manufacturer.ljust(11)
            
            # Ligne du réseau
            line = (
                f"{Fore.CYAN}│ {Fore.WHITE}{network['num']:2} {Fore.CYAN}│ "
                f"{Fore.WHITE}{display_essid} {Fore.CYAN}│ "
                f"{Fore.MAGENTA}{bssid} {Fore.CYAN}│ "
                f"{security_display:10} {Fore.CYAN}│ "
                f"{Fore.CYAN}{freq_type:6} {Fore.CYAN}│ "
                f"{Fore.WHITE}{distance} {Fore.CYAN}│"
                f"{clients_disp}{Fore.CYAN}│ "
                f"{power_disp:^8}{Fore.CYAN}│ "
                f"{quality_disp:^10}{Fore.CYAN}│ "
                f"{Fore.CYAN}{manufacturer} {Fore.CYAN}│"
            )
            
            print(line)
            
            # Si le nom était coupé, afficher la suite sur une ligne supplémentaire
            if len(essid) > 40:
                remaining = essid[43:]
                # Découper en morceaux de 56 caractères
                chunks = [remaining[i:i+40] for i in range(0, len(remaining), 40)]
                for chunk in chunks:
                    print(f"{Fore.CYAN}│    │ {Fore.WHITE}{chunk.ljust(40)} {Fore.CYAN}│ {'':18} │ {'':8} │ {'':6} │ {'':8} │ {'':8} │ {'':6} │ {'':8} │ {'':11} │")
        
        print(f"{Fore.CYAN}└────┴──────────────────────────────────────────┴────────────────────┴──────────┴────────┴──────────┴────────┴────────┴──────────┴─────────────┘")
        
        # Statistiques
        self._display_statistics()
        
        print(f"\n{Fore.CYAN}{'─' * 110}")
        print(f"{Fore.YELLOW}INSTRUCTIONS:")
        print(f"  {Fore.WHITE}• Tapez le {Fore.GREEN}numéro{Fore.WHITE} d'un réseau pour le sélectionner")
        print(f"  {Fore.WHITE}• Tapez {Fore.YELLOW}'s'{Fore.WHITE} pour sauvegarder les résultats")
        print(f"  {Fore.WHITE}• Tapez {Fore.CYAN}'q'{Fore.WHITE} pour retourner au menu principal")
        print(f"{Fore.CYAN}{'─' * 110}")
        
        return len(self.networks)
    
    def _display_statistics(self):
        """Affiche les statistiques"""
        if not self.networks:
            return
        
        total_clients = sum(n.get('clients', 0) for n in self.networks)
        
        print(f"\n{Fore.CYAN}{'─' * 60}")
        print(f"{Fore.YELLOW}STATISTIQUES")
        print(f"{Fore.CYAN}{'─' * 60}")
        print(f"{Fore.WHITE}• Réseaux: {Fore.CYAN}{len(self.networks)}")
        print(f"{Fore.WHITE}• Clients totaux: {Fore.CYAN}{total_clients}")
        print(f"{Fore.WHITE}• Moyenne clients/réseau: {Fore.CYAN}{total_clients/len(self.networks):.1f}")
    
    def select_network_menu(self, network_num):
        """
        Menu interactif après sélection d'un réseau
        Retourne l'action choisie et le réseau
        """
        if network_num < 1 or network_num > len(self.networks):
            print(f"{Fore.RED}[✗] Numéro invalide")
            return None, None
        
        network = self.networks[network_num - 1]
        
        # Afficher les détails du réseau
        self.show_network_details(network_num)
        
        print(f"\n{Fore.CYAN}{'═' * 80}")
        print(f"{Fore.YELLOW} ACTIONS POSSIBLES POUR CE RÉSEAU")
        print(f"{Fore.CYAN}{'═' * 80}")
        
        print(f"\n{Fore.CYAN} VEILLEZ CHOIR L'OPTION QUI VOUS CONVIENT")
        print(f"  {Fore.WHITE}[{Fore.GREEN}1{Fore.WHITE}] Déauthentifier un client")
        print(f"  {Fore.WHITE}[{Fore.GREEN}2{Fore.WHITE}] Déauthentifier tous les clients")
        print(f"  {Fore.WHITE}[{Fore.GREEN}3{Fore.WHITE}] Capturer le handshake WPA2")
        print(f"  {Fore.WHITE}[{Fore.GREEN}4{Fore.WHITE}] Tenter de cracker le mot de passe")
        print(f"  {Fore.WHITE}[{Fore.GREEN}5{Fore.WHITE}] Retourner à la liste")
        print(f"  {Fore.WHITE}[{Fore.GREEN}6{Fore.WHITE}] Quitter")
        
        while True:
            try:
                choix = input(f"\n{Fore.YELLOW}[?] Votre choix s'il vous plaît de 1-6 :) ").strip()
                
                if choix == '1':
                    return 'deauth_client', network
                elif choix == '2':
                    return 'deauth_all', network
                elif choix == '3':
                    return 'capture_handshake', network
                elif choix == '4':
                    return 'crack_password', network
                elif choix == '5':
                    return 'back', network
                elif choix == '6':
                    return 'quit', network
                else:
                    print(f"{Fore.RED}[✗] votre hoix est invalide veillez resaisir un choix correct ")
                    
            except KeyboardInterrupt:
                return 'back', network
    
    def show_network_details(self, network_num):
        """Affiche les détails complets d'un réseau"""
        if network_num < 1 or network_num > len(self.networks):
            print(f"{Fore.RED}[✗] Numéro invalide")
            return None
        
        network = self.networks[network_num - 1]
        
        print(f"\n{Fore.CYAN}{'═' * 80}")
        print(f"{Fore.YELLOW} 📡 RÉSEAU #{network_num} - {network['essid']}")
        print(f"{Fore.CYAN}{'═' * 80}")
        
        print(f"\n{Fore.CYAN}📋 INFORMATIONS PRINCIPALES:")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Nom complet: {Fore.GREEN}{network['essid']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}BSSID: {Fore.MAGENTA}{network['bssid']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Fabricant: {Fore.CYAN}{network['manufacturer']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Sécurité: {network['security_icon']} {Fore.WHITE}{network['security']}")
        
        print(f"\n{Fore.CYAN}📶 CARACTÉRISTIQUES TECHNIQUES:")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Fréquence: {Fore.MAGENTA}{network['frequency']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Canal: {Fore.MAGENTA}{network['channel']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Puissance: {Fore.WHITE}{network['power']} dBm")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Distance: {Fore.WHITE}{network['distance']}")
        print(f"  {Fore.WHITE}• {Fore.CYAN}Qualité: {network['quality_stars']} {Fore.WHITE}({network['quality']})")
        
        print(f"\n{Fore.CYAN}👥 CLIENT(S) CONNECTÉ(S): {Fore.CYAN}{network['clients']}")
        if network['client_macs']:
            for i, client in enumerate(network['client_macs'], 1):
                client_manuf = self.get_manufacturer(client)
                print(f"  {Fore.WHITE}{i:2}. {Fore.MAGENTA}{client} {Fore.CYAN}({client_manuf})")
        else:
            print(f"  {Fore.YELLOW}Aucun client détecté")
        
        return network
    
    def perform_deauth(self, network, client_mac=None, count=10):
        """
        Exécute une déauthentification
        Retourne True si succès
        """
        if not self.interface_mon:
            print(f"{Fore.RED}[✗] Mode monitor non activé")
            return False
        
        print(f"\n{Fore.CYAN}[*] Préparation de la déauthentification...")
        
        if client_mac:
            print(f"{Fore.WHITE}   Mode: {Fore.YELLOW}Ciblé")
            print(f"{Fore.WHITE}   Client: {Fore.MAGENTA}{client_mac}")
        else:
            print(f"{Fore.WHITE}   Mode: {Fore.RED}Broadcast (tous les clients)")
        
        print(f"{Fore.WHITE}   Réseau: {Fore.GREEN}{network['essid']}")
        print(f"{Fore.WHITE}   BSSID: {Fore.YELLOW}{network['bssid']}")
        print(f"{Fore.WHITE}   Paquets: {Fore.CYAN}{count}")
        
        # Importer le module deauth
        try:
            import modules.deauth
            DeauthAttack = modules.deauth.DeauthAttack
        except ImportError:
            print(f"{Fore.RED}[✗] Module deauth non disponible")
            return False
        
        # Créer l'attaque
        deauth = DeauthAttack(self.interface_mon, network['bssid'], client_mac)
        
        # Exécuter
        print(f"\n{Fore.CYAN}[*] Envoi des paquets...")
        if deauth.send_deauth(count=count):
            print(f"{Fore.GREEN}[✓] la déauthentification a réussie")
            return True
        else:
            print(f"{Fore.RED}[✗] Échec de la déauthentification")
            return False
    
    def save_results(self, filename=None):
        """Sauvegarde les résultats"""
        import json
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"wifi_scan_{timestamp}.json"
        
        data = {
            'scan_date': datetime.now().isoformat(),
            'interface': self.interface,
            'total_networks': len(self.networks),
            'networks': []
        }
        
        for net in self.networks:
            net_copy = net.copy()
            if 'security_icon' in net_copy:
                net_copy['security_icon'] = str(net_copy['security_icon'])
            if 'quality_stars' in net_copy:
                net_copy['quality_stars'] = str(net_copy['quality_stars'])
            data['networks'].append(net_copy)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}[✓] Lesrésultats sont sauvegardés dans {filename}")
        return filename
    
    def cleanup(self):
        """Nettoyage"""
        if self.interface_mon:
            print(f"{Fore.CYAN}[*] Nettoyage de {self.interface_mon}...")
            subprocess.run(['airmon-ng', 'stop', self.interface_mon],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            print(f"{Fore.GREEN}[✓] Interface nettoyée")
