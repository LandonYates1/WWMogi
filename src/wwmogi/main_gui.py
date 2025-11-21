# Libraries for the GUI, os calls, I/O, create new processes, read JSON and file operations
import os
import sys
import subprocess
import json
import shutil
import wwmogi
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QIcon, QFont, QColor, QBrush
from PyQt6.QtCore import Qt, QTimer

# Column name mapping (Aliases)
COLUMN_ALIASES = {
    "name": "Name",
    "wins": "Wins",
    "losses": "Losses",
    "playedMatchCount": "Matches Played",
    "points": "Points"
}

def get_asset_path(filename):
    """
    Get absolute path to resources located within the package folder.
    This works regardless of where the application is launched from.
    """
    # Get the directory containing this script (main_gui.py)
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Look for assets inside the resources subfolder next to this script
    return os.path.join(base_path, 'resources', filename)

# EXTERNAL_SCRIPT needs to be handled differently now.
# We calculate the path based on where main_gui.py is located.
base_dir = os.path.dirname(os.path.abspath(__file__))
EXTERNAL_SCRIPT_PATH = os.path.join(base_dir, "data_fetcher.py")

# These JSON files will be created in the user's current working directory
# when they run the app.
DATA_FILE = "player_data.json"
CACHE_FILE = "leaderboard_cache.json"

# Use the new function for assets
QSS_FILE = get_asset_path("leaderboard_style.qss")
ICON_PATH = get_asset_path("WWMOGIlogo.png")

# -----------------------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WWMOGI")
        self.setGeometry(500, 200, 650, 800)

        # --- FIX 1: Use the global ICON_PATH variable directly ---
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)

        self.table_widget = None
        self.status_label = None

        self.initUI()

        # Initial Data Load & Auto-Load Logic
        if os.path.exists(CACHE_FILE):
            self.status_label.setText("Loading data from cache...")
            self.load_data_into_table(CACHE_FILE)
            self.button.setText("Refresh Leaderboard")
        else:
            self.status_label.setText("First run. Fetching live data...")
            self.table_widget.hide()
            self.button.setText("Refresh Leaderboard")
            QTimer.singleShot(100, self.on_click)

    # Tells window to close when prompted
    def closeEvent(self, event):
        QApplication.quit()
        event.accept()

    # Reads JSON file and populates table (Essential Function)
    def load_data_into_table(self, file_path):
        """Reads the JSON file and populates the QTableWidget with aliases and centering."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
             self.status_label.setText(f"Error reading file: {e}")
             return

        if not data:
            self.status_label.setText("Error: Data file is empty.")
            return

        # 1. Map headers to display names
        json_keys = list(data[0].keys())
        display_headers = [COLUMN_ALIASES.get(key, key) for key in json_keys]

        self.table_widget.setColumnCount(len(json_keys))
        self.table_widget.setHorizontalHeaderLabels(display_headers)

        # Activates the alternating row colors defined in QSS
        self.table_widget.setAlternatingRowColors(True)

        self.table_widget.setRowCount(len(data))
        for row_index, record in enumerate(data):

            # Top 3 highlighting logic
            special_color = None
            if row_index == 0:
                special_color = QColor(255, 215, 0, 150)
            elif row_index == 1:
                special_color = QColor(192, 192, 192, 150)
            elif row_index == 2:
                special_color = QColor(205, 127, 50, 150)

            for col_index, key in enumerate(json_keys):
                value = str(record.get(key, ""))
                item = QTableWidgetItem(value)

                # 2. Centering the data
                # Centering the first column (Player Name or Rank)
                if col_index == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    # Keep other columns centered
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Disable editing
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Apply dynamic background color ONLY if it's a top 3 row
                if special_color:
                    item.setBackground(QBrush(special_color))

                self.table_widget.setItem(row_index, col_index, item)

        # Table Sizing (Stretch to full width)
        self.table_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table_widget.show()
        self.status_label.hide()

    def initUI(self):
        # Title label
        label = QLabel("Leaderboard")
        label.setFont(QFont("Roboto", 30))
        label.setStyleSheet("color: #8c93a5;")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(label)

        # Button
        self.button = QPushButton("Click to Load Leaderboard")
        self.button.setStyleSheet("font-size: 15px;")
        self.button.clicked.connect(self.on_click)
        self.button.setMaximumWidth(300)
        self.layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Status label creation
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.status_label)
        self.status_label.hide()

        # QTableWidget: Displays the actual data
        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(400)
        self.table_widget.hide()

        # Table container setup (ensures full horizontal stretch)
        table_container = QWidget()
        table_container.setLayout(QVBoxLayout())
        table_container.layout().addWidget(self.table_widget)
        table_container.layout().setContentsMargins(0, 0, 0, 0)

        # Allows the container to stretch to full width
        self.layout.addWidget(table_container)

        # Give the table container vertical stretch priority
        self.layout.setStretch(3, 1)

    # Function triggered when refresh button is pressed
    def on_click(self):
        self.button.setDisabled(True)
        self.status_label.show()
        self.status_label.setText("Fetching new data, please wait...")
        self.table_widget.hide()

        # 1. Deletes old, temporary file if exists
        if os.path.exists(DATA_FILE):
            try:
                os.remove(DATA_FILE)
            except Exception:
                pass

        try:
            # --- FIX 2: Use the global EXTERNAL_SCRIPT_PATH variable directly ---
            api_script_path = EXTERNAL_SCRIPT_PATH

            # 2. Run the external script
            result = subprocess.run(
                [sys.executable, api_script_path],
                capture_output=True,
                text=True,
                check=False
            )

            # 3. Manual check for an error or crash
            if result.returncode != 0:
                error_message = (
                    f"Data Script CRASHED or FAILED (Exit Code {result.returncode}):\n"
                    f"--- CRASH OUTPUT (STDERR) ---\n{result.stderr.strip()}"
                )
                self.status_label.setText(error_message)

                # If the cache file exists, load new data into it
                if os.path.exists(CACHE_FILE):
                    self.load_data_into_table(CACHE_FILE)
                    self.status_label.show()
                    self.table_widget.show()
                self.button.setDisabled(False)
                return

            # 4. If successful, load the NEW temporary file and update the cache
            if os.path.exists(DATA_FILE):
                self.load_data_into_table(DATA_FILE)
                shutil.copyfile(DATA_FILE, CACHE_FILE)
                self.status_label.setText("Live data loaded successfully.")
            else:
                self.status_label.setText(f"Error: Script ran successfully, but {DATA_FILE} was not created.")

        except Exception as e:
            error_message = f"An unexpected error occurred during loading: {e}"
            self.status_label.setText(error_message)

        finally:
            self.button.setDisabled(False)
            # 5. Clean up the temporary file
            if os.path.exists(DATA_FILE):
                try:
                    os.remove(DATA_FILE)
                except Exception as e:
                    print(f"Warning: Failed to clean up {DATA_FILE}: {e}")

# -------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)

    # STYLESHEET LOADING
    # --- FIX 3: Use the global QSS_FILE variable directly ---
    if os.path.exists(QSS_FILE):
        try:
            with open(QSS_FILE, 'r') as f:
                qss_content = f.read()
            app.setStyleSheet(qss_content)
        except Exception as e:
            print(f"Error loading QSS file: {e}")
    # --------------------------

    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# Run the file
if __name__ == "__main__":
    main()
