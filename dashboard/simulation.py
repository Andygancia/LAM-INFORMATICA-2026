from dataclasses import dataclass
import base64
import io
import math
import os
import random
import tempfile
import threading

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "lam-matplotlib"))
from matplotlib.figure import Figure
import numpy as np

# La simulazione usa lo stato globale di random/np.random e i grafici Matplotlib
# non sono thread-safe: serializziamo ogni richiesta per mantenere i risultati
# riproducibili con lo stesso seed anche sotto richieste concorrenti.
_LOCK_SIMULAZIONE = threading.Lock()


@dataclass
class Trader:
    id_trader: int
    cash: float
    bitcoin: float

    tipo = "Base"

    def genera_ricchezza(self, prezzo_bitcoin):
        return self.cash + self.bitcoin * prezzo_bitcoin


class RandomTrader(Trader):
    tipo = "Random"
    probabilita_essere_attivo = 0.10

    def attivita_trader(self):
        return random.random() < self.probabilita_essere_attivo

    def decide_ordine(self, prezzo_corrente, storico_prezzi, notizia):
        if random.random() < 0.5 and self.cash > 0:
            return "compra"
        if self.bitcoin > 0:
            return "vendi"
        return None


class Chartist(Trader):
    tipo = "Chartist"
    probabilita_essere_attivo = 0.50
    soglia = 0.01

    def attivita_trader(self):
        return random.random() < self.probabilita_essere_attivo

    def variazione_prezzo(self, storico_prezzi):
        if len(storico_prezzi) < 2 or storico_prezzi[-2] == 0:
            return 0
        return (storico_prezzi[-1] - storico_prezzi[-2]) / storico_prezzi[-2]

    def decide_ordine(self, prezzo_corrente, storico_prezzi, notizia):
        variazione = self.variazione_prezzo(storico_prezzi)
        if variazione > self.soglia and self.cash > 0:
            return "compra"
        if variazione < -self.soglia and self.bitcoin > 0:
            return "vendi"
        return None


class NoiseTrader(Trader):
    tipo = "Noise"
    probabilita_essere_attivo = 0.60

    def __init__(
        self,
        id_trader,
        cash,
        bitcoin,
        sensibilita_notizie=0.70,
        probabilita_panico=0.10,
    ):
        super().__init__(id_trader, cash, bitcoin)
        self.sensibilita_notizie = sensibilita_notizie
        self.probabilita_panico = probabilita_panico

    def attivita_trader(self):
        return random.random() < self.probabilita_essere_attivo

    def decide_ordine(self, prezzo_corrente, storico_prezzi, notizia):
        if random.random() < self.probabilita_panico and self.bitcoin > 0:
            return "vendi"
        if notizia == "positiva" and random.random() < self.sensibilita_notizie and self.cash > 0:
            return "compra"
        if notizia == "negativa" and random.random() < self.sensibilita_notizie and self.bitcoin > 0:
            return "vendi"
        if random.random() < 0.5 and self.cash > 0:
            return "compra"
        if self.bitcoin > 0:
            return "vendi"
        return None


DEFAULT_PARAMS = {
    "numero_trader": 100,
    "bitcoin_totali": 80000,
    "cash_totale": 400000,
    "prezzo_iniziale": 5.0,
    "numero_giorni": 120,
    "beta": 1.0,
    "percentuale_random": 60,
    "percentuale_noise": 15,
    "percentuale_chartist": 25,
    "trader_random_attivo": True,
    "trader_noise_attivo": True,
    "trader_chartist_attivo": True,
    "prob_notizia_positiva": 10,
    "prob_notizia_neutra": 80,
    "prob_notizia_negativa": 10,
    "impatto_domanda_offerta": 0.08,
    "seed": 42,
}

# Intervalli ammessi lato server: gli input del form sono di tipo testo e
# possono superare i limiti dell'interfaccia, quindi vanno ricontrollati qui
# per evitare simulazioni che bloccano il thread (giorni/trader enormi).
LIMITI_PARAMETRI = {
    "numero_trader": (10, 2000),
    "numero_giorni": (1, 1000),
    "prezzo_iniziale": (0.01, 1_000_000),
    "beta": (0.1, 5),
    "bitcoin_totali": (0, 1_000_000_000_000),
    "cash_totale": (0, 1_000_000_000_000),
    "impatto_domanda_offerta": (0, 1),
    "seed": (0, 2**32 - 1),
}

CLASSI_TRADER = ("Random", "Noise", "Chartist")
COLORI_CLASSI = {
    "Random": "#00c48c",
    "Noise": "#f3b33d",
    "Chartist": "#5f8cff",
    "Smart": "#5f8cff",
    "Dumb": "#ff5d57",
}
FRAZIONE_SCAMBIO = 0.10


def ricchezza_proporzionale_pareto(numero_trader, ricchezza_totale, beta):
    pareto_values = np.random.pareto(beta, numero_trader) + 0.01
    return (pareto_values / pareto_values.sum()) * ricchezza_totale


def leggi_percentuale(params, chiave):
    valore = float(params[chiave])
    if valore < 0:
        raise ValueError("Le percentuali non possono essere negative")
    return valore


def parametro_attivo(params, chiave):
    valore = params.get(chiave, True)
    if isinstance(valore, str):
        return valore.lower() not in ("false", "0", "no", "off", "")
    return bool(valore)


def valida_somma_percentuali(params, chiavi, nome_gruppo):
    if not chiavi:
        raise ValueError(f"Attiva almeno una categoria per {nome_gruppo}")
    totale = sum(leggi_percentuale(params, chiave) for chiave in chiavi)
    if abs(totale - 100) > 0.000001:
        raise ValueError(f"La somma percentuale per {nome_gruppo} deve essere 100%, ora e' {totale:g}%")


def percentuali_trader(params):
    random_pct = leggi_percentuale(params, "percentuale_random") if parametro_attivo(params, "trader_random_attivo") else 0
    noise_pct = leggi_percentuale(params, "percentuale_noise") if parametro_attivo(params, "trader_noise_attivo") else 0
    chartist_pct = (
        leggi_percentuale(params, "percentuale_chartist")
        if parametro_attivo(params, "trader_chartist_attivo")
        else 0
    )
    return random_pct / 100, noise_pct / 100, chartist_pct / 100


def valida_percentuali(params):
    chiavi_trader_attive = []
    if parametro_attivo(params, "trader_random_attivo"):
        chiavi_trader_attive.append("percentuale_random")
    if parametro_attivo(params, "trader_noise_attivo"):
        chiavi_trader_attive.append("percentuale_noise")
    if parametro_attivo(params, "trader_chartist_attivo"):
        chiavi_trader_attive.append("percentuale_chartist")

    valida_somma_percentuali(
        params,
        chiavi_trader_attive,
        "i tipi di trader",
    )
    if parametro_attivo(params, "trader_noise_attivo"):
        valida_somma_percentuali(
            params,
            ["prob_notizia_positiva", "prob_notizia_neutra", "prob_notizia_negativa"],
            "le notizie",
        )


def valida_limiti(params):
    for chiave, (minimo, massimo) in LIMITI_PARAMETRI.items():
        grezzo = params.get(chiave, "")
        if chiave == "seed" and grezzo in (None, ""):
            continue
        try:
            valore = float(grezzo)
        except (TypeError, ValueError):
            raise ValueError(f"Il parametro '{chiave}' non e' un numero valido")
        if not math.isfinite(valore) or not (minimo <= valore <= massimo):
            raise ValueError(
                f"Il parametro '{chiave}' deve essere tra {minimo:g} e {massimo:g}"
            )


def crea_popolazione_trader(params):
    numero_trader = int(float(params["numero_trader"]))
    beta = float(params["beta"])
    bitcoin_assegnati = ricchezza_proporzionale_pareto(
        numero_trader, float(params["bitcoin_totali"]), beta
    )
    cash_assegnato = ricchezza_proporzionale_pareto(
        numero_trader, float(params["cash_totale"]), beta
    )

    p_random, p_noise, _ = percentuali_trader(params)
    traders = []

    for i in range(numero_trader):
        scelta_tipo = random.random()
        if scelta_tipo < p_random:
            trader = RandomTrader(i + 1, cash_assegnato[i], bitcoin_assegnati[i])
        elif scelta_tipo < p_random + p_noise:
            trader = NoiseTrader(
                i + 1,
                cash_assegnato[i],
                bitcoin_assegnati[i],
                sensibilita_notizie=random.uniform(0.50, 0.90),
                probabilita_panico=random.uniform(0.05, 0.20),
            )
        else:
            trader = Chartist(i + 1, cash_assegnato[i], bitcoin_assegnati[i])
        traders.append(trader)

    return traders


def estrai_notizia(params):
    if not parametro_attivo(params, "trader_noise_attivo"):
        return "neutra"

    pesi = [
        leggi_percentuale(params, "prob_notizia_positiva"),
        leggi_percentuale(params, "prob_notizia_neutra"),
        leggi_percentuale(params, "prob_notizia_negativa"),
    ]
    return random.choices(["positiva", "neutra", "negativa"], weights=pesi, k=1)[0]


def calcola_gini(valori):
    valori = np.array(valori, dtype=float)
    if len(valori) == 0 or np.sum(valori) == 0:
        return 0
    valori = np.sort(valori)
    n = len(valori)
    indice = np.arange(1, n + 1)
    return float((np.sum((2 * indice - n - 1) * valori)) / (n * np.sum(valori)))


def esegui_ordine(trader, ordine, prezzo_corrente):
    if prezzo_corrente <= 0:
        return
    if ordine == "compra" and trader.cash > 0:
        investimento = trader.cash * FRAZIONE_SCAMBIO
        trader.cash -= investimento
        trader.bitcoin += investimento / prezzo_corrente
    elif ordine == "vendi" and trader.bitcoin > 0:
        bitcoin_venduti = trader.bitcoin * FRAZIONE_SCAMBIO
        trader.bitcoin -= bitcoin_venduti
        trader.cash += bitcoin_venduti * prezzo_corrente


def aggrega_classi(traders, prezzo):
    aggregati = {
        tipo: {"conteggio": 0, "patrimonio": 0.0, "cash": 0.0, "bitcoin": 0.0}
        for tipo in CLASSI_TRADER
    }
    for trader in traders:
        tipo = trader.tipo
        aggregati[tipo]["conteggio"] += 1
        aggregati[tipo]["patrimonio"] += trader.genera_ricchezza(prezzo)
        aggregati[tipo]["cash"] += trader.cash
        aggregati[tipo]["bitcoin"] += trader.bitcoin

    for dati in aggregati.values():
        conteggio = max(dati["conteggio"], 1)
        dati["patrimonio_medio"] = dati["patrimonio"] / conteggio

    return aggregati


def aggrega_smart_dumb(classi):
    gruppi = {
        "Smart": {"conteggio": 0, "patrimonio": 0.0},
        "Dumb": {"conteggio": 0, "patrimonio": 0.0},
    }
    for tipo, dati in classi.items():
        gruppo = "Smart" if tipo == "Chartist" else "Dumb"
        gruppi[gruppo]["conteggio"] += dati["conteggio"]
        gruppi[gruppo]["patrimonio"] += dati["patrimonio"]

    for dati in gruppi.values():
        conteggio = max(dati["conteggio"], 1)
        dati["patrimonio_medio"] = dati["patrimonio"] / conteggio

    return gruppi


def arrotonda_aggregati(aggregati):
    return {
        nome: {
            "conteggio": int(dati["conteggio"]),
            "patrimonio": round(float(dati["patrimonio"]), 2),
            "patrimonio_medio": round(float(dati["patrimonio_medio"]), 2),
            **(
                {"cash": round(float(dati["cash"]), 2), "bitcoin": round(float(dati["bitcoin"]), 6)}
                if "cash" in dati
                else {}
            ),
        }
        for nome, dati in aggregati.items()
    }


def rendimento_percentuale(valore, valore_iniziale):
    if valore_iniziale <= 0:
        return 0.0
    return (valore / valore_iniziale - 1) * 100


def costruisci_serie(snapshot):
    serie_classi = []
    serie_smart_dumb = []
    iniziale_classi = snapshot[0]["classi"]
    iniziale_gruppi = snapshot[0]["smart_dumb"]

    for record in snapshot:
        classi_arrotondate = arrotonda_aggregati(record["classi"])
        gruppi_arrotondati = arrotonda_aggregati(record["smart_dumb"])
        classi = {}
        for tipo, dati in record["classi"].items():
            classi[tipo] = {
                **classi_arrotondate[tipo],
                "rendimento_percentuale": round(
                    float(
                        rendimento_percentuale(
                            dati["patrimonio_medio"],
                            iniziale_classi[tipo]["patrimonio_medio"],
                        )
                    ),
                    2,
                ),
            }

        gruppi = {}
        for nome, dati in record["smart_dumb"].items():
            gruppi[nome] = {
                **gruppi_arrotondati[nome],
                "rendimento_percentuale": round(
                    float(
                        rendimento_percentuale(
                            dati["patrimonio_medio"],
                            iniziale_gruppi[nome]["patrimonio_medio"],
                        )
                    ),
                    2,
                ),
            }

        serie_classi.append({"giorno": record["giorno"], "classi": classi})
        serie_smart_dumb.append({"giorno": record["giorno"], "gruppi": gruppi})

    return serie_classi, serie_smart_dumb


def prepara_figura(titolo, asse_y):
    fig = Figure(figsize=(9.8, 3.9), dpi=120)
    ax = fig.subplots()
    fig.patch.set_facecolor("#080d0c")
    ax.set_facecolor("#050908")
    ax.set_title(titolo, color="#eef7f3", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Giorno", color="#8fa19b")
    ax.set_ylabel(asse_y, color="#8fa19b")
    ax.tick_params(colors="#8fa19b", labelsize=8)
    ax.grid(True, color="#1a2a26", linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_color("#1a2a26")
    return fig, ax


def figura_to_data_uri(fig):
    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def genera_grafico_linee(titolo, asse_y, giorni, serie_per_nome):
    fig, ax = prepara_figura(titolo, asse_y)
    for nome, valori in serie_per_nome.items():
        if not valori:
            continue
        ax.plot(
            giorni,
            valori,
            label=nome,
            color=COLORI_CLASSI.get(nome, "#eef7f3"),
            linewidth=2.4,
        )
    legenda = ax.legend(facecolor="#0d1513", edgecolor="#1a2a26", fontsize=8)
    for testo in legenda.get_texts():
        testo.set_color("#eef7f3")
    return figura_to_data_uri(fig)


def genera_grafico_barre(titolo, asse_y, valori_per_nome):
    fig, ax = prepara_figura(titolo, asse_y)
    nomi = list(valori_per_nome)
    valori = [valori_per_nome[nome] for nome in nomi]
    colori = [COLORI_CLASSI.get(nome, "#eef7f3") for nome in nomi]
    ax.bar(nomi, valori, color=colori, width=0.56)
    ax.axhline(0, color="#8fa19b", linewidth=0.9)
    for indice, valore in enumerate(valori):
        offset = 1 if valore >= 0 else -5
        ax.text(
            indice,
            valore + offset,
            f"{valore:.2f}%",
            ha="center",
            va="bottom" if valore >= 0 else "top",
            color="#eef7f3",
            fontsize=8,
            fontweight="bold",
        )
    return figura_to_data_uri(fig)


def genera_grafici(serie_classi, serie_smart_dumb):
    giorni = [record["giorno"] for record in serie_classi]
    patrimonio_classi = {
        tipo: [record["classi"][tipo]["patrimonio"] for record in serie_classi]
        for tipo in CLASSI_TRADER
    }
    rendimento_classi = {
        tipo: [record["classi"][tipo]["rendimento_percentuale"] for record in serie_classi]
        for tipo in CLASSI_TRADER
    }
    rendimento_gruppi = {
        nome: [record["gruppi"][nome]["rendimento_percentuale"] for record in serie_smart_dumb]
        for nome in ("Smart", "Dumb")
    }
    rendimento_finale = {
        tipo: serie_classi[-1]["classi"][tipo]["rendimento_percentuale"]
        for tipo in CLASSI_TRADER
    }

    return {
        "patrimonio_classi": genera_grafico_linee(
            "Patrimonio per classe trader",
            "Patrimonio totale",
            giorni,
            patrimonio_classi,
        ),
        "performance_classi": genera_grafico_linee(
            "Performance media per classe",
            "Rendimento medio (%)",
            giorni,
            rendimento_classi,
        ),
        "smart_vs_dumb": genera_grafico_linee(
            "Smart vs Dumb",
            "Rendimento medio (%)",
            giorni,
            rendimento_gruppi,
        ),
        "rendimento_finale": genera_grafico_barre(
            "Rendimento finale per classe",
            "Rendimento medio (%)",
            rendimento_finale,
        ),
    }


def simula_mercato(user_params):
    with _LOCK_SIMULAZIONE:
        return _esegui_simulazione(user_params)


def _esegui_simulazione(user_params):
    params = DEFAULT_PARAMS | user_params
    valida_percentuali(params)
    valida_limiti(params)

    seed = params.get("seed")
    if seed not in (None, ""):
        random.seed(int(float(seed)))
        np.random.seed(int(float(seed)))

    traders = crea_popolazione_trader(params)
    storico_prezzi = [float(params["prezzo_iniziale"])]
    giorni = []
    classi_iniziali = aggrega_classi(traders, storico_prezzi[0])
    snapshot = [
        {
            "giorno": 0,
            "classi": classi_iniziali,
            "smart_dumb": aggrega_smart_dumb(classi_iniziali),
        }
    ]

    for giorno in range(1, int(float(params["numero_giorni"])) + 1):
        prezzo_corrente = storico_prezzi[-1]
        notizia = estrai_notizia(params)
        compratori = 0
        venditori = 0
        inattivi = 0

        for trader in traders:
            if not trader.attivita_trader():
                inattivi += 1
                continue
            ordine = trader.decide_ordine(prezzo_corrente, storico_prezzi, notizia)
            if ordine == "compra":
                compratori += 1
                esegui_ordine(trader, ordine, prezzo_corrente)
            elif ordine == "vendi":
                venditori += 1
                esegui_ordine(trader, ordine, prezzo_corrente)
            else:
                inattivi += 1

        squilibrio = (compratori - venditori) / max(len(traders), 1)
        impatto = float(params["impatto_domanda_offerta"])
        rumore = random.uniform(-0.01, 0.01)
        shock = {"positiva": 0.015, "neutra": 0, "negativa": -0.015}[notizia]
        nuovo_prezzo = max(0.01, prezzo_corrente * (1 + impatto * squilibrio + shock + rumore))
        storico_prezzi.append(nuovo_prezzo)

        ricchezze = [t.genera_ricchezza(nuovo_prezzo) for t in traders]
        classi = aggrega_classi(traders, nuovo_prezzo)
        smart_dumb = aggrega_smart_dumb(classi)
        snapshot.append({"giorno": giorno, "classi": classi, "smart_dumb": smart_dumb})
        giorni.append(
            {
                "giorno": giorno,
                "prezzo": round(nuovo_prezzo, 4),
                "notizia": notizia,
                "compratori": compratori,
                "venditori": venditori,
                "inattivi": inattivi,
                "gini": round(calcola_gini(ricchezze), 4),
            }
        )

    conteggi = {
        "Random": sum(isinstance(t, RandomTrader) for t in traders),
        "Noise": sum(isinstance(t, NoiseTrader) for t in traders),
        "Chartist": sum(isinstance(t, Chartist) for t in traders),
    }
    prezzo_finale = storico_prezzi[-1]
    ricchezze_finali = [t.genera_ricchezza(prezzo_finale) for t in traders]
    serie_classi, serie_smart_dumb = costruisci_serie(snapshot)

    return {
        "params": params,
        "conteggi": conteggi,
        "giorni": giorni,
        "grafici": genera_grafici(serie_classi, serie_smart_dumb),
        "summary": {
            "prezzo_iniziale": round(storico_prezzi[0], 4),
            "prezzo_finale": round(prezzo_finale, 4),
            "variazione_percentuale": round((prezzo_finale / storico_prezzi[0] - 1) * 100, 2),
            "gini_finale": round(calcola_gini(ricchezze_finali), 4),
            "totale_compratori": sum(g["compratori"] for g in giorni),
            "totale_venditori": sum(g["venditori"] for g in giorni),
        },
    }
