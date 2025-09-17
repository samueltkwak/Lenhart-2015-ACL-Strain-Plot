import dash
from dash import dcc, html, Input, Output
import dash_daq as daq
import pandas as pd
import numpy as np
import plotly.graph_objects as go

df = pd.read_csv('data.zip', compression='zip', sep='\t')

knee_flexion_angle = df.iloc[:, 0]
knee_adduction_angle = df.iloc[:, 1]
knee_internal_rotation_angle = df.iloc[:, 2]
knee_posterior_translation = -df.iloc[:, 3]
knee_medial_translation = -df.iloc[:, 4]
aclpl_strain_raw = df.iloc[:, 17]
aclam_strain_raw = df.iloc[:, 18]

aclpl_strain_percent = aclpl_strain_raw * 100
aclam_strain_percent = aclam_strain_raw * 100

scroll_bar1_label = "Knee Flexion (°)"
x_axis_label = "Knee Adduction (°)"
y_axis_label = "Knee Internal Rotation (°)"
scroll_bar2_label = "Anterior Tibial Translation (mm)"
scroll_bar3_label = "Medial Tibial Translation (mm)"

unique_knee_flexion_values = sorted(knee_flexion_angle.unique())
unique_anterior_translation_values = sorted(knee_posterior_translation.unique())
unique_lateral_translation_values = sorted(knee_medial_translation.unique())
unique_x = sorted(knee_adduction_angle.unique())
unique_y = sorted(knee_internal_rotation_angle.unique())

def get_z_matrix(selected_flexion, selected_anterior, selected_lateral, strain_col):
    filtered_data = df[
        (knee_flexion_angle == selected_flexion) &
        (knee_posterior_translation == selected_anterior) &
        (knee_medial_translation == selected_lateral)
    ]
    z_matrix = np.full((len(unique_y), len(unique_x)), np.nan)
    for i, y_val in enumerate(unique_y):
        for j, x_val in enumerate(unique_x):
            mask = (filtered_data.iloc[:, 1] == x_val) & (filtered_data.iloc[:, 2] == y_val)
            if mask.any():
                z_matrix[i, j] = filtered_data[mask].iloc[0, strain_col] * 100
    return z_matrix

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H2("ACL Strain 3D Surface Visualization", style={'fontSize': '30px', 'marginBottom': '10px'}),
    html.Div([
        html.Span("ACLpl", style={'fontSize': '18px', 'fontWeight': 'bold', 'marginRight': '16px'}),
        daq.ToggleSwitch(
            id='z-axis-toggle',
            value=False,  # False: PL, True: AM
            style={'display': 'inline-block'}
        ),
        html.Span("ACLam", style={'fontSize': '18px', 'fontWeight': 'bold', 'marginLeft': '16px'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px', 'gap': '10px'}),
    html.Div([
        dcc.Graph(
            id='surface-plot',
            style={'width': '100%', 'height': '65vh', 'margin': 'auto'}
        ),
    ], style={
        'width': '70vw',
        'margin': 'auto',
        'display': 'block',
        'padding': '0px'
    }),
    html.Div([
        html.Label(scroll_bar1_label, style={'fontSize': '20px'}),
        dcc.Slider(
            id='flexion-slider',
            min=0,
            max=len(unique_knee_flexion_values)-1,
            value=0,
            marks={i: str(val) for i, val in enumerate(unique_knee_flexion_values)},
            step=None,
            included=False
        ),
        html.Br(),
        html.Label(scroll_bar2_label, style={'fontSize': '20px'}),
        dcc.Slider(
            id='anterior-slider',
            min=0,
            max=len(unique_anterior_translation_values)-1,
            value=0,
            marks={i: str(val) for i, val in enumerate(unique_anterior_translation_values)},
            step=None,
            included=False
        ),
        html.Br(),
        html.Label(scroll_bar3_label, style={'fontSize': '20px'}),
        dcc.Slider(
            id='lateral-slider',
            min=0,
            max=len(unique_lateral_translation_values)-1,
            value=0,
            marks={i: str(val) for i, val in enumerate(unique_lateral_translation_values)},
            step=None,
            included=False
        ),
    ], style={'padding': '20px', 'marginTop': '30px', 'width': '60vw', 'margin': 'auto'})
])

@app.callback(
    Output('surface-plot', 'figure'),
    Input('z-axis-toggle', 'value'),
    Input('flexion-slider', 'value'),
    Input('anterior-slider', 'value'),
    Input('lateral-slider', 'value')
)
def update_surface(toggle_value, flexion_ix, anterior_ix, lateral_ix):
    flexion = unique_knee_flexion_values[flexion_ix]
    anterior = unique_anterior_translation_values[anterior_ix]
    lateral = unique_lateral_translation_values[lateral_ix]

    if toggle_value:
        strain_col = 18
        z_axis_label = "ACL AM Strain (%)"
        global_min = aclam_strain_percent.min()
        global_max = aclam_strain_percent.max()
    else:
        strain_col = 17
        z_axis_label = "ACL PL Strain (%)"
        global_min = aclpl_strain_percent.min()
        global_max = aclpl_strain_percent.max()

    z_matrix = get_z_matrix(flexion, anterior, lateral, strain_col)
    x_grid, y_grid = np.meshgrid(unique_x, unique_y)
    z_plane = np.zeros_like(x_grid)
    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=x_grid,
        y=y_grid,
        z=z_matrix,
        colorscale='Balance',
        cmin=global_min,
        cmax=global_max,
        colorbar=dict(title=z_axis_label, tickfont=dict(size=18))
    ))
    fig.add_trace(go.Surface(
        x=x_grid,
        y=y_grid,
        z=z_plane,
        colorscale=[[0, 'rgba(150,150,150,0.5)'], [1, 'rgba(150,150,150,0.5)']],
        showscale=False,
        opacity=0.5,
        name='z=0 plane'
    ))
    fig.update_layout(
        title="ACL Strain 3D Surface Visualization",
        font=dict(size=18, family="Arial, sans-serif"),
        scene=dict(
            xaxis_title=x_axis_label,
            yaxis_title=y_axis_label,
            zaxis_title=z_axis_label,
            xaxis=dict(title_font=dict(size=20), tickfont=dict(size=18), range=[min(unique_x), max(unique_x)]),
            yaxis=dict(title_font=dict(size=20), tickfont=dict(size=18), range=[min(unique_y), max(unique_y)]),
            zaxis=dict(title_font=dict(size=20), tickfont=dict(size=18), range=[global_min, global_max]),
            aspectmode='cube',
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
        ),
        margin=dict(l=75, r=75, t=75, b=120)
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
