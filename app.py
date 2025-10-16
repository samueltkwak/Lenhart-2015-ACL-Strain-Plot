import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_daq as daq
import pandas as pd
import numpy as np
import plotly.graph_objects as go

columns_needed = [
    'knee_flexion', 'knee_adduction', 'knee_introtation',
    'knee_anttrans', 'knee_medtrans', 'ACLpl.strain', 'ACLam.strain'
]
df = pd.read_parquet('https://osf.io/download/68d2d1d44ccad223871e45ce/', columns=columns_needed)

for col in df.columns:
    if pd.api.types.is_float_dtype(df[col]):
        df[col] = df[col].astype('float32')
    elif pd.api.types.is_integer_dtype(df[col]):
        df[col] = df[col].astype('int32')

knee_flexion_angle = df["knee_flexion"]
knee_adduction_angle = df["knee_adduction"]
knee_internal_rotation_angle = df["knee_introtation"]
knee_posterior_translation = -df["knee_anttrans"]
knee_medial_translation = -df["knee_medtrans"]
aclpl_strain_raw = df["ACLpl.strain"]
aclam_strain_raw = df["ACLam.strain"]

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
                z_matrix[i, j] = filtered_data[mask][strain_col].iloc[0] * 100
    return z_matrix

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H2("ACL Strain 3D Surface Visualization", style={'fontSize': '24px', 'marginBottom': '10px', 'textAlign': 'center'}),
    html.Div([
        html.Span("ACLpl", style={'fontSize': '18px', 'fontWeight': 'bold', 'marginRight': '16px'}),
        daq.ToggleSwitch(
            id='z-axis-toggle',
            value=False,  # False: PL, True: AM
            style={'display': 'inline-block'}
        ),
        html.Span("ACLam", style={'fontSize': '18px', 'fontWeight': 'bold', 'marginLeft': '16px'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px', 'gap': '10px'}),
    dcc.Store(id='camera-store', data=None),
    html.Div([
        # --- Loading spinner above the graph ---
        dcc.Loading(
            id="custom-loading",
            type="default",  # "default", "dot", "cube", "circle" -- pick your favorite
            children=[html.Div(id="loading-message", style={'height': '30px'})],
            style={"marginBottom": "0px"}
        ),
        # --- Your graph ---
        dcc.Graph(
            id='surface-plot',
            style={'width': '100vh', 'maxWidth': '900px', 'height': '60vh', 'margin': 'auto', 'marginTop':'0px', 'marginBottom':'0px'}
        ),
    ], style={
        'width': '100%',
        'margin': 'auto',
        'display': 'block',
        'padding': '0px',
        'marginTop': '0px',
        'marginBottom': '0px'
    }),
    html.Div([
        html.Label(scroll_bar1_label, style={'fontSize': '16px'}),
        dcc.Slider(
            id='flexion-slider',
            min=0,
            max=len(unique_knee_flexion_values)-1,
            value=0,
            step=1,  # or just omit this line, as 1 is the default
            marks={i: str(val) for i, val in enumerate(unique_knee_flexion_values) if val % 10 == 0},
            included=False
        ),
        html.Br(),
        html.Label(scroll_bar2_label, style={'fontSize': '16px'}),
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
        html.Label(scroll_bar3_label, style={'fontSize': '16px'}),
        dcc.Slider(
            id='lateral-slider',
            min=0,
            max=len(unique_lateral_translation_values)-1,
            value=0,
            marks={i: str(val) for i, val in enumerate(unique_lateral_translation_values)},
            step=None,
            included=False
        ),
    ], style={'padding': '0px', 'marginTop': '0px', 'width': '100%', 'margin': 'auto'})
])

@app.callback(
    Output('surface-plot', 'figure'),
    Output('camera-store', 'data'),
    Output('loading-message','children'),
    [
        Input('z-axis-toggle', 'value'),
        Input('flexion-slider', 'value'),
        Input('anterior-slider', 'value'),
        Input('lateral-slider', 'value'),
        Input('surface-plot', 'relayoutData')
    ],
    State('camera-store', 'data')
)
def update_surface(toggle_value, flexion_ix, anterior_ix, lateral_ix, relayoutData, stored_camera):
    flexion = unique_knee_flexion_values[flexion_ix]
    anterior = unique_anterior_translation_values[anterior_ix]
    lateral = unique_lateral_translation_values[lateral_ix]

    if toggle_value:
        strain_col = "ACLam.strain"
        z_axis_label = "ACLam Strain (%)"
        global_min = aclam_strain_percent.min()
        global_max = aclam_strain_percent.max()
    else:
        strain_col = "ACLpl.strain"
        z_axis_label = "ACLpl Strain (%)"
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
        colorbar=dict(
            title=dict(
                text=z_axis_label,
                font=dict(size=16)),
            tickfont=dict(size=16)
        )
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

    # Camera logic: default camera, then use stored, then update if user moves camera
    camera = stored_camera if stored_camera else dict(eye=dict(x=1.2, y=1.2, z=1.2))
    if relayoutData and 'scene.camera' in relayoutData:
        camera = relayoutData['scene.camera']

    fig.update_layout(
        scene=dict(
            xaxis_title=x_axis_label,
            yaxis_title=y_axis_label,
            zaxis_title=z_axis_label,
            xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14), range=[min(unique_x), max(unique_x)]),
            yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14), range=[min(unique_y), max(unique_y)]),
            zaxis=dict(title_font=dict(size=16), tickfont=dict(size=14), range=[global_min, global_max]),
            aspectmode='cube',
            camera=camera,
        ),
        margin=dict(l=75, r=75, t=75, b=0)
    )

    return fig, camera, ""

if __name__ == '__main__':
    app.run(debug=True)
