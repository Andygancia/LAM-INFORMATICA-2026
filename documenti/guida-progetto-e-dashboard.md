# Guida al progetto — Mercato Bitcoin Artificiale

LAM di Informatica, Liceo Lugano 2, 2026. Questa guida spiega come è fatto il
progetto e come si usa la dashboard, così puoi consultarla mentre lavori o
mentre ti prepari per la presentazione.

## Di cosa si tratta

Il progetto simula un mercato finanziario artificiale del Bitcoin: un
gruppo di agenti software (i "trader"), ognuno con una logica di
comportamento diversa, compra e vende bitcoin giorno dopo giorno all'interno
di un mercato semplificato. Dal loro comportamento collettivo emerge un
prezzo, esattamente come in un mercato reale nessuno decide il prezzo a
tavolino: è il risultato di tante decisioni individuali.

Il punto di riferimento teorico è il paper di Cocco, Concas e Marchesi
(2017), *"Using an artificial financial market for studying a cryptocurrency
market"* (lo trovi in `documenti/bibliografia-artificial-financial-market.pdf`).
L'idea del paper, e quindi del progetto, è verificare se un mercato
"giocattolo" con regole semplici riesce comunque a riprodurre alcune
proprietà statistiche tipiche dei mercati finanziari reali — le cosiddette
*stylized facts*: code grasse nei rendimenti (movimenti estremi più frequenti
del normale), raggruppamento della volatilità nel tempo, e un prezzo che si
comporta come una "camminata casuale" senza un livello a cui torna sempre.
Se la simulazione le riproduce, è un indizio che il modello cattura qualcosa
di reale nel comportamento dei mercati, pur essendo molto più semplice della
realtà.

## Struttura del progetto

Tutto si trova nella cartella `Desktop/LAM` sul tuo Mac:

- `dashboard/app.py` — il server che fa girare la dashboard nel browser.
- `dashboard/simulation.py` — il motore della simulazione: le classi dei
  trader, la formazione del prezzo, le statistiche e i grafici.
- `dashboard/static/` — il frontend: `index.html` (la pagina), `app.js`
  (interattività e grafico del prezzo), `styles.css`, e `guida.html` (una
  guida più tecnica ai singoli parametri, raggiungibile dal link "Guida
  parametri" dentro la dashboard stessa).
- `documenti/` — il paper di riferimento, il programma di lavoro, l'esempio
  dei compagni Cattaneo & Bartoli e i report di sviluppo.
- `requirements.txt` e `LAM_env/` — le librerie Python usate (numpy e
  matplotlib) e l'ambiente virtuale in cui sono installate.
- `checkpoint_1/` — uno stato congelato del progetto a un punto precedente,
  utile come riferimento o come "rete di sicurezza".
- `.git` — la cronologia di tutte le modifiche fatte al codice: puoi vedere
  cosa è cambiato e quando con `git log`, e tornare indietro se serve.

## Come avviare la dashboard

Nel terminale:

```
cd ~/Desktop/LAM
LAM_env/bin/python dashboard/app.py
```

Poi apri `http://127.0.0.1:8765` nel browser (se la porta è occupata, il
server prova automaticamente quelle successive fino alla 8784, e te lo dice
a schermo). Se l'ambiente `LAM_env` non esiste ancora, si crea una volta
sola con:

```
python3 -m venv LAM_env
LAM_env/bin/pip install -r requirements.txt
```

## Come funziona il motore, in breve

All'inizio della simulazione viene creata una popolazione di trader, e a
ciascuno viene assegnata una quota di cash e di bitoin secondo una
distribuzione di Pareto (parametro "Beta Pareto"): con beta basso pochi
trader partono già molto più ricchi degli altri, con beta alto la ricchezza
iniziale è più equamente distribuita.

Poi, per ogni giorno simulato: viene estratta una notizia (positiva, neutra
o negativa, secondo le probabilità impostate); ogni trader, in base al suo
tipo, decide se comprare, vendere o restare fermo; si contano compratori e
venditori e il prezzo si aggiorna in base allo squilibrio fra i due (più
compratori → prezzo su, più venditori → prezzo giù), con l'aggiunta di un
piccolo rumore casuale e di uno shock legato alla notizia del giorno. Ogni
scambio paga inoltre metà dello spread bid/ask impostato, come costo
implicito di esecuzione — chi compra paga un po' sopra il prezzo di mercato,
chi vende incassa un po' sotto.

Le cinque classi di trader nel codice (`simulation.py`) sono:

- **Trader** — la classe base: tiene traccia di cash, bitcoin e ricchezza
  totale (cash + bitcoin al prezzo corrente) di ogni agente.
- **RandomTrader** — agisce con una piccola probabilità ogni giorno e, se
  agisce, decide a caso se comprare o vendere. Rappresenta il "rumore di
  fondo" neutro del mercato: nel confronto psicologico è il gruppo "Normal".
- **Chartist** — guarda la variazione recente del prezzo: se è salito
  abbastanza tende a comprare (segue il trend), se è sceso tende a vendere.
  Insegue anche il semplice rumore di breve periodo, quindi è nel gruppo
  "Dumb".
- **NoiseTrader** — reagisce alla notizia del giorno (compra su notizie
  positive, vende su notizie negative) e può vendere per panico anche senza
  una notizia negativa: è il trader più emotivo, ed è anche lui nel gruppo
  "Dumb".
- **SmartTrader** — guarda la media dei prezzi delle ultime giornate e fa il
  contrario della massa: compra quando il prezzo è sceso sotto quella media,
  vende quando è salito sopra. È un contrarian disciplinato (ispirato a
  *Trading in the Zone* di Mark Douglas) ed è l'unico membro del gruppo
  "Smart".

Due meccaniche sono opzionali e disattivate di default: il **mining** (ogni
giorno un RandomTrader a caso riceve nuovi bitcoin, che si aggiungono al
totale in circolazione) e l'**ingresso di nuovi trader** (ogni giorno entrano
in media alcuni nuovi trader con solo cash, a rappresentare chi scopre
Bitcoin per la prima volta).

## Guida all'uso della dashboard

### Colonna sinistra — parametri

**Parametri generali**

- *Trader* — quanti agenti partecipano al mercato (default 100, tra 10 e
  2000). Più trader significa una simulazione più popolata e meno dominata
  da singoli comportamenti casuali.
- *Giorni* — durata della simulazione (default 120, tra 1 e 1000).
- *Prezzo iniziale* — prezzo di partenza del bitcoin (default 5.0).
- *Beta Pareto* — quanto è diseguale la distribuzione iniziale di cash e
  bitcoin (default 1.0, tra 0.1 e 5): valori bassi concentrano di più la
  ricchezza.
- *Bitcoin totali* / *Cash totale* — quantità complessive distribuite tra i
  trader all'inizio (default 80'000 BTC e 400'000 di cash).
- *Impatto domanda/offerta* — quanto il prezzo reagisce allo squilibrio tra
  compratori e venditori (default 0.08, tra 0 e 1): più è alto, più basta
  poco per muovere il prezzo.
- *Spread bid/ask (%)* — il costo implicito di ogni scambio (default 0.4%,
  tra 0 e 20).
- *Seed* — il numero che rende la simulazione ripetibile: stesso seed e
  stessi parametri danno sempre lo stesso risultato, utile per confrontare
  scenari cambiando un solo parametro alla volta.

**Tipi di trader**

Per ciascuna delle quattro classi (Random, Chartist, Smart, Noise) puoi
attivarla o disattivarla con l'interruttore e impostarne la quota
percentuale. Le quote delle categorie attive devono sommare esattamente a
100; se disattivi una categoria viene esclusa dal totale. Se la somma non è
100, compare un pulsante "Bilancia a 100" che riscala i valori mantenendone
le proporzioni. Quando il Noise trader è attivo, sotto compaiono anche le
probabilità delle **notizie** (positiva / neutra / negativa, di default
10/80/10): sono pesi, non serve che siano percentuali "pulite".

**Meccaniche avanzate**

Qui attivi, se vuoi, il *Mining* (quanti BTC nuovi al giorno) e l'*Ingresso
di nuovi trader* (quanti in media al giorno).

Il pulsante **Reset** riporta tutti i parametri ai valori di default.

### Risultati di una simulazione singola

Dopo aver lanciato la simulazione trovi, in ordine:

- **Indicatori principali**: prezzo finale, variazione percentuale rispetto
  al prezzo iniziale, e indice di Gini finale (disuguaglianza della
  ricchezza: vicino a 0 = ricchezza distribuita in modo simile, vicino a 1 =
  concentrata in pochi trader).
- **Grafico del prezzo nel tempo**.
- **Proprietà statistiche (stylized facts)**: media, deviazione standard,
  asimmetria e curtosi dei rendimenti giornalieri (in scala logaritmica), più
  tre schede con l'esito del test di Dickey-Fuller (verifica se il prezzo si
  comporta come una camminata casuale, la stessa proprietà dei mercati
  finanziari reali). Il valore di riferimento per la curtosi di una
  distribuzione normale è 3; quella del Bitcoin reale, secondo il paper, è
  15.001 — più la curtosi simulata è alta, più ci sono "code grasse" (fat
  tail), cioè movimenti estremi frequenti. Aumentando la quota di Chartist
  la curtosi tende a salire.
- **Analisi classi trader e statistiche**: istogramma dei rendimenti con
  curva normale sovrapposta (rende visibile la fat tail a colpo d'occhio),
  grafico di autocorrelazione dei rendimenti grezzi vs assoluti (mostra il
  *volatility clustering*: i rendimenti assoluti restano positivi più a
  lungo, i grezzi restano vicini a zero), Gini nel tempo, curva di Lorenz,
  volumi giornalieri, ricchezza per gruppo psicologico (Smart vs Normal vs
  Dumb), e — se hai attivato mining o nuovi trader — i relativi grafici di
  BTC in circolazione e trader attivi nel tempo.
- **Popolazione**: quanti trader di ogni tipo sono effettivamente presenti.
- **Ultimi giorni**: tabella con notizia e prezzo esatto delle ultime
  giornate.

Ogni grafico si può ingrandire con un clic.

### Simulazioni multiple (Monte Carlo / sensitivity)

In fondo alla pagina puoi ripetere la stessa simulazione N volte (default
30) con semi diversi, invece di fidarti di una singola run che potrebbe
essere stata particolarmente fortunata o sfortunata per una categoria di
trader. Ottieni: il prezzo medio con una fascia minimo-massimo (più è
stretta, più il risultato è stabile), il **win-rate** Smart vs Dumb
(percentuale di run in cui gli Smart battono i Dumb), uno scatter plot
Smart vs Dumb (una run = un punto) e un istogramma della differenza di
rendimento tra i due gruppi. Puoi anche scegliere un parametro (es. lo
spread) e fino a 3 valori da confrontare: la dashboard ripete l'intera
analisi per ciascun valore, utile per vedere come cambia il risultato medio
al variare di quel parametro — lo stesso tipo di confronto (fees, spread,
% smart, miners) usato nella sezione avanzata dell'esempio dei compagni.
Con molti trader/giorni/run il calcolo può richiedere qualche secondo in
più; se il carico stimato è troppo alto, la dashboard riduce automaticamente
il numero di run eseguite (e te lo segnala nel risultato).

## Cosa guardare per l'esame

Il confronto più diretto con il paper si fa sui quattro numeri del pannello
statistiche (media, deviazione standard, asimmetria, curtosi) contro i
valori reali riportati nella Tabella 3 del paper (media 0.007, deviazione
standard 0.057, asimmetria 0.239, curtosi 15.001), e sull'esito del test
di Dickey-Fuller, che nel paper non riesce a rifiutare l'ipotesi di random
walk sia sui dati reali che su quelli simulati. Il grafico di
autocorrelazione è la prova visiva del volatility clustering (Fig. 5-6 del
paper). Le simulazioni multiple in fondo alla pagina sono utili per mostrare
che un risultato (es. "gli Smart trader battono i Dumb") non dipende da un
singolo seed fortunato, ma è sistematico su tante run — un punto che dà
rigore statistico alla presentazione.

## Cosa manca ancora (sviluppi futuri possibili)

Alcune parti del programma di lavoro non sono ancora state implementate, di
proposito, per tenere il codice solido e ben testato nel tempo a
disposizione:

- Un **order book completo**, con classi dedicate per gli ordini
  (`BuyOrder`/`SellOrder`) e un vero motore di abbinamento (`match()`),
  come descritto nel programma di lavoro (Settimana 3) e nel paper. Oggi c'è
  una versione semplificata con lo spread bid/ask.
- L'**uscita dei trader** dal mercato nel tempo (oggi è implementato solo
  l'ingresso di nuovi trader).
- Idee più "creative" non ancora realizzate: un indice di sentiment come
  termometro, uno shock event iniettabile dall'interfaccia, un confronto
  A/B affiancato tra due configurazioni diverse.

## Dove trovare altro materiale

- `documenti/programma-di-lavoro.pdf` — il programma di lavoro ufficiale del
  LAM.
- `documenti/bibliografia-artificial-financial-market.pdf` — il paper di
  Cocco, Concas e Marchesi (2017).
- `documenti/esempio-progetto-LAM.pdf` — l'esempio di riferimento di
  Cattaneo & Bartoli (2025).
- `documenti/report-migliorie-dashboard.md` — cronologia dettagliata di cosa
  è stato aggiunto alla dashboard e perché.
- `dashboard/static/guida.html` (link "Guida parametri" dentro la
  dashboard) — spiegazione tecnica di ogni singolo parametro e classe di
  trader, utile come riferimento rapido mentre usi l'interfaccia.
