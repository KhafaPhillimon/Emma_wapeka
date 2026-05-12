# Web Server Log Analytics

A Dash-based web application for analyzing, visualizing, and diagnosing web server CSV logs. The tool processes logs in-memory and provides interactive filtering, volume tracking, and anomaly detection using Z-Score statistical analysis.

## Setup Instructions

1. Ensure you have Python 3.8+ installed.
2. Install the required dependencies:
   ```bash
   pip install pandas dash plotly
   ```

## Running the Application

1. If you don't have a dataset, generate a synthetic one:
   ```bash
   python generate_dataset.py
   ```
   This will create a `dataset.csv` file with 10,000 rows of test data.

2. Start the Dash server:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to `http://127.0.0.1:8050/`.
4. Drag and drop the `dataset.csv` file into the upload zone.

## Architecture

- `app.py`: The main Dash application, containing layout definitions, upload callbacks, data cleaning logic, and Plotly chart generation.
- `generate_dataset.py`: Utility script that creates synthetic log data matching the required schema.

## Features

- **Volume Tracking:** Line charts and heatmaps visualizing requests over time.
- **Latency Analysis:** Moving averages, box plots, and histograms covering response times across services.
- **Geographic Data:** 3D interactive orthographic map showing traffic origins.
- **Anomaly Detection:** Automatically flags requests with latency Z-scores > 2.5 or HTTP 4xx/5xx errors, isolating them in a searchable data table.
