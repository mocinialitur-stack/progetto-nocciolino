# Fuga della Nocciolina

Gioco arcade 2D in Python ambientato in una mappa infinita ispirata a Montefiascone.

## Requisiti

- Python 3.10 o piu recente
- `pygame` (installato dal file `requirements.txt`)

## Avvio

Apri PowerShell nella cartella del progetto ed esegui:

```powershell
python -m pip install -r requirements.txt
python game.py
```

Per installare le dipendenze in un ambiente isolato:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python game.py
```

## Comandi

- `WASD` oppure frecce direzionali: movimento
- `Invio` / `Spazio`: inizia o ricomincia
- Dopo la morte: scrivi 3 caratteri e premi `Invio` per il record arcade
- `Esc`: chiude il gioco

## Note

- La freccia `CAMPARI` indica il prossimo bicchiere.
- Le inseguitrici arrivano sia con i bicchieri sia con il passare del tempo.
- Musica, suoni, grafica e mappa sono generati direttamente dal codice: non servono file esterni.
- I record sono salvati localmente in `fuga_nocciolina_records.json`, creato automaticamente e non incluso nel repository.
