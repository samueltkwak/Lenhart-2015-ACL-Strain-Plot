
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import io
import base64
import os

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # Required for deployment

DATA_URL = "https://raw.githubusercontent.com/samueltkwak/Lenhart-2015-ACL-Strain-Plot/main/data.txt"

# For deployment, we'll include sample data or allow file upload
# This version will work with uploaded files through the web interface

def parse_contents(contents, filename):
    """Parse uploaded file contents"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'txt' in filename:
            # Assume tab-separated text file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep='\t')
        else:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return df
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

# Define the layout
app.layout = html.Div([
    html.H1("Lenhart (2015) ACL model", 
            style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),

    html.Div([
        html.H3("Upload Data File", style={'color': '#34495e'}),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files', style={'color': '#3498db', 'cursor': 'pointer'})
            ]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px', 'backgroundColor': '#ecf0f1'
            },
            multiple=False
        ),
        html.Div(id='output-data-upload'),
    ], style={'margin': '20px 0'}),

    html.Div(id='slider-container', children=[], style={'margin': '20px 0'}),

    dcc.Graph(id='acl-surface-plot', style={'height': '600px'}),

    # Store component to hold the data
    dcc.Store(id='stored-data')
], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})

@app.callback(
    [Output('stored-data', 'data'), 
     Output('output-data-upload', 'children'),
     Output('slider-container', 'children')],
    [Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename')]
)
def update_output(contents, filename):
    """Update stored data and create sliders when file is uploaded"""
    if contents is None:
        return None, "Please upload a tab-separated text file (.txt)", []

    df = parse_contents(contents, filename)
    if df is None:
        return None, f"Error reading file {filename}", []

    # Verify required columns exist
    if df.shape[1] < 18:
        return None, f"File must have at least 18 columns. Found {df.shape[1]}", []

    # Get unique values for sliders
    unique_flexion = sorted(df.iloc[:, 0].unique())
    unique_anterior = sorted(df.iloc[:, 3].unique()) 
    unique_lateral = sorted(df.iloc[:, 4].unique())

    # Create sliders
    sliders = [
        html.Div([
            html.Label("Knee Flexion Angle (°):", 
                      style={'fontWeight': 'bold', 'marginBottom': 5, 'color': '#2c3e50'}),
            dcc.Slider(
                id='flexion-slider',
                min=min(unique_flexion),
                max=max(unique_flexion),
                step=None,
                marks={int(v): f'{v}°' for v in unique_flexion[::max(1, len(unique_flexion)//8)]},
                value=unique_flexion[0],
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'margin': '20px 0'}),

        html.Div([
            html.Label("Knee Anterior Translation (mm):", 
                      style={'fontWeight': 'bold', 'marginBottom': 5, 'color': '#2c3e50'}),
            dcc.Slider(
                id='anterior-slider',
                min=min(unique_anterior),
                max=max(unique_anterior),
                step=None,
                marks={v: f'{v}mm' for v in unique_anterior[::max(1, len(unique_anterior)//8)]},
                value=unique_anterior[0],
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'margin': '20px 0'}),

        html.Div([
            html.Label("Knee Lateral Translation (mm):", 
                      style={'fontWeight': 'bold', 'marginBottom': 5, 'color': '#2c3e50'}),
            dcc.Slider(
                id='lateral-slider',
                min=min(unique_lateral),
                max=max(unique_lateral),
                step=None,
                marks={v: f'{v}mm' for v in unique_lateral[::max(1, len(unique_lateral)//8)]},
                value=unique_lateral[0],
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'margin': '20px 0'})
    ]

    success_msg = html.Div([
        html.P(f"✅ Successfully loaded {filename}", style={'color': '#27ae60', 'fontWeight': 'bold'}),
        html.P(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns", style={'color': '#7f8c8d'})
    ])

    return df.to_dict('records'), success_msg, sliders

@app.callback(
    Output('acl-surface-plot', 'figure'),
    [Input('flexion-slider', 'value'),
     Input('anterior-slider', 'value'), 
     Input('lateral-slider', 'value'),
     Input('stored-data', 'data')]
)
def update_surface(flexion_val, anterior_val, lateral_val, stored_data):
    """Update surface plot based on slider values"""

    if stored_data is None or flexion_val is None:
        # Return empty plot
        fig = go.Figure()
        fig.update_layout(
            title="Please upload a data file to begin",
            xaxis_title="No data loaded",
            yaxis_title="No data loaded"
        )
        return fig

    # Convert back to DataFrame
    df = pd.DataFrame(stored_data)

    # Get axis ranges
    unique_x = sorted(df.iloc[:, 1].unique())  # Knee Adduction Angle
    unique_y = sorted(df.iloc[:, 2].unique())  # Knee Internal Rotation Angle
    x_grid, y_grid = np.meshgrid(unique_x, unique_y)

    # Filter data based on slider values
    filtered_data = df[(df.iloc[:, 0] == flexion_val) & 
                       (df.iloc[:, 3] == anterior_val) & 
                       (df.iloc[:, 4] == lateral_val)]

    # Create surface data
    z_matrix = np.full((len(unique_y), len(unique_x)), np.nan)
    for i, y_val in enumerate(unique_y):
        for j, x_val in enumerate(unique_x):
            mask = (filtered_data.iloc[:, 1] == x_val) & (filtered_data.iloc[:, 2] == y_val)
            if mask.any():
                z_matrix[i, j] = filtered_data[mask].iloc[0, 17] * 100  # Convert to percentage

    # Calculate global min/max for consistent coloring
    global_min = (df.iloc[:, 17] * 100).min()
    global_max = (df.iloc[:, 17] * 100).max()

    # Create the figure
    fig = go.Figure()

    # Add surface plot
    fig.add_trace(go.Surface(
        x=x_grid,
        y=y_grid,
        z=z_matrix,
        colorscale='Balance',
        cmin=global_min,
        cmax=global_max,
        colorbar=dict(title="ACLpl Strain (%)")
    ))

    # Add reference plane at z=0
    z_plane = np.zeros_like(x_grid)
    fig.add_trace(go.Surface(
        x=x_grid,
        y=y_grid,
        z=z_plane,
        colorscale=[[0, 'rgba(150,150,150,0.5)'], [1, 'rgba(150,150,150,0.5)']], 
        showscale=False,
        opacity=0.5,
        name='z=0 plane'
    ))

    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis_title="Knee Adduction Angle (°)",
            yaxis_title="Knee Internal Rotation Angle (°)",
            zaxis_title="ACLpl Strain (%)",
            xaxis=dict(range=[min(unique_x), max(unique_x)]),
            yaxis=dict(range=[min(unique_y), max(unique_y)]),
            zaxis=dict(range=[global_min, global_max]),
            aspectmode='cube',
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
