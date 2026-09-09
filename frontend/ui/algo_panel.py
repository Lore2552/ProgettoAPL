"""
Pannello di controllo per la selezione dell'algoritmo e dei parametri.
Usa signal/slot Qt per comunicare con Visualizer e BenchmarkView.
"""
from __future__ import annotations
import random

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QLineEdit,
    QGroupBox, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot

from api.client import APIClient
from models.types import AlgoResult, AlgorithmInfo


class _WorkerThread(QThread):
    """Thread separato per la chiamata HTTP per evitare di bloccare la UI."""
    finished = pyqtSignal(object)  # AlgoResult
    error    = pyqtSignal(str)

    def __init__(self, client: APIClient, algo: str,
                 data: list[int], target: int) -> None:
        super().__init__()
        self.client = client
        self.algo   = algo
        self.data   = data
        self.target = target

    def run(self) -> None:
        try:
            result = self.client.run_algorithm(self.algo, self.data, self.target)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AlgoPanel(QWidget):
    """
    Pannello superiore per la configurazione e l'avvio dell'algoritmo.

    Segnali emessi:
      result_ready(AlgoResult) — quando la risposta del middleware è pronta
      status_message(str)      — messaggi di stato per la status bar
    """
    result_ready   = pyqtSignal(object, str, list)   # AlgoResult, algo, data
    status_message = pyqtSignal(str)

    def __init__(self, client: APIClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.client   = client
        self.algos: list[AlgorithmInfo] = []
        self._worker: _WorkerThread | None = None
        self._last_algo = ""
        self._last_data = []

        self._build_ui()
        self._load_algorithms()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # --- Gruppo selezione algoritmo ---
        algo_group = QGroupBox("Algoritmo")
        algo_layout = QVBoxLayout(algo_group)

        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(180)
        algo_layout.addWidget(self.algo_combo)

        main_layout.addWidget(algo_group)

        # --- Gruppo dati ---
        data_group  = QGroupBox("Dati")
        data_layout = QVBoxLayout(data_group)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Dimensione N:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(3, 200)
        self.size_spin.setValue(10)
        size_row.addWidget(self.size_spin)
        data_layout.addLayout(size_row)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Array (opzionale):"))
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("es. 5,3,8,1,2  (lascia vuoto per generare casualmente)")
        input_row.addWidget(self.data_input)
        data_layout.addLayout(input_row)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target (search):"))
        self.target_spin = QSpinBox()
        self.target_spin.setRange(-9999, 9999)
        self.target_spin.setValue(0)
        target_row.addWidget(self.target_spin)
        data_layout.addLayout(target_row)

        main_layout.addWidget(data_group, stretch=2)

        # --- Pulsanti ---
        btn_group  = QGroupBox("Azioni")
        btn_layout = QVBoxLayout(btn_group)

        self.run_btn = QPushButton("▶  Avvia Visualizzazione")
        self.run_btn.setFixedHeight(40)
        self.run_btn.clicked.connect(self._on_run_clicked)
        btn_layout.addWidget(self.run_btn)

        self.rand_btn = QPushButton("🔀  Genera Array Casuale")
        self.rand_btn.clicked.connect(self._on_generate_random)
        btn_layout.addWidget(self.rand_btn)

        main_layout.addWidget(btn_group)

    # ------------------------------------------------------------------
    # Logica
    # ------------------------------------------------------------------

    def _load_algorithms(self) -> None:
        """Carica la lista degli algoritmi dal middleware."""
        try:
            self.algos = self.client.list_algorithms()
            for info in self.algos:
                self.algo_combo.addItem(f"{info.name}  [{info.time_complexity}]", userData=info.id)
        except Exception:
            # Se il middleware non è attivo, popola con una lista statica di algoritmi
            static = [
                ("bubble_sort",    "Bubble Sort    [O(n²)]"),
                ("insertion_sort", "Insertion Sort [O(n²)]"),
                ("selection_sort", "Selection Sort [O(n²)]"),
                ("merge_sort",     "Merge Sort     [O(n log n)]"),
                ("quick_sort",     "Quick Sort     [O(n log n)]"),
                ("linear_search",  "Linear Search  [O(n)]"),
                ("binary_search",  "Binary Search  [O(log n)]"),
            ]
            for algo_id, label in static:
                self.algo_combo.addItem(label, userData=algo_id)

    def _get_data(self) -> list[int]:
        """Legge i dati dall'input, oppure genera un array casuale."""
        algo = self.algo_combo.currentData()
        n = self.size_spin.value()
        
        if algo == "dijkstra":
            # Genera sempre matrice di adiacenza N x N, ignorando l'input testuale
            adj = []
            for i in range(n):
                for j in range(n):
                    if i == j:
                        adj.append(0)
                    elif random.random() < 0.3: # 30% prob di arco
                        adj.append(random.randint(1, 20))
                    else:
                        adj.append(0) # 0 significa no arco
            return adj

        raw = self.data_input.text().strip()
        if raw:
            try:
                return [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                pass
        
        return [random.randint(1, n * 5) for _ in range(n)]

    @pyqtSlot()
    def _on_generate_random(self) -> None:
        n    = self.size_spin.value()
        data = [random.randint(1, n * 5) for _ in range(n)]
        self.data_input.setText(",".join(map(str, data)))

    @pyqtSlot()
    def _on_run_clicked(self) -> None:
        algo   = self.algo_combo.currentData()
        data   = self._get_data()
        target = self.target_spin.value()

        if not algo:
            self.status_message.emit("Seleziona un algoritmo prima di avviare.")
            return

        # Disabilita il bottone durante l'esecuzione
        self.run_btn.setEnabled(False)
        self.status_message.emit(f"Esecuzione di {algo} su {len(data)} elementi...")

        self._last_algo = algo
        self._last_data = data

        # Esegui in un thread separato per non bloccare la UI
        self._worker = _WorkerThread(self.client, algo, data, target)
        self._worker.finished.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    @pyqtSlot(object)
    def _on_result(self, result: AlgoResult) -> None:
        self.run_btn.setEnabled(True)
        total = len(result.steps)
        self.status_message.emit(
            f"Completato: {total} step, "
            f"{result.steps[-1].comparisons if result.steps else 0} confronti, "
            f"{result.steps[-1].swaps if result.steps else 0} swap  |  "
            f"Complessità: {result.complexity.time}"
        )
        self.result_ready.emit(result, self._last_algo, self._last_data)

    @pyqtSlot(str)
    def _on_error(self, msg: str) -> None:
        self.run_btn.setEnabled(True)
        self.status_message.emit(f"❌ Errore: {msg}")
