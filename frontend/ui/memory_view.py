"""
Pannello per la visualizzazione dello stato della memoria (Stack e Heap).
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor, QFont

from models.types import StepEvent


class MemoryView(QWidget):
    """
    Visualizza lo stack delle chiamate (con variabili locali) e le allocazioni heap
    dinamiche in base allo snapshot di memoria dello step corrente.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(200) # Altezza fissa in basso
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Stack View ---
        stack_group = QGroupBox("Memoria Stack (Chiamate e Variabili Locali)")
        stack_layout = QVBoxLayout(stack_group)
        self.stack_list = QListWidget()
        self.stack_list.setFont(QFont("Consolas", 10))
        self.stack_list.setWordWrap(True)
        stack_layout.addWidget(self.stack_list)
        main_layout.addWidget(stack_group, stretch=2)

        # --- Heap View ---
        heap_group = QGroupBox("Memoria Heap (Allocazioni Dinamiche)")
        heap_layout = QVBoxLayout(heap_group)
        self.heap_list = QListWidget()
        self.heap_list.setFont(QFont("Consolas", 10))
        self.heap_list.setWordWrap(True)
        heap_layout.addWidget(self.heap_list)
        main_layout.addWidget(heap_group, stretch=1)

    @pyqtSlot(object)
    def update_step(self, ev: StepEvent | None) -> None:
        """Aggiorna le view leggendo lo snapshot della memoria dal StepEvent."""
        self.stack_list.clear()
        self.heap_list.clear()

        if not ev or not ev.memory:
            return

        # Popola Stack 
        for i, frame in enumerate(reversed(ev.memory.stack)):
            vars_str = ", ".join(f"{k}={v}" for k, v in frame.vars.items())
            text = f"[{frame.name}]  {vars_str}"
            item = QListWidgetItem(text)
            
            # Evidenzia il top dello stack (il frame corrente attivo)
            if i == 0:
                item.setBackground(QColor("#e8f4f8")) # Azzurrino chiaro
                item.setForeground(QColor("black"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                
            self.stack_list.addItem(item)

        if not ev.memory.stack:
            self.stack_list.addItem(QListWidgetItem("Stack vuoto"))

        # Popola Heap
        for block in ev.memory.heap:
            text = f"Alloc: '{block.label}' ({block.size} elementi)"
            if block.content:
                text += f" -> {block.content}"
            item = QListWidgetItem(text)
            item.setBackground(QColor("#fcf5e3")) # Giallo chiaro
            item.setForeground(QColor("black"))
            self.heap_list.addItem(item)

        if not ev.memory.heap:
            self.heap_list.addItem(QListWidgetItem("Nessuna allocazione dinamica attiva"))
