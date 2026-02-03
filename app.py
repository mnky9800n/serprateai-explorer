"""
SerpRateAI Time Series Explorer
Bokeh server app for interactive visualization of environmental datasets.
"""

import os
import io
import base64
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row, Spacer
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
                'filename': filename,
                'min_time': df['datetime'].min(),
                'max_time': df['datetime'].max(),
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
    
    # === TOP BAR: Title + Links ===
    header_bar = Div(text="""
        <div style="background: #f5f5f5; padding: 10px 20px; margin-bottom: 10px; 
                    display: flex; justify-content: space-between; align-items: center;">
            <h1 style="margin: 0; font-size: 24px;">SerpRateAI Time Series Explorer</h1>
            <div style="display: flex; align-items: center; gap: 20px;">
                <a href="https://github.com/mnky9800n/serprateai-explorer" target="_blank">📦 Explorer Repo</a>
                <a href="https://github.com/SerpRateAI/datasets" target="_blank">📊 Datasets Repo</a>
                <a href="https://github.com/mnky9800n/serprateai-explorer/issues/new" target="_blank" 
                   style="background: #0066cc; color: white; padding: 8px 16px; border-radius: 5px; 
                          text-decoration: none; font-weight: bold;">
                    🐞🐞🐞 Report Bug! 🐞🐞🐞
                </a>
            </div>
        </div>
    """, sizing_mode='stretch_width')
    
    # Create checkbox group for dataset selection
    checkbox_group = CheckboxGroup(
        labels=dataset_names,
        active=[0, 1] if n_datasets >= 2 else [0],  # Default: first two selected
        width=250
    )
    
    # Instructions
    instructions = Div(text="""
        <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 10px;">
            <p style="font-weight: bold; margin-bottom: 10px;">Instructions:</p>
            <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                <li>Select datasets using checkboxes</li>
                <li>Drag to pan, scroll to zoom</li>
                <li>Box zoom: select tool, then drag</li>
                <li>All plots zoom/pan together</li>
                <li>Toggle "Σ" for cumulative sum</li>
                <li>Use ▲▼ to reorder plots</li>
            </ul>
        </div>
    """, width=250)
    
    # Find global time range for initial view
    all_times = []
    for name in dataset_names:
        all_times.extend(datasets[name]['df']['datetime'].tolist())
    
    global_min_time = min(all_times)
    global_max_time = max(all_times)
    
    # Shared x_range for linked panning/zooming
    shared_x_range = Range1d(start=global_min_time, end=global_max_time)
    
    # Create figures dictionary and controls
    figures = {}
    cumulative_toggles = {}
    move_up_buttons = {}
    move_down_buttons = {}
    cumulative_state = {}
    plot_order = list(range(n_datasets))  # Track current order
    
    # Common tools
    tools = "pan,box_zoom,wheel_zoom,reset,save"
    
    for i, name in enumerate(dataset_names):
        df = datasets[name]['df']
        unit = datasets[name]['unit']
        cumulative_state[name] = False
        
        # Create cumulative toggle button
        cumulative_toggle = Toggle(
            label="Σ",
            button_type="default",
            active=False,
            width=40
        )
        cumulative_toggles[name] = cumulative_toggle
        
        # Create move up/down buttons
        move_up = Button(label="▲", button_type="light", width=30)
        move_down = Button(label="▼", button_type="light", width=30)
        move_up_buttons[name] = move_up
        move_down_buttons[name] = move_down
        
        # Create figure with shared x_range
        p = figure(
            title=f"{name} ({unit})",
            x_axis_type='datetime',
            x_range=shared_x_range,
            height=180,
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
        p.xaxis.axis_label = None
        p.yaxis.axis_label = f"{unit}"
        p.title.text_font_size = "11pt"
        p.min_border_left = 80
        
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
                    figures[dataset_name].yaxis.axis_label = f"Σ {unit}"
                    cumulative_toggles[dataset_name].button_type = "success"
                    cumulative_state[dataset_name] = True
                else:  # Cumulative is OFF
                    source.data['value'] = orig.copy()
                    figures[dataset_name].yaxis.axis_label = f"{unit}"
                    cumulative_toggles[dataset_name].button_type = "default"
                    cumulative_state[dataset_name] = False
            return callback
        
        cumulative_toggle.on_change('active', make_cumulative_callback(name))
    
    # Container for plot rows (will be rebuilt on reorder)
    plot_container = column(sizing_mode='stretch_width')
    
    def build_plot_layout():
        """Rebuild the plot layout based on current order."""
        plot_rows = []
        for idx in plot_order:
            name = dataset_names[idx]
            if figures[name].visible:
                controls_col = column(
                    move_up_buttons[name],
                    cumulative_toggles[name],
                    move_down_buttons[name],
                    width=50
                )
                plot_row = row(
                    controls_col,
                    figures[name],
                    sizing_mode='stretch_width'
                )
                plot_rows.append(plot_row)
        
        plot_container.children = plot_rows if plot_rows else [Div(text="<p style='text-align:center; color:#666;'>Select datasets to display</p>")]
    
    # Move callbacks
    def make_move_callback(direction, dataset_name):
        def callback():
            nonlocal plot_order
            idx = dataset_names.index(dataset_name)
            pos = plot_order.index(idx)
            
            if direction == 'up' and pos > 0:
                plot_order[pos], plot_order[pos-1] = plot_order[pos-1], plot_order[pos]
            elif direction == 'down' and pos < len(plot_order) - 1:
                plot_order[pos], plot_order[pos+1] = plot_order[pos+1], plot_order[pos]
            
            build_plot_layout()
        return callback
    
    for name in dataset_names:
        move_up_buttons[name].on_click(make_move_callback('up', name))
        move_down_buttons[name].on_click(make_move_callback('down', name))
    
    # Function to auto-zoom to visible datasets
    def update_zoom_to_visible():
        active_indices = checkbox_group.active
        if not active_indices:
            return
        
        active_names = [dataset_names[i] for i in active_indices]
        
        # Find time bounds of visible datasets
        min_times = [datasets[name]['min_time'] for name in active_names]
        max_times = [datasets[name]['max_time'] for name in active_names]
        
        new_min = min(min_times)
        new_max = max(max_times)
        
        # Add 2% padding
        time_range = (new_max - new_min).total_seconds()
        padding = timedelta(seconds=time_range * 0.02)
        
        shared_x_range.start = new_min - padding
        shared_x_range.end = new_max + padding
    
    # Callback to toggle plot visibility AND auto-zoom
    def checkbox_callback(attr, old, new):
        for i, name in enumerate(dataset_names):
            visible = i in new
            figures[name].visible = visible
            cumulative_toggles[name].visible = visible
            move_up_buttons[name].visible = visible
            move_down_buttons[name].visible = visible
        
        build_plot_layout()
        update_zoom_to_visible()
    
    checkbox_group.on_change('active', checkbox_callback)
    
    # Initialize
    for i, name in enumerate(dataset_names):
        visible = i in checkbox_group.active
        figures[name].visible = visible
        cumulative_toggles[name].visible = visible
        move_up_buttons[name].visible = visible
        move_down_buttons[name].visible = visible
    
    build_plot_layout()
    update_zoom_to_visible()
    
    # Export button and state
    export_button = Button(label="📥 Export to Matplotlib", button_type="success", width=200)
    status_div = Div(text="", width=250)
    
    # Store for generated file data
    export_data = {'b64': '', 'filename': ''}
    
    # Download button (initially hidden)
    download_button = Button(label="⬇️ Click to Download", button_type="primary", width=200, visible=False)
    
    def export_callback():
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        active_indices = checkbox_group.active
        active_names = [dataset_names[i] for i in active_indices]
        
        if not active_names:
            status_div.text = "<p style='color:red'>No datasets selected!</p>"
            return
        
        x_start = shared_x_range.start
        x_end = shared_x_range.end
        
        if isinstance(x_start, (int, float)):
            x_start = pd.Timestamp(x_start, unit='ms')
            x_end = pd.Timestamp(x_end, unit='ms')
        
        n_plots = len(active_names)
        
        fig, axes = plt.subplots(n_plots, 1, figsize=(12, 2.5 * n_plots), sharex=True)
        if n_plots == 1:
            axes = [axes]
        
        for ax, name in zip(axes, active_names):
            df = datasets[name]['df'].copy()
            unit = datasets[name]['unit']
            color = colors[dataset_names.index(name) % len(colors)]
            is_cumulative = cumulative_state[name]
            
            if is_cumulative:
                df['value'] = np.nancumsum(df['value'].values)
                unit_label = f"Σ {unit}"
            else:
                unit_label = unit
            
            mask = (df['datetime'] >= x_start) & (df['datetime'] <= x_end)
            df_view = df[mask]
            
            ax.plot(df_view['datetime'], df_view['value'], color=color, linewidth=1)
            ax.set_ylabel(f"{name}\n({unit_label})", fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', labelsize=8)
        
        axes[-1].set_xlabel("Time", fontsize=10)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        fig.suptitle("SerpRateAI Time Series Data", fontsize=12, fontweight='bold')
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"serprateai_export_{timestamp}.png"
        
        export_data['b64'] = b64
        export_data['filename'] = filename
        
        status_div.text = f"<p style='color:green'>✓ Generated {filename}</p>"
        download_button.visible = True
        download_button.label = f"⬇️ Download {filename}"
    
    export_button.on_click(export_callback)
    
    # Download callback using CustomJS
    download_callback = CustomJS(args=dict(export_data=export_data), code="""
        // This gets the current export data and triggers download
        const b64 = export_data.b64;
        const filename = export_data.filename;
        
        if (b64 && filename) {
            const link = document.createElement('a');
            link.href = 'data:image/png;base64,' + b64;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    """)
    
    # Use a simpler approach: embed download link directly
    download_div = Div(text="", width=250)
    
    def trigger_download():
        if export_data['b64'] and export_data['filename']:
            download_div.text = f'''
                <a id="dl_{export_data['filename']}" 
                   href="data:image/png;base64,{export_data['b64']}" 
                   download="{export_data['filename']}"
                   style="display:inline-block; background:#28a745; color:white; 
                          padding:10px 20px; border-radius:5px; text-decoration:none;
                          font-weight:bold; margin-top:10px;">
                    ⬇️ Download {export_data['filename']}
                </a>
            '''
    
    def export_and_show_link():
        export_callback()
        trigger_download()
    
    export_button.on_click(export_and_show_link)
    
    # Layout - clean sidebar + main area
    controls = column(
        Div(text="<h3>Select Datasets</h3>"),
        checkbox_group,
        Div(text="<hr>"),
        export_button,
        download_div,
        status_div,
        Div(text="<hr>"),
        instructions,
        width=280
    )
    
    # Main content area
    content_area = column(
        plot_container,
        sizing_mode='stretch_width'
    )
    
    main_row = row(
        controls,
        content_area,
        sizing_mode='stretch_width'
    )
    
    main_layout = column(
        header_bar,
        main_row,
        sizing_mode='stretch_width',
        styles={'padding': '0 40px'}
    )
    
    return main_layout


# Create and add to document
layout = create_app()
curdoc().add_root(layout)
curdoc().title = "SerpRateAI Time Series Explorer"
