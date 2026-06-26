"""
=============================================================
  APLIKASI MANAJEMEN ANTRIAN RUMAH SAKIT
  Final Project - Struktur Data & Algoritma
  Database: antrian.csv
=============================================================
  Fitur:
  - Queue FIFO untuk pemanggilan pasien
  - Hash Map / Dictionary untuk atribut pasien
  - CRUD (Create, Read, Update, Delete)
  - Searching (by ID) & Sorting (by nomor antrian)
  - Penyimpanan persisten via CSV
=============================================================
"""

import csv
import os
import sys
from collections import OrderedDict
from datetime import datetime

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
CSV_FILE = "antrian.csv"
FIELDNAMES = ["no_antrian", "id_pasien", "nama", "poli", "waktu_daftar", "status"]

DAFTAR_POLI = {
    "1": "Umum",
    "2": "Anak",
    "3": "Gigi",
    "4": "Mata",
    "5": "Bedah",
    "6": "Jantung",
    "7": "Kandungan",
}

# ─────────────────────────────────────────────
#  UTILITAS TAMPILAN
# ─────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def garis(karakter="─", panjang=60):
    return karakter * panjang

def header(judul):
    print("\n" + garis("═"))
    print(f"  🏥  {judul}")
    print(garis("═"))

def pesan_sukses(teks):
    print(f"\n  ✅  {teks}")

def pesan_error(teks):
    print(f"\n  ❌  {teks}")

def pesan_info(teks):
    print(f"\n  ℹ️   {teks}")

def tekan_enter():
    input("\n  Tekan [Enter] untuk kembali ke menu...")

# ─────────────────────────────────────────────
#  STRUKTUR DATA: QUEUE (FIFO)
# ─────────────────────────────────────────────
class AntrianQueue:
    """
    Implementasi Queue dengan prinsip FIFO.
    Setiap elemen adalah dictionary (Hash Map) yang merepresentasikan pasien.
    """

    def __init__(self):
        # Menggunakan list sebagai underlying structure queue
        self._queue: list[dict] = []

    def enqueue(self, pasien: dict):
        """Menambah pasien ke belakang antrian (FIFO - masuk belakang)."""
        self._queue.append(pasien)

    def dequeue(self) -> dict | None:
        """Mengambil & menghapus pasien dari depan antrian (FIFO - keluar depan)."""
        if self.is_empty():
            return None
        return self._queue.pop(0)

    def peek(self) -> dict | None:
        """Melihat pasien terdepan tanpa menghapus."""
        if self.is_empty():
            return None
        return self._queue[0]

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)

    def to_list(self) -> list[dict]:
        """Mengembalikan salinan list queue."""
        return list(self._queue)

    def load_from_list(self, data: list[dict]):
        """Mengisi queue dari list (dipakai saat load CSV)."""
        self._queue = list(data)

    # ── Searching: Linear Search berdasarkan id_pasien ──
    def cari_by_id(self, id_pasien: str) -> tuple[int, dict | None]:
        """
        Linear Search O(n).
        Mengembalikan (index, data_pasien) atau (-1, None) jika tidak ditemukan.
        """
        target = id_pasien.upper()
        for idx, pasien in enumerate(self._queue):
            if pasien["id_pasien"].upper() == target:
                return idx, pasien
        return -1, None

    # ── Sorting: Selection Sort berdasarkan no_antrian ──
    def sort_by_no_antrian(self):
        """
        Selection Sort O(n²) — mengurutkan queue berdasarkan no_antrian (ascending).
        Digunakan untuk memastikan urutan tampil konsisten setelah load CSV.
        """
        n = len(self._queue)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                if int(self._queue[j]["no_antrian"]) < int(self._queue[min_idx]["no_antrian"]):
                    min_idx = j
            self._queue[i], self._queue[min_idx] = self._queue[min_idx], self._queue[i]


# ─────────────────────────────────────────────
#  FUNGSI CSV (DATABASE)
# ─────────────────────────────────────────────
def inisialisasi_csv():
    """Membuat file CSV beserta header jika belum ada."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def baca_csv() -> list[dict]:
    """Membaca semua data dari CSV dan mengembalikan list of dict."""
    inisialisasi_csv()
    pasien_list = []
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pasien_list.append(dict(row))
    return pasien_list

def tulis_csv(data: list[dict]):
    """Menulis ulang seluruh data ke CSV (overwrite)."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(data)

def nomor_antrian_berikutnya(data: list[dict]) -> int:
    """Menghitung nomor antrian berikutnya (auto-increment sederhana)."""
    if not data:
        return 1
    nomor_list = [int(p["no_antrian"]) for p in data]
    return max(nomor_list) + 1


# ─────────────────────────────────────────────
#  LOAD DATA KE QUEUE
# ─────────────────────────────────────────────
def load_queue(queue: AntrianQueue):
    """Membaca CSV dan memuat data yang berstatus 'Menunggu' ke dalam queue."""
    semua_data = baca_csv()
    menunggu = [p for p in semua_data if p["status"] == "Menunggu"]
    queue.load_from_list(menunggu)
    queue.sort_by_no_antrian()   # Sorting saat load


# ─────────────────────────────────────────────
#  OPERASI CRUD
# ─────────────────────────────────────────────

# ── CREATE ──────────────────────────────────
def daftarkan_pasien(queue: AntrianQueue):
    header("PENDAFTARAN PASIEN BARU")

    # Input ID Pasien
    while True:
        id_pasien = input("  Masukkan ID Pasien (contoh: P001): ").strip().upper()
        if not id_pasien:
            pesan_error("ID Pasien tidak boleh kosong.")
            continue
        # Cek duplikat ID di queue
        _, existing = queue.cari_by_id(id_pasien)
        if existing:
            pesan_error(f"Pasien dengan ID '{id_pasien}' sudah ada dalam antrian!")
            tekan_enter()
            return
        break

    # Input Nama
    while True:
        nama = input("  Masukkan Nama Pasien     : ").strip().title()
        if not nama:
            pesan_error("Nama tidak boleh kosong.")
        else:
            break

    # Pilih Poli
    print("\n  Daftar Poli:")
    for kode, poli in DAFTAR_POLI.items():
        print(f"    [{kode}] {poli}")
    while True:
        pilihan_poli = input("  Pilih Poli (1-7)          : ").strip()
        if pilihan_poli in DAFTAR_POLI:
            poli = DAFTAR_POLI[pilihan_poli]
            break
        pesan_error("Pilihan tidak valid. Masukkan angka 1-7.")

    # Buat Hash Map / Dictionary pasien
    semua_data = baca_csv()
    no_antrian = nomor_antrian_berikutnya(semua_data)
    waktu_daftar = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pasien: dict = {
        "no_antrian"   : str(no_antrian),
        "id_pasien"    : id_pasien,
        "nama"         : nama,
        "poli"         : poli,
        "waktu_daftar" : waktu_daftar,
        "status"       : "Menunggu",
    }

    # Enqueue ke struktur Queue
    queue.enqueue(pasien)

    # Simpan ke CSV
    semua_data.append(pasien)
    tulis_csv(semua_data)

    print(f"\n  {garis('─')}")
    pesan_sukses(f"Pasien berhasil didaftarkan!")
    print(f"  {'Nomor Antrian':<20}: {no_antrian}")
    print(f"  {'ID Pasien':<20}: {id_pasien}")
    print(f"  {'Nama':<20}: {nama}")
    print(f"  {'Poli':<20}: {poli}")
    print(f"  {'Waktu Daftar':<20}: {waktu_daftar}")
    print(f"  {garis('─')}")
    tekan_enter()


# ── READ ────────────────────────────────────
def tampilkan_antrian(queue: AntrianQueue):
    header("DAFTAR ANTRIAN SAAT INI")

    if queue.is_empty():
        pesan_info("Tidak ada pasien dalam antrian.")
        tekan_enter()
        return

    print(f"\n  Total pasien menunggu: {queue.size()} orang")
    print(f"  {garis()}")
    print(f"  {'No':<5} {'No.Antrian':<12} {'ID Pasien':<12} {'Nama':<22} {'Poli':<12} {'Waktu Daftar'}")
    print(f"  {garis()}")

    for idx, pasien in enumerate(queue.to_list(), start=1):
        marker = "◀ TERDEPAN" if idx == 1 else ""
        print(
            f"  {idx:<5} "
            f"{pasien['no_antrian']:<12} "
            f"{pasien['id_pasien']:<12} "
            f"{pasien['nama']:<22} "
            f"{pasien['poli']:<12} "
            f"{pasien['waktu_daftar']}  {marker}"
        )

    print(f"  {garis()}")
    tekan_enter()


# ── UPDATE ──────────────────────────────────
def update_pasien(queue: AntrianQueue):
    header("UPDATE DATA PASIEN")

    if queue.is_empty():
        pesan_info("Antrian kosong, tidak ada yang bisa diupdate.")
        tekan_enter()
        return

    id_cari = input("  Masukkan ID Pasien yang ingin diubah: ").strip().upper()
    idx, pasien = queue.cari_by_id(id_cari)

    if pasien is None:
        pesan_error(f"Pasien dengan ID '{id_cari}' tidak ditemukan dalam antrian.")
        tekan_enter()
        return

    print(f"\n  Data saat ini:")
    print(f"  {'No. Antrian':<20}: {pasien['no_antrian']}")
    print(f"  {'ID Pasien':<20}: {pasien['id_pasien']}")
    print(f"  {'Nama':<20}: {pasien['nama']}")
    print(f"  {'Poli':<20}: {pasien['poli']}")
    print(f"\n  (Kosongkan input untuk tidak mengubah field tersebut)")

    # Update Nama
    nama_baru = input(f"  Nama baru [{pasien['nama']}]: ").strip().title()
    if nama_baru:
        pasien["nama"] = nama_baru

    # Update Poli
    print("\n  Daftar Poli:")
    for kode, poli in DAFTAR_POLI.items():
        print(f"    [{kode}] {poli}")
    pilihan_poli = input(f"  Poli baru (1-7) [{pasien['poli']}]: ").strip()
    if pilihan_poli in DAFTAR_POLI:
        pasien["poli"] = DAFTAR_POLI[pilihan_poli]

    # Update di queue (in-place melalui referensi list)
    queue.to_list()[idx].update(pasien)  # sudah dimodifikasi via referensi

    # Sinkronisasi ke CSV
    semua_data = baca_csv()
    for row in semua_data:
        if row["id_pasien"].upper() == id_cari and row["status"] == "Menunggu":
            row["nama"] = pasien["nama"]
            row["poli"] = pasien["poli"]
            break
    tulis_csv(semua_data)

    pesan_sukses("Data pasien berhasil diperbarui!")
    tekan_enter()


# ── DELETE (Panggil Pasien) ──────────────────
def panggil_pasien(queue: AntrianQueue):
    header("PANGGIL PASIEN BERIKUTNYA")

    if queue.is_empty():
        pesan_info("Tidak ada pasien dalam antrian.")
        tekan_enter()
        return

    terdepan = queue.peek()
    print(f"\n  Pasien berikutnya:")
    print(f"  {'No. Antrian':<20}: {terdepan['no_antrian']}")
    print(f"  {'ID Pasien':<20}: {terdepan['id_pasien']}")
    print(f"  {'Nama':<20}: {terdepan['nama']}")
    print(f"  {'Poli':<20}: {terdepan['poli']}")

    konfirmasi = input("\n  Konfirmasi panggil pasien ini? (y/n): ").strip().lower()
    if konfirmasi != "y":
        pesan_info("Pembatalan. Pasien tidak dipanggil.")
        tekan_enter()
        return

    # Dequeue dari queue (FIFO - ambil dari depan)
    dipanggil = queue.dequeue()

    # Update status di CSV menjadi "Dipanggil"
    semua_data = baca_csv()
    for row in semua_data:
        if row["id_pasien"] == dipanggil["id_pasien"] and row["no_antrian"] == dipanggil["no_antrian"]:
            row["status"] = "Dipanggil"
            break
    tulis_csv(semua_data)

    print(f"\n  {'═'*50}")
    print(f"  🔔  MEMANGGIL PASIEN:")
    print(f"      Nomor Antrian : {dipanggil['no_antrian']}")
    print(f"      Nama          : {dipanggil['nama']}")
    print(f"      Poli          : {dipanggil['poli']}")
    print(f"  {'═'*50}")
    print(f"\n  Sisa antrian   : {queue.size()} pasien")
    tekan_enter()


# ── SEARCHING ───────────────────────────────
def cari_pasien(queue: AntrianQueue):
    header("PENCARIAN PASIEN (by ID)")

    id_cari = input("  Masukkan ID Pasien: ").strip().upper()
    idx, pasien = queue.cari_by_id(id_cari)

    if pasien is None:
        pesan_error(f"Pasien dengan ID '{id_cari}' tidak ditemukan dalam antrian aktif.")
    else:
        print(f"\n  ✅  Pasien ditemukan! (Posisi antrian: #{idx + 1})")
        print(f"  {garis()}")
        print(f"  {'No. Antrian':<20}: {pasien['no_antrian']}")
        print(f"  {'ID Pasien':<20}: {pasien['id_pasien']}")
        print(f"  {'Nama':<20}: {pasien['nama']}")
        print(f"  {'Poli':<20}: {pasien['poli']}")
        print(f"  {'Waktu Daftar':<20}: {pasien['waktu_daftar']}")
        print(f"  {'Status':<20}: {pasien['status']}")
        print(f"  {garis()}")

    tekan_enter()


# ── RIWAYAT SEMUA PASIEN ─────────────────────
def tampilkan_riwayat():
    header("RIWAYAT SEMUA PASIEN (CSV)")

    semua_data = baca_csv()
    if not semua_data:
        pesan_info("Belum ada data pasien.")
        tekan_enter()
        return

    print(f"\n  {'No':<5} {'No.Ant':<8} {'ID':<10} {'Nama':<22} {'Poli':<12} {'Status':<12} {'Waktu Daftar'}")
    print(f"  {garis(panjang=90)}")
    for idx, p in enumerate(semua_data, 1):
        status_icon = "✅" if p["status"] == "Dipanggil" else "⏳"
        print(
            f"  {idx:<5} "
            f"{p['no_antrian']:<8} "
            f"{p['id_pasien']:<10} "
            f"{p['nama']:<22} "
            f"{p['poli']:<12} "
            f"{status_icon} {p['status']:<10} "
            f"{p['waktu_daftar']}"
        )
    print(f"  {garis(panjang=90)}")
    print(f"  Total: {len(semua_data)} pasien (termasuk yang sudah dipanggil)")
    tekan_enter()


# ─────────────────────────────────────────────
#  MENU UTAMA
# ─────────────────────────────────────────────
def menu_utama(queue: AntrianQueue):
    while True:
        clear()
        print(f"\n  {'═'*50}")
        print(f"  🏥   SISTEM ANTRIAN RUMAH SAKIT")
        print(f"  {'─'*50}")
        print(f"  File Database : {CSV_FILE}")
        print(f"  Antrian aktif : {queue.size()} pasien")
        if not queue.is_empty():
            print(f"  Terdepan      : {queue.peek()['nama']} ({queue.peek()['poli']})")
        print(f"  {'═'*50}")
        print()
        print("  [1] Daftarkan Pasien Baru       ")
        print("  [2] Tampilkan Antrian           ")
        print("  [3] Update Data Pasien          ")
        print("  [4] Panggil Pasien Berikutnya   ")
        print("  [5] Cari Pasien by ID           ")
        print("  [6] Riwayat Semua Pasien        ")
        print("  [0] Keluar")
        print()

        pilihan = input("  Pilih menu [0-6]: ").strip()

        if pilihan == "1":
            clear()
            daftarkan_pasien(queue)
        elif pilihan == "2":
            clear()
            tampilkan_antrian(queue)
        elif pilihan == "3":
            clear()
            update_pasien(queue)
        elif pilihan == "4":
            clear()
            panggil_pasien(queue)
        elif pilihan == "5":
            clear()
            cari_pasien(queue)
        elif pilihan == "6":
            clear()
            tampilkan_riwayat()
        elif pilihan == "0":
            clear()
            print("\n  Terima kasih telah menggunakan Sistem Antrian Rumah Sakit.")
            print("  Sampai jumpa! 👋\n")
            sys.exit(0)
        else:
            pesan_error("Pilihan tidak valid. Masukkan angka 0-6.")
            tekan_enter()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    clear()
    print("\n  Memuat data dari CSV...")
    queue = AntrianQueue()
    inisialisasi_csv()
    load_queue(queue)
    print(f"  {queue.size()} pasien aktif berhasil dimuat.")
    menu_utama(queue)


if __name__ == "__main__":
    main()