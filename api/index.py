#!/usr/bin/env python3
"""
Telegram CSV Lookup
Baca Telegram_27.csv (28M+ baris), cari by User_ID atau username.
Format kolom: First|Last|Phone|Phone2|Username|User_ID|???|Was_Online
"""

import csv
import os
import sys
import time
import pickle
import mmap
from pathlib import Path

CSV_FILE = "Telegram_27.csv"
INDEX_FILE = "Telegram_27.idx"

# ─── Deteksi separator otomatis ───────────────────────────────────────────────
def detect_sep(filepath):
    with open(filepath, "rb") as f:
        sample = f.read(2048).decode("utf-8", errors="replace")
    for sep in ["|", ",", "\t", ";"]:
        if sample.count(sep) > 5:
            return sep
    return "|"

# ─── Build index (offset per baris) — cuma sekali ─────────────────────────────
def build_index(filepath, index_path):
    print(f"[*] Building index dari {filepath} ...")
    print("    (Ini hanya dilakukan SEKALI, berikutnya langsung cepat)")
    start = time.time()
    offsets = []
    with open(filepath, "rb") as f:
        offset = 0
        for line in f:
            offsets.append(offset)
            offset += len(line)
    with open(index_path, "wb") as f:
        pickle.dump(offsets, f)
    elapsed = time.time() - start
    print(f"[+] Index selesai: {len(offsets):,} baris dalam {elapsed:.1f}s")
    return offsets

# ─── Load index ───────────────────────────────────────────────────────────────
def load_index(index_path):
    print("[*] Loading index ...")
    with open(index_path, "rb") as f:
        return pickle.load(f)

# ─── Baca satu baris dari offset ──────────────────────────────────────────────
def read_line(mm, offset):
    mm.seek(offset)
    return mm.readline().decode("utf-8", errors="replace").rstrip("\n\r")

# ─── Parse baris jadi dict ────────────────────────────────────────────────────
def parse_row(line, sep, header):
    parts = line.split(sep)
    # Pad kalau kolom kurang
    while len(parts) < len(header):
        parts.append("")
    return dict(zip(header, parts))

# ─── Format hasil ─────────────────────────────────────────────────────────────
def format_result(row, line_num):
    out = [f"\n{'='*50}", f"  Baris #{line_num:,}", f"{'='*50}"]
    for k, v in row.items():
        v = v.strip()
        if v:
            out.append(f"  {k:<15}: {v}")
    out.append("=" * 50)
    return "\n".join(out)

# ─── Scan penuh (fallback kalau gak ada field User_ID di header) ───────────────
def scan_full(filepath, sep, query, header, max_results=50):
    results = []
    query_low = query.lower().strip()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=sep)
        for i, parts in enumerate(reader):
            if i == 0:
                continue  # skip header
            row_str = sep.join(parts).lower()
            if query_low in row_str:
                while len(parts) < len(header):
                    parts.append("")
                results.append((i + 1, dict(zip(header, parts))))
                if len(results) >= max_results:
                    break
    return results

# ─── Cari dengan mmap + scan (tercepat untuk keyword search) ──────────────────
def search_mmap(filepath, query, sep, header, max_results=50):
    results = []
    query_bytes = query.lower().encode("utf-8", errors="replace")
    line_num = 0

    with open(filepath, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        # Skip header
        mm.readline()
        line_num = 1

        while True:
            line_bytes = mm.readline()
            if not line_bytes:
                break
            line_num += 1
            if query_bytes in line_bytes.lower():
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\n\r")
                parts = line.split(sep)
                while len(parts) < len(header):
                    parts.append("")
                results.append((line_num, dict(zip(header, parts))))
                if len(results) >= max_results:
                    break
        mm.close()
    return results

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(CSV_FILE):
        print(f"[!] File '{CSV_FILE}' tidak ditemukan.")
        print(f"    Jalankan script ini di folder yang sama dengan {CSV_FILE}")
        sys.exit(1)

    sep = detect_sep(CSV_FILE)
    print(f"[*] Separator terdeteksi: '{sep}'")

    # Baca header
    with open(CSV_FILE, "r", encoding="utf-8", errors="replace") as f:
        raw_header = f.readline().rstrip("\n\r")
    header = raw_header.split(sep)
    print(f"[*] Kolom ({len(header)}): {header}")

    # Build/load index
    if os.path.exists(INDEX_FILE):
        offsets = load_index(INDEX_FILE)
    else:
        offsets = build_index(CSV_FILE, INDEX_FILE)

    total_rows = len(offsets) - 1  # minus header
    print(f"[*] Total data: {total_rows:,} baris")
    print(f"[*] File: {Path(CSV_FILE).stat().st_size / 1e9:.2f} GB\n")

    # Kolom yang bisa dicari langsung
    id_cols = [h for h in header if any(x in h.lower() for x in ["user_id", "userid", "id"])]
    user_cols = [h for h in header if any(x in h.lower() for x in ["username", "user_name"])]
    phone_cols = [h for h in header if any(x in h.lower() for x in ["phone", "hp", "nomor"])]

    print("Kolom ID terdeteksi :", id_cols or "tidak ada")
    print("Kolom Username      :", user_cols or "tidak ada")
    print("Kolom Phone         :", phone_cols or "tidak ada")
    print()

    # ─── Loop interaktif ──────────────────────────────────────────────────────
    with open(CSV_FILE, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            try:
                query = input("🔍 Masukkan query (User_ID / username / nomor / 'q' keluar): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[*] Keluar.")
                break

            if query.lower() in ("q", "quit", "exit"):
                print("[*] Keluar.")
                break
            if not query:
                continue

            start = time.time()
            print(f"[*] Mencari '{query}' ...")

            results = search_mmap(CSV_FILE, query, sep, header, max_results=50)

            elapsed = time.time() - start

            if not results:
                print(f"[-] Tidak ditemukan. ({elapsed:.2f}s)")
            else:
                print(f"[+] Ditemukan {len(results)} hasil dalam {elapsed:.2f}s:")
                for line_num, row in results:
                    print(format_result(row, line_num))

                if len(results) >= 50:
                    print("\n[!] Hasil dibatasi 50. Perjelas query untuk hasil lebih spesifik.\n")

        mm.close()

if __name__ == "__main__":
    main()