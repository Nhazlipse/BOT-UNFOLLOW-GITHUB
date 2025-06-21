import os
import requests
import csv
import time
import sys
import random
from colorama import init, Fore, Style
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)

class Tampilan:
    """Kelas untuk mengelola semua output tampilan dan warna."""
    PROMPT = Fore.YELLOW + Style.BRIGHT
    INFO = Fore.CYAN
    SUKSES = Fore.GREEN
    PERINGATAN = Fore.YELLOW
    GAGAL = Fore.RED
    RESET = Style.RESET_ALL

class GitHubRelationshipManager:
    """
    Hello Sir. i hope u enjoy using this tool. dont forget to leave a STAR if u like it.
    """
    def __init__(self, username, token):
        """Konstruktor untuk inisialisasi tool."""
        self.username = username
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {token}"
        }
        self.following = set()
        self.followers = set()
        self.non_followers = []
        
        self.banner = f"""
{Tampilan.INFO}====================================================
        Bot Auto Unfollow Github
====================================================
{Tampilan.RESET}
 Pengguna Aktif : {Tampilan.PROMPT}{self.username}{Tampilan.RESET}
 Dibuat oleh    : {Tampilan.PROMPT}nhazlipse{Tampilan.RESET}
 GitHub         : {Tampilan.PROMPT}https://github.com/Nhazlipse{Tampilan.RESET}

{Tampilan.INFO}----------------------------------------------------{Tampilan.RESET}
        """
    

    def _jalankan_api_request(self, endpoint):
        """Metode internal untuk menangani semua request ke API GitHub."""
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()  # Akan raise error jika status code 4xx atau 5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Tampilan.GAGAL}[GAGAL] Terjadi kesalahan saat mengakses API: {e}")
            return None

    def _ambil_data_berhalaman(self, tipe_relasi):
        """Mengambil semua data dari endpoint yang memiliki paginasi (halaman)."""
        data_list = []
        page = 1
        while True:
            endpoint = f"https://api.github.com/users/{self.username}/{tipe_relasi}?per_page=100&page={page}"
            page_data = self._jalankan_api_request(endpoint)
            
            if page_data is None or not page_data:
                break
                
            data_list.extend([user['login'] for user in page_data])
            page += 1
        return set(data_list)

    def _tampilkan_proses_loading(self, pesan, durasi=1):
        """PERUBAHAN TAMPILAN: Spinner loading baru."""
        spinner_chars = ['.', 'o', 'O', 'o']
        t_end = time.time() + durasi
        i = 0
        while time.time() < t_end:
            char = spinner_chars[i % len(spinner_chars)]
            sys.stdout.write(f"\r{Tampilan.INFO}{pesan} {char}")
            sys.stdout.flush()
            time.sleep(0.25)
            i += 1
        sys.stdout.write(f"\r{Tampilan.SUKSES}{pesan} [SELESAI]\n")
        sys.stdout.flush()

    def analisis_koneksi(self):
        """Menganalisis dan menemukan pengguna yang tidak follow back."""
        print(self.banner)
        self._tampilkan_proses_loading("[ANALISIS] Mengambil daftar following...")
        self.following = self._ambil_data_berhalaman("following")
        
        self._tampilkan_proses_loading("[ANALISIS] Mengambil daftar followers...")
        self.followers = self._ambil_data_berhalaman("followers")
        
        if not self.following:
            print(f"{Tampilan.PERINGATAN}[INFO] Gagal mengambil data 'following' atau Anda tidak mengikuti siapa pun.")
            return False

        self.non_followers = sorted(list(self.following - self.followers))
        
        if not self.non_followers:
            print(f"{Tampilan.SUKSES}Selamat! Semua yang Anda ikuti juga mengikuti Anda kembali.")
            return False
            
        print(f"\n{Tampilan.PERINGATAN}[DITEMUKAN] {len(self.non_followers)} pengguna yang tidak mengikuti Anda kembali.")
        return True

    def _eksekusi_unfollow(self, username):
        """Metode internal untuk melakukan satu aksi unfollow."""
        endpoint = f"https://api.github.com/user/following/{username}"
        try:
            response = requests.delete(endpoint, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            return False

    def jalankan_mode_interaktif(self):
        """Menjalankan proses unfollow satu per satu dengan konfirmasi."""
        print("\n--- Mode Interaktif: Konfirmasi Setiap Aksi ---")
        unfollowed_count = 0
        for user in self.non_followers:
            prompt = f"{Tampilan.PROMPT}Hapus {user}? (y/n/q untuk keluar): {Tampilan.RESET}"
            choice = input(prompt).lower().strip()
            
            if choice == 'y':
                if self._eksekusi_unfollow(user):
                    print(f"{Tampilan.SUKSES}[SUKSES] {user} telah di-unfollow.")
                    unfollowed_count += 1
                else:
                    print(f"{Tampilan.GAGAL}[GAGAL] Gagal unfollow {user}.")

                # Delay acak ben ndak dikiro bot mbod jembod
                time.sleep(random.uniform(1, 2))
            elif choice == 'q':
                print(f"{Tampilan.INFO}Proses interaktif dihentikan.")
                break
            else:
                print(f"{Tampilan.INFO}[SKIP] Melewati {user}.")
        print(f"\n{Tampilan.SUKSES}Total pengguna di-unfollow: {unfollowed_count}")

    def jalankan_mode_otomatis(self):
        """Menjalankan proses unfollow massal dengan batch dan jeda."""
        try:
            batch_size = int(input(f"{Tampilan.PROMPT}Jumlah unfollow per sesi (misal: 15): {Tampilan.RESET}"))
            delay = int(input(f"{Tampilan.PROMPT}Jeda antar sesi (dalam menit, misal: 10): {Tampilan.RESET}"))
        except ValueError:
            print(f"{Tampilan.GAGAL}Input tidak valid. Harap masukkan angka. Proses dibatalkan.")
            return

        unfollowed_count = 0
        for i in range(0, len(self.non_followers), batch_size):
            batch = self.non_followers[i:i + batch_size]
            print(f"\n{Tampilan.INFO}--- Memulai Sesi {i//batch_size + 1}/{len(self.non_followers)//batch_size + 1} ---")
            for user in batch:
                print(f"Memproses unfollow untuk: {user}...")
                if self._eksekusi_unfollow(user):
                    print(f"{Tampilan.SUKSES}[SUKSES] {user} telah di-unfollow.")
                    unfollowed_count += 1
                else:
                    print(f"{Tampilan.GAGAL}[GAGAL] Gagal unfollow {user}.")
                time.sleep(random.uniform(1.5, 2.5))
            
            # Logika jeda setelah sesi selesai
            if i + batch_size < len(self.non_followers):
                print(f"\n{Tampilan.INFO}Sesi selesai. Memulai jeda selama {delay} menit.")
                for remaining in range(delay * 60, 0, -1):
                    sys.stdout.write(f"\r{Tampilan.PERINGATAN}Waktu tunggu: {remaining//60:02d}:{remaining%60:02d}...")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\rJeda selesai, melanjutkan sesi berikutnya.          \n")
        
        print(f"\n{Tampilan.SUKSES}Proses otomatis selesai. Total di-unfollow: {unfollowed_count}")

    def jalankan(self):
        """Metode utama untuk menjalankan keseluruhan alur program."""
        if not self.analisis_koneksi():
            return

        # MENU NE IKI COK
        print("\n" + "="*50)
        print(f"{Tampilan.PROMPT}Pilih Tindakan Selanjutnya:{Tampilan.RESET}")
        print(" 1. Unfollow Interaktif (Satu per satu)")
        print(" 2. Unfollow Otomatis (Per Sesi)")
        print(" 0. Keluar")
        
        pilihan = input(f"{Tampilan.PROMPT}Masukkan pilihan Anda (1/2/0): {Tampilan.RESET}").strip()
        
        if pilihan == '1':
            self.jalankan_mode_interaktif()
        elif pilihan == '2':
            self.jalankan_mode_otomatis()
        else:
            print(f"{Tampilan.INFO}Terima kasih telah menggunakan tool ini.")
            
if __name__ == "__main__":
    # 1. Muat kredensial dari file .env.local
    load_dotenv(dotenv_path=".env.local")
    USERNAME = os.getenv("GITHUB_USERNAME")
    TOKEN = os.getenv("GITHUB_TOKEN")

    # 2. Lakukan validasi. Jika gagal, program berhenti.
    if not USERNAME or not TOKEN:
        print(f"{Tampilan.GAGAL}[FATAL] Variabel GITHUB_USERNAME atau GITHUB_TOKEN tidak ditemukan di .env.local")
        sys.exit(1)
    
    # 3. JIKA VALIDASI BERHASIL, jalankan program utama.
    # Kode ini sekarang berada di luar blok 'if' di atas.
    try:
        print(f"{Tampilan.INFO}Mencoba menjalankan manager untuk pengguna: {Tampilan.PROMPT}{USERNAME}{Tampilan.RESET}")
        manager = GitHubRelationshipManager(USERNAME, TOKEN)
        manager.jalankan()
    except KeyboardInterrupt:
        # Menangani jika pengguna menekan Ctrl+C
        print(f"\n\n{Tampilan.PERINGATAN}Program dihentikan oleh pengguna.")
        sys.exit(0)

    
    if not USERNAME or not TOKEN:
        print(f"{Fore.RED}[FATAL] Variabel GITHUB_USERNAME atau GITHUB_TOKEN tidak ditemukan di .env.local")
        sys.exit(1)
        print(f"{Fore.CYAN}Mencoba menjalankan manager untuk pengguna: {Fore.YELLOW}{USERNAME}{Style.RESET_ALL}")
        manager = GitHubRelationshipManager(USERNAME, TOKEN)
        manager.jalankan()
