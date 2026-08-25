# Progetto Advanced Programming Languages (APL)

Questo progetto implementa una piattaforma in tre livelli (Frontend Python, Middleware Go, Backend C++) per la visualizzazione step-by-step e l'analisi di performance di algoritmi di ordinamento e ricerca.

## Requisiti di Sistema

- **Python 3.13+** (con `PyQt6` e `matplotlib` e `requests`)
- **Go 1.21+**
- **C++20 Compiler** (es. GCC/MinGW-w64 o MSVC)
- **CMake 3.16+**

---

## Istruzioni per l'Avvio (Primo Setup)

Per far funzionare l'intero stack, i 3 componenti devono essere avviati e connessi correttamente.

### 1. Compilare il Backend (C++)

Se non lo hai già fatto, devi prima compilare l'eseguibile C++.
> **Nota su Windows (MinGW)**: Se il percorso del tuo progetto contiene caratteri speciali (come la "à" di Università), CMake potrebbe fallire la compilazione. In tal caso, si consiglia di copiare la cartella `backend` in un percorso semplice come `C:\APL_Project\backend` e compilarlo lì.

```bash
cd backend
# Genera i file di build
cmake -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
# Compila il progetto
cmake --build build
```
L'eseguibile sarà generato in `backend/build/backend.exe`.

### 2. Avviare il Middleware (Go)

Il middleware farà da ponte tra il frontend e il backend. Devi fornirgli il percorso esatto dell'eseguibile C++ appena compilato.

Apri un terminale (lascialo aperto in background):
```bash
cd middleware
# Esegui il server Go indicando dove si trova l'eseguibile C++
go run main.go -backend "..\backend\build\backend.exe"
```
*(Se hai compilato il backend in `C:\APL_Project`, usa `-backend "C:\APL_Project\backend\build\backend.exe"`)*

Il server si avvierà in ascolto sulla porta `8080`.

### 3. Avviare il Frontend GUI (Python)

Infine, con il middleware Go in esecuzione, puoi avviare l'interfaccia utente.

Apri un nuovo terminale (separato da quello di Go):
```bash
cd frontend
# Installa le dipendenze se non l'hai già fatto
pip install PyQt6 matplotlib requests
# Avvia la GUI
python main.py
```

Si aprirà la finestra PyQt6 dell'applicazione.

---

## Utilizzo dell'Applicazione

L'interfaccia ha due tab principali:

1. **Visualizzatore**:
   - Scegli un algoritmo dal menu a tendina.
   - Scegli la grandezza $N$ o inserisci manualmente un array diviso da virgole.
   - Clicca "Avvia Visualizzazione".
   - Usa i tasti Play/Pausa e lo slider della velocità per vedere l'avanzamento dell'algoritmo nel grafico a barre animato.
   - In basso, osserva come lo **Stack** (chiamate di funzione) e l'**Heap** (allocazioni di memoria) si comportano in tempo reale (particolarmente evidente in algoritmi ricorsivi come MergeSort o QuickSort).

2. **Benchmark**:
   - Vai nel secondo tab per lanciare misurazioni di performance.
   - Scegli un algoritmo e quanti "Run" effettuare (default: 30).
   - Il middleware avvierà i run garantendo isolamento in sequenza (per evitare fluttuazioni da scheduling del S.O.).
   - Al termine, potrai osservare un **Boxplot** delle performance e una tabella dettagliata con i valori dei quartili, della media e della mediana.
