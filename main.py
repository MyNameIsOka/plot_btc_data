from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QMessageBox,
    QWidget,
)
import sys
import csv
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


app = QApplication(sys.argv)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.currentPlot = None  # Track the current plot displayed

    def initUI(self):
        self.setWindowTitle("CSV Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        # Central Widget and Layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        # Button to open CSV file
        self.openCsvButton = QPushButton("Open CSV File", self)
        self.openCsvButton.clicked.connect(self.openFileDialog)
        layout.addWidget(self.openCsvButton)

        # Matplotlib Figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Button to show the initial graph
        self.showGraphButton = QPushButton("Show Graph", self)
        self.showGraphButton.clicked.connect(self.showGraph)
        layout.addWidget(self.showGraphButton)
        self.showGraphButton.hide()  # Initially hide this button

        # Button to show the average % changes on weekday
        self.showAvgChangesButton = QPushButton(
            "Show Average % Changes on Weekday", self
        )
        self.showAvgChangesButton.clicked.connect(self.showAvgChanges)
        layout.addWidget(self.showAvgChangesButton)
        self.showAvgChangesButton.hide()  # Initially hide this button

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

    def plotData(self, rows):
        self.figure.clear()  # Clear the existing plot
        ax = self.figure.add_subplot(111)  # Add a subplot

        dates = [row["date"] for row in rows]
        closes = [float(row.get("close", "0")) for row in rows]

        # Define a list of date formats to try
        date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]
        converted_dates = []
        unrecognized_dates = False  # Flag to track unrecognized date formats

        for date in dates:
            date_converted = False
            for fmt in date_formats:
                try:
                    converted_date = datetime.strptime(date, fmt).date()
                    converted_dates.append(converted_date)
                    date_converted = True
                    break  # Break if the date was successfully parsed
                except ValueError:
                    continue  # Try the next format if there was a parsing error

            if not date_converted:
                unrecognized_dates = True  # Set the flag if no format matched

        if unrecognized_dates:
            # Log a warning if there were any unrecognized date formats
            QMessageBox.warning(
                self,
                "Warning",
                "Some dates were in an unrecognized format and were not plotted.",
            )

        ax.plot(converted_dates, closes, marker="o", linestyle="-")  # Plot the data
        ax.set_xlabel("Date")
        ax.set_ylabel("Close")
        ax.grid(True)
        self.canvas.draw()

    def showGraph(self):
        # Check if the graph is already displayed
        if self.currentPlot == "graph":
            return  # Do nothing if the graph is already shown

        # Assuming self.rows stores the CSV data
        self.plotData(self.rows)
        self.currentPlot = "graph"  # Update the current plot state

    def showAvgChanges(self):
        # Check if the average % changes plot is already displayed
        if self.currentPlot == "avgChanges":
            return  # Do nothing if already shown

        # Placeholder for average % changes plot logic
        print(
            "Average % Changes on Weekday plot functionality will be implemented here."
        )
        self.currentPlot = "avgChanges"  # Update the current plot state


if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
