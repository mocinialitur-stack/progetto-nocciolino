# Fuga della Nocciolina

Un gioco arcade 2D in Python ambientato a Montefiascone: guida una nocciolina cartoon, raccogli i bicchieri di Campari & Prosecco e sfuggi alle inseguitrici.

## Avvio

Apri PowerShell in questa cartella ed esegui:

```powershell
& 'C:\Users\Luca\AppData\Local\Programs\Python\Python313\python.exe' .\game.py
```

In un nuovo terminale, dopo l'aggiornamento del PATH, dovrebbe funzionare anche:

```powershell
python .\game.py
```

## Comandi

- `WASD` oppure frecce direzionali: movimento
- `Invio` / `Spazio`: inizia o ricomincia
- Dopo la morte: scrivi 3 caratteri e premi `Invio` per salvare il record
- `Esc`: chiude il gioco

Ogni bicchiere raccolto vale un punto, allunga la protuberanza della nocciolina, riduce leggermente accelerazione e velocita, e fa arrivare una nuova inseguitrice. Le inseguitrici non aumentano piu con il passare del tempo.

Ogni tanto appare Michele in bicicletta: raccoglilo per diventare immune alle inseguitrici per 10 secondi. I record arcade vengono salvati in `fuga_nocciolina_records.json` accanto al gioco.
