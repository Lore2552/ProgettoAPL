"""
Visualizzatore step-by-step dell'algoritmo usando Matplotlib incorporato in PyQt6.
Mostra l'array come un bar chart animato, con colori per evidenziare i confronti.
"""
from __future__ import annotations
import matplotlib
matplotlib.use('QtAgg')

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from models.types import StepEvent


class Visualizer(QWidget):
    """
    Componente UI per visualizzare l'esecuzione di un algoritmo passo dopo passo.

    Segnali:
        step_changed(StepEvent): emesso ogni volta che viene visualizzato un nuovo step,
                                 utile per aggiornare altri pannelli (es. MemoryView).
    """
    step_changed = pyqtSignal(object)  # StepEvent

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._steps: list[StepEvent] = []
        self._current_idx: int = 0
        self._is_playing: bool = False

        self._build_ui()
        self._init_plot()

        # Timer per l'animazione automatica
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # Matplotlib Canvas
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, stretch=1)

        # Pannello info e controlli
        ctrl_layout = QHBoxLayout()

        self.info_label = QLabel("Nessun dato. Seleziona un algoritmo e avvia.")
        self.info_label.setMinimumWidth(250)
        ctrl_layout.addWidget(self.info_label)

        ctrl_layout.addStretch()

        self.prev_btn = QPushButton("⏮ Precedente")
        self.prev_btn.clicked.connect(self.prev_step)
        ctrl_layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        ctrl_layout.addWidget(self.play_btn)

        self.next_btn = QPushButton("⏭ Successivo")
        self.next_btn.clicked.connect(self.next_step)
        ctrl_layout.addWidget(self.next_btn)

        ctrl_layout.addStretch()

        ctrl_layout.addWidget(QLabel("Velocità:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 1000)  # ms per step
        self.speed_slider.setValue(200)
        self.speed_slider.setInvertedAppearance(True) # Invertito: slider a dx = più veloce (meno ms)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        ctrl_layout.addWidget(self.speed_slider)

        main_layout.addLayout(ctrl_layout)

        self._update_buttons()

    def _init_plot(self) -> None:
        self.ax = self.figure.add_subplot(111)
        self.ax.set_axis_off()  # Rimuove assi e griglia all'inizio
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Logica di Animazione
    # ------------------------------------------------------------------

    @pyqtSlot(object, str, list)
    def load_steps(self, result: object, algo: str, data: list[int]) -> None:
        """Carica una nuova lista di step e resetta la visualizzazione."""
        from models.types import AlgoResult # import locale per type hint
        if not hasattr(result, "steps"):
            return
            
        res: AlgoResult = result
        self._steps = res.steps
        self._algo = algo
        self._data = data
        
        # Se l'algoritmo è dijkstra, precalcoliamo le coordinate del grafo
        if self._algo == "dijkstra":
            import networkx as nx
            import math
            n = int(math.sqrt(len(data)))
            self._nx_graph = nx.DiGraph()
            for i in range(n):
                self._nx_graph.add_node(i)
            for i in range(n):
                for j in range(n):
                    w = data[i * n + j]
                    if w > 0:
                        self._nx_graph.add_edge(i, j, weight=w)
            # Layout fisso (ad es. spring_layout con seed fisso per stabilità)
            self._pos = nx.spring_layout(self._nx_graph, seed=42)
            
        self._current_idx = 0
        self._is_playing = False
        self._timer.stop()
        self.play_btn.setText("▶ Play")
        self._update_ui_for_step()

    def _draw_step(self, ev: StepEvent) -> None:
        """Disegna il bar chart o il grafo per uno specifico StepEvent."""
        self.ax.clear()
        if not ev.array:
            self.ax.set_axis_off()
            self.canvas.draw()
            return

        self.ax.set_axis_on()
        
        if getattr(self, "_algo", "") == "dijkstra":
            import networkx as nx
            self.ax.set_axis_off()
            
            # Array ev.array contiene le distanze attuali
            # highlight: [u, v] (l'arco in valutazione) o [u] (nodo analizzato)
            
            # Colori dei nodi:
            # - verde se visitato (distanza < INF e non più in highlight se elaborato, o semplicemente non INF)
            # - rosso se in highlight (nodo u)
            # - azzurro per gli altri
            node_colors = []
            for i in range(len(self._nx_graph.nodes)):
                if i in ev.highlight:
                    node_colors.append("crimson")
                elif ev.array[i] < 99999999: # INF
                    node_colors.append("mediumseagreen")
                else:
                    node_colors.append("lightblue")
                    
            # Colori degli archi
            edge_colors = []
            edge_widths = []
            for u, v in self._nx_graph.edges():
                if len(ev.highlight) == 2 and (u == ev.highlight[0] and v == ev.highlight[1]):
                    edge_colors.append("crimson")
                    edge_widths.append(2.5)
                else:
                    edge_colors.append("gray")
                    edge_widths.append(1.0)
                    
            # Etichette nodi (mostriamo l'ID e la distanza se < INF)
            labels = {}
            for i in range(len(self._nx_graph.nodes)):
                dist = str(ev.array[i]) if ev.array[i] < 99999999 else "∞"
                labels[i] = f"{i}\n(d:{dist})"
                
            nx.draw(
                self._nx_graph,
                self._pos,
                ax=self.ax,
                labels=labels,
                node_color=node_colors,
                edge_color=edge_colors,
                width=edge_widths,
                node_size=1200,
                font_size=9,
                font_color="black",
                font_weight="bold",
                arrows=True,
                arrowsize=15
            )
            
            # Disegna i pesi sugli archi
            edge_labels = nx.get_edge_attributes(self._nx_graph, 'weight')
            nx.draw_networkx_edge_labels(self._nx_graph, self._pos, edge_labels=edge_labels, ax=self.ax, font_size=8)
            
        else:
            x = range(len(ev.array))
            
            # Colori: default blu scuro (steelblue), highlight rosso (crimson)
            colors = ['steelblue' if i not in ev.highlight else 'crimson' for i in x]
            
            bars = self.ax.bar(x, ev.array, color=colors, edgecolor='white')

            # Rimuove i bordi del grafico per un look più moderno
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_visible(False)
            self.ax.get_yaxis().set_visible(False) # Nasconde asse Y, i valori li mostriamo sulle barre

            # Aggiunge etichette con il valore sopra le barre se l'array è piccolo
            if len(ev.array) <= 50:
                for bar in bars:
                    height = bar.get_height()
                    self.ax.annotate(f'{height}',
                                     xy=(bar.get_x() + bar.get_width() / 2, height),
                                     xytext=(0, 3),  # 3 points vertical offset
                                     textcoords="offset points",
                                     ha='center', va='bottom', fontsize=8)

        self.figure.tight_layout()
        self.canvas.draw()

    def _update_ui_for_step(self) -> None:
        """Aggiorna tutto (grafico, testo, bottoni) in base allo step corrente."""
        if not self._steps:
            self.info_label.setText("Nessun dato.")
            self.ax.clear()
            self.ax.set_axis_off()
            self.canvas.draw()
            self._update_buttons()
            return

        ev = self._steps[self._current_idx]
        total = len(self._steps)
        
        self.info_label.setText(
            f"Step: {self._current_idx + 1} / {total}\n"
            f"Confronti: {ev.comparisons} | Swap: {ev.swaps}"
        )
        
        self._draw_step(ev)
        self._update_buttons()
        
        # Emette il segnale per notificare altri componenti (es. MemoryView)
        self.step_changed.emit(ev)

    def _update_buttons(self) -> None:
        has_steps = len(self._steps) > 0
        is_first = self._current_idx == 0
        is_last = self._current_idx == len(self._steps) - 1

        self.prev_btn.setEnabled(has_steps and not is_first)
        self.next_btn.setEnabled(has_steps and not is_last)
        self.play_btn.setEnabled(has_steps)

    # ------------------------------------------------------------------
    # Azioni Utente
    # ------------------------------------------------------------------

    @pyqtSlot()
    def prev_step(self) -> None:
        if self._current_idx > 0:
            self._current_idx -= 1
            self._update_ui_for_step()

    @pyqtSlot()
    def next_step(self) -> None:
        if self._current_idx < len(self._steps) - 1:
            self._current_idx += 1
            self._update_ui_for_step()

    @pyqtSlot()
    def toggle_play(self) -> None:
        if not self._steps:
            return

        if not self._is_playing:
            # Se siamo alla fine e premiamo play, ricomincia
            if self._current_idx == len(self._steps) - 1:
                self._current_idx = 0
                self._update_ui_for_step()
                
            self._is_playing = True
            self.play_btn.setText("⏸ Pausa")
            delay_ms = self.speed_slider.value()
            self._timer.start(delay_ms)
        else:
            self._is_playing = False
            self.play_btn.setText("▶ Play")
            self._timer.stop()

    @pyqtSlot(int)
    def _on_speed_changed(self, value: int) -> None:
        if self._is_playing:
            self._timer.setInterval(value)

    @pyqtSlot()
    def _on_timer_tick(self) -> None:
        if self._current_idx < len(self._steps) - 1:
            self._current_idx += 1
            self._update_ui_for_step()
            
            # Se abbiamo appena raggiunto l'ultimo step, fermiamo l'animazione senza resettare
            if self._current_idx == len(self._steps) - 1:
                self._is_playing = False
                self.play_btn.setText("▶ Play")
                self._timer.stop()
