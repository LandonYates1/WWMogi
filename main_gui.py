import os
import sys
import json
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QIcon, QFont, QColor, QBrush
from PyQt6.QtCore import Qt, QTimer

COLUMN_ALIASES = {
    "name": "Name",
    "wins": "Wins",
    "losses": "Losses",
    "playedMatchCount": "Matches Played",
    "rating": "Rating"
}

def get_asset_path(filename):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Default to the directory of main_gui.py
        base_path = os.path.dirname(os.path.abspath(__file__))

    # First check the 'resources' subfolder (standard for your setup)
    resource_path = os.path.join(base_path, 'resources', filename)

    if os.path.exists(resource_path):
        return resource_path

    # Fallback to base_path if not in resources
    return os.path.join(base_path, filename)

DATA_FILE = "player_data.json"
CACHE_FILE = "leaderboard_cache.json"
QSS_FILE = get_asset_path("leaderboard_style.qss")
ICON_PATH = get_asset_path("WWMOGIlogo.png")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WWMOGI")
        self.setGeometry(500, 200, 650, 800)

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.table_widget = None
        self.status_label = None

        self.initUI()

        # --- AUTO-REFRESH TIMER ---
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)

        if os.path.exists(CACHE_FILE):
            self.load_data_into_table(CACHE_FILE)

        self.refresh_data() # Trigger first update immediately
        # Set to 900,000ms (15 minutes) as per your current file
        self.refresh_timer.start(900000)

    def initUI(self):
        label = QLabel("Leaderboard")
        label.setFont(QFont("Roboto", 30))
        label.setStyleSheet("color: #8c93a5;")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(label)

        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.status_label)

        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(400)

        table_container = QWidget()
        table_container.setLayout(QVBoxLayout())
        table_container.layout().addWidget(self.table_widget)
        table_container.layout().setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(table_container)
        self.layout.setStretch(2, 1)

    def refresh_data(self):
        """Runs the external data_fetcher.py script by importing it."""
        self.status_label.setText("Refreshing leaderboard...")

        try:
            # Import and run the main function directly
            import data_fetcher
            data_fetcher.main()

            if os.path.exists(DATA_FILE):
                self.load_data_into_table(DATA_FILE)
                shutil.copyfile(DATA_FILE, CACHE_FILE)
                self.status_label.setText("Last Updated: Just now")
            else:
                self.status_label.setText("Update failed: Data file not found.")

        except Exception as e:
            self.status_label.setText(f"Error: {e}")

        finally:
            # Clean up the temporary data file if it exists
            if os.path.exists(DATA_FILE):
                try:
                    os.remove(DATA_FILE)
                except:
                    pass

    def load_data_into_table(self, file_path):
        """Reads JSON and populates the table."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except:
            return

        if not data: return

        json_keys = list(data[0].keys())
        display_headers = [COLUMN_ALIASES.get(key, key) for key in json_keys]

        self.table_widget.setColumnCount(len(json_keys))
        self.table_widget.setRowCount(len(data))
        self.table_widget.setHorizontalHeaderLabels(display_headers)
        self.table_widget.setAlternatingRowColors(True)

        for row_index, record in enumerate(data):
            special_color = None
            if row_index == 0: special_color = QColor(255, 215, 0, 150)
            elif row_index == 1: special_color = QColor(192, 192, 192, 150)
            elif row_index == 2: special_color = QColor(205, 127, 50, 150)

            for col_index, key in enumerate(json_keys):
                value = str(record.get(key, ""))
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if special_color:
                    item.setBackground(QBrush(special_color))
                self.table_widget.setItem(row_index, col_index, item)

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.show()

def main():
    app = QApplication(sys.argv)
    if os.path.exists(QSS_FILE):
        with open(QSS_FILE, 'r') as f:
            app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    # Standard requirement for PyInstaller apps with multiple processes
    import multiprocessing
    multiprocessing.freeze_support()
    main()
