"""Grafico del prezzo storico del Bitcoin (USD) in scala logaritmica.

Legge dati/prezzi_btc.csv (colonne: date, price_usd) e salva il grafico
vettoriale in figure/prezzo_bitcoin_log.pdf, per il paragrafo 2.1 del LAM.
Fonte dei dati: vedi dati/FONTE.txt.
"""

import csv
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

CARTELLA = Path(__file__).resolve().parent
FILE_DATI = CARTELLA / "dati" / "prezzi_btc.csv"
FILE_GRAFICO = CARTELLA / "figure" / "prezzo_bitcoin_log.pdf"

HALVING = [
    date(2012, 11, 28),
    date(2016, 7, 9),
    date(2020, 5, 11),
    date(2024, 4, 20),
]


def leggi_prezzi(percorso):
    """Restituisce date e prezzi, scartando le righe con prezzo zero o mancante."""
    date_valide, prezzi = [], []
    with open(percorso, newline="") as f:
        for riga in csv.DictReader(f):
            valore = (riga.get("price_usd") or "").strip()
            if not valore:
                continue
            prezzo = float(valore)
            if prezzo <= 0:
                continue
            date_valide.append(date.fromisoformat(riga["date"]))
            prezzi.append(prezzo)
    return date_valide, prezzi


def main():
    giorni, prezzi = leggi_prezzi(FILE_DATI)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(giorni, prezzi, color="#1f3b73", linewidth=1.0)
    ax.set_yscale("log")

    # Linee verticali agli halving, con etichetta piccola in alto
    for i, giorno in enumerate(HALVING, start=1):
        ax.axvline(giorno, color="grey", linestyle="--", linewidth=0.8)
        ax.text(giorno, 0.98, f" halving {i}", transform=ax.get_xaxis_transform(),
                fontsize=7, color="dimgrey", ha="left", va="top")

    ax.set_xlabel("Anno")
    ax.set_ylabel("Prezzo (USD, scala logaritmica)")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda y, _: f"{y:,.2f}".rstrip("0").rstrip(".").replace(",", "'"))
    )
    ax.set_xlim(giorni[0], giorni[-1])
    ax.grid(True, which="major", color="0.85", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)

    FILE_GRAFICO.parent.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(FILE_GRAFICO)
    print(f"Grafico salvato in {FILE_GRAFICO} ({len(prezzi)} giorni, "
          f"{giorni[0]} - {giorni[-1]})")


if __name__ == "__main__":
    main()
