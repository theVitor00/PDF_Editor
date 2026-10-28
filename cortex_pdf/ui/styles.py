"""
Folha de estilos QSS moderna, clean e clara (Light & Clean Theme) para o Cortex PDF Editor.
"""

MODERN_STYLESHEET = """
QMainWindow, QWidget#MainCentralWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* Barra lateral de navegação (Clean White) */
QFrame#SidebarFrame {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

QLabel#BrandTitle {
    color: #0f172a;
    font-size: 18px;
    font-weight: 700;
    padding: 2px 0px;
}

QLabel#BrandSubtitle {
    color: #64748b;
    font-size: 11px;
    padding-bottom: 12px;
}

QPushButton.NavButton {
    background-color: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.NavButton:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton.NavButton[active="true"] {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
}

/* Cards de Etapa (Entrada -> Processamento -> Saída) */
QFrame.StepCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

QFrame#PipelineBanner {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
}

QLabel.StepTitle {
    color: #0f172a;
    font-size: 14px;
    font-weight: 700;
}

QLabel.StepSubtitle {
    color: #64748b;
    font-size: 12px;
}

QLabel.PageHeaderTitle {
    color: #0f172a;
    font-size: 20px;
    font-weight: 700;
}

QLabel.PageHeaderDesc {
    color: #475569;
    font-size: 13px;
}

/* Inputs e Campos Claros */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

QListWidget, QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
    color: #1e293b;
}

QListWidget::item:hover {
    background-color: #f1f5f9;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Botões Primários e Secundários */
QPushButton.PrimaryButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton.PrimaryButton:hover {
    background-color: #1d4ed8;
}

QPushButton.PrimaryButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton.SecondaryButton {
    background-color: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton.SecondaryButton:hover {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #94a3b8;
}

QPushButton.SecondaryButton:disabled {
    background-color: #f8fafc;
    color: #cbd5e1;
    border: 1px solid #e2e8f0;
}

QRadioButton, QCheckBox {
    color: #1e293b;
    spacing: 8px;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
}
"""
