# Cosa è stato aggiunto alla dashboard — spiegato semplice

Ho implementato direttamente sul tuo Mac (cartella `Desktop/LAM`) la maggior
parte delle migliorie proposte, testandole una per una prima di considerarle
finite. Ogni fase è un commit git separato, quindi puoi vedere esattamente
cosa è cambiato e quando (e tornare indietro se serve — oltre al Checkpoint 1
di prima, ora hai anche tutta la cronologia di questi passaggi).

Cerco di spiegare ogni cosa come la spiegherei a voce, senza troppo
gergo tecnico.

## 1. Il pannello "Proprietà statistiche (stylized facts)"

Questo è il pezzo più importante, perché risponde direttamente a quello che
il vostro programma di lavoro chiede alla Settimana 5 e a quello che il paper
di riferimento (Cocco, Concas, Marchesi, 2017) usa per giudicare se il
modello è realistico.

In pratica: ogni volta che lanci una simulazione, la dashboard calcola i
"rendimenti" giornalieri (di quanto sale o scende il prezzo in percentuale,
in scala logaritmica) e ne misura quattro cose:

- **media** e **deviazione standard**: quanto in media il prezzo si muove
  ogni giorno, e quanto è "nervoso".
- **asimmetria**: se il prezzo tende a fare salti più grandi verso l'alto o
  verso il basso.
- **curtosi**: quanto sono frequenti i movimenti estremi rispetto a una
  normale distribuzione statistica (dove il valore di riferimento è 3). Il
  Bitcoin reale ha una curtosi altissima (15 secondo il paper): significa che
  crolli e impennate enormi capitano molto più spesso di quanto una
  distribuzione "normale" farebbe pensare. Questo fenomeno si chiama "fat
  tail" (coda grassa) e lo vedi anche visivamente nel nuovo istogramma dei
  rendimenti, dove ho sovrapposto una curva normale di confronto.

Sotto trovi anche tre schede colorate che mostrano il risultato del **test
di Dickey-Fuller** (un test statistico standard): verifica se il prezzo si
comporta come una "camminata casuale" (random walk), cioè senza un livello a
cui torna sempre — proprietà tipica di tutti i mercati finanziari reali,
Bitcoin incluso. Ho implementato il test da zero con la matematica di base
(niente librerie esterne), usando esattamente le stesse soglie di
riferimento citate nel paper, così il codice resta leggibile e spiegabile
in sede di esame.

C'è anche un nuovo grafico di **autocorrelazione**: confronta come i
rendimenti "grezzi" e quelli "in valore assoluto" si comportano nei 20 giorni
successivi. Serve a mostrare il "volatility clustering", cioè il fatto che i
periodi turbolenti tendono a raggrupparsi nel tempo (un giorno molto mosso è
spesso seguito da altri giorni molto mossi).

## 2. Tre grafici che avevi già i dati per fare (quick win)

- **Gini nel tempo**: prima calcolavi l'indice di disuguaglianza solo per
  l'ultimo giorno, ora lo vedi giorno per giorno in un grafico.
- **Curva di Lorenz**: mostra visivamente cosa significa un certo valore di
  Gini — più la curva si allontana dalla linea diagonale, più la ricchezza è
  concentrata in pochi trader.
- **Volumi giornalieri**: quanti trader hanno comprato/venduto ogni giorno,
  in un grafico a barre (prima questo dato si vedeva solo nella tabellina
  delle ultime 12 righe).

## 3. Un nuovo tipo di trader: lo Smart trader

Prima la dashboard etichettava "Smart" i Chartist, ma un Chartist segue solo
il trend, non è davvero "furbo". Ho creato una quarta categoria vera e
propria, lo **SmartTrader**: guarda la media dei prezzi delle ultime 20
giornate e fa il contrario della massa — compra quando il prezzo è sceso
sotto quella media, vende quando è salito sopra. È lo stesso tipo di
comportamento disciplinato descritto nel libro *Trading in the Zone* di Mark
Douglas, citato dai vostri compagni.

Ho anche riorganizzato il confronto psicologico: ora è **Smart vs Normal vs
Dumb** (prima era solo Smart vs Dumb, e "Smart" era un'etichetta finta).
Random trader = "Normal" (rumore di fondo neutro), Chartist + Noise trader =
"Dumb" (inseguono impulsivamente il trend o le notizie), il nuovo
SmartTrader = "Smart".

**Nota onesta**: nei test che ho fatto, lo Smart trader non vince sempre —
a volte sì, a volte no, a seconda dei parametri. Non ho "aggiustato" la
simulazione per farlo vincere sempre, perché sarebbe scientificamente
scorretto: il bello è che ora puoi usare le simulazioni multiple (punto 6)
per scoprire *in quali condizioni* essere contrarian conviene davvero, che è
esattamente il tipo di domanda di ricerca che un LAM dovrebbe porsi.

## 4. Spread bid/ask

Nuovo parametro: ogni scambio ora ha un piccolo costo implicito (chi compra
paga un po' sopra il prezzo di mercato, chi vende incassa un po' sotto),
proprio come nei mercati reali. È una versione semplificata ma efficace del
vero "order book" con prezzi di acquisto/vendita separati che il paper
descrive in dettaglio — implementare l'order book completo (con classi
dedicate per gli ordini e un motore di abbinamento) resta un possibile
sviluppo futuro, più impegnativo (vedi in fondo).

## 5. Mining e nuovi trader nel tempo

Due meccaniche opzionali (disattivate di default, le attivi tu quando
vuoi con gli interruttori "Mining" e "Nuovi trader nel tempo"):

- **Mining**: ogni giorno un trader Random a caso riceve una quantità fissa
  di nuovi bitcoin, che si aggiungono al totale in circolazione (grafico
  dedicato "Bitcoin in circolazione").
- **Nuovi trader nel tempo**: ogni giorno entrano in media alcuni nuovi
  trader nel mercato, con solo cash e zero bitcoin (rappresentano chi
  scopre Bitcoin per la prima volta), come descritto nel paper. Il loro
  numero cresce nel grafico "Trader attivi nel tempo".

## 6. Simulazioni multiple (Monte Carlo / sensitivity)

Questa è la sezione più "avanzata", in fondo alla pagina. Invece di lanciare
una sola simulazione (che dipende dal caso), puoi:

- Lanciarne **N di fila** con parametri identici ma semi diversi, e vedere
  una fascia di prezzo medio (minimo-massimo) invece di una singola linea:
  più la fascia è stretta, più il risultato è affidabile e non frutto del
  caso.
- Vedere il **win-rate**: su N simulazioni, quante volte gli Smart trader
  battono i Dumb trader.
- Vedere uno **scatter plot** (ogni punto è una simulazione) e un
  **istogramma della differenza di rendimento** tra Smart e Dumb.
- **Confrontare fino a 3 valori di un parametro** (es. spread basso/medio/
  alto), esattamente come la sezione 8 del progetto dei vostri compagni
  (fees0.0001/0.0005/0.001, ecc.), per vedere come cambia il risultato medio.

Per non appesantire troppo il tuo Mac, se chiedi troppe run con troppi
trader/giorni la dashboard riduce automaticamente il numero di run eseguite
(te lo dice comunque nel risultato quante ne ha fatte davvero).

## Cosa NON ho ancora fatto (di proposito)

- **Order book completo** con classi `BuyOrder`/`SellOrder`/`OrderBook` e un
  vero meccanismo di matching (Settimana 3 del programma di lavoro): è il
  pezzo più fedele al paper ma anche il più rischioso da costruire bene in
  poco tempo senza test approfonditi; ho preferito la versione "spread"
  (punto 4) che dà già un beneficio concreto senza rischiare di rompere
  quello che funziona. Se vuoi, possiamo affrontarlo in una sessione
  dedicata.
- **Uscita dei trader dal mercato**: ho implementato solo l'ingresso di
  nuovi trader, non la loro uscita (il paper la prevede entrambe): l'ho
  lasciata fuori per tenere il codice più semplice da leggere e spiegare.
- Le idee più "creative" (indice di sentiment come termometro, shock event
  iniettabile da UI, confronto A/B affiancato) restano ancora da fare, se ti
  interessano.

## Come vedere tutto in azione

Nel terminale, dalla cartella del progetto:

```
cd ~/Desktop/LAM
LAM_env/bin/python dashboard/app.py
```

poi apri `http://127.0.0.1:8765` come sempre. Tutti i nuovi controlli sono
nella colonna di sinistra (Smart, Spread, Mining, Nuovi trader), le nuove
statistiche subito sotto il grafico del prezzo, i nuovi grafici nella
sezione "Analisi classi trader e statistiche", e le simulazioni multiple in
fondo alla pagina. La guida (`Guida parametri`) è stata aggiornata con la
spiegazione di ogni cosa nuova.

## Cronologia dei cambiamenti (git)

```
96a5567  Frontend: nuovi controlli, pannello statistiche avanzate e sezione
         simulazioni multiple
7f693b1  Aggiunto endpoint /api/multirun
df200cc  Motore di simulazione: stylized facts, SmartTrader, spread, mining,
         nuovi trader, Gini/Lorenz/volumi
3426d6f  Riorganizzazione cartelle (sessione precedente)
8f3fd37  Checkpoint 1: stato originale del progetto
```
