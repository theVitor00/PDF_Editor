"""
Folha de estilos QSS moderna (Dark Slate & Indigo) para o Cortex PDF Editor.
"""

MODERN_STYLESHEET = """
QMainWindow, QWidget#MainCentralWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* Barra lateral de navegação */
QFrame#SidebarFrame {
    background-color: #1e293b;
    border-right: 1px solid #334155;
}

QLabel#BrandTitle {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
    padding: 4px 0px;
}

QLabel#BrandSubtitle {
    color: #94a3b8;
    font-size: 11px;
    padding-bottom: 12px;
}

QPushButton.NavButton {
    background-color: transparent;
    color: #cbd5e1;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.NavButton:hover {
    background-color: #334155;
    color: #ffffff;
}

QPushButton.NavButton[active="true"] {
    background-color: #4f46e5;
    color: #ffffff;
}

/* Cards de Etapa (Entrada -> Processamento -> Saída) */
QFrame.StepCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
}

QFrame#PipelineBanner {
    background-color: #172033;
    border: 1px solid #2dd4bf;
    border-radius: 8px;
}

QLabel.StepTitle {
    color: #e2e8f0;
    font-size: 14px;
    font-weight: 700;
}

QLabel.StepSubtitle {
    color: #94a3b8;
    font-size: 12px;
}

QLabel.PageHeaderTitle {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 700;
}

QLabel.PageHeaderDesc {
    color: #94a3b8;
    font-size: 13px;
}

/* Inputs e Campos */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: #4f46e5;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #6366f1;
}

QLineEdit:disabled {
    background-color: #1e293b;
    color: #64748b;
    border: 1px solid #334155;
}

QListWidget, QTableWidget {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #4f46e5;
    color: #ffffff;
}

/* Botões Primários e Secundários */
QPushButton.PrimaryButton {
    background-color: #4f46e5;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton.PrimaryButton:hover {
    background-color: #4338ca;
}

QPushButton.PrimaryButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton.SecondaryButton {
    background-color: #334155;
    color: #f1f5f9;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton.SecondaryButton:hover {
    background-color: #475569;
}

QPushButton.SuccessButton {
    background-color: #0d9488;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 700;
}

QPushButton.SuccessButton:hover {
    background-color: #0f766e;
}

QRadioButton, QCheckBox {
    color: #e2e8f0;
    spacing: 8px;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QStatusBar {
    background-color: #1e293b;
    color: #94a3b8;
    border-top: 1px solid #334155;
}
"""
