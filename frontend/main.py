import sys
import argparse
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main() -> None:
    # Parsing opzionale degli argomenti da linea di comando
    parser = argparse.ArgumentParser(description="APL - Visualizzatore di Algoritmi")
    parser.add_argument("--middleware", type=str, default="http://localhost:8080",
                        help="URL del middleware Go (default: http://localhost:8080)")
    args = parser.parse_args()

    # Avvio applicazione PyQt
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Stile pulito cross-platform
    
    # Crea e mostra la finestra principale
    window = MainWindow()
    window.client.base_url = args.middleware.rstrip("/")
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
