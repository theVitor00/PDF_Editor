"""
Ponto de entrada principal da aplicação Cortex PDF Editor.
"""

import sys
from PyQt6.QtWidgets import QApplication

from cortex_pdf.ui.main_window import CortexMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Cortex PDF Editor")
    window = CortexMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

