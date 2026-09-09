"""
Vista per i risultati di Benchmark.
Usa Matplotlib per disegnare un boxplot dei tempi di esecuzione e mostra le statistiche raw in una tabella.
"""
from __future__ import annotations
import matplotlib
matplotlib.use('QtAgg')

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from api.client import APIClient
from models.types import BenchmarkResult, AlgorithmInfo


class _BenchWorker(QThread):
    """Thread per non bloccare la UI durante benchmark lunghi."""
    finished = pyqtSignal(object)  # BenchmarkResult o CurveResponse
    error    = pyqtSignal(str)

    def __init__(self, client: APIClient, algo: str, n: int, runs: int, 
                 struct: str, dist: str, is_curve: bool) -> None:
        super().__init__()
        self.client = client
        self.algo = algo
        self.n = n
        self.runs = runs
        self.struct = struct
        self.dist = dist
        self.is_curve = is_curve

    def run(self) -> None:
        try:
            if self.is_curve:
                res = self.client.get_benchmark_curve(self.algo, 1000, 20000, 1000, self.runs, self.struct, self.dist)
                self.finished.emit(res)
            else:
                res = self.client.get_benchmark(self.algo, self.n, self.runs, self.struct, self.dist)
                self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class BenchmarkView(QWidget):
    """Pannello per eseguire benchmark e visualizzare boxplot e statistiche."""

    def __init__(self, client: APIClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.client = client
        self._worker: _BenchWorker | None = None
        
        # Storico dei benchmark eseguiti per confrontarli nel boxplot
        self._results: list[BenchmarkResult] = []

        self._build_ui()
        self._load_algorithms()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # --- Pannello Controlli ---
        ctrl_group = QGroupBox("Configurazione Benchmark")
        ctrl_layout = QHBoxLayout(ctrl_group)

        ctrl_layout.addWidget(QLabel("Algoritmo:"))
        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(150)
        ctrl_layout.addWidget(self.algo_combo)

        ctrl_layout.addWidget(QLabel("N (dimensione):"))
        self.n_spin = QSpinBox()
        self.n_spin.setRange(10, 100000)
        self.n_spin.setValue(1000)
        self.n_spin.setSingleStep(500)
        ctrl_layout.addWidget(self.n_spin)

        ctrl_layout.addWidget(QLabel("Runs:"))
        self.runs_spin = QSpinBox()
        self.runs_spin.setRange(5, 100)
        self.runs_spin.setValue(30)
        ctrl_layout.addWidget(self.runs_spin)
        
        ctrl_layout.addWidget(QLabel("Struttura:"))
        self.struct_combo = QComboBox()
        self.struct_combo.addItems(["vector", "stack", "heap"])
        ctrl_layout.addWidget(self.struct_combo)
        
        ctrl_layout.addWidget(QLabel("Distribuzione:"))
        self.dist_combo = QComboBox()
        self.dist_combo.addItems(["random", "sorted", "reversed", "nearly_sorted"])
        ctrl_layout.addWidget(self.dist_combo)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Boxplot (Singolo N)", "Curva O(N)"])
        ctrl_layout.addWidget(self.mode_combo)

        self.run_btn = QPushButton("▶ Avvia Benchmark")
        self.run_btn.clicked.connect(self._on_run_clicked)
        ctrl_layout.addWidget(self.run_btn)

        self.clear_btn = QPushButton("🗑 Pulisci Grafico")
        self.clear_btn.clicked.connect(self._clear_results)
        ctrl_layout.addWidget(self.clear_btn)
        
        ctrl_layout.addStretch()
        main_layout.addWidget(ctrl_group)

        self.status_label = QLabel("Pronto.")
        main_layout.addWidget(self.status_label)

        # --- Area Risultati (Grafico + Tabella) ---
        res_layout = QHBoxLayout()

        # Grafico (Boxplot)
        plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Confronto Tempi (Boxplot)")
        self.ax.set_ylabel("Tempo (ms)")
        
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)
        res_layout.addWidget(plot_widget, stretch=2)

        # Tabella Statistiche
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Algoritmo", "N", "Media (ms)", "Mediana (ms)", "Min (Q1) (ms)", "Max (Q3) (ms)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        res_layout.addWidget(self.table, stretch=1)

        main_layout.addLayout(res_layout)

    def _load_algorithms(self) -> None:
        try:
            algos = self.client.list_algorithms()
            for info in algos:
                if "search" not in info.id and "dijkstra" not in info.id:
                    self.algo_combo.addItem(info.name, userData=info.id)
        except Exception:
            # Fallback, sempre lista statica
            static = [
                ("bubble_sort",    "Bubble Sort"),
                ("insertion_sort", "Insertion Sort"),
                ("selection_sort", "Selection Sort"),
                ("merge_sort",     "Merge Sort"),
                ("quick_sort",     "Quick Sort"),
            ]
            for algo_id, label in static:
                self.algo_combo.addItem(label, userData=algo_id)

    # ------------------------------------------------------------------
    # Logica
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_run_clicked(self) -> None:
        algo = self.algo_combo.currentData()
        n    = self.n_spin.value()
        runs = self.runs_spin.value()
        struct = self.struct_combo.currentText()
        dist = self.dist_combo.currentText()
        is_curve = self.mode_combo.currentIndex() == 1

        if not algo:
            return

        self.run_btn.setEnabled(False)
        self.status_label.setText(f"Esecuzione benchmark in corso per {algo}... attendere.")
        
        self._worker = _BenchWorker(self.client, algo, n, runs, struct, dist, is_curve)
        self._worker.finished.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    @pyqtSlot(object)
    def _on_result(self, res: object) -> None:
        from models.types import BenchmarkResult, CurveResponse
        
        self.run_btn.setEnabled(True)
        
        if isinstance(res, CurveResponse):
            self.status_label.setText("Completato benchmark curva O(N).")
            self._draw_curve(res)
        else:
            self.status_label.setText(f"Completato benchmark per {res.algorithm}.")
            self._results.append(res)
            self._update_chart()
            self._add_to_table(res)

    def _draw_curve(self, res: object) -> None:
        self.ax.clear()
        
        ns = [b.n for b in res.curve]
        means = [b.stats.mean_ns / 1_000_000.0 for b in res.curve]
        
        self.ax.plot(ns, means, marker='o', linestyle='-', color='#bf616a', linewidth=2, markersize=6)
        
        self.ax.set_title(f"Curva di Complessità: {res.curve[0].algorithm}")
        self.ax.set_xlabel("Dimensione Array (N)")
        self.ax.set_ylabel("Tempo Medio (ms)")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot(str)
    def _on_error(self, msg: str) -> None:
        self.run_btn.setEnabled(True)
        self.status_label.setText(f"❌ Errore: {msg}")

    @pyqtSlot()
    def _clear_results(self) -> None:
        self._results.clear()
        self.table.setRowCount(0)
        self.ax.clear()
        self.ax.set_title("Confronto Tempi (Boxplot)")
        self.ax.set_ylabel("Tempo (ms)")
        self.canvas.draw()
        self.status_label.setText("Risultati puliti.")

    def _update_chart(self) -> None:
        self.ax.clear()
        if not self._results:
            return

        data = [[x / 1_000_000.0 for x in r.stats.run_times_ns] for r in self._results]
        labels = [f"{r.algorithm}\nN={r.n}" for r in self._results]

        bp = self.ax.boxplot(data, tick_labels=labels, patch_artist=True)
        
        colors = ['#88c0d0', '#81a1c1', '#5e81ac', '#8fbcbb', '#a3be8c', '#ebcb8b', '#d08770', '#bf616a']
        for i, box in enumerate(bp['boxes']):
            box.set_facecolor(colors[i % len(colors)])
            box.set_edgecolor('#2e3440')
            box.set_linewidth(1.5)
            
        for median in bp['medians']:
            median.set_color('#bf616a')
            median.set_linewidth(2)
            
        for whisker in bp['whiskers']:
            whisker.set_color('#4c566a')
            whisker.set_linewidth(1.5)
            whisker.set_linestyle('--')
            
        for cap in bp['caps']:
            cap.set_color('#4c566a')
            cap.set_linewidth(1.5)
            
        for flier in bp['fliers']:
            flier.set(marker='o', markerfacecolor='#d08770', markeredgecolor='none', alpha=0.6)

        self.ax.set_title("Confronto Tempi di Esecuzione")
        self.ax.set_ylabel("Tempo (ms)")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def _add_to_table(self, res: BenchmarkResult) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(res.algorithm))
        self.table.setItem(row, 1, QTableWidgetItem(str(res.n)))
        self.table.setItem(row, 2, QTableWidgetItem(f"{res.stats.mean_ns / 1_000_000.0:,.2f}"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{res.stats.median_ns / 1_000_000.0:,.2f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{res.stats.q1_ns / 1_000_000.0:,.2f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{res.stats.q3_ns / 1_000_000.0:,.2f}"))
