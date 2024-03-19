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
)
import sys
import csv
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from collections import defaultdict

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
        mainLayout.addWidget(self.canvas)
        # ---------------------------------------------------------------------
        # Horizontal layout for buttons
        buttonsLayout = QHBoxLayout()

        # Button to open CSV file
        self.openCsvButton = QPushButton("Open CSV File", self)
        self.openCsvButton.clicked.connect(self.openFileDialog)
        mainLayout.addWidget(self.openCsvButton)

        # Button to show the initial graph
        self.showGraphButton = QPushButton("Show Graph", self)
        self.showGraphButton.clicked.connect(self.showGraph)
        mainLayout.addWidget(self.showGraphButton)
        self.showGraphButton.hide()  # Initially hide this button

        # Button to show the average % changes on weekday
        # Show Average % Changes on Weekday Button
        self.showAvgChangesButton = QPushButton(
            "Show Average % Changes on Weekday", self
        )
        self.showAvgChangesButton.clicked.connect(self.showAvgChanges)
        buttonsLayout.addWidget(
            self.showAvgChangesButton, 50
        )  # Adding to horizontal layout with stretch factor
        self.showAvgChangesButton.hide()  # Initially hide this button

        # Start Date Button
        self.startDateButton = QPushButton("Start Date", self)
        self.startDateButton.clicked.connect(self.showStartDateCalendar)
        self.startDateButton.hide()  # Initially hidden
        buttonsLayout.addWidget(
            self.startDateButton, 25
        )  # Adding to horizontal layout with stretch factor

        # End Date Button
        self.endDateButton = QPushButton("End Date", self)
        self.endDateButton.clicked.connect(self.showEndDateCalendar)
        self.endDateButton.hide()  # Initially hidden
        buttonsLayout.addWidget(
            self.endDateButton, 25
        )  # Adding to horizontal layout with stretch factor

        mainLayout.addLayout(
            buttonsLayout
        )  # Add the horizontal layout to the main layout

    def showStartDateCalendar(self):
        # Initialize the calendar widget
        self.startDateCalendar = QCalendarWidget()
        self.startDateCalendar.setGridVisible(True)
        self.startDateCalendar.clicked.connect(self.updateStartDate)
        self.startDateCalendar.show()

    def updateStartDate(self, date):
        # Update the start date button label and hide the calendar
        self.startDateButton.setText(date.toString("yyyy-MM-dd"))
        self.startDateCalendar.hide()

    def showEndDateCalendar(self):
        # Initialize the calendar widget
        self.endDateCalendar = QCalendarWidget()
        self.endDateCalendar.setGridVisible(True)
        self.endDateCalendar.clicked.connect(self.updateEndDate)
        self.endDateCalendar.show()

    def updateEndDate(self, date):
        # Update the end date button label and hide the calendar
        self.endDateButton.setText(date.toString("yyyy-MM-dd"))
        self.endDateCalendar.hide()

    def openFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if fileName:
            self.loadData(fileName)

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
            self.startDateButton.hide()
            self.endDateButton.hide()

            # Reset current plot state
            self.currentPlot = None

    def plotData(self, rows):
        self.figure.clear()  # Clear the existing plot
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

        changes = defaultdict(lambda: {"total": 0, "count": 0})
        sorted_rows = sorted(self.rows, key=lambda x: self.parseDate(x["date"]))

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
        self.startDateButton.hide()
        self.endDateButton.hide()

    def showAvgChanges(self):
        if self.currentPlot == "avgChanges":
            return  # Do nothing if already shown

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
        ax = self.figure.add_subplot(111)
        ax.bar(weekdays, avg_percentage_changes, color="skyblue")
        ax.set_xlabel("Weekday")
        ax.set_ylabel("Average % Change")
        ax.set_title("Average % Change in Close Price by Weekday")
        ax.set_xticklabels(weekdays, rotation=45, ha="right")

        self.canvas.draw()
        self.currentPlot = "avgChanges"

        # Show the date selection buttons
        self.startDateButton.show()
        self.endDateButton.show()


if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
