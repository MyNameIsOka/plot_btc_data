# CSV Viewer and Analyzer

This project is a simple tool for visualizing and analyzing BTC data in CSV format. Built with PySide6 and Matplotlib, it offers a graphical user interface (GUI) for opening CSV files, displaying closing prices over time, and analyzing average percentage changes by weekdays.

## Features

- **Open and Display CSV Files**: Users can select and load CSV data files to visualize the closing prices over a specified timeframe.
- **Graphical Data Visualization**: Provides a plot of the closing prices over time, allowing for easy trend identification.
- **Weekday Analysis**: Calculates and displays the average percentage changes in closing prices for each weekday, offering insights into weekly trends.
- **Editable Date Range for Analysis**: Users can specify the date range for the analysis to focus on particular periods.

## Prerequisites

- Python 3.8 or higher
- Poetry for dependency management

## Installation

To run the CSV Viewer and Analyzer, you need Python installed on your system. This project is developed with Python 3.8 or later in mind. You also need to install the project dependencies.

1. Clone the repository:

```
git clone git@github.com:MyNameIsOka/plot_btc_data.git
```

2. Navigate to the project directory:

```
cd plot_btc_data
```

3.  Install dependencies with Poetry:

```
poetry install
```

This command will create a virtual environment and install all the necessary dependencies defined in pyproject.toml.

Running the Application
To run the application, use the following command:

```
poetry run python main.py
```

This will launch the PySide6 GUI where you can interact with the application's features.

## Usage

**Open CSV File**: Click the "Open CSV File" button to select a CSV file containing the data you wish to visualize.
**Show Graph**: Displays a graph of the closing prices over time from the selected CSV file.
**Show Average % Changes on Weekday**: Calculates and displays the average percentage changes of closing prices for each weekday.
