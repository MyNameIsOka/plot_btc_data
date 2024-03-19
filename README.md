# CSV Viewer and Analyzer

This project is a comprehensive tool for visualizing and analyzing BTC data in CSV format. Built with PySide6 and Matplotlib, it offers a graphical user interface (GUI) for opening CSV files, displaying closing prices over time, analyzing average percentage changes by weekdays, and viewing a heatmap of average percentage changes per day.

## Features

- **Open and Display CSV Files**: Users can select and load CSV data files to visualize the closing prices over a specified timeframe.
- **Graphical Data Visualization**: Provides a plot of the closing prices over time, allowing for easy trend identification.
- **Weekday Analysis**: Calculates and displays the average percentage changes in closing prices for each weekday, offering insights into weekly trends.
- **Editable Date Range for Analysis**: Users can specify the date range for the analysis to focus on particular periods.
- **Heatmap Visualization**: Offers a heatmap view to analyze the average percentage change per day throughout the selected date range, with color coding indicating positive (green) and negative (red) changes.

https://github.com/MyNameIsOka/plot_btc_data/assets/18796117/a76ecf27-7193-40db-a97f-b260bad8a82d

## Prerequisites

- Python 3.8 or higher
- Poetry for dependency management

## Installation

To run the CSV Viewer and Analyzer, ensure you have Python 3.8 or later installed on your system. Follow these steps to install the project dependencies using Poetry.

1. Clone the repository:

```
git clone git@github.com:MyNameIsOka/plot_btc_data.git
```

2. Navigate to the project directory:

```
cd plot_btc_data
```

3. Install dependencies with Poetry:

```
poetry install
```

This command will create a virtual environment and install all the necessary dependencies defined in `pyproject.toml`.

## Running the Application

To launch the application, use the following command:

```
poetry run python main.py
```

This will open the PySide6 GUI, providing access to the application's features.

## Usage

- **Open CSV File**: Click the "Open CSV File" button to select and load a CSV file.
- **Show Graph**: After loading a CSV file, click "Show Graph" to display a plot of the closing prices over time.
- **Show Average % Changes on Weekday**: Click this button to calculate and display a bar chart showing the average percentage changes of closing prices for each weekday within the selected date range.
- **Show Heatmap per Day**: To view the heatmap visualization, click "Show heatmap per day". This displays a heatmap indicating the average percentage change for each day across the selected timeframe. Red indicates a negative change, while green represents a positive change. You can adjust the start and end dates to refine the analysis period for this visualization.

Adjust the start and end dates by clicking on the respective input fields to refine your analysis for both the "Show Average % Changes on Weekday" and "Show Heatmap per Day" features.

Enjoy exploring BTC data trends with this versatile tool!
