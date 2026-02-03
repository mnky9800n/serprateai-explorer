#!/bin/bash
# Run the SerpRateAI Time Series Explorer
cd "$(dirname "$0")"
bokeh serve app.py --show --port 5006
