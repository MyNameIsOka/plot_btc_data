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
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from collections import defaultdict
from matplotlib.colors import Normalize

app = QApplication(sys.argv)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.currentPlot = None  # Track the current plot displayed

    def parseDate(self, date_str):
        date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None  # Return None if all parsing attempts fail

    def initUI(self):
        self.setWindowTitle("CSV Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        # Central Widget and Layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        # Matplotlib Figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        mainLayout.addWidget(self.canvas, 1)

        # Button to open CSV file
        self.openCsvButton = QPushButton("Open CSV File", self)
        self.openCsvButton.clicked.connect(self.openFileDialog)
        mainLayout.addWidget(self.openCsvButton)

        # Button to show the initial graph
        self.showGraphButton = QPushButton("Show Graph", self)
        self.showGraphButton.clicked.connect(self.showGraph)
        mainLayout.addWidget(self.showGraphButton)
        self.showGraphButton.hide()

        # Create a layout for "Show Average % Changes on Weekday" button and its date selectors
        self.avgChangesLayout = QHBoxLayout()
        self.showAvgChangesButton = QPushButton(
            "Show Average % Changes on Weekday", self
        )
        self.showAvgChangesButton.clicked.connect(self.showAvgChanges)
        self.avgChangesLayout.addWidget(self.showAvgChangesButton)

        # Create a layout for "Show heatmap per day" button and its date selectors
        self.heatmapLayout = QHBoxLayout()
        self.showHeatmapButton = QPushButton("Show heatmap per day", self)
        self.showHeatmapButton.clicked.connect(self.showHeatmap)
        self.heatmapLayout.addWidget(self.showHeatmapButton)

        # Shared Layout for date selection
        self.dateSelectionLayout = QHBoxLayout()

        # Start and End Date Label and Text Field
        self.startLabel = QLabel("Start:", self)
        self.startDateEdit = QLineEdit(self)
        self.startDateEdit.setReadOnly(True)
        self.startDateEdit.mousePressEvent = self.showStartDateCalendar

        self.endLabel = QLabel("End:", self)
        self.endDateEdit = QLineEdit(self)
        self.endDateEdit.setReadOnly(True)
        self.endDateEdit.mousePressEvent = self.showEndDateCalendar

        # Add the start and end date widgets to the date selection layout
        self.dateSelectionLayout.addWidget(self.startLabel)
        self.dateSelectionLayout.addWidget(self.startDateEdit)
        self.dateSelectionLayout.addWidget(self.endLabel)
        self.dateSelectionLayout.addWidget(self.endDateEdit)

        # Add the date selection layout to the avgChanges and heatmap layouts
        self.avgChangesLayout.addLayout(self.dateSelectionLayout)
        # layout for heatmap button is not done to avoid parent errors. Instead it is handled in the toggleDateSelectors function

        # Add the avgChanges and heatmap layouts to the main layout
        mainLayout.addLayout(self.avgChangesLayout)
        mainLayout.addLayout(self.heatmapLayout)

        # Initialize the Start Date Calendar Widget
        self.startDateCalendar = QCalendarWidget()
        self.startDateCalendar.setGridVisible(True)
        self.startDateCalendar.clicked.connect(self.updateStartDate)
        self.startDateCalendar.setWindowModality(Qt.ApplicationModal)
        self.startDateCalendar.hide()  # Initially hide the calendar

        # Initialize the End Date Calendar Widget
        self.endDateCalendar = QCalendarWidget()
        self.endDateCalendar.setGridVisible(True)
        self.endDateCalendar.clicked.connect(self.updateEndDate)
        self.endDateCalendar.setWindowModality(Qt.ApplicationModal)
        self.endDateCalendar.hide()  # Initially hide the calendar

        # Initially hide the date selection UI elements and the heatmap button
        self.showAvgChangesButton.hide()
        self.showHeatmapButton.hide()
        self.startLabel.hide()
        self.startDateEdit.hide()
        self.endLabel.hide()
        self.endDateEdit.hide()

    def toggleDateSelectors(self, show_next_to=None):
        # Ensure the widgets are in their respective layout
        if self.dateSelectionLayout not in (self.avgChangesLayout, self.heatmapLayout):
            # Add date selection layout to the main layout just once
            self.avgChangesLayout.addLayout(self.dateSelectionLayout)

        # Now manage the visibility based on the button clicked
        isVisible = show_next_to == "avgChanges" or show_next_to == "heatmap"
        self.startLabel.setVisible(isVisible)
        self.startDateEdit.setVisible(isVisible)
        self.endLabel.setVisible(isVisible)
        self.endDateEdit.setVisible(isVisible)

    def showStartDateCalendar(self, event):
        if not hasattr(self, "startDateCalendar"):
            self.startDateCalendar = QCalendarWidget()
            self.startDateCalendar.setGridVisible(True)
            self.startDateCalendar.clicked.connect(self.updateStartDate)
            self.startDateCalendar.setWindowModality(Qt.ApplicationModal)
        self.startDateCalendar.show()

    def updateStartDate(self, date):
        selectedDate = date.toPython()
        # Ensure the selected start date is within the dataset's date range
        if selectedDate < self.oldestDate:
            selectedDate = self.oldestDate
        elif selectedDate > self.mostRecentDate:
            selectedDate = self.mostRecentDate

        self.startDateEdit.setText(selectedDate.strftime("%Y-%m-%d"))
        if selectedDate > datetime.strptime(self.endDateEdit.text(), "%Y-%m-%d").date():
            self.endDateEdit.setText(selectedDate.strftime("%Y-%m-%d"))

        self.startDateCalendar.close()
        if self.currentPlot == "avgChanges":
            self.showAvgChanges()

    def showEndDateCalendar(self, event):
        if not hasattr(self, "endDateCalendar"):
            self.endDateCalendar = QCalendarWidget()
            self.endDateCalendar.setGridVisible(True)
            self.endDateCalendar.clicked.connect(self.updateEndDate)
            self.endDateCalendar.setWindowModality(Qt.ApplicationModal)
        self.endDateCalendar.show()

    def updateEndDate(self, date):
        selectedDate = date.toPython()
        # Ensure the selected end date is within the dataset's date range
        if selectedDate > self.mostRecentDate:
            selectedDate = self.mostRecentDate
        elif selectedDate < self.oldestDate:
            selectedDate = self.oldestDate

        self.endDateEdit.setText(selectedDate.strftime("%Y-%m-%d"))
        if (
            selectedDate
            < datetime.strptime(self.startDateEdit.text(), "%Y-%m-%d").date()
        ):
            self.startDateEdit.setText(selectedDate.strftime("%Y-%m-%d"))

        self.endDateCalendar.close()
        if self.currentPlot == "avgChanges":
            self.showAvgChanges()

    def openFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if fileName:
            self.loadData(fileName)

    def initializeDateRange(self):
        if self.rows:
            dates = [
                self.parseDate(row["date"]).date()
                for row in self.rows
                if self.parseDate(row["date"])
            ]
            self.oldestDate = min(dates)
            self.mostRecentDate = max(dates)

            # Update QLineEdit widgets to show the initial date range
            self.startDateEdit.setText(self.oldestDate.strftime("%Y-%m-%d"))
            self.endDateEdit.setText(self.mostRecentDate.strftime("%Y-%m-%d"))

            # Update calendar widgets to set their minimum and maximum selectable dates
            self.startDateCalendar.setMinimumDate(
                QDate(self.oldestDate.year, self.oldestDate.month, self.oldestDate.day)
            )
            self.startDateCalendar.setMaximumDate(
                QDate(
                    self.mostRecentDate.year,
                    self.mostRecentDate.month,
                    self.mostRecentDate.day,
                )
            )
            self.endDateCalendar.setMinimumDate(
                QDate(self.oldestDate.year, self.oldestDate.month, self.oldestDate.day)
            )
            self.endDateCalendar.setMaximumDate(
                QDate(
                    self.mostRecentDate.year,
                    self.mostRecentDate.month,
                    self.mostRecentDate.day,
                )
            )

    def loadData(self, filePath):
        with open(filePath, "r", newline="", encoding="utf-8") as csvfile:
            delimiter = csv.Sniffer().sniff(csvfile.readline()).delimiter
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            self.rows = list(reader)  # Store the data in an instance variable
            self.plotData(self.rows)

            # Show the buttons after data is loaded
            self.plotData(self.rows)
            self.currentPlot = (
                "graph"  # Assume graph is the default plot shown after loading data
            )
            self.showGraphButton.show()
            self.showAvgChangesButton.show()
            self.showHeatmapButton.show()
            self.startLabel.hide()
            self.startDateEdit.hide()
            self.endLabel.hide()
            self.endDateEdit.hide()

            # Reset current plot state
            self.currentPlot = None

            # Initialize the date range
            self.initializeDateRange()

    def plotData(self, rows):
        self.figure.clear()  # Clear the existing plot
        self.figure.subplots_adjust(bottom=0.1)
        ax = self.figure.add_subplot(111)  # Add a subplot

        dates = [
            self.parseDate(row["date"])
            for row in rows
            if self.parseDate(row["date"]) is not None
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

    def calculateAvgPercentageChanges(self):
        if not hasattr(self, "rows") or not self.rows:
            QMessageBox.warning(
                self, "Warning", "No data available to calculate average % changes."
            )
            return {}

        # Parse the start and end dates from the QLineEdit widgets
        start_date = datetime.strptime(self.startDateEdit.text(), "%Y-%m-%d").date()
        end_date = datetime.strptime(self.endDateEdit.text(), "%Y-%m-%d").date()

        # Filter rows for those within the selected date range
        filtered_rows = [
            row
            for row in self.rows
            if start_date <= self.parseDate(row["date"]).date() <= end_date
        ]

        changes = defaultdict(lambda: {"total": 0, "count": 0})
        sorted_rows = sorted(filtered_rows, key=lambda x: self.parseDate(x["date"]))

        for i in range(1, len(sorted_rows)):
            prev_row = sorted_rows[i - 1]
            current_row = sorted_rows[i]

            prev_close = float(prev_row["close"])
            current_close = float(current_row["close"])
            percentage_change = ((current_close - prev_close) / prev_close) * 100

            current_date = self.parseDate(current_row["date"])
            if current_date is None:  # Skip rows with unrecognized date formats
                continue
            weekday = current_date.strftime("%A")

            changes[weekday]["total"] += percentage_change
            changes[weekday]["count"] += 1

        avg_changes = {
            weekday: data["total"] / data["count"] for weekday, data in changes.items()
        }

        return avg_changes

    def showGraph(self):
        # Check if the graph is already displayed
        if self.currentPlot == "graph":
            return  # Do nothing if the graph is already shown

        # Assuming self.rows stores the CSV data
        self.plotData(self.rows)
        self.currentPlot = "graph"  # Update the current plot state

        # Hide the date selection buttons
        self.startLabel.hide()
        self.startDateEdit.hide()
        self.endLabel.hide()
        self.endDateEdit.hide()

    def showAvgChanges(self):
        avg_changes = self.calculateAvgPercentageChanges()

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
        ax.set_xticklabels(weekdays, rotation=45, ha="right")

        self.canvas.draw()
        self.currentPlot = "avgChanges"

        # Show the date selection buttons
        self.startLabel.show()
        self.startDateEdit.show()
        self.endLabel.show()
        self.endDateEdit.show()

        self.toggleDateSelectors("avgChanges")

    def processDataForHeatmap(self, start_date, end_date):
        sorted_rows = sorted(self.rows, key=lambda x: self.parseDate(x["date"]))
        daily_changes = defaultdict(lambda: {"sum": 0, "count": 0})
        for i in range(1, len(sorted_rows)):
            prev_close = float(sorted_rows[i - 1]["close"])
            curr_close = float(sorted_rows[i]["close"])
            date = self.parseDate(sorted_rows[i]["date"]).date()
            if prev_close != 0:  # Avoid division by zero
                percentage_change = ((curr_close - prev_close) / prev_close) * 100
                daily_changes[date.day]["sum"] += percentage_change
                daily_changes[date.day]["count"] += 1

        average_daily_changes = {
            day: changes["sum"] / changes["count"]
            for day, changes in daily_changes.items()
            if changes["count"] > 0
        }

        # Initialize the matrix with zeros or another placeholder for days without data
        heatmap_data = np.zeros((6, 5))  # 6 rows for weeks, 5 columns for weekdays
        for day, avg_change in average_daily_changes.items():
            if day == 31:  # Handle the 31st day as a special case
                row, col = 5, 0
            else:
                row = (day - 1) // 5
                col = (day - 1) % 5
            heatmap_data[row, col] = avg_change

        # Handle the 31st day separately if present
        if 31 in average_daily_changes:
            heatmap_data[5, 0] = average_daily_changes[31]

        min_change = min(heatmap_data.flatten())
        max_change = max(heatmap_data.flatten())

        return heatmap_data, min_change, max_change

    def showHeatmap(self):
        # Call the function to process data and get heatmap_data, min_change, max_change
        heatmap_data, _, _ = self.processDataForHeatmap(
            self.startDateEdit.text(), self.endDateEdit.text()
        )

        # Normalize the data for color mapping
        min_change = np.min(heatmap_data)
        max_change = np.max(heatmap_data)
        norm = Normalize(
            vmin=min(min_change, -max_change), vmax=max(max_change, -min_change)
        )

        # Clear the current figure
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Create the heatmap using imshow
        cax = ax.imshow(heatmap_data, cmap="RdBu", norm=norm, aspect="equal")

        # Add a colorbar
        cbar = self.figure.colorbar(cax, ax=ax)
        cbar.set_label("Average % Change")

        # Set the tick labels for days and weeks
        ax.set_xticks(range(5))
        ax.set_yticks(range(6))
        ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri"], minor=False)
        ax.set_yticklabels(
            ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Day 31"], minor=False
        )

        # Optionally, add annotations to each cell
        for i in range(heatmap_data.shape[0]):
            for j in range(heatmap_data.shape[1]):
                value = heatmap_data[i, j]
                if not np.isclose(value, 0):  # Skip zero or close-to-zero values
                    ax.text(j, i, f"{value:.2f}%", ha="center", va="center", color="w")

        # Set the title and show the plot
        ax.set_title("Heatmap of Average % Changes per Day")
        self.canvas.draw()

        # Update UI elements for the heatmap
        self.startLabel.show()
        self.startDateEdit.show()
        self.endLabel.show()
        self.endDateEdit.show()

        # Hide or show UI elements as needed
        self.toggleDateSelectors("heatmap")
        self.currentPlot = "heatmap"


if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
