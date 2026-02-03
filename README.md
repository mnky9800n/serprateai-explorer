# SerpRateAI Time Series Explorer

Interactive browser-based visualization for the [SerpRateAI datasets](https://github.com/SerpRateAI/datasets).

## Features

- **16 time series datasets**: pressure, temperature, precipitation, soil temps, earth tides, bubble counts, etc.
- **Checkboxes** to select which series to display
- **Cumulative sum toggle** per plot for cumulative analysis
- **Stacked subplots** sharing a common time axis
- **Linked zoom/pan** - all plots zoom and pan together
- **Click-and-drag zoom** via box zoom tool
- **Matplotlib export** - downloads publication-quality PNG of current view

## Installation

Requires [uv](https://docs.astral.sh/uv/) for package management.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Dependencies are automatically handled by uv
```

## Running

```bash
./run.sh
```

This will:
1. Clone the [datasets repo](https://github.com/SerpRateAI/datasets) if not present
2. Check for and offer to download dataset updates
3. Install dependencies (via uv)
4. Launch the Bokeh server

Then open http://localhost:5006/app in your browser.

## Datasets

| Dataset | Points | Description |
|---------|--------|-------------|
| BA1D Pressure | 39,027 | Borehole pressure (bar) |
| BA1D Temperature | 39,027 | Borehole temperature (°C) |
| Bubble Count | 2,434 | Bubble detection counts |
| Fractures | 101,724 | Detected fracture events |
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
- **Cumulative**: Toggle cumulative sum for individual plots
- **Export**: Click "Export to Matplotlib" to download current view as PNG

## Links

- [Explorer Repository](https://github.com/mnky9800n/serprateai-explorer)
- [Datasets Repository](https://github.com/SerpRateAI/datasets)
- [Report a Bug](https://github.com/mnky9800n/serprateai-explorer/issues/new)

## Project Structure

```
serprateai-explorer/
├── app.py              # Main Bokeh server application
├── pyproject.toml      # Python dependencies (uv)
├── uv.lock             # Locked dependencies
├── run.sh              # Launch script (clones data on first run)
├── README.md           # This file
└── data/               # Cloned from SerpRateAI/datasets (gitignored)
```
