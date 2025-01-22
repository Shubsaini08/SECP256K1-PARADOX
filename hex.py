import os
import re
from multiprocessing import Pool, cpu_count

# Kompilierte Regex für mehrfache Nutzung
KEYS_PATTERN = re.compile(r"Keys:\s*(.*?)")

def dec_to_hex(dec_val: int) -> str:
    """
    Konvertiert einen ganzzahligen Dezimalwert in
    eine 64-stellige Hex-Darstellung (Kleinbuchstaben).
    """
    return format(dec_val, 'x').zfill(64)

def process_decimal(dec_str: str) -> list[str]:
    """
    Wandelt den Dezimalstring in int um und gibt eine Liste
    der Hexwerte für (dec-1), dec, (dec+1) zurück.
    Falls der String kein gültiger int ist, wird eine leere Liste zurückgegeben.
    """
    try:
        dec = int(dec_str)
    except ValueError:
        return []

    # Für den Fall, dass dec = 0 ist, wollen wir (dec - 1) vermeiden? 
    # Bei negativen Zahlen ist es meist kein Problem, aber du kannst es anpassen.
    return [
        dec_to_hex(dec - 1),
        dec_to_hex(dec),
        dec_to_hex(dec + 1)
    ]

def parse_collisions(file_path: str) -> set[str]:
    """
    Liest die collisions.txt ein und extrahiert alle Dezimalwerte,
    die in Zeilen mit 'Keys: [ ... ]' gefunden werden.
    Gibt ein Set aller gefundenen Stringwerte (nur Ziffern) zurück.
    """
    decimals = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = KEYS_PATTERN.search(line)
            if match:
                keys = match.group(1).split(",")
                # Nur Ziffern ins Set übernehmen
                for k in keys:
                    k = k.strip()
                    if k.isdigit():
                        decimals.add(k)
    return decimals

def process_files(found_keys_path: str, collisions_path: str, output_path: str) -> None:
    """
    Ließt found_keys.txt und collisions.txt ein, sammelt alle Dezimalwerte,
    berechnet jeweils dec-1, dec und dec+1 als Hex und speichert
    die einzigartigen Ergebnisse in HEXFOUND.txt.
    """
    # Sammeln aller Dezimalwerte in einem Set (Duplikate werden automatisch entfernt)
    decimals = set()

    # 1. found_keys.txt einlesen
    with open(found_keys_path, "r", encoding="utf-8") as f:
        for line in f:
            val = line.strip()
            if val.isdigit():
                decimals.add(val)

    # 2. collisions.txt einlesen
    decimals.update(parse_collisions(collisions_path))

    # 3. Dezimalwerte parallel verarbeiten
    with Pool(cpu_count()) as pool:
        # process_decimal gibt je eine Liste zurück, die wir in eine flache Liste umwandeln
        all_hex_values = pool.map(process_decimal, decimals)

    # 4. Liste flach machen und eindeutige Hexwerte ermitteln
    unique_hex_values = set(hex_val for sublist in all_hex_values for hex_val in sublist)

    # 5. Sortierte Ausgabe
    with open(output_path, "w", encoding="utf-8") as f:
        for hex_val in sorted(unique_hex_values):
            f.write(hex_val + "\n")

if __name__ == "__main__":
    # Dateinamen anpassen, falls nötig
    found_keys_file = "found_keys.txt"
    collisions_file = "collisions.txt"
    output_file = "HEXFOUND.txt"

    # Prüfung: Existieren beide Dateien?
    if not os.path.exists(found_keys_file) or not os.path.exists(collisions_file):
        print("Eine oder beide Eingabedateien fehlen. Bitte sicherstellen, dass "
              "'found_keys.txt' und 'collisions.txt' vorhanden sind.")
    else:
        print("Verarbeite Dateien... Bitte warten.")
        process_files(found_keys_file, collisions_file, output_file)
        print(f"Hex-Werte wurden in '{output_file}' gespeichert.")