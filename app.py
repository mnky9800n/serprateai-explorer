"""
SerpRateAI Time Series Explorer
Bokeh server app for interactive visualization of environmental datasets.
"""

import os
import io
import base64
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, CheckboxGroup, Button, Div, Toggle,
    RangeTool, Range1d, DataRange1d, HoverTool,
    BoxZoomTool, PanTool, ResetTool, WheelZoomTool,
    CrosshairTool, CustomJS
)
from bokeh.plotting import figure
from bokeh.palettes import Category10_10, Turbo256

# Data directory
DATA_DIR = Path(__file__).parent / "data"

# Define datasets to load - (filename, datetime_col, value_col, display_name, unit)
DATASETS = [
    ("ba1d_pressure.csv", "datetime", "pressure_bar", "BA1D Pressure", "bar"),
    ("ba1d_temperature.csv", "datetime", "temperature_c", "BA1D Temperature", "°C"),
    ("bubble_count.csv", "datetime", "bubble_count", "Bubble Count", "count"),
    ("fractures.csv", "datetime", "count", "Fractures", "count"),
    ("daily_precipitation.csv", "datetime", "total_precipitation_sum", "Daily Precipitation", "mm"),
    ("hourly_precipitation.csv", "datetime", "total_precip", "Hourly Precipitation", "mm"),
    ("hourly_surface_pressure.csv", "datetime", "surface_pressure", "Surface Pressure", "Pa"),
    ("hourly_temp2m.csv", "datetime", "temperature_2m", "Temperature (2m)", "K"),
    ("hourly_soil_temp_lvl1.csv", "datetime", "soil_temperature_level_1", "Soil Temp Level 1", "K"),
    ("hourly_soil_temp_lvl2.csv", "datetime", "soil_temperature_level_2", "Soil Temp Level 2", "K"),
    ("hourly_soil_temp_lvl3.csv", "datetime", "soil_temperature_level_3", "Soil Temp Level 3", "K"),
    ("hourly_soil_temp_lvl4.csv", "datetime", "soil_temperature_level_4", "Soil Temp Level 4", "K"),
    ("hourly_volu_soil_water_layer1.csv", "datetime", "volumetric_soil_water_layer_1", "Soil Water Layer 1", "m³/m³"),
    ("hourly_volu_soil_water_layer2.csv", "datetime", "volumetric_soil_water_layer_2", "Soil Water Layer 2", "m³/m³"),
    ("hourly_volu_soil_water_layer3.csv", "datetime", "volumetric_soil_water_layer_3", "Soil Water Layer 3", "m³/m³"),
    ("hourly_volu_soil_water_layer4.csv", "datetime", "volumetric_soil_water_layer_4", "Soil Water Layer 4", "m³/m³"),
    ("earthtide_oman_waves-all_tidalarealstrain.csv", "datetime", "tide_nstr", "Earth Tides", "nstr"),
]


def load_dataset(filename, datetime_col, value_col):
    """Load a CSV dataset with robust datetime parsing."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"Warning: {filename} not found")
        return None
    
    try:
        df = pd.read_csv(filepath)
        # Try ISO8601 format first (handles mixed formats), fall back to mixed
        try:
            df[datetime_col] = pd.to_datetime(df[datetime_col], format='ISO8601', utc=True)
        except ValueError:
            df[datetime_col] = pd.to_datetime(df[datetime_col], format='mixed', utc=True)
        
        df = df.dropna(subset=[datetime_col, value_col])
        df = df.sort_values(datetime_col)
        # Convert to naive datetime for Bokeh
        df[datetime_col] = df[datetime_col].dt.tz_localize(None)
        return df[[datetime_col, value_col]].rename(columns={datetime_col: 'datetime', value_col: 'value'})
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def create_app():
    """Create the Bokeh application."""
    
    # Load all datasets
    print("Loading datasets...")
    datasets = {}
    sources = {}
    original_values = {}  # Store original values for cumulative toggle
    
    for filename, dt_col, val_col, display_name, unit in DATASETS:
        df = load_dataset(filename, dt_col, val_col)
        if df is not None and len(df) > 0:
            datasets[display_name] = {
                'df': df,
                'unit': unit,
                'filename': filename
            }
            sources[display_name] = ColumnDataSource(data={
                'datetime': df['datetime'].values,
                'value': df['value'].values
            })
            original_values[display_name] = df['value'].values.copy()
            print(f"  Loaded {display_name}: {len(df)} points")
    
    dataset_names = list(datasets.keys())
    n_datasets = len(dataset_names)
    
    # Color palette
    colors = Category10_10 if n_datasets <= 10 else [Turbo256[i * 256 // n_datasets] for i in range(n_datasets)]
    
    # === TOP LINKS BAR ===
    links_bar = Div(text="""
        <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <a href="https://github.com/mnky9800n/serprateai-explorer" target="_blank" style="margin-right: 20px;">📦 Explorer Repo</a>
                <a href="https://github.com/SerpRateAI/datasets" target="_blank" style="margin-right: 20px;">📊 Datasets Repo</a>
            </div>
            <a href="https://github.com/mnky9800n/serprateai-explorer/issues/new" target="_blank" 
               style="background: #0066cc; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none; font-weight: bold;">
                🐞🐞🐞 Report Bug! 🐞🐞🐞
            </a>
        </div>
    """, width=1200)
    
    # Create checkbox group for dataset selection
    checkbox_group = CheckboxGroup(
        labels=dataset_names,
        active=[0, 1] if n_datasets >= 2 else [0],  # Default: first two selected
        width=250
    )
    
    # Title
    title_div = Div(text="<h1>SerpRateAI Time Series Explorer</h1>", width=600)
    
    # Instructions
    instructions = Div(text="""
        <p><b>Instructions:</b></p>
        <ul>
            <li>Select datasets using checkboxes on the left</li>
            <li>Drag to pan, scroll to zoom</li>
            <li>Box zoom: click box zoom tool, then drag</li>
            <li>All plots zoom/pan together</li>
            <li>Toggle "Σ Cumulative" per plot for cumulative sum</li>
            <li>Click "Export to Matplotlib" to download figure</li>
        </ul>
    """, width=250)
    
    # Find global time range
    all_times = []
    for name in dataset_names:
        all_times.extend(datasets[name]['df']['datetime'].tolist())
    
    min_time = min(all_times)
    max_time = max(all_times)
    
    # Shared x_range for linked panning/zooming
    shared_x_range = Range1d(start=min_time, end=max_time)
    
    # Create figures dictionary and cumulative toggles
    figures = {}
    cumulative_toggles = {}
    cumulative_state = {}  # Track cumulative state per dataset
    
    # Common tools
    tools = "pan,box_zoom,wheel_zoom,reset,save"
    
    for i, name in enumerate(dataset_names):
        df = datasets[name]['df']
        unit = datasets[name]['unit']
        cumulative_state[name] = False
        
        # Create cumulative toggle button for this dataset
        cumulative_toggle = Toggle(
            label="Σ Cumulative",
            button_type="default",
            active=False,
            width=100
        )
        cumulative_toggles[name] = cumulative_toggle
        
        # Create figure with shared x_range
        p = figure(
            title=f"{name} ({unit})",
            x_axis_type='datetime',
            x_range=shared_x_range,
            height=200,
            width=800,
            tools=tools,
            active_drag='pan',
            active_scroll='wheel_zoom'
        )
        
        # Add line
        line = p.line(
            'datetime', 'value',
            source=sources[name],
            line_width=1.5,
            color=colors[i % len(colors)],
            legend_label=name
        )
        
        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ('Time', '@datetime{%F %H:%M}'),
                ('Value', '@value{0.000}'),
            ],
            formatters={'@datetime': 'datetime'},
            mode='vline'
        )
        p.add_tools(hover)
        
        # Crosshair for alignment
        crosshair = CrosshairTool(dimensions='height')
        p.add_tools(crosshair)
        
        # Style
        p.legend.visible = False
        p.xaxis.axis_label = "Time"
        p.yaxis.axis_label = f"{name} ({unit})"
        p.xaxis.visible = True
        
        # Initially hide if not in active checkboxes
        p.visible = i in checkbox_group.active
        
        figures[name] = p
        
        # Cumulative toggle callback
        def make_cumulative_callback(dataset_name):
            def callback(attr, old, new):
                source = sources[dataset_name]
                orig = original_values[dataset_name]
                unit = datasets[dataset_name]['unit']
                
                if new:  # Cumulative is ON
                    cumsum = np.nancumsum(orig)
                    source.data['value'] = cumsum
                    figures[dataset_name].yaxis.axis_label = f"{dataset_name} (cumulative {unit})"
                    cumulative_toggles[dataset_name].button_type = "success"
                    cumulative_state[dataset_name] = True
                else:  # Cumulative is OFF
                    source.data['value'] = orig.copy()
                    figures[dataset_name].yaxis.axis_label = f"{dataset_name} ({unit})"
                    cumulative_toggles[dataset_name].button_type = "default"
                    cumulative_state[dataset_name] = False
            return callback
        
        cumulative_toggle.on_change('active', make_cumulative_callback(name))
    
    # Create plot layout with toggle buttons
    plot_rows = []
    for name in dataset_names:
        plot_row = row(
            cumulative_toggles[name],
            figures[name],
            sizing_mode='stretch_width'
        )
        plot_rows.append(plot_row)
    
    plot_column = column(*plot_rows, sizing_mode='stretch_width')
    
    # Callback to toggle plot visibility
    def checkbox_callback(attr, old, new):
        for i, name in enumerate(dataset_names):
            visible = i in new
            figures[name].visible = visible
            cumulative_toggles[name].visible = visible
    
    checkbox_group.on_change('active', checkbox_callback)
    
    # Initialize visibility
    for i, name in enumerate(dataset_names):
        visible = i in checkbox_group.active
        figures[name].visible = visible
        cumulative_toggles[name].visible = visible
    
    # Export button
    export_button = Button(label="📥 Export to Matplotlib", button_type="success", width=200)
    
    # Hidden download div for triggering browser download
    download_div = Div(text="", width=1, height=1)
    
    # Status div
    status_div = Div(text="", width=250)
    
    # Export callback - generates matplotlib figure server-side and triggers download
    def export_callback():
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        # Get current visible plots and x_range
        active_indices = checkbox_group.active
        active_names = [dataset_names[i] for i in active_indices]
        
        if not active_names:
            status_div.text = "<p style='color:red'>No datasets selected!</p>"
            return
        
        # Get current x_range
        x_start = shared_x_range.start
        x_end = shared_x_range.end
        
        # Convert to datetime if needed
        if isinstance(x_start, (int, float)):
            x_start = pd.Timestamp(x_start, unit='ms')
            x_end = pd.Timestamp(x_end, unit='ms')
        
        n_plots = len(active_names)
        
        # Create matplotlib figure with subplots
        fig, axes = plt.subplots(n_plots, 1, figsize=(12, 3 * n_plots), sharex=True)
        if n_plots == 1:
            axes = [axes]
        
        for ax, name in zip(axes, active_names):
            df = datasets[name]['df'].copy()
            unit = datasets[name]['unit']
            color = colors[dataset_names.index(name) % len(colors)]
            is_cumulative = cumulative_state[name]
            
            # Apply cumulative if toggled
            if is_cumulative:
                df['value'] = np.nancumsum(df['value'].values)
                unit_label = f"cumulative {unit}"
            else:
                unit_label = unit
            
            # Filter to current view range
            mask = (df['datetime'] >= x_start) & (df['datetime'] <= x_end)
            df_view = df[mask]
            
            ax.plot(df_view['datetime'], df_view['value'], color=color, linewidth=1)
            ax.set_ylabel(f"{name}\n({unit_label})", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', labelsize=9)
        
        # Format x-axis
        axes[-1].set_xlabel("Time", fontsize=11)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        # Title
        fig.suptitle("SerpRateAI Time Series Data", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        # Encode as base64 and trigger download via hidden link
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"serprateai_export_{timestamp}.png"
        
        # Create auto-clicking download link
        download_div.text = f'''
            <a id="download_link_{timestamp}" 
               download="{filename}" 
               href="data:image/png;base64,{b64}"
               style="display:none;">Download</a>
            <script>
                (function() {{
                    var link = document.getElementById('download_link_{timestamp}');
                    if (link) {{
                        link.click();
                    }}
                }})();
            </script>
        '''
        
        status_div.text = f"<p style='color:green'>✓ Downloaded {filename}</p>"
    
    export_button.on_click(export_callback)
    
    # Layout
    controls = column(
        Div(text="<h3>Select Datasets:</h3>"),
        checkbox_group,
        Div(text="<hr>"),
        export_button,
        status_div,
        Div(text="<hr>"),
        instructions,
        width=280
    )
    
    main_area = column(
        links_bar,
        title_div,
        row(controls, plot_column, sizing_mode='stretch_width'),
        download_div,
        sizing_mode='stretch_width'
    )
    
    return main_area


# Create and add to document
layout = create_app()
curdoc().add_root(layout)
curdoc().title = "SerpRateAI Time Series Explorer"
