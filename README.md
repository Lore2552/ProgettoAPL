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

Per prima cosa bisogna compilare l'eseguibile C++.

```bash
cd backend
cmake -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build
```
L'eseguibile sarà generato in `backend/build/backend.exe`.

### 2. Avviare il Middleware (Go)

Il middleware farà da ponte tra il frontend e il backend. Bisogna fornirgli il percorso esatto dell'eseguibile C++ appena compilato.

Da un terminale aperto in backgruond:

```bash
cd middleware
go run main.go -backend "..\backend\build\backend.exe"
```

Il server si avvierà in ascolto sulla porta `8080`.

### 3. Avviare il Frontend GUI (Python)

Infine, con il middleware Go in esecuzione, bisogna avviare l'interfaccia utente.

Da un nuovo terminale (separato da quello di Go):
```bash
cd frontend
pip install PyQt6 matplotlib requests
python main.py
```

Si aprirà la finestra dell'applicazione.

---

## Utilizzo dell'Applicazione

L'interfaccia ha due tab principali:

1. **Visualizzatore**:
   - Permette di scegliere un algoritmo dal menu a tendina.
   - Permette di scegliere la grandezza $N$ e generare un array casuale all'avvio (in questo caso l'array generato sarà visualizzabile solo dopo l'avvio), oppure di inserire manualmente un array diviso da virgole, oppure di generare un array casuale e visualizzarlo prima dell'avvio (utile nei casi di algoritmi di ricerca, in cui bisogna specificare l'elemento target da ricercare prima dell'avvio).
   - Una volta settati questi campi si può procedere con cliccare "Avvia Visualizzazione".
   - Si possono usarre i tasti Play/Pausa e lo slider della velocità per vedere l'avanzamento dell'algoritmo nel grafico.
   - In basso invece si può osservare come lo **Stack** e l'**Heap** si comportano in tempo reale (particolarmente interessante negli algoritmi ricorsivi come MergeSort o QuickSort).

2. **Benchmark**:
   - Andando nel secondo tab si possono lanciare misurazioni di performance.
   - Si può scegliere un algoritmo e quanti "Run" effettuare (default: 30). 
   - Inoltre è possibile scegliere la distribuzione dell'array iniziale e la struttura da analizzare (array stack o heap).
   - Il middleware avvierà i run garantendo isolamento in sequenza.
   - Al termine, si potrà osservare un **Boxplot** delle performance e una tabella dettagliata con i valori dei quartili, della media e della mediana.
