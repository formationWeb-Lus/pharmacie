MODERN_STYLE = """
QMainWindow {
    background-color: #F8FAFC;
}

#sidebar {
    background-color: #0F172A;
    border: none;
}

#brand {
    color: #FFFFFF;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 10px 10px 15px;
}

#navButton {
    color: #94A3B8;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    margin: 2px 10px;
}

#navButton:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

#navButton:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: bold;
}

QLabel#pageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #0F172A;
    margin-bottom: 10px;
}

QFrame.card {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    padding: 8px 12px;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    background-color: #FFFFFF;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 2px solid #2563EB;
}

QPushButton {
    padding: 9px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QPushButton.btn-primary {
    background-color: #2563EB;
    color: white;
}
QPushButton.btn-primary:hover {
    background-color: #1D4ED8;
}

QPushButton.btn-success {
    background-color: #16A34A;
    color: white;
}
QPushButton.btn-success:hover {
    background-color: #15803D;
}

QPushButton.btn-danger {
    background-color: #DC2626;
    color: white;
}
QPushButton.btn-danger:hover {
    background-color: #B91C1C;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
}
"""