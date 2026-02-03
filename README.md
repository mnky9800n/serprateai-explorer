# SerpRateAI Time Series Explorer

Interactive browser-based visualization for the [SerpRateAI datasets](https://github.com/SerpRateAI/datasets).

## Features

- **16 time series datasets**: pressure, temperature, precipitation, soil temps, earth tides, bubble counts, etc.
- **Checkboxes** to select which series to display
- **Stacked subplots** sharing a common time axis
- **Linked zoom/pan** - all plots zoom and pan together
- **Click-and-drag zoom** via box zoom tool
- **Matplotlib export** - button to download publication-quality PNG of current view

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
# Option 1: Run script
./run.sh

# Option 2: Direct command
bokeh serve app.py --show --port 5006
```

Then open http://localhost:5006/app in your browser.

## Datasets

| Dataset | Points | Description |
|---------|--------|-------------|
| BA1D Pressure | 39,027 | Borehole pressure (bar) |
| BA1D Temperature | 39,027 | Borehole temperature (°C) |
| Bubble Count | 2,434 | Bubble detection counts |
| Daily Precipitation | 425 | Daily precipitation (mm) |
| Hourly Precipitation | 35,064 | Hourly precipitation (mm) |
| Surface Pressure | 35,064 | Atmospheric pressure (Pa) |
| Temperature (2m) | 35,064 | Air temperature at 2m (K) |
| Soil Temp Levels 1-4 | 35,064 | Soil temperature by depth (K) |
| Soil Water Layers 1-4 | ~35,000 | Volumetric soil water content |
| Earth Tides | 84,484 | Tidal areal strain |

## Controls

- **Pan**: Click and drag on plot
- **Box Zoom**: Select box zoom tool, then drag to zoom
- **Wheel Zoom**: Scroll to zoom
- **Reset**: Reset button returns to full view
- **Export**: Click "Export to Matplotlib" to download current view as PNG

## Project Structure

```
serprateai-explorer-bokeh/
├── app.py              # Main Bokeh server application
├── requirements.txt    # Python dependencies
├── run.sh             # Launch script
├── README.md          # This file
└── data/              # Cloned SerpRateAI datasets repo
```
