# Graph Report - LAM  (2026-10-23)

## Corpus Check
- Corpus is ~16,936 words - fits in a single context window. You may not need a graph.

## Summary
- 549 nodes · 991 edges · 21 communities (20 shown, 1 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 100 edges (avg confidence: 0.89)
- Token cost: 555,156 input · 0 output

## Community Hubs (Navigation)
- Simulation Engine (current + checkpoint)
- Checkpoint & Run Notes
- Dashboard Frontend (current)
- Paper Model, Order Book & Work Plan
- Example Project Overview
- Paper Figures & Citations
- Dashboard Frontend (checkpoint)
- HTTP Server & API
- MATLAB Multi-run Mechanics
- MATLAB Advanced Version
- Work Plan Modules (checkpoint)
- Stylized Facts Validation
- Mining & New Traders
- Checkpoint Trader Classes
- Irrational Trader Psychology
- Example Project Authors
- MATLAB Standard GUI
- Order Construction Rules
- Calibration & Wealth Distribution
- Python Trader Classes Plan
- Smart Contrarian Traders

## God Nodes (most connected - your core abstractions)
1. `Using an artificial financial market for studying a cryptocurrency market (Cocco, Concas, Marchesi 2017)` - 79 edges
2. `_esegui_simulazione()` - 26 edges
3. `Progetto Python Mercato Bitcoin Artificiale - Programma di lavoro` - 19 edges
4. `_esegui_simulazione()` - 13 edges
5. `Trader razionali e irrazionali: un esperimento nel mercato delle criptovalute` - 13 edges
6. `figura_to_data_uri()` - 12 edges
7. `Agent-based Artificial Cryptocurrency Market` - 12 edges
8. `genera_grafici()` - 11 edges
9. `index.html (dashboard page)` - 11 edges
10. `Trader razionali e irrazionali: un esperimento nel mercato delle criptovalute (esempio progetto LAM)` - 11 edges

## Surprising Connections (you probably didn't know these)
- `statistiche_rendimenti()` --implements--> `Exam comparison vs paper Table 3 (mean 0.007, sd 0.057, skew 0.239, kurt 15.001)`  [INFERRED]
  dashboard/simulation.py → documenti/guida-progetto-e-dashboard.md
- `aggrega_gruppi_psicologici()` --implements--> `Psychological groups Smart vs Normal vs Dumb`  [INFERRED]
  dashboard/simulation.py → documenti/guida-progetto-e-dashboard.md
- `esegui_ordine()` --implements--> `Bid/Ask Spread (half-spread execution price)`  [EXTRACTED]
  dashboard/simulation.py → documenti/confronto-order-book-vs-meccanismo-attuale.pdf
- `_esegui_simulazione()` --implements--> `Impatto domanda/offerta (price impact)`  [INFERRED]
  dashboard/simulation.py → dashboard/static/guida.html
- `_esegui_simulazione()` --implements--> `Aggregate Imbalance Price Mechanism (dashboard/simulation.py)`  [EXTRACTED]
  dashboard/simulation.py → documenti/confronto-order-book-vs-meccanismo-attuale.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ciclo giornaliero: sentiment, decisioni, order book, matching, prezzo, portafogli** — checkpoint_1_lam_documenti_originale_esempio_progettolam_update_sentiment, checkpoint_1_lam_documenti_originale_esempio_progettolam_make_trading_decisions_advanced, checkpoint_1_lam_documenti_originale_esempio_progettolam_order_book, checkpoint_1_lam_documenti_originale_esempio_progettolam_order_matching, checkpoint_1_lam_documenti_originale_esempio_progettolam_market_impact, checkpoint_1_lam_documenti_originale_esempio_progettolam_portfolio_performance [EXTRACTED 1.00]
- **Esperimenti multi-run di sensitività (100 run x 3 valori)** — checkpoint_1_lam_documenti_originale_esempio_progettolam_sim_fees, checkpoint_1_lam_documenti_originale_esempio_progettolam_sim_smart_traders, checkpoint_1_lam_documenti_originale_esempio_progettolam_sim_spread, checkpoint_1_lam_documenti_originale_esempio_progettolam_sim_miners, checkpoint_1_lam_documenti_originale_esempio_progettolam_sim_volatility, checkpoint_1_lam_documenti_originale_esempio_progettolam_advanced_multirun_version [EXTRACTED 1.00]
- **Tre tipologie di trader del simulatore** — checkpoint_1_lam_documenti_originale_esempio_progettolam_smart_traders, checkpoint_1_lam_documenti_originale_esempio_progettolam_dumb_traders, checkpoint_1_lam_documenti_originale_esempio_progettolam_normal_traders, checkpoint_1_lam_documenti_originale_esempio_progettolam_make_trading_decisions_advanced [EXTRACTED 1.00]
- **Mechanisms reproducing Bitcoin stylized facts (Chartists, Zipf wealth, order book)** — documenti_bibliografia_artificial_financial_market_chartists, documenti_bibliografia_artificial_financial_market_pareto_zipf_wealth, documenti_bibliografia_artificial_financial_market_limit_order_book, documenti_bibliografia_artificial_financial_market_fat_tails, documenti_bibliografia_artificial_financial_market_volatility_clustering, documenti_bibliografia_artificial_financial_market_unit_root_property [EXTRACTED 1.00]
- **Daily simulation cycle: decisions -> order book -> matching -> price/portfolio update** — documenti_esempio_progetto_lam_make_trading_decisions_advanced, documenti_esempio_progetto_lam_order_book_aggregato, documenti_esempio_progetto_lam_matching_pro_quota, documenti_esempio_progetto_lam_market_impact, documenti_esempio_progetto_lam_portafogli_performance [EXTRACTED 1.00]
- **Recommended Python code structure** — checkpoint_1_lam_documenti_originale_lam_trader_py, checkpoint_1_lam_documenti_originale_lam_orders_py, checkpoint_1_lam_documenti_originale_lam_orderbook_py, checkpoint_1_lam_documenti_originale_lam_market_py, checkpoint_1_lam_documenti_originale_lam_analysis_py, checkpoint_1_lam_documenti_originale_lam_main_py [EXTRACTED 1.00]
- **Order generation and clearing flow** — checkpoint_1_lam_documenti_originale_file_bitcoin_buy_and_sell_orders, checkpoint_1_lam_documenti_originale_file_bitcoin_lognormal_beta_order_size, checkpoint_1_lam_documenti_originale_file_bitcoin_limit_price_gaussian, checkpoint_1_lam_documenti_originale_file_bitcoin_market_order_probability_plim, checkpoint_1_lam_documenti_originale_file_bitcoin_order_expiration, checkpoint_1_lam_documenti_originale_file_bitcoin_order_book, checkpoint_1_lam_documenti_originale_file_bitcoin_transaction_price_rule [EXTRACTED 1.00]
- **Multi-run sensitivity experiments (fees, smart %, spread, miners, volatility)** — documenti_esempio_progetto_lam_simulazione_fees, documenti_esempio_progetto_lam_simulazione_smart_traders, documenti_esempio_progetto_lam_simulazione_spread, documenti_esempio_progetto_lam_simulazione_miners, documenti_esempio_progetto_lam_simulazione_volatilita, documenti_esempio_progetto_lam_versione_avanzata_multirun [EXTRACTED 1.00]
- **Endogenous mechanisms reproducing Bitcoin stylized facts** — checkpoint_1_lam_documenti_originale_file_bitcoin_chartists, checkpoint_1_lam_documenti_originale_file_bitcoin_pareto_zipf_wealth_distribution, checkpoint_1_lam_documenti_originale_file_bitcoin_limit_price_gaussian, checkpoint_1_lam_documenti_originale_file_bitcoin_fat_tail_phenomenon, checkpoint_1_lam_documenti_originale_file_bitcoin_volatility_clustering, checkpoint_1_lam_documenti_originale_file_bitcoin_unit_root_property [EXTRACTED 1.00]
- **Stylized facts validation against Cocco et al. 2017** — dashboard_static_guida_stylized_facts, dashboard_static_guida_fat_tail, dashboard_static_guida_volatility_clustering, dashboard_static_guida_adf_test, documenti_bibliografia_artificial_financial_market_paper, dashboard_static_index_stats_panel [EXTRACTED 1.00]
- **Three-class trader typology (smart/normal/dumb)** — documenti_esempio_progetto_lam_smart_traders, documenti_esempio_progetto_lam_normal_traders, documenti_esempio_progetto_lam_dumb_traders [EXTRACTED 1.00]
- **Trader agent classes (Random, Chartist, Noise, Smart)** — dashboard_static_guida_trader, dashboard_static_guida_randomtrader, dashboard_static_guida_chartist, dashboard_static_guida_noisetrader, dashboard_static_guida_smarttrader [EXTRACTED 1.00]
- **Six-week work plan replicating the Cocco et al. model** — documenti_programma_di_lavoro_fase1_setup_pareto, documenti_programma_di_lavoro_fase2_trader_classes, documenti_programma_di_lavoro_fase3_order_book, documenti_programma_di_lavoro_fase4_simulation_loop, documenti_programma_di_lavoro_fase5_statistical_analysis, documenti_programma_di_lavoro_fase6_extensions [EXTRACTED 1.00]
- **Monte Carlo multi-run flow** — dashboard_static_index_multirun_panel, documenti_report_migliorie_dashboard_api_multirun, dashboard_static_guida_monte_carlo, dashboard_static_guida_win_rate_smart_vs_dumb [INFERRED 0.85]
- **Order book prototype implementation (orders, book, match)** — documenti_confronto_order_book_vs_meccanismo_attuale_order_book_prototype, documenti_confronto_order_book_vs_meccanismo_attuale_buyorder_sellorder, documenti_confronto_order_book_vs_meccanismo_attuale_orderbook_class, documenti_confronto_order_book_vs_meccanismo_attuale_match_method, documenti_programma_di_lavoro_fase3_order_book [INFERRED 0.85]

## Communities (21 total, 1 thin omitted)

### Community 0 - "Simulation Engine (current + checkpoint)"
Cohesion: 0.05
Nodes (69): aggrega_classi(), aggrega_smart_dumb(), arrotonda_aggregati(), calcola_gini(), costruisci_serie(), crea_popolazione_trader(), esegui_ordine(), _esegui_simulazione() (+61 more)

### Community 1 - "Checkpoint & Run Notes"
Cohesion: 0.06
Nodes (55): informazioni.txt (checkpoint 1), Port auto-fallback 8765-8784 (PORT env override), guida.html (checkpoint 1, original parameter guide), index.html (checkpoint 1, original dashboard page), Buy / Sell metric (orders total), requirements.txt (checkpoint 1), LEGGIMI_RIPRISTINO.txt (Checkpoint 1 restore guide), Checkpoint 1 (backup pre-riorganizzazione, commit 8f3fd37) (+47 more)

### Community 2 - "Dashboard Frontend (current)"
Cohesion: 0.07
Nodes (48): balancePercentageGroup(), canvas, clampInputValue(), countDecimals(), ctx, defaults, descriviErrore(), DESCRIZIONI_GRAFICI (+40 more)

### Community 3 - "Paper Model, Order Book & Work Plan"
Cohesion: 0.07
Nodes (42): esegui_ordine(), Agent-based Artificial Cryptocurrency Market, Augmented Dickey-Fuller Test, Autocorrelation of Raw vs Absolute Returns, Bae et al. 2003 - Traders choice between limit and market orders, Bitcoin, Blockchain / Blockchain.info data, Buy and Sell Orders (amount, limit price, expiration) (+34 more)

### Community 4 - "Example Project Overview"
Cohesion: 0.06
Nodes (30): Alan Greenspan (espressione 'irrational exuberance', 1996), Bitcoin (BTC), Blockchain, Using an Artificial Financial Market for Studying a Cryptocurrency Market (Cocco, Concas, Marchesi, 2015), Crisi finanziaria 2008 (bolla immobiliare USA), Trader razionali e irrazionali: un esperimento nel mercato delle criptovalute (esempio progetto LAM), Figura 1: interfaccia parametri simulazione, Figura 2: output singola simulazione (prezzo, volumi, performance relativa) (+22 more)

### Community 5 - "Paper Figures & Citations"
Cohesion: 0.08
Nodes (36): Agent-based artificial cryptocurrency market, Androulaki et al. 2013 User privacy in Bitcoin, Bitcoin, Bornholdt & Sneppen 2014 Competing crypto-currencies (Moran process), Chakraborti et al. 2011 Econophysics review, Cincotti et al. 2003 Who wins?, Eyal & Sirer 2013 Bitcoin mining vulnerable, Fig 3: Simulated Bitcoin price (+28 more)

### Community 6 - "Dashboard Frontend (checkpoint)"
Cohesion: 0.11
Nodes (32): canvas, clampInputValue(), countDecimals(), ctx, defaults, descriviErrore(), drawChart(), fillForm() (+24 more)

### Community 8 - "MATLAB Multi-run Mechanics"
Cohesion: 0.14
Nodes (18): Bid/ask spread, Fee rate (commissioni), Figura 4: Output multi-run (candele performance, winrate smart, scatter smart vs dumb, istogramma differenze), Market impact (impact_k), Matching aggregato pro-quota, Mining e offerta, multirun1.m, multisimulationresult.m (+10 more)

### Community 9 - "MATLAB Advanced Version"
Cohesion: 0.16
Nodes (16): Versione avanzata (multi-run), Bid/ask e spread, Fee rate (commissioni), Figura 4: grafici output multi-run (candele, winrate, scatter, distribuzione differenze), Impatto di mercato (impact_k), Miners, multirun1.m, multisimulationresult.m (+8 more)

### Community 10 - "Work Plan Modules (checkpoint)"
Cohesion: 0.17
Nodes (16): Transaction price formation rules, analysis.py (returns, plots, statistics), collections_deque, Distribuzione di Pareto script, Fase 1: Fondamenta teoriche e setup, Fase 3: Ordini e Order Book, Fase 5: Analisi statistica dei risultati, Log-returns giornalieri (+8 more)

### Community 11 - "Stylized Facts Validation"
Cohesion: 0.14
Nodes (15): Augmented Dickey-Fuller test, Autocorrelation of raw vs absolute returns, Chartists, Fat-tail phenomenon (excess kurtosis), Fig 5: ACF of real raw and absolute returns, Fig 6: ACF of simulated raw and absolute returns, Kolmogorov-Smirnov test, Lux & Marchesi 2000 Volatility clustering (+7 more)

### Community 12 - "Mining & New Traders"
Cohesion: 0.18
Nodes (13): Block reward halving (50 to 25 BTC), Blockchain.info empirical data, Fig 1: Unique addresses NU(t) and total Bitcoins, Fig 2: Real Bitcoin price and unique addresses, Mining of new Bitcoins (not explicitly modelled), New traders inflow from Blockchain unique addresses, Random Traders, Fase 4: Ciclo di simulazione (200 giorni) (+5 more)

### Community 13 - "Checkpoint Trader Classes"
Cohesion: 0.17
Nodes (4): Chartist, NoiseTrader, RandomTrader, Trader

### Community 14 - "Irrational Trader Psychology"
Cohesion: 0.23
Nodes (10): Alan Greenspan (irrational exuberance, 1996), Dumb traders (agenti irrazionali), Irrational Exuberance 3rd ed. (Robert J. Shiller, 2015), make_trading_decisions_advanced(), Normal traders, Prezzo di riferimento (Cref), price_ratio (prezzo / prezzo di riferimento), run_crypto_simulation_internal() (+2 more)

### Community 15 - "Example Project Authors"
Cohesion: 0.17
Nodes (13): Bitcoin (BTC), Blockchain, Simulatore agent-based del mercato BTC, Using an Artificial Financial Market for Studying a Cryptocurrency Market (Cocco, Concas, Marchesi 2015), Codice sorgente (Google Drive), Lavoro di maturità (LAM), Liceo Lugano 2, Dott. Marco Favino (+5 more)

### Community 16 - "MATLAB Standard GUI"
Cohesion: 0.24
Nodes (10): Figura 1: Interfaccia parametri simulazione, Figura 2: Output singola simulazione (prezzo, volumi, performance relativa), Figura 3: Plot performance traders (smart verde, dumb rosso, normal blu), MATLAB, Parametri di simulazione (traders, giorni, allocation, capitale, volatilità, %smart, %dumb, fee, impact K), plot_results(), Portafogli USD/BTC e performance per categoria, run_simulation() (+2 more)

### Community 17 - "Order Construction Rules"
Cohesion: 0.29
Nodes (8): Bae et al. 2003 Limit vs market orders NYSE, Buy and sell orders, Lognormal beta order-size factor (mean 0.25, sd 0.2), Market order probability Plim (0.2 Random, 0.7 Chartist), Order expiration time, BuyOrder class, orders.py (BuyOrder, SellOrder), SellOrder class

### Community 18 - "Calibration & Wealth Distribution"
Cohesion: 0.33
Nodes (6): Levy & Solomon 1997 Power-law wealth, Model calibration (830 daily steps, 1/100 market scale), Newman 2005 Power laws, Pareto and Zipf, Pareto / Zipf wealth distribution (alpha=1), Simulation parameters (Table 1), Takayasu 1990 Fractals in the physical sciences

### Community 19 - "Python Trader Classes Plan"
Cohesion: 0.47
Nodes (6): Chartist class, Fase 2: Modellare i trader, RandomTrader class, Ricchezza distribuita secondo Zipf, Trader class, trader.py (Trader, RandomTrader, Chartist)

### Community 20 - "Smart Contrarian Traders"
Cohesion: 0.33
Nodes (5): Crisi finanziaria 2008 / bolla immobiliare USA, is_rally / is_crash / recent_trend, Smart traders (agenti razionali), The Big Short (film), Trading in the Zone (Mark Douglas, 2000)

## Ambiguous Edges - Review These
- `Unit-root property` → `Mean-reverting price toward cash/Bitcoin ratio`  [AMBIGUOUS]
  checkpoint_1/LAM-documenti-originale/file bitcoin.pdf · relation: semantically_similar_to

## Knowledge Gaps
- **62 isolated node(s):** `Fig 7: Bitcoin and cash per trader population`, `Luthe 2013 Cryptocurrencies, network effects, switching costs`, `Bornholdt & Sneppen 2014 Competing crypto-currencies (Moran process)`, `Hommes 2006 HAMs in economics and finance`, `LeBaron 2006 Agent-based computational finance` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 133 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Using an artificial financial market for studying a cryptocurrency market (Cocco, Concas, Marchesi 2017)` connect `Paper Figures & Citations` to `Checkpoint & Run Notes`, `Paper Model, Order Book & Work Plan`, `Work Plan Modules (checkpoint)`, `Stylized Facts Validation`, `Mining & New Traders`, `Order Construction Rules`, `Calibration & Wealth Distribution`?**
  _High betweenness centrality (0.222) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Using an artificial financial market for studying a cryptocurrency market (Cocco, Concas, Marchesi 2017)` (e.g. with `Fase 6: Estensioni e confronto col paper` and `Progetto Python Mercato Bitcoin Artificiale - Programma di lavoro`) actually correct?**
  _`Using an artificial financial market for studying a cryptocurrency market (Cocco, Concas, Marchesi 2017)` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Fig 7: Bitcoin and cash per trader population`, `Luthe 2013 Cryptocurrencies, network effects, switching costs`, `Bornholdt & Sneppen 2014 Competing crypto-currencies (Moran process)` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Simulation Engine (current + checkpoint)` be split into smaller, more focused modules?**
  _Cohesion score 0.051535087719298246 - nodes in this community are weakly interconnected._
- **Why does `_esegui_simulazione()` connect `Simulation Engine (current + checkpoint)` to `Checkpoint & Run Notes`, `Paper Model, Order Book & Work Plan`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `_esegui_simulazione()` (e.g. with `Impatto domanda/offerta (price impact)` and `Mining mechanic`) actually correct?**
  _`_esegui_simulazione()` has 5 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Unit-root property` and `Mean-reverting price toward cash/Bitcoin ratio`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._