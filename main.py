from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QMessageBox,
    QWidget,
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
)
from PySide6.QtCore import Qt, QDate
import sys
import csv
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from collections import defaultdict
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt


app = QApplication(sys.argv)


class DataProcessor:
    def __init__(self):
        super().__init__()
        self.current_plot = None

    def parse_date(self, date_str):
        date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def calculate_avg_percentage_changes(self, rows, start_date_str, end_date_str):
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # Filter rows for those within the selected date range
        filtered_rows = [
            row
            for row in rows
            if start_date <= self.parse_date(row["date"]).date() <= end_date
        ]

        changes = defaultdict(lambda: {"total": 0, "count": 0})
        sorted_rows = sorted(filtered_rows, key=lambda x: self.parse_date(x["date"]))

        for i in range(1, len(sorted_rows)):
            prev_row = sorted_rows[i - 1]
            current_row = sorted_rows[i]

            prev_close = float(prev_row["close"])
            current_close = float(current_row["close"])
            percentage_change = ((current_close - prev_close) / prev_close) * 100

            current_date = self.parse_date(current_row["date"])
            if current_date is None:  # Skip rows with unrecognized date formats
                continue
            weekday = current_date.strftime("%A")

            changes[weekday]["total"] += percentage_change
            changes[weekday]["count"] += 1

        avg_changes = {
            weekday: data["total"] / data["count"] for weekday, data in changes.items()
        }

        return avg_changes

    def process_data_for_heatmap(self, rows, start_date_str, end_date_str):
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        sorted_rows = sorted(rows, key=lambda x: self.parse_date(x["date"]))
        daily_changes = defaultdict(lambda: {"sum": 0, "count": 0})
        # Filter rows based on the selected date range
        for row in sorted_rows:
            date = self.parse_date(row["date"]).date()
            if date < start_date or date > end_date:
                continue  # Skip dates outside the selected range

            if len(sorted_rows) > 1:
                prev_close = float(sorted_rows[sorted_rows.index(row) - 1]["close"])
                curr_close = float(row["close"])
                if prev_close != 0:  # Avoid division by zero
                    percentage_change = ((curr_close - prev_close) / prev_close) * 100
                    daily_changes[date.day]["sum"] += percentage_change
                    daily_changes[date.day]["count"] += 1

        average_daily_changes = {
            day: changes["sum"] / changes["count"]
            for day, changes in daily_changes.items()
            if changes["count"] > 0
        }

        # Initialize the matrix to accommodate 31 days across 5 rows and 7 columns
        heatmap_data = np.zeros((5, 7))
        for day, avg_change in average_daily_changes.items():
            if day > 31:
                continue
            row = (day - 1) // 7
            col = (day - 1) % 7
            heatmap_data[row, col] = avg_change

        min_change = min(heatmap_data.flatten(), default=0)
        max_change = max(heatmap_data.flatten(), default=0)

        return heatmap_data, min_change, max_change


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_processor = DataProcessor()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("CSV Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        # Central Widget and Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Matplotlib Figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, 1)

        # Button to open CSV file
        self.open_csv_button = QPushButton("Open CSV File", self)
        self.open_csv_button.clicked.connect(self.open_file_dialog)
        main_layout.addWidget(self.open_csv_button)

        # Button to show the initial graph
        self.show_graph_button = QPushButton("Show Graph", self)
        self.show_graph_button.clicked.connect(self.show_graph)
        main_layout.addWidget(self.show_graph_button)
        self.show_graph_button.hide()

        # Create a layout for "Show Average % Changes on Weekday" button and its date selectors
        self.avg_changes_layout = QHBoxLayout()
        self.show_avg_changes_button = QPushButton(
            "Show Average % Changes on Weekday", self
        )
        self.show_avg_changes_button.clicked.connect(self.show_avg_changes)
        self.avg_changes_layout.addWidget(self.show_avg_changes_button)

        # Create a layout for "Show heatmap per day" button and its date selectors
        self.heatmap_layout = QHBoxLayout()
        self.show_heatmap_button = QPushButton("Show heatmap per day", self)
        self.show_heatmap_button.clicked.connect(self.show_heatmap)
        self.heatmap_layout.addWidget(self.show_heatmap_button)

        # Shared Layout for date selection
        self.date_selection_layout = QHBoxLayout()

        # Start and End Date Label and Text Field
        self.start_label = QLabel("Start:", self)
        self.start_date_edit = QLineEdit(self)
        self.start_date_edit.setReadOnly(True)
        self.start_date_edit.mousePressEvent = self.show_start_date_calendar

        self.end_label = QLabel("End:", self)
        self.end_date_edit = QLineEdit(self)
        self.end_date_edit.setReadOnly(True)
        self.end_date_edit.mousePressEvent = self.show_end_date_calendar

        # Add the start and end date widgets to the date selection layout
        self.date_selection_layout.addWidget(self.start_label)
        self.date_selection_layout.addWidget(self.start_date_edit)
        self.date_selection_layout.addWidget(self.end_label)
        self.date_selection_layout.addWidget(self.end_date_edit)

        # Add the date selection layout to the avg_changes and heatmap layouts
        self.avg_changes_layout.addLayout(self.date_selection_layout)
        # layout for heatmap button is not done to avoid parent errors. Instead it is handled in the toggle_date_selectors function

        # Add the avg_changes and heatmap layouts to the main layout
        main_layout.addLayout(self.avg_changes_layout)
        main_layout.addLayout(self.heatmap_layout)

        # Initialize the Start Date Calendar Widget
        self.start_date_calendar = QCalendarWidget()
        self.start_date_calendar.setGridVisible(True)
        self.start_date_calendar.clicked.connect(self.update_start_date)
        self.start_date_calendar.setWindowModality(Qt.ApplicationModal)
        self.start_date_calendar.hide()  # Initially hide the calendar

        # Initialize the End Date Calendar Widget
        self.end_date_calendar = QCalendarWidget()
        self.end_date_calendar.setGridVisible(True)
        self.end_date_calendar.clicked.connect(self.update_end_date)
        self.end_date_calendar.setWindowModality(Qt.ApplicationModal)
        self.end_date_calendar.hide()  # Initially hide the calendar

        # Initially hide the date selection UI elements and the heatmap button
        self.show_avg_changes_button.hide()
        self.show_heatmap_button.hide()
        self.start_label.hide()
        self.start_date_edit.hide()
        self.end_label.hide()
        self.end_date_edit.hide()

    def toggle_date_selectors(self, show_next_to=None):
        # Hide the date selectors initially
        self.start_label.setVisible(False)
        self.start_date_edit.setVisible(False)
        self.end_label.setVisible(False)
        self.end_date_edit.setVisible(False)

        # Decide where to show the date selectors based on the current plot
        if show_next_to == "avgChanges":
            self.avg_changes_layout.addWidget(self.start_label)
            self.avg_changes_layout.addWidget(self.start_date_edit)
            self.avg_changes_layout.addWidget(self.end_label)
            self.avg_changes_layout.addWidget(self.end_date_edit)
            # Make visible
            self.start_label.setVisible(True)
            self.start_date_edit.setVisible(True)
            self.end_label.setVisible(True)
            self.end_date_edit.setVisible(True)
        elif show_next_to == "heatmap":
            self.heatmap_layout.addWidget(self.start_label)
            self.heatmap_layout.addWidget(self.start_date_edit)
            self.heatmap_layout.addWidget(self.end_label)
            self.heatmap_layout.addWidget(self.end_date_edit)
            # Make visible
            self.start_label.setVisible(True)
            self.start_date_edit.setVisible(True)
            self.end_label.setVisible(True)
            self.end_date_edit.setVisible(True)

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if file_name:
            self.load_data(file_name)

    def load_data(self, file_path):
        with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
            delimiter = csv.Sniffer().sniff(csvfile.readline()).delimiter
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            self.rows = list(reader)  # Store the data in an instance variable
            self.plot_data(self.rows)

            # Show the buttons after data is loaded
            self.plot_data(self.rows)
            self.current_plot = (
                "graph"  # Assume graph is the default plot shown after loading data
            )
            self.show_graph_button.show()
            self.show_avg_changes_button.show()
            self.show_heatmap_button.show()
            self.start_label.hide()
            self.start_date_edit.hide()
            self.end_label.hide()
            self.end_date_edit.hide()

            # Reset current plot state
            self.current_plot = None

            # Initialize the date range
            self.initialize_date_range()

    def initialize_date_range(self):
        if self.rows:
            dates = [
                self.data_processor.parse_date(row["date"]).date()
                for row in self.rows
                if self.data_processor.parse_date(row["date"])
            ]
            self.oldest_date = min(dates)
            self.most_recent_date = max(dates)

            # Update QLineEdit widgets to show the initial date range
            self.start_date_edit.setText(self.oldest_date.strftime("%Y-%m-%d"))
            self.end_date_edit.setText(self.most_recent_date.strftime("%Y-%m-%d"))

            # Update calendar widgets to set their minimum and maximum selectable dates
            self.start_date_calendar.setMinimumDate(
                QDate(
                    self.oldest_date.year, self.oldest_date.month, self.oldest_date.day
                )
            )
            self.start_date_calendar.setMaximumDate(
                QDate(
                    self.most_recent_date.year,
                    self.most_recent_date.month,
                    self.most_recent_date.day,
                )
            )
            self.end_date_calendar.setMinimumDate(
                QDate(
                    self.oldest_date.year, self.oldest_date.month, self.oldest_date.day
                )
            )
            self.end_date_calendar.setMaximumDate(
                QDate(
                    self.most_recent_date.year,
                    self.most_recent_date.month,
                    self.most_recent_date.day,
                )
            )

    def validate_date_range(self):
        start_date_str = self.start_date_edit.text()
        end_date_str = self.end_date_edit.text()

        if not start_date_str or not end_date_str:
            QMessageBox.warning(self, "Warning", "Please select a valid date range.")
            return False
        return True

    def plot_data(self, rows):
        # Keep the plot_data method here
        self.figure.clear()  # Clear the existing plot
        self.figure.subplots_adjust(bottom=0.1)
        ax = self.figure.add_subplot(111)  # Add a subplot

        dates = [
            self.data_processor.parse_date(row["date"])
            for row in rows
            if self.data_processor.parse_date(row["date"]) is not None
        ]
        closes = [float(row.get("close", "0")) for row in rows]

        if None in dates:
            # Log a warning if there were any unrecognized date formats
            QMessageBox.warning(
                self,
                "Warning",
                "Some dates were in an unrecognized format and were not plotted.",
            )

        ax.plot(dates, closes, marker="o", linestyle="-")  # Plot the data
        ax.set_xlabel("Date")
        ax.set_ylabel("Close")
        ax.grid(True)
        self.canvas.draw()

    def show_calendar(self, is_start_date):
        if is_start_date:
            if not hasattr(self, "start_date_calendar"):
                self.start_date_calendar = QCalendarWidget()
                self.start_date_calendar.setGridVisible(True)
                self.start_date_calendar.clicked.connect(self.update_start_date)
                self.start_date_calendar.setWindowModality(Qt.ApplicationModal)
            self.start_date_calendar.show()
        else:
            if not hasattr(self, "end_date_calendar"):
                self.end_date_calendar = QCalendarWidget()
                self.end_date_calendar.setGridVisible(True)
                self.end_date_calendar.clicked.connect(self.update_end_date)
                self.end_date_calendar.setWindowModality(Qt.ApplicationModal)
            self.end_date_calendar.show()

    def show_start_date_calendar(self, event):
        self.show_calendar(is_start_date=True)

    def show_end_date_calendar(self, event):
        self.show_calendar(is_start_date=False)

    def update_date(self, date, is_start_date):
        selected_date = date.toPython()
        # Ensure the selected date is within the dataset's date range
        if is_start_date:
            if selected_date < self.oldest_date:
                selected_date = self.oldest_date
            elif selected_date > self.most_recent_date:
                selected_date = self.most_recent_date
            self.start_date_edit.setText(selected_date.strftime("%Y-%m-%d"))
            if (
                selected_date
                > datetime.strptime(self.end_date_edit.text(), "%Y-%m-%d").date()
            ):
                self.end_date_edit.setText(selected_date.strftime("%Y-%m-%d"))
        else:
            if selected_date > self.most_recent_date:
                selected_date = self.most_recent_date
            elif selected_date < self.oldest_date:
                selected_date = self.oldest_date
            self.end_date_edit.setText(selected_date.strftime("%Y-%m-%d"))
            if (
                selected_date
                < datetime.strptime(self.start_date_edit.text(), "%Y-%m-%d").date()
            ):
                self.start_date_edit.setText(selected_date.strftime("%Y-%m-%d"))

        if is_start_date:
            self.start_date_calendar.close()
        else:
            self.end_date_calendar.close()

        if self.current_plot == "avgChanges":
            self.show_avg_changes()
        elif self.current_plot == "heatmap":
            self.show_heatmap()

    def update_start_date(self, date):
        self.update_date(date, is_start_date=True)

    def update_end_date(self, date):
        self.update_date(date, is_start_date=False)

    def show_graph(self):
        # Check if the graph is already displayed
        if self.current_plot == "graph":
            return  # Do nothing if the graph is already shown

        # Assuming self.rows stores the CSV data
        self.plot_data(self.rows)
        self.current_plot = "graph"  # Update the current plot state

        # Hide the date selection buttons
        self.start_label.hide()
        self.start_date_edit.hide()
        self.end_label.hide()
        self.end_date_edit.hide()

    def show_avg_changes(self):
        if not self.validate_date_range():
            return

        start_date_str = self.start_date_edit.text()
        end_date_str = self.end_date_edit.text()

        avg_changes = self.data_processor.calculate_avg_percentage_changes(
            self.rows, start_date_str, end_date_str
        )

        # Check if there's data to plot
        if not avg_changes:
            return

        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        avg_percentage_changes = [avg_changes.get(weekday, 0) for weekday in weekdays]

        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.3)
        ax = self.figure.add_subplot(111)
        ax.bar(weekdays, avg_percentage_changes, color="skyblue")
        ax.set_xlabel("Weekday")
        ax.set_ylabel("Average % Change")
        ax.set_title("Average % Change in Close Price by Weekday")
        ax.set_xticks(range(len(weekdays)))  # Set tick locations
        ax.set_xticklabels(weekdays, rotation=45, ha="right")

        self.canvas.draw()
        self.current_plot = "avgChanges"

        # Show the date selection buttons
        self.start_label.show()
        self.start_date_edit.show()
        self.end_label.show()
        self.end_date_edit.show()

        self.toggle_date_selectors("avgChanges")

    def show_heatmap(self):
        if not self.validate_date_range():
            return

        start_date_str = self.start_date_edit.text()
        end_date_str = self.end_date_edit.text()

        heatmap_data, min_val, max_val = self.data_processor.process_data_for_heatmap(
            self.rows, start_date_str, end_date_str
        )

        # Clear the current figure
        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.1)
        ax = self.figure.add_subplot(111)

        cmap = LinearSegmentedColormap.from_list(
            name="red_green", colors=["red", "white", "green"]
        )

        norm = plt.Normalize(vmin=min_val, vmax=max_val)

        cax = ax.matshow(heatmap_data, cmap=cmap, norm=norm)

        # Add a colorbar
        cbar = self.figure.colorbar(cax, ax=ax)
        cbar.set_label("Average % Change")

        # Annotate each cell
        for i in range(heatmap_data.shape[0]):
            for j in range(heatmap_data.shape[1]):
                value = heatmap_data[i, j]
                # Determine text color based on cell's value for better contrast
                text_color = (
                    "white" if abs(value) > 25 else "black"
                )  # Adjust the threshold as needed
                if i * 7 + j + 1 > 31:
                    continue
                text = f"Day {i*7+j+1}\n{value:.1f}%"
                ax.text(j, i, text, ha="center", va="center", color=text_color)

        self.canvas.draw()

        # Update UI elements for the heatmap
        self.start_label.show()
        self.start_date_edit.show()
        self.end_label.show()
        self.end_date_edit.show()
        self.current_plot = "heatmap"
        self.toggle_date_selectors("heatmap")


if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
