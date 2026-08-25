"""
Finestra principale dell'applicazione APL.
Usa QMainWindow con un QTabWidget per le tre sezioni.
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMenuBar, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from api.client import APIClient
from ui.algo_panel import AlgoPanel
from ui.visualizer import Visualizer
from ui.memory_view import MemoryView
from ui.benchmark_view import BenchmarkView


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("APL — Visualizzatore di Algoritmi")
        self.setMinimumSize(1200, 750)

        # Client per la comunicazione con il middleware Go
        self.client = APIClient()

        self._build_menu()
        self._build_tabs()
        self._build_status_bar()

        # Controlla subito se il middleware è attivo
        self._check_middleware()

    # ------------------------------------------------------------------
    # Setup UI
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        # Menu File
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Esci", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Menu Info
        help_menu = menu_bar.addMenu("Info")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Visualizzatore step-by-step
        self.viz_tab = QWidget()
        viz_layout   = QVBoxLayout(self.viz_tab)

        self.algo_panel  = AlgoPanel(self.client)
        self.visualizer  = Visualizer()
        self.memory_view = MemoryView()

        viz_layout.addWidget(self.algo_panel,  stretch=0)
        viz_layout.addWidget(self.visualizer,  stretch=3)
        viz_layout.addWidget(self.memory_view, stretch=1)

        self.tabs.addTab(self.viz_tab, "🔍 Visualizzatore")

        # Tab 2: Benchmark
        self.bench_tab  = BenchmarkView(self.client)
        self.tabs.addTab(self.bench_tab, "📊 Benchmark")

        # Collega i segnali
        self.algo_panel.result_ready.connect(self.visualizer.load_steps)
        self.algo_panel.result_ready.connect(
            lambda result, algo, data: self.memory_view.update_step(result.steps[0] if result.steps else None)
        )
        self.visualizer.step_changed.connect(self.memory_view.update_step)
        self.algo_panel.status_message.connect(self.statusBar().showMessage)

    def _build_status_bar(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Pronto. Assicurarsi che il middleware Go sia avviato.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_middleware(self) -> None:
        """Controlla se il middleware è raggiungibile e mostra un avviso se no."""
        if not self.client.health_check():
            self.status.showMessage(
                "⚠️  Middleware non raggiungibile su http://localhost:8080 — "
                "avviare middleware.exe prima di usare l'applicazione."
            )

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "About APL",
            "Visualizzatore di Algoritmi — APL Project\n\n"
            "Frontend: Python + PyQt6 + Matplotlib\n"
            "Middleware: Go (net/http, goroutine, channels)\n"
            "Backend: C++ (STL, chrono, RAII)\n\n"
            "Autori: Pappalardo, Varsallona",
        )
