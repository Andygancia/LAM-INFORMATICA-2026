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


class SmartTrader(Trader):
    """Trader razionale e contrarian, ispirato alla descrizione degli "smart
    trader" nel LAM di riferimento (Cattaneo & Bartoli, 2025) e alla
    disciplina descritta in "Trading in the Zone" di Mark Douglas: compra
    quando il prezzo e' sceso sotto la sua media recente e vende quando e'
    salito sopra, ignorando il rumore di brevissimo periodo a cui invece
    reagisce il Chartist."""

    tipo = "Smart"
    probabilita_essere_attivo = 0.35
    finestra_media = 20
    soglia_deviazione = 0.03

    def attivita_trader(self):
        return random.random() < self.probabilita_essere_attivo

    def decide_ordine(self, prezzo_corrente, storico_prezzi, notizia):
        finestra = storico_prezzi[-self.finestra_media :]
        if len(finestra) < 2:
            return None
        media_riferimento = sum(finestra) / len(finestra)
        if media_riferimento <= 0:
            return None
        deviazione = (prezzo_corrente - media_riferimento) / media_riferimento
        if deviazione < -self.soglia_deviazione and self.cash > 0:
            return "compra"
        if deviazione > self.soglia_deviazione and self.bitcoin > 0:
            return "vendi"
        return None


DEFAULT_PARAMS = {
    "numero_trader": 100,
    "bitcoin_totali": 80000,
    "cash_totale": 400000,
    "prezzo_iniziale": 5.0,
    "numero_giorni": 120,
    "beta": 1.0,
    "percentuale_random": 50,
    "percentuale_noise": 15,
    "percentuale_chartist": 20,
    "percentuale_smart": 15,
    "trader_random_attivo": True,
    "trader_noise_attivo": True,
    "trader_chartist_attivo": True,
    "trader_smart_attivo": True,
    "prob_notizia_positiva": 10,
    "prob_notizia_neutra": 80,
    "prob_notizia_negativa": 10,
    "impatto_domanda_offerta": 0.08,
    "spread_bid_ask": 0.4,
    "mining_attivo": False,
    "mining_giornaliero": 2,
    "ingresso_nuovi_trader_attivo": False,
    "tasso_ingresso_giornaliero": 1,
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
    "spread_bid_ask": (0, 20),
    "mining_giornaliero": (0, 1_000_000),
    "tasso_ingresso_giornaliero": (0, 200),
    "seed": (0, 2**32 - 1),
}

CLASSI_TRADER = ("Random", "Noise", "Chartist", "Smart")
COLORI_CLASSI = {
    "Random": "#00c48c",
    "Noise": "#f3b33d",
    "Chartist": "#5f8cff",
    "Smart": "#c9a4ff",
    "Normal": "#8fa19b",
    "Dumb": "#ff5d57",
}
FRAZIONE_SCAMBIO = 0.10

# Gruppo psicologico a cui appartiene ciascuna classe di trader, usato per il
# confronto "Smart vs Normal vs Dumb" (terminologia ripresa dal LAM di
# Cattaneo & Bartoli, 2025): i Chartist e i Noise trader inseguono in modo
# impulsivo il trend o le notizie (Dumb), i Random trader fanno da "rumore
# di fondo" neutro (Normal), e i nuovi SmartTrader sono i soli contrarian
# disciplinati (Smart).
GRUPPO_PSICOLOGICO = {
    "Random": "Normal",
    "Noise": "Dumb",
    "Chartist": "Dumb",
    "Smart": "Smart",
}

# Valori critici del test tau1 di Dickey-Fuller (ipotesi nulla: random walk
# senza drift), le stesse soglie citate nel paper di riferimento (Cocco,
# Concas, Marchesi, 2017, Sez. 5).
VALORI_CRITICI_ADF = {"1%": -2.58, "5%": -1.95, "10%": -1.62}

LIMITE_CARICO_MULTIRUN = 3_000_000
MASSIMO_RUN_MULTIRUN = 200


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
    smart_pct = (
        leggi_percentuale(params, "percentuale_smart")
        if parametro_attivo(params, "trader_smart_attivo")
        else 0
    )
    return random_pct / 100, noise_pct / 100, chartist_pct / 100, smart_pct / 100


def valida_percentuali(params):
    chiavi_trader_attive = []
    if parametro_attivo(params, "trader_random_attivo"):
        chiavi_trader_attive.append("percentuale_random")
    if parametro_attivo(params, "trader_noise_attivo"):
        chiavi_trader_attive.append("percentuale_noise")
    if parametro_attivo(params, "trader_chartist_attivo"):
        chiavi_trader_attive.append("percentuale_chartist")
    if parametro_attivo(params, "trader_smart_attivo"):
        chiavi_trader_attive.append("percentuale_smart")

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

    p_random, p_noise, p_chartist, _p_smart = percentuali_trader(params)
    soglia_random = p_random
    soglia_noise = soglia_random + p_noise
    soglia_chartist = soglia_noise + p_chartist
    # Chi non rientra nelle prime tre soglie diventa Smart: cosi' la somma
    # copre sempre l'intero intervallo [0, 1) anche con arrotondamenti.
    traders = []

    for i in range(numero_trader):
        scelta_tipo = random.random()
        if scelta_tipo < soglia_random:
            trader = RandomTrader(i + 1, cash_assegnato[i], bitcoin_assegnati[i])
        elif scelta_tipo < soglia_noise:
            trader = NoiseTrader(
                i + 1,
                cash_assegnato[i],
                bitcoin_assegnati[i],
                sensibilita_notizie=random.uniform(0.50, 0.90),
                probabilita_panico=random.uniform(0.05, 0.20),
            )
        elif scelta_tipo < soglia_chartist:
            trader = Chartist(i + 1, cash_assegnato[i], bitcoin_assegnati[i])
        else:
            trader = SmartTrader(i + 1, cash_assegnato[i], bitcoin_assegnati[i])
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


def calcola_log_rendimenti(prezzi):
    prezzi = np.clip(np.array(prezzi, dtype=float), 1e-9, None)
    if len(prezzi) < 2:
        return np.array([])
    return np.diff(np.log(prezzi))


def statistiche_rendimenti(rendimenti):
    """Media, deviazione standard, asimmetria e curtosi (di Pearson, quindi
    con la normale a quota 3, come nella Tabella 3 del paper di riferimento)
    dei log-rendimenti giornalieri."""
    if len(rendimenti) == 0:
        return {"media": 0.0, "deviazione_standard": 0.0, "asimmetria": 0.0, "curtosi": 0.0}
    media = float(np.mean(rendimenti))
    dev = float(np.std(rendimenti))
    if dev == 0:
        asimmetria = 0.0
        curtosi = 0.0
    else:
        z = (np.array(rendimenti) - media) / dev
        asimmetria = float(np.mean(z**3))
        curtosi = float(np.mean(z**4))
    return {
        "media": round(media, 6),
        "deviazione_standard": round(dev, 6),
        "asimmetria": round(asimmetria, 4),
        "curtosi": round(curtosi, 4),
    }


def autocorrelazione(serie, max_lag=20):
    serie = np.array(serie, dtype=float)
    n = len(serie)
    if n < 3:
        return [0.0] * (max_lag + 1)
    max_lag = min(max_lag, n - 2)
    media = serie.mean()
    varianza = float(np.sum((serie - media) ** 2))
    risultati = []
    for lag in range(0, max_lag + 1):
        if varianza == 0:
            risultati.append(0.0)
            continue
        cov = float(np.sum((serie[: n - lag] - media) * (serie[lag:] - media)))
        risultati.append(cov / varianza)
    return risultati


def test_adf_senza_drift(serie, lag=1):
    """Test di Dickey-Fuller aumentato con un ritardo, ipotesi nulla H0:
    radice unitaria (random walk senza drift) - stessa formulazione e stessi
    valori critici (tau1) usati nel paper di riferimento (Sez. 5): la
    regressione e' Delta y_t = rho * y_(t-1) + phi * Delta y_(t-1) + errore.
    Implementato con i minimi quadrati di numpy per restare trasparente e
    senza aggiungere dipendenze esterne (statsmodels)."""
    y = np.array(serie, dtype=float)
    n = len(y)
    if n < lag + 15:
        return None

    dy = np.diff(y)
    righe = []
    dipendente = []
    for t in range(lag, len(dy)):
        dipendente.append(dy[t])
        riga = [y[t]]
        for i in range(1, lag + 1):
            riga.append(dy[t - i])
        righe.append(riga)

    X = np.array(righe, dtype=float)
    Y = np.array(dipendente, dtype=float)
    if len(Y) < X.shape[1] + 5:
        return None

    try:
        coefficienti, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
    except np.linalg.LinAlgError:
        return None

    residui = Y - X @ coefficienti
    gradi_liberta = max(len(Y) - X.shape[1], 1)
    sigma2 = float(np.sum(residui**2) / gradi_liberta)
    xtx_inv = np.linalg.pinv(X.T @ X)
    errore_standard_rho = math.sqrt(max(sigma2 * xtx_inv[0, 0], 0.0))
    rho = float(coefficienti[0])
    statistica_tau = rho / errore_standard_rho if errore_standard_rho > 0 else 0.0

    return {
        "statistica_tau": round(statistica_tau, 4),
        "valori_critici": VALORI_CRITICI_ADF,
        "rifiuta_ipotesi_random_walk": {
            livello: statistica_tau < soglia for livello, soglia in VALORI_CRITICI_ADF.items()
        },
        "osservazioni": len(Y),
    }


def esegui_ordine(trader, ordine, prezzo_corrente, spread=0.0):
    if prezzo_corrente <= 0:
        return
    meta_spread = max(spread, 0.0) / 2
    if ordine == "compra" and trader.cash > 0:
        prezzo_esecuzione = prezzo_corrente * (1 + meta_spread)
        investimento = trader.cash * FRAZIONE_SCAMBIO
        trader.cash -= investimento
        trader.bitcoin += investimento / prezzo_esecuzione
    elif ordine == "vendi" and trader.bitcoin > 0:
        prezzo_esecuzione = prezzo_corrente * (1 - meta_spread)
        bitcoin_venduti = trader.bitcoin * FRAZIONE_SCAMBIO
        trader.bitcoin -= bitcoin_venduti
        trader.cash += bitcoin_venduti * prezzo_esecuzione


def aggrega_classi(traders, prezzo):
    aggregati = {
        tipo: {"conteggio": 0, "patrimonio": 0.0, "cash": 0.0, "bitcoin": 0.0}
        for tipo in CLASSI_TRADER
    }
    for trader in traders:
        tipo = trader.tipo
        if tipo not in aggregati:
            aggregati[tipo] = {"conteggio": 0, "patrimonio": 0.0, "cash": 0.0, "bitcoin": 0.0}
        aggregati[tipo]["conteggio"] += 1
        aggregati[tipo]["patrimonio"] += trader.genera_ricchezza(prezzo)
        aggregati[tipo]["cash"] += trader.cash
        aggregati[tipo]["bitcoin"] += trader.bitcoin

    for dati in aggregati.values():
        conteggio = max(dati["conteggio"], 1)
        dati["patrimonio_medio"] = dati["patrimonio"] / conteggio

    return aggregati


def aggrega_gruppi_psicologici(classi):
    gruppi = {
        "Smart": {"conteggio": 0, "patrimonio": 0.0},
        "Normal": {"conteggio": 0, "patrimonio": 0.0},
        "Dumb": {"conteggio": 0, "patrimonio": 0.0},
    }
    for tipo, dati in classi.items():
        gruppo = GRUPPO_PSICOLOGICO.get(tipo, "Normal")
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
    serie_gruppi = []
    iniziale_classi = snapshot[0]["classi"]
    iniziale_gruppi = snapshot[0]["gruppi_psicologici"]

    for record in snapshot:
        classi_arrotondate = arrotonda_aggregati(record["classi"])
        gruppi_arrotondati = arrotonda_aggregati(record["gruppi_psicologici"])
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
        for nome, dati in record["gruppi_psicologici"].items():
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
        serie_gruppi.append({"giorno": record["giorno"], "gruppi": gruppi})

    return serie_classi, serie_gruppi


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


def _stila_legenda(ax):
    legenda = ax.legend(facecolor="#0d1513", edgecolor="#1a2a26", fontsize=8)
    for testo in legenda.get_texts():
        testo.set_color("#eef7f3")
    return legenda


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
    _stila_legenda(ax)
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


def genera_grafico_istogramma_rendimenti(rendimenti):
    fig, ax = prepara_figura("Istogramma dei log-rendimenti", "Densita'")
    ax.set_xlabel("Log-rendimento giornaliero")
    if len(rendimenti) > 0:
        ax.hist(rendimenti, bins=30, color="#00c48c", alpha=0.75, density=True, edgecolor="#050908")
        media = float(np.mean(rendimenti))
        dev = float(np.std(rendimenti))
        if dev > 0:
            xs = np.linspace(float(np.min(rendimenti)), float(np.max(rendimenti)), 200)
            normale = (1 / (dev * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((xs - media) / dev) ** 2)
            ax.plot(xs, normale, color="#f3b33d", linewidth=2.2, label="Normale (stessa media/dev.std)")
            _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_acf(acf_grezzi, acf_assoluti):
    fig, ax = prepara_figura("Autocorrelazione: rendimenti grezzi vs assoluti", "Autocorrelazione")
    ax.set_xlabel("Lag (giorni)")
    lags = list(range(len(acf_grezzi)))
    larghezza = 0.38
    ax.bar([l - larghezza / 2 for l in lags], acf_grezzi, width=larghezza, color="#5f8cff", label="Rendimenti grezzi")
    ax.bar([l + larghezza / 2 for l in lags], acf_assoluti, width=larghezza, color="#f3b33d", label="Rendimenti assoluti")
    ax.axhline(0, color="#8fa19b", linewidth=0.8)
    _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_lorenz(ricchezze):
    fig, ax = prepara_figura("Curva di Lorenz (distribuzione del patrimonio)", "Quota cumulata di patrimonio")
    ax.set_xlabel("Quota cumulata di trader (dal piu' povero)")
    valori = np.clip(np.sort(np.array(ricchezze, dtype=float)), 0, None)
    n = len(valori)
    ax.plot([0, 1], [0, 1], color="#8fa19b", linewidth=1.4, linestyle="--", label="Uguaglianza perfetta")
    if n > 0 and valori.sum() > 0:
        cumulato = np.cumsum(valori) / valori.sum()
        x = np.arange(1, n + 1) / n
        ax.plot(
            np.concatenate([[0], x]),
            np.concatenate([[0], cumulato]),
            color="#00c48c",
            linewidth=2.4,
            label="Popolazione simulata",
        )
    _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_volumi(giorni_lista):
    fig, ax = prepara_figura("Volumi giornalieri (ordini eseguiti)", "Numero di trader")
    giorni_idx = [g["giorno"] for g in giorni_lista]
    compratori = [g["compratori"] for g in giorni_lista]
    venditori = [-g["venditori"] for g in giorni_lista]
    ax.bar(giorni_idx, compratori, color="#00c48c", width=0.9, label="Compratori")
    ax.bar(giorni_idx, venditori, color="#ff5d57", width=0.9, label="Venditori")
    ax.axhline(0, color="#8fa19b", linewidth=0.9)
    _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_fan(titolo, asse_y, giorni, media, minimo, massimo):
    fig, ax = prepara_figura(titolo, asse_y)
    ax.fill_between(giorni, minimo, massimo, color="#00c48c", alpha=0.18, label="Min-Max tra le run")
    ax.plot(giorni, media, color="#00c48c", linewidth=2.4, label="Media")
    _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_scatter(titolo, asse_x, asse_y, valori_x, valori_y):
    fig, ax = prepara_figura(titolo, asse_y)
    ax.set_xlabel(asse_x)
    if valori_x and valori_y:
        ax.scatter(valori_x, valori_y, color="#5f8cff", alpha=0.65, s=26, edgecolor="#050908", linewidth=0.4)
        limite = max(max(abs(v) for v in valori_x), max(abs(v) for v in valori_y), 1) * 1.1
        ax.plot([-limite, limite], [-limite, limite], color="#8fa19b", linewidth=1, linestyle="--", label="Parita'")
        _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafico_istogramma_generico(titolo, asse_x, valori, colore="#00c48c"):
    fig, ax = prepara_figura(titolo, "Frequenza")
    ax.set_xlabel(asse_x)
    if valori:
        numero_bin = min(20, max(5, len(valori) // 3))
        ax.hist(valori, bins=numero_bin, color=colore, alpha=0.8, edgecolor="#050908")
        media = float(np.mean(valori))
        ax.axvline(media, color="#f3b33d", linewidth=2, label=f"Media: {media:.2f}")
        _stila_legenda(ax)
    return figura_to_data_uri(fig)


def genera_grafici(contesto):
    serie_classi = contesto["serie_classi"]
    serie_gruppi = contesto["serie_gruppi"]
    giorni_lista = contesto["giorni_lista"]
    rendimenti = contesto["rendimenti"]
    ricchezze_finali = contesto["ricchezze_finali"]
    storico_offerta_bitcoin = contesto["storico_offerta_bitcoin"]
    storico_trader_attivi = contesto["storico_trader_attivi"]
    params = contesto["params"]

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
        nome: [record["gruppi"][nome]["rendimento_percentuale"] for record in serie_gruppi]
        for nome in ("Smart", "Normal", "Dumb")
    }
    rendimento_finale = {
        tipo: serie_classi[-1]["classi"][tipo]["rendimento_percentuale"]
        for tipo in CLASSI_TRADER
    }
    acf_grezzi = autocorrelazione(rendimenti, max_lag=20)
    acf_assoluti = autocorrelazione(np.abs(rendimenti), max_lag=20)

    grafici = {
        "patrimonio_classi": genera_grafico_linee(
            "Patrimonio per classe trader", "Patrimonio totale", giorni, patrimonio_classi
        ),
        "performance_classi": genera_grafico_linee(
            "Performance media per classe", "Rendimento medio (%)", giorni, rendimento_classi
        ),
        "smart_vs_dumb": genera_grafico_linee(
            "Smart vs Normal vs Dumb", "Rendimento medio (%)", giorni, rendimento_gruppi
        ),
        "rendimento_finale": genera_grafico_barre(
            "Rendimento finale per classe", "Rendimento medio (%)", rendimento_finale
        ),
        "curva_lorenz": genera_grafico_lorenz(ricchezze_finali),
        "volumi_giornalieri": genera_grafico_volumi(giorni_lista),
        "istogramma_rendimenti": genera_grafico_istogramma_rendimenti(rendimenti),
        "acf_rendimenti": genera_grafico_acf(acf_grezzi, acf_assoluti),
    }

    # Il Gini nel tempo e' quasi piatto quando la popolazione e la quantita'
    # di bitcoin sono fisse (la disuguaglianza la decide la Pareto iniziale):
    # ha senso mostrarlo solo quando mining o ingresso trader la fanno variare.
    if parametro_attivo(params, "mining_attivo") or parametro_attivo(
        params, "ingresso_nuovi_trader_attivo"
    ):
        grafici["gini_nel_tempo"] = genera_grafico_linee(
            "Indice di Gini nel tempo",
            "Gini (0=uguaglianza, 1=disuguaglianza)",
            [g["giorno"] for g in giorni_lista],
            {"Gini": [g["gini"] for g in giorni_lista]},
        )

    if parametro_attivo(params, "mining_attivo") and storico_offerta_bitcoin:
        grafici["offerta_bitcoin"] = genera_grafico_linee(
            "Bitcoin totali in circolazione (mining)",
            "BTC totali",
            list(range(len(storico_offerta_bitcoin))),
            {"BTC in circolazione": storico_offerta_bitcoin},
        )

    if parametro_attivo(params, "ingresso_nuovi_trader_attivo") and storico_trader_attivi:
        grafici["trader_attivi"] = genera_grafico_linee(
            "Trader attivi nel mercato nel tempo",
            "Numero di trader",
            list(range(len(storico_trader_attivi))),
            {"Trader nel mercato": storico_trader_attivi},
        )

    return grafici


def simula_mercato(user_params):
    with _LOCK_SIMULAZIONE:
        risultato = _esegui_simulazione(user_params, includi_grafici=True)
    # Questi campi servono solo internamente a esegui_multirun; la dashboard
    # non li usa, quindi non li spediamo nella risposta di /api/simulate.
    for chiave in ("classi_finali", "gruppi_psicologici_finali"):
        risultato.pop(chiave, None)
    return risultato


def _esegui_simulazione(user_params, includi_grafici=True):
    params = DEFAULT_PARAMS | user_params
    valida_percentuali(params)
    valida_limiti(params)

    seed = params.get("seed")
    if seed not in (None, ""):
        seed_usato = int(float(seed))
    else:
        # Campo vuoto = seed casuale: lo generiamo qui e lo restituiamo nella
        # risposta (summary.seed_usato), cosi' la corsa resta riproducibile
        # anche se non era stato scelto un numero esplicito.
        seed_usato = random.SystemRandom().randrange(2**32 - 1)
    random.seed(seed_usato)
    np.random.seed(seed_usato % (2**32 - 1))

    traders = crea_popolazione_trader(params)
    prossimo_id = int(float(params["numero_trader"])) + 1
    storico_prezzi = [float(params["prezzo_iniziale"])]
    giorni = []

    mining_attivo = parametro_attivo(params, "mining_attivo")
    quantita_mining = float(params.get("mining_giornaliero", 0) or 0)
    ingresso_attivo = parametro_attivo(params, "ingresso_nuovi_trader_attivo")
    tasso_ingresso = max(float(params.get("tasso_ingresso_giornaliero", 0) or 0), 0)
    spread = float(params.get("spread_bid_ask", 0) or 0) / 100

    bitcoin_totali_correnti = float(params["bitcoin_totali"])
    storico_offerta_bitcoin = [bitcoin_totali_correnti]
    storico_trader_attivi = [len(traders)]

    classi_iniziali = aggrega_classi(traders, storico_prezzi[0])
    snapshot = [
        {
            "giorno": 0,
            "classi": classi_iniziali,
            "gruppi_psicologici": aggrega_gruppi_psicologici(classi_iniziali),
        }
    ]

    numero_giorni = int(float(params["numero_giorni"]))

    for giorno in range(1, numero_giorni + 1):
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
                esegui_ordine(trader, ordine, prezzo_corrente, spread=spread)
            elif ordine == "vendi":
                venditori += 1
                esegui_ordine(trader, ordine, prezzo_corrente, spread=spread)
            else:
                inattivi += 1

        squilibrio = (compratori - venditori) / max(len(traders), 1)
        impatto = float(params["impatto_domanda_offerta"])
        rumore = random.uniform(-0.01, 0.01)
        shock = {"positiva": 0.015, "neutra": 0, "negativa": -0.015}[notizia]
        nuovo_prezzo = max(0.01, prezzo_corrente * (1 + impatto * squilibrio + shock + rumore))
        storico_prezzi.append(nuovo_prezzo)

        if mining_attivo and quantita_mining > 0:
            candidati_random = [t for t in traders if isinstance(t, RandomTrader)]
            if candidati_random:
                minatore = random.choice(candidati_random)
                minatore.bitcoin += quantita_mining
                bitcoin_totali_correnti += quantita_mining
        storico_offerta_bitcoin.append(bitcoin_totali_correnti)

        if ingresso_attivo and tasso_ingresso > 0:
            nuovi_entranti = int(np.random.poisson(tasso_ingresso))
            cash_medio = float(params["cash_totale"]) / max(int(float(params["numero_trader"])), 1)
            for _ in range(nuovi_entranti):
                cash_nuovo = cash_medio * random.uniform(0.5, 1.5)
                traders.append(RandomTrader(prossimo_id, cash_nuovo, 0.0))
                prossimo_id += 1
        storico_trader_attivi.append(len(traders))

        ricchezze = [t.genera_ricchezza(nuovo_prezzo) for t in traders]
        classi = aggrega_classi(traders, nuovo_prezzo)
        gruppi_psicologici = aggrega_gruppi_psicologici(classi)
        snapshot.append({"giorno": giorno, "classi": classi, "gruppi_psicologici": gruppi_psicologici})
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
        "Smart": sum(isinstance(t, SmartTrader) for t in traders),
    }
    prezzo_finale = storico_prezzi[-1]
    ricchezze_finali = [t.genera_ricchezza(prezzo_finale) for t in traders]
    serie_classi, serie_gruppi = costruisci_serie(snapshot)
    rendimenti = calcola_log_rendimenti(storico_prezzi)

    risultato = {
        "params": params,
        "conteggi": conteggi,
        "giorni": giorni,
        "classi_finali": serie_classi[-1]["classi"],
        "gruppi_psicologici_finali": serie_gruppi[-1]["gruppi"],
        "statistiche_rendimenti": statistiche_rendimenti(rendimenti),
        "test_adf_prezzo": test_adf_senza_drift(storico_prezzi),
        "summary": {
            "prezzo_iniziale": round(storico_prezzi[0], 4),
            "prezzo_finale": round(prezzo_finale, 4),
            "variazione_percentuale": round((prezzo_finale / storico_prezzi[0] - 1) * 100, 2),
            "gini_finale": round(calcola_gini(ricchezze_finali), 4),
            "trader_finali": len(traders),
            "seed_usato": seed_usato,
        },
    }

    if includi_grafici:
        risultato["grafici"] = genera_grafici(
            {
                "serie_classi": serie_classi,
                "serie_gruppi": serie_gruppi,
                "giorni_lista": giorni,
                "rendimenti": rendimenti,
                "ricchezze_finali": ricchezze_finali,
                "storico_offerta_bitcoin": storico_offerta_bitcoin,
                "storico_trader_attivi": storico_trader_attivi,
                "params": params,
            }
        )

    return risultato


def _limita_numero_run(numero_run, params_livello):
    numero_trader = int(float(params_livello.get("numero_trader", DEFAULT_PARAMS["numero_trader"])))
    numero_giorni = int(float(params_livello.get("numero_giorni", DEFAULT_PARAMS["numero_giorni"])))
    numero_run = max(1, min(int(numero_run), MASSIMO_RUN_MULTIRUN))
    carico_stimato = numero_run * numero_giorni * numero_trader
    if carico_stimato > LIMITE_CARICO_MULTIRUN:
        fattore = LIMITE_CARICO_MULTIRUN / carico_stimato
        numero_run = max(3, int(numero_run * fattore))
    return numero_run


def esegui_multirun(user_params, numero_run=30, parametro_confronto=None, valori_confronto=None):
    """Esegue piu' simulazioni Monte Carlo con lo stesso set di parametri
    (seed diversi ad ogni run), oppure - se viene indicato un parametro e
    fino a 3 valori da confrontare - ripete il confronto per ciascun valore,
    replicando l'analisi "fees0.0001 / fees0.0005 / fees0.001" della
    versione avanzata del LAM di riferimento (Cattaneo & Bartoli, Sez. 8)."""
    with _LOCK_SIMULAZIONE:
        if parametro_confronto and valori_confronto:
            livelli_richiesti = [
                (f"{parametro_confronto} = {valore:g}", {**user_params, parametro_confronto: float(valore)})
                for valore in list(valori_confronto)[:3]
            ]
        else:
            livelli_richiesti = [("Scenario unico", dict(user_params))]

        risultati_livelli = []
        for etichetta, parametri_livello in livelli_richiesti:
            run_effettivi = _limita_numero_run(numero_run, parametri_livello)
            prezzi_matrice = []
            prezzi_finali = []
            rendimento_per_gruppo = {"Smart": [], "Normal": [], "Dumb": []}
            rendimento_per_classe = {tipo: [] for tipo in CLASSI_TRADER}

            for indice_run in range(run_effettivi):
                parametri_run = dict(parametri_livello)
                seme_base = parametri_run.get("seed", DEFAULT_PARAMS["seed"])
                seme_base = int(float(seme_base)) if seme_base not in (None, "") else 0
                parametri_run["seed"] = seme_base + indice_run

                esito = _esegui_simulazione(parametri_run, includi_grafici=False)
                prezzi_matrice.append([g["prezzo"] for g in esito["giorni"]])
                prezzi_finali.append(esito["summary"]["prezzo_finale"])
                for gruppo, dati in esito["gruppi_psicologici_finali"].items():
                    rendimento_per_gruppo[gruppo].append(dati["rendimento_percentuale"])
                for tipo, dati in esito["classi_finali"].items():
                    rendimento_per_classe[tipo].append(dati["rendimento_percentuale"])

            lunghezza_minima = min((len(p) for p in prezzi_matrice), default=0)
            grafico_fan = None
            if lunghezza_minima > 0:
                matrice = np.array([p[:lunghezza_minima] for p in prezzi_matrice])
                giorni_idx = list(range(lunghezza_minima))
                grafico_fan = genera_grafico_fan(
                    f"Prezzo medio su {run_effettivi} run ({etichetta})",
                    "Prezzo",
                    giorni_idx,
                    matrice.mean(axis=0).tolist(),
                    matrice.min(axis=0).tolist(),
                    matrice.max(axis=0).tolist(),
                )

            smart_vals = rendimento_per_gruppo["Smart"]
            dumb_vals = rendimento_per_gruppo["Dumb"]
            win_rate = None
            differenze = []
            if smart_vals and dumb_vals:
                differenze = [s - d for s, d in zip(smart_vals, dumb_vals)]
                vittorie = sum(1 for diff in differenze if diff > 0)
                win_rate = round(100 * vittorie / len(differenze), 1)

            risultati_livelli.append(
                {
                    "etichetta": etichetta,
                    "numero_run": run_effettivi,
                    "prezzo_medio_finale": round(float(np.mean(prezzi_finali)), 2) if prezzi_finali else None,
                    "rendimento_medio_gruppi": {
                        gruppo: (round(float(np.mean(valori)), 2) if valori else None)
                        for gruppo, valori in rendimento_per_gruppo.items()
                    },
                    "rendimento_medio_classi": {
                        tipo: (round(float(np.mean(valori)), 2) if valori else None)
                        for tipo, valori in rendimento_per_classe.items()
                    },
                    "win_rate_smart_vs_dumb": win_rate,
                    "grafico_fan_prezzo": grafico_fan,
                    "grafico_scatter_smart_dumb": genera_grafico_scatter(
                        "Smart vs Dumb, ogni punto e' una run",
                        "Rendimento Dumb (%)",
                        "Rendimento Smart (%)",
                        dumb_vals,
                        smart_vals,
                    ),
                    "grafico_istogramma_differenza": genera_grafico_istogramma_generico(
                        "Differenza di rendimento (Smart - Dumb)", "Differenza percentuale", differenze
                    ),
                }
            )

        return {"livelli": risultati_livelli}
