import json
from functools import lru_cache
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, callback_context
import numpy as np
import plotly.graph_objects as go


FLEXION_VALUES = list(range(0, 91))
ANTERIOR_TRANSLATION_VALUES = list(range(-10, 11, 2))
LATERAL_TRANSLATION_VALUES = list(range(-10, 11, 2))
PROXIMAL_TRANSLATION_VALUES = list(range(-5, 3))
ADDUCTION_VALUES = list(range(-20, 21))
INTERNAL_ROTATION_VALUES = list(range(-20, 21))
SURFACE_SELECTION_DEFAULT = {"adduction": 0, "rotation": 0}
ANATOMY_ASSETS_PATH = Path(__file__).resolve().parent / "data" / "anatomy_assets.json"
BONE_OPACITY = 0.58
BONE_COLORSCALE = [
    [0.0, "#aaa294"],
    [0.45, "#d4ccbd"],
    [1.0, "#f2eadc"],
]
BONE_LIGHTING = dict(
    ambient=0.28,
    diffuse=0.82,
    specular=0.18,
    roughness=0.42,
    fresnel=0.12,
)
BONE_LIGHTPOSITION = dict(x=-0.4, y=-1.2, z=1.8)
KNEE_JOINT_CENTER = np.array([0.0, 0.0, 0.0])
ANTERIOR_ANATOMY_CAMERA = dict(eye=dict(x=2.35, y=0.0, z=0.15))
SURFACE_CAMERA = dict(
    eye=dict(x=1.85, y=1.85, z=0.82),
    center=dict(x=0.0, y=0.0, z=-0.06),
    up=dict(x=0.0, y=0.0, z=1.0),
)
INTERACTIVE_3D_GRAPH_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
}
STATIC_GRAPH_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}

scroll_bar1_label = "Knee Flexion (deg)"
translation_pad_x_label = "M/L Translation (mm): + Lateral"
translation_pad_y_label = "A/P Translation (mm): + Anterior"
rotation_pad_x_label = "Adduction (deg): + Adduction"
rotation_pad_y_label = "Internal Rotation (deg): + Internal"
proximal_slider_label = "Proximal Translation (mm)"

SURFACE_DOF_OPTIONS = {
    "flexion": {
        "label": "Flexion",
        "unit": "deg",
        "values": tuple(FLEXION_VALUES),
        "ticks": (0, 30, 60, 90),
        "param": "flexion",
    },
    "adduction": {
        "label": "Adduction",
        "unit": "deg",
        "values": tuple(ADDUCTION_VALUES),
        "ticks": (-20, -10, 0, 10, 20),
        "param": "adduction",
    },
    "internal_rotation": {
        "label": "Internal Rotation",
        "unit": "deg",
        "values": tuple(INTERNAL_ROTATION_VALUES),
        "ticks": (-20, -10, 0, 10, 20),
        "param": "internal_rotation",
    },
    "anterior_translation": {
        "label": "Anterior Translation",
        "unit": "mm",
        "values": tuple(ANTERIOR_TRANSLATION_VALUES),
        "ticks": (-10, 0, 10),
        "param": "anterior_translation",
    },
    "lateral_translation": {
        "label": "Lateral Translation",
        "unit": "mm",
        "values": tuple(LATERAL_TRANSLATION_VALUES),
        "ticks": (-10, 0, 10),
        "param": "lateral_translation",
    },
    "proximal_translation": {
        "label": "Proximal Translation",
        "unit": "mm",
        "values": tuple(PROXIMAL_TRANSLATION_VALUES),
        "ticks": (-5, 0, 2),
        "param": "proximal_translation",
    },
}
SURFACE_DOF_DROPDOWN_OPTIONS = [
    {"label": definition["label"], "value": key}
    for key, definition in SURFACE_DOF_OPTIONS.items()
]


def acl_fiber_color(fiber_name):
    return "#e69f00" if fiber_name.startswith("ACLam") else "#0072b2"


THREEDOF_INDIVIDUAL_FIBER_EQUATIONS = {
    # x0=knee_flex, x1=knee_add, x2=knee_int
    "ACLpl1": "-0.277853300000000*x0 + (0.00124893840000000*x0 + 0.43144423)*(1.17103140000000e-7*(x0*(x0 - 21.372904) + 1.58475790000000*x1*x2 + (x2 + 0.2870663)^2)^2 + x1 + 0.473216500000000*x2 + 0.49951407) - 0.00130187367317487*x2^2 + 14.986267",
    "ACLpl2": "(x0*(0.000125013534757098*x0 + 0.0486692403958545) + 0.00943605100000000*x1 - 4.53726933822564)^2 + (-7.29149200000000e-8*(x0 - x2)^3 + 0.00137933260000000*x1 + 0.31902942)*x2 + 0.00270856800000000*x1^2 + 0.611550200000000*x1 - 7.9574816",
    "ACLpl3": "3.68667055408608e-6*x0^3 - 0.0996990169754504*x0 - 0.0996990169754504*(-0.00895259700000000*x0 + 0.0484209730000000*x2 + 0.6284462)^3 + 0.000196126113189468*(x0 + x1 + 0.281504000000000*x2 - 1.3717061)*x1 + 0.328682773409237*x1 + 0.224692128369878*x2 + 6.05556537129456",
    "ACLpl4": "1/2.6043468*(0.00929182500000000*(x0 + (-0.0666799700000000*x2 + 1.1775122)^2 + 2.2517896)^2 + 0.810906400000000*(-x0 + x2) + x1) + 0.00318214180000000*(x0*(-0.00981092000000000*x2 + 0.18723786) + 0.893974700000000*x1 + x2)*x1 - 1.8224671",
    "ACLpl5": "(0.0326471480000000*x0 + 3.78709920000000e-5*(-x0*x1 + (x1 - 3.0395112)^3 + (x1 + x1 - x2 + 1.7465912 - -1.7909743)^2) - 3.0395112)^2 + 0.254846870000000*(x0^3*(5.87098300000000e-9*(x2 - 3.207589)^2 + 1.7247597e-05) + 1.80611990000000*x1 + x2)",
    "ACLpl6": "(-0.0356316830000000*(x0 - 0.236851230000000*(-0.162780460000000*x1 + x2)) + 4.6671023)^2 + 0.228491650000000*(4.35803050000000e-5*(x0 + 0.177725760000000*x1 + 0.00700388554420840*x2^2)^3 + x1 + x1 + x2) + 0.00145512480000000*(x1 + 0.44999388)*(x1 + x2) - 13.591203",
    "ACLam1": "-0.00136241010000000*((x0 + 0.00428717440000000*(-x1 + x2)*x2 + 0.693863030000000*(0.794243900000000*x1 + x2 - 78.07827))^2 + (-0.000314591484672529*(-2.39869200000000*x0 + 86.53701)^2 + x0 + -0.266555580000000*x1 + 7.1516147)*(1.21719860000000*x1 + x2 + 8.552297))",
    "ACLam2": "(-0.000138530460000000*x0 + 0.2494647)*x1 - 0.000302087720000000*(0.0184209500000000*x0*x1 - 0.00943732800000000*x2^2 - x2)^2 + (-0.00252424480000000*(x0 + 43.165283)^2 + x2)*(-0.000906290400000000*x1 - 0.000294773100000000*x2 + 0.17291246) + 6.933997",
    "ACLam3": "-0.00151464470000000*(x0 + -0.219782740000000*(0.0283390900000000*(0.310540560000000*(x0 + x1 - x2) + x1 - 1.0504253)*x2 + x1) - 14.833601)^2 + (-0.00165030560000000*(0.383081900000000*x0 + x1 + 0.542210700000000*x2) + 0.10463336)*x2 - -0.159735710000000*x1 + 3.1270137",
    "ACLam4": "0.138184860000000*(0.589286800000000*(x0 + 1.0993301) + -0.00352761820000000*(x0^2 + (0.245000440000000*(x0 + 0.0477366150000000*(x0 + x2)*x2) + x1 + x1 - 8.999825)*x2 + (-x1 + 0.0663720100000000*x2)^2) + x2 - 30.060455) + 0.162451600000000*x1",
    "ACLam5": "0.0873050600000000*(-(-0.111461270000000*x0 + -0.000546637800000000*(-(-0.111358910000000*x0 - x1 + 5.6741185)^2 + (-0.147958010000000*x0 + x2 + 21.968864)*(-x1 + x2 + 8.476481)) + 5.6741157)^2 + 1.39557290000000*x1 + -0.00685543800000000*(x1 + x2 - 8.654959)^2 + x2) - 1.2718467",
    "ACLam6": "0.000710741300000000*(-(x0 + -0.00822787800000000*(x1 + 2.8384106)*(x1 + x2 + 9.811958) - -0.00195807730000000*x2^2 - 15.594888)^2 + 1.35777258011656*x1^2 + (0.223959000000000*x2 - 1.7213081)^3 + (1/0.72047025*x1 + x2 - 10.791454)*(-x2 + 195.00777))",
}

THREEDOF_INDIVIDUAL_FIBER_MODELS = {
    name: compile(equation.replace("^", "**"), f"<{name}_3dof_strain>", "eval")
    for name, equation in THREEDOF_INDIVIDUAL_FIBER_EQUATIONS.items()
}

THREEDOF_MEAN_BUNDLE_EQUATIONS = {
    # x0=knee_flex, x1=knee_add, x2=knee_int
    "ACLpl": "(--0.00360271240000000*(0.0763059850000000*x0 - 6.4229074)^2*x0 - -1.07774770000000*((0.0900114300000000*x0 - 6.3839808)^2 + x2 - 10.6373005) + 1/0.5897782*x1)*(-1.27552560000000e-5*(-x0 + x1 + x2)*(x2 - -19.873894) + 0.25822142) + -0.000513236450000000*x0*(x2 + 0.16690251)",
    "ACLam": "-0.000978456000000000*(-x0 + (0.00831488800000000*x0*x2 + x1 - x2 - 1.9854839)*(0.00740933050000000*x2 + 0.12993854) + 35.091446)^2 + 0.165297520000000*x1 - 0.000576448448450400*(x1 + x2)^2 + 0.118142330000000*x2 + 0.27168083",
}

THREEDOF_MEAN_BUNDLE_MODELS = {
    name: compile(equation.replace("^", "**"), f"<{name}_3dof_mean_strain>", "eval")
    for name, equation in THREEDOF_MEAN_BUNDLE_EQUATIONS.items()
}

SIXDOF_EQUATIONS = {
    # x0=knee_flex, x1=knee_add, x2=knee_int, x3=knee_ant, x4=knee_prox, x5=knee_lat
    "ACLpl1": "-(x0 - 34.809135)*(63.4788440000000*x3 + 0.2761004) + (x0*x4 - 276.202820000000*x3)^2 + 0.441463680000000*x1 - 29.8360250000000*(2*x1 + x2 - 2301.61748931002*x5 + 43.210583)*x5 + 0.208517245543903*x2 - 3698.33840000000*x4 + 5.7335176",
    "ACLpl2": "-(x0 - 33.111416)*((x0*x4 + 2.1356351)*(37.6007420000000*x3 - 0.3601098) + 1.0103464) - 34.8035470000000*(2*x1 + (x1 + 35.69067)*x2*x3 + x2 + 20.343311)*(x5 - 0.008030077) + (285.155940000000*x3)^2 - 4193.07400000000*x4 - 2.2094288",
    "ACLpl3": "(x0 - 34.20155)*(-61.0115360000000*x3 - 0.06456746) + (-x0*(x0 - 52.733982)*(-20.5594120000000*x3 + 0.36518446) + 3522.5583)*(16.8210090000000*(x3*x3 + x5^2) - x4) + (1.61687720000000*x1 + x2 + 16.789593)*(x3 + 34.2085080000000*(-x5 + 0.0058085155))",
    "ACLpl4": "-(73.8514400000000*(x0 - 0.155492650000000*x2 - 945.668400000000*x3 - 33.473907)*x3 + 73.8514400000000*(0.185134417741925*x0^2*(x3 - 0.006981589) + 49.533405)*x4 + 73.8514400000000*(x1 + 0.596970200000000*x2)*(x5 - 0.00570674) + 147.702880000000*x5 + 2.65241843)",
    "ACLpl5": "((x0 - 32.67652)*(x3 + 0.0013623238) + 1/0.019699348*x4)*(x0^3*x4^2 - 72.69223) + (((x0 + 1/(-1.9447919)*x2)*x3 - 1.944792)^-1*x2 - x1 - 12.863291)*(x3 + 1/0.015374125*x5 - 0.44170365) + 74481.4500000000*x3^2 - -0.8452492",
    "ACLpl6": "71.5004000000000*((x0 + 1/0.115981385*(x0*x4 - 0.0166674670000000*x2) - -15.327085)*(-x3 - 0.002462248) + 49.4977340000000*(x3 - x4)) + x0*x4 + (x1 + x1 + x2 - -13.092675)*(-1/0.02717516*x5 + 0.23758522) + 72743.9587903744*x3^2 + 7.5001183",
    "ACLam1": "-(x0*(x4 + x4 + x5^3 - 0.03951113) + x5 + 2.144635)^2 + -42.2967500000000*((x0 - 34.726818)*x3 + (x1 + 0.653482700000000*x2)*(x5 - 0.0018377672) + 1/0.054127015*(-56.8651275646090*x3^2 + x5) + 67.8689200000000*x4) + x4 + 0.9728942",
    "ACLam2": "-51.8912734601096*(x0 - 35.750355)*(x3 + 0.00079133944) + 0.000809632203023568*x0^3*(x4 - 0.0071268436) + (1.59672770000000*x1 + x2)*(43.9307400000000*x5 - 0.37357137)^2 + 35023.8548934404*x3^2 - 3287.55980000000*x4 - 795.809940000000*x5 + 5.88824",
    "ACLam3": "-0.00130345239889526*x0^2 - 44.8841656383704*x0*x3 + 0.114757950000000*x1 - 25.5467905457520*(1.67836712333917*x1 + x2)*x5 + 0.0711546283380525*x2 + (222.614560000000*x3)^2 + 1441.57801008659*x3 - 3196.83688610925*x4 - 1006.61810122992*x5 + 4.6786187855795",
    "ACLam4": "-((2*x0 - 2129.03780000000*x3 - 75.903366)*x3 + 1.37676470000000*(-(2*x0*x5 + 2.3181846)^3 + x1 + x2)*(x5 - 0.0036609492) + 114.895930000000*x4 + 36.2556800000000*x5)*(((x0 - 60.908016)*x3 + 1.9399457)^3 + 16.184116)",
    "ACLam5": "-1.03666715573168*(x0 - 963.280150000000*x3 - 35.34071)*((x0 - 44.007164)*(-0.320599600000000*x4 + 0.0015204152) + 44.0071640000000*x3 - 0.01188406) + 1.03666715573168*(x1 + x2)*(-31.3431660000000*x5 + 0.08905915) - 2963.83160557029*x4 - 681.831617923627*x5 - 0.445927579458896",
    "ACLam6": "-0.0116385950000000*(0.380276680000000*x0 - 10.5686627669055)^2 - 46.1567788845661*(x0 - 37.177414)*x3 - (x1 + 0.767247440000000*x2 + 15.939155)*(37.1774140000000*x5 - 0.16253783) + (214.666980000000*x3)^2 - 2834.48020000000*x4 - 3.08217248",
    "ACLpl": "(x0 + (--0.0537609570000000*(x1 - x2) + 0.9697227)^2 - 938.858100000000*x3 - 33.991817)*(-68.9586400000000*x3 - -12.7478820000000*x4 - 0.13223389) + (0.105501650000000*(x1 + x1 + x2) - 318.990360000000*x5)*(-318.990000000000*x5 + 2.175888) - 3694.53600000000*x4 - 2.680973",
    "ACLam": "(0.332297945918410*(x0 - 34.607643)^2 - 3101.2253)*(-17.1095808141759*x3^2 + x4 - 0.0033823408) + -45.6939620000000*((x0 - 35.403862)*x3 + (x1 + 1/1.5905658*x2 + 15.755187)*(x5 - 0.003627654) + x4 + x4 - 967.635525117490*x5^2 + 0.16718635) - 5.085127",
}

SIXDOF_MODELS = {
    name: compile(equation.replace("^", "**"), f"<{name}_6dof_strain>", "eval")
    for name, equation in SIXDOF_EQUATIONS.items()
}

SIXDOF_EQUATION_DISPLAY_ORDER = [
    "ACLam",
    "ACLpl",
    "ACLam1",
    "ACLam2",
    "ACLam3",
    "ACLam4",
    "ACLam5",
    "ACLam6",
    "ACLpl1",
    "ACLpl2",
    "ACLpl3",
    "ACLpl4",
    "ACLpl5",
    "ACLpl6",
]


def threedof_variables(flexion, adduction, internal_rotation):
    return {
        "x0": flexion,
        "x1": adduction,
        "x2": internal_rotation,
    }


def calculate_3dof_individual_fiber_strains(flexion, adduction, internal_rotation):
    values = {}
    variables = threedof_variables(flexion, adduction, internal_rotation)
    for fiber_name, model in THREEDOF_INDIVIDUAL_FIBER_MODELS.items():
        values[fiber_name] = eval(model, {"__builtins__": {}}, variables)
    return values


def calculate_3dof_bundle_strain(bundle, flexion, adduction, internal_rotation):
    variables = threedof_variables(flexion, adduction, internal_rotation)
    return eval(THREEDOF_MEAN_BUNDLE_MODELS[bundle], {"__builtins__": {}}, variables)


def sixdof_variables(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    return {
        "x0": flexion,
        "x1": adduction,
        "x2": internal_rotation,
        "x3": anterior_translation / 1000,
        "x4": proximal_translation / 1000,
        "x5": lateral_translation / 1000,
    }


def calculate_6dof_strain(
    target,
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    variables = sixdof_variables(
        flexion=flexion,
        adduction=adduction,
        internal_rotation=internal_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )
    return eval(SIXDOF_MODELS[target], {"__builtins__": {}}, variables)


def calculate_6dof_individual_fiber_strains(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    return {
        fiber_name: calculate_6dof_strain(
            target=fiber_name,
            flexion=flexion,
            adduction=adduction,
            internal_rotation=internal_rotation,
            anterior_translation=anterior_translation,
            lateral_translation=lateral_translation,
            proximal_translation=proximal_translation,
        )
        for fiber_name in THREEDOF_INDIVIDUAL_FIBER_EQUATIONS
    }


def calculate_3dof_placeholder_strain(
    bundle,
    flexion,
    adduction,
    internal_rotation,
):
    return calculate_3dof_bundle_strain(
        bundle=bundle,
        flexion=flexion,
        adduction=adduction,
        internal_rotation=internal_rotation,
    )


def calculate_placeholder_strain(
    model_mode,
    bundle,
    flexion,
    anterior_translation,
    lateral_translation,
    proximal_translation,
    adduction,
    internal_rotation,
):
    if model_mode == "3DOF":
        return calculate_3dof_placeholder_strain(
            bundle=bundle,
            flexion=flexion,
            adduction=adduction,
            internal_rotation=internal_rotation,
        )

    return calculate_6dof_strain(
        target=bundle,
        flexion=flexion,
        adduction=adduction,
        internal_rotation=internal_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )


@lru_cache(maxsize=512)
def get_z_matrix(
    model_mode,
    bundle,
    x_axis,
    y_axis,
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    current_values = {
        "flexion": flexion,
        "adduction": adduction,
        "internal_rotation": internal_rotation,
        "anterior_translation": anterior_translation,
        "lateral_translation": lateral_translation,
        "proximal_translation": proximal_translation,
    }
    x_definition = SURFACE_DOF_OPTIONS[x_axis]
    y_definition = SURFACE_DOF_OPTIONS[y_axis]
    x_grid, y_grid = np.meshgrid(
        np.array(x_definition["values"]),
        np.array(y_definition["values"]),
    )
    surface_values = dict(current_values)
    surface_values[x_definition["param"]] = x_grid
    surface_values[y_definition["param"]] = y_grid

    return calculate_placeholder_strain(
        model_mode=model_mode,
        bundle=bundle,
        **surface_values,
    )


def current_surface_values(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    return {
        "flexion": flexion,
        "adduction": adduction,
        "internal_rotation": internal_rotation,
        "anterior_translation": anterior_translation,
        "lateral_translation": lateral_translation,
        "proximal_translation": proximal_translation,
    }


def surface_axis_title(axis):
    definition = SURFACE_DOF_OPTIONS[axis]
    return f"{definition['label']} ({definition['unit']})"


def fallback_surface_axis(excluded_axis):
    for axis in SURFACE_DOF_OPTIONS:
        if axis != excluded_axis:
            return axis
    return "internal_rotation"


def surface_dof_dropdown_options(disabled_axis=None):
    return [
        {
            "label": definition["label"],
            "value": key,
            "disabled": key == disabled_axis,
        }
        for key, definition in SURFACE_DOF_OPTIONS.items()
    ]


def shared_z_range_for_surfaces(*z_matrices):
    z_min = min(float(np.nanmin(z_matrix)) for z_matrix in z_matrices)
    z_max = max(float(np.nanmax(z_matrix)) for z_matrix in z_matrices)
    max_abs = max(abs(z_min), abs(z_max), 1.0)
    return -max_abs, max_abs


def format_percent_tick(value):
    return f"{value:.1f}"


def surface_contour_values(z_range):
    z_min, z_max = z_range
    return [float(value) for value in np.linspace(z_min, z_max, 5)]


def legend_position_percent(value, z_range):
    z_min, z_max = z_range
    if z_max == z_min:
        return 50.0
    return ((z_max - value) / (z_max - z_min)) * 100


def legend_horizontal_position_percent(value, z_range):
    z_min, z_max = z_range
    if z_max == z_min:
        return 50.0
    return ((value - z_min) / (z_max - z_min)) * 100


def make_surface_legend(z_range):
    z_min, z_max = z_range
    contour_values = surface_contour_values(z_range)
    return html.Div([
        html.Div("Strain (%)", className="surface-legend-title", style={
            "fontSize": "13px",
            "fontWeight": "600",
            "textAlign": "center",
            "marginBottom": "6px",
            "whiteSpace": "nowrap",
        }),
        html.Div([
            html.Div([
                html.Div(
                    className="surface-legend-contour-line",
                    style={
                        "--legend-position": f"{legend_position_percent(value, z_range):.2f}%",
                        "--legend-x-position": f"{legend_horizontal_position_percent(value, z_range):.2f}%",
                    },
                )
                for value in contour_values
            ], className="surface-legend-bar", style={
                "width": "18px",
                "height": "100%",
                "background": "linear-gradient(to bottom, #7b1b22 0%, #f7f7f7 50%, #1f5f9f 100%)",
                "border": "1px solid rgba(0, 0, 0, 0.18)",
                "boxSizing": "border-box",
            }),
            html.Div([
                html.Div(
                    format_percent_tick(value),
                    className="surface-legend-contour-label",
                    style={
                        "--legend-position": f"{legend_position_percent(value, z_range):.2f}%",
                        "--legend-x-position": f"{legend_horizontal_position_percent(value, z_range):.2f}%",
                    },
                )
                for value in contour_values
            ], className="surface-legend-ticks", style={
                "height": "100%",
                "fontSize": "13px",
                "lineHeight": "1",
                "color": "#222222",
            }),
        ], className="surface-legend-body", style={
            "height": "calc(100% - 25px)",
            "display": "flex",
            "gap": "6px",
            "alignItems": "stretch",
            "justifyContent": "center",
        }),
    ], className="surface-legend", style={
        "height": "100%",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "center",
    })


def make_regression_equation_section():
    return html.Div([
        html.Div("Regression Equations Used", style={
            "fontSize": "13px",
            "fontWeight": "600",
            "marginBottom": "6px",
        }),
        html.Div(
            "6DOF inputs: x0 = flexion (deg), x1 = adduction (deg), "
            "x2 = internal rotation (deg), x3 = anterior translation (m), "
            "x4 = proximal translation (m), x5 = lateral translation (m).",
            style={
                "fontSize": "11px",
                "color": "#444444",
                "marginBottom": "8px",
            },
        ),
        html.Div([
            html.Div([
                html.Span(f"{target}: ", style={"fontWeight": "600"}),
                html.Code(SIXDOF_EQUATIONS[target], style={
                    "fontSize": "10px",
                    "whiteSpace": "nowrap",
                }),
            ], style={
                "padding": "4px 0",
                "borderTop": "1px solid #eeeeee",
                "overflowX": "auto",
            })
            for target in SIXDOF_EQUATION_DISPLAY_ORDER
        ]),
    ], style={
        "fontSize": "11px",
        "lineHeight": "1.35",
        "maxWidth": "1180px",
        "margin": "18px auto 8px",
        "padding": "8px 12px",
        "color": "#222222",
        "boxSizing": "border-box",
    })


def make_kinematic_readout_item(label, value, unit):
    return html.Div([
        html.Div(label, style={
            "fontSize": "12px",
            "color": "#555555",
            "lineHeight": "1.1",
            "whiteSpace": "nowrap",
        }),
        html.Div([
            html.Span(str(value), style={
                "fontSize": "18px",
                "fontWeight": "650",
                "color": "#1f1f1f",
            }),
            html.Span(f" {unit}", style={
                "fontSize": "12px",
                "color": "#555555",
            }),
        ], style={"lineHeight": "1.15"}),
    ], className="kinematic-readout-item", style={
        "minWidth": "112px",
        "padding": "7px 10px",
        "border": "1px solid #d6d6d6",
        "borderRadius": "6px",
        "background": "#ffffff",
        "boxSizing": "border-box",
    })


def snap_to_values(value, values):
    return min(values, key=lambda candidate: abs(candidate - value))


def normalized_translation(translation):
    translation = translation or {}
    return {
        "anterior": translation.get("anterior", 0),
        "lateral": translation.get("lateral", -translation.get("medial", 0)),
    }


def load_anatomy_assets():
    with ANATOMY_ASSETS_PATH.open("r", encoding="utf-8") as asset_file:
        payload = json.load(asset_file)

    for mesh in payload["meshes"].values():
        for key in ("x", "y", "z"):
            mesh[key] = np.array(mesh[key], dtype=float)

    return payload


ANATOMY_ASSETS = load_anatomy_assets()


def rotation_x(angle):
    cosine = np.cos(angle)
    sine = np.sin(angle)
    return np.array([
        [1, 0, 0],
        [0, cosine, -sine],
        [0, sine, cosine],
    ])


def rotation_y(angle):
    cosine = np.cos(angle)
    sine = np.sin(angle)
    return np.array([
        [cosine, 0, sine],
        [0, 1, 0],
        [-sine, 0, cosine],
    ])


def rotation_z(angle):
    cosine = np.cos(angle)
    sine = np.sin(angle)
    return np.array([
        [cosine, -sine, 0],
        [sine, cosine, 0],
        [0, 0, 1],
    ])


def knee_transforms(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    flexion_rad = np.deg2rad(flexion)
    # The OpenSim equation convention is +adduction; this display transform
    # needs the opposite sign to show negative values as visual abduction.
    adduction_rad = np.deg2rad(-adduction)
    # Positive internal rotation should move anterior tibia medially in the
    # displayed right-knee anatomy; equations still receive +knee_int.
    rotation_rad = np.deg2rad(-internal_rotation)
    femur_transform = rotation_z(flexion_rad / 2)
    tibia_transform = (
        rotation_z(-flexion_rad / 2)
        @ rotation_x(adduction_rad)
        @ rotation_y(rotation_rad)
    )
    relative_translation = np.array([
        anterior_translation / 1000,
        proximal_translation / 1000,
        -lateral_translation / 1000,
    ])
    femur_translation = np.zeros(3)
    tibia_translation = femur_transform @ relative_translation
    return femur_transform, femur_translation, tibia_transform, tibia_translation


def transform_coordinates(x_values, y_values, z_values, transform, translation):
    points = np.vstack((x_values, y_values, z_values))
    moved = (
        transform @ (points - KNEE_JOINT_CENTER.reshape(3, 1))
        + KNEE_JOINT_CENTER.reshape(3, 1)
        + translation.reshape(3, 1)
    )
    return moved[0], moved[1], moved[2]


def display_coordinates(x_values, y_values, z_values):
    return x_values, z_values, y_values


def mesh_trace(name, mesh, transform=None, translation=None):
    if transform is None:
        x_values = mesh["x"]
        y_values = mesh["y"]
        z_values = mesh["z"]
    else:
        x_values, y_values, z_values = transform_coordinates(
            mesh["x"],
            mesh["y"],
            mesh["z"],
            transform,
            translation,
        )

    display_x, display_y, display_z = display_coordinates(x_values, y_values, z_values)
    return go.Mesh3d(
        x=display_x,
        y=display_y,
        z=display_z,
        i=mesh["i"],
        j=mesh["j"],
        k=mesh["k"],
        name=name,
        intensity=display_z,
        colorscale=BONE_COLORSCALE,
        cmin=float(np.min(display_z)),
        cmax=float(np.max(display_z)),
        opacity=BONE_OPACITY,
        flatshading=False,
        lighting=BONE_LIGHTING,
        lightposition=BONE_LIGHTPOSITION,
        hoverinfo="name",
        showscale=False,
    )


def transform_point(point, transform, translation):
    moved = transform @ (np.array(point) - KNEE_JOINT_CENTER) + KNEE_JOINT_CENTER + translation
    return moved.tolist()


def transformed_acl_fibers(femur_transform, femur_translation, tibia_transform, tibia_translation):
    fibers = []
    for fiber in ANATOMY_ASSETS["acl_fibers"]:
        points = []
        for path_point in fiber["points"]:
            location = path_point["location"]
            if path_point["frame"] == "tibia_proximal_r":
                location = transform_point(location, tibia_transform, tibia_translation)
            elif path_point["frame"] == "femur_distal_r":
                location = transform_point(location, femur_transform, femur_translation)
            points.append(location)

        if len(points) == 2:
            reference_points = [np.array(path_point["location"]) for path_point in fiber["points"]]
            reference_length = float(np.linalg.norm(reference_points[1] - reference_points[0]))
            current_points = [np.array(point) for point in points]
            current_length = float(np.linalg.norm(current_points[1] - current_points[0]))
            fibers.append({
                "name": fiber["name"].replace("_r", ""),
                "points": points,
                "reference_length": reference_length,
                "current_length": current_length,
                "strain": ((current_length - reference_length) / reference_length) * 100,
            })

    return fibers


def acl_traces(fibers):
    traces = []
    for fiber in fibers:
        x_values, y_values, z_values = zip(*fiber["points"])
        display_x, display_y, display_z = display_coordinates(
            np.array(x_values),
            np.array(y_values),
            np.array(z_values),
        )
        traces.append(go.Scatter3d(
            x=display_x,
            y=display_y,
            z=display_z,
            mode="lines",
            name=fiber["name"],
            line=dict(
                color=acl_fiber_color(fiber["name"]),
                width=6,
            ),
            hoverinfo="name",
            showlegend=False,
        ))

    return traces


def orientation_label_traces():
    display_x, display_y, display_z = display_coordinates(
        np.array([0.0, 0.0]),
        np.array([0.0, 0.0]),
        np.array([0.045, -0.045]),
    )
    return go.Scatter3d(
        x=display_x,
        y=display_y,
        z=display_z,
        mode="text",
        text=["Medial", "Lateral"],
        textfont=dict(color="#333333", size=13),
        textposition="middle center",
        hoverinfo="skip",
        showlegend=False,
    )


def make_fiber_figure(fibers, bundle_mean_strains=None):
    fig = go.Figure()
    max_display_length = 1.0
    bundle_mean_strains = bundle_mean_strains or {}
    mean_annotations = []
    display_fibers = sorted(
        fibers,
        key=lambda fiber: (
            0 if fiber["name"].startswith("ACLam") else 1,
            fiber["name"],
        ),
    )

    for index, fiber in enumerate(display_fibers):
        reference_length = fiber["reference_length"]
        current_length = fiber["current_length"]
        current_display_length = current_length / reference_length if reference_length else 1.0
        max_display_length = max(max_display_length, current_display_length)
        hover_display_length = max(current_display_length, 1.0)
        hover_y_values = np.linspace(0, hover_display_length, 28)

        fig.add_trace(go.Scatter(
            x=[index, index],
            y=[0, 1],
            mode="lines",
            line=dict(color="rgba(70, 70, 70, 0.25)", width=12),
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.add_trace(go.Scatter(
            x=[index, index],
            y=[0, current_display_length],
            mode="lines",
            line=dict(color=acl_fiber_color(fiber["name"]), width=7),
            hovertemplate=(
                f"{fiber['name']}<br>"
                f"Strain: {fiber['strain']:.1f}%<br>"
                f"Reference: {reference_length * 1000:.1f} mm<br>"
                f"Current: {current_length * 1000:.1f} mm<extra></extra>"
            ),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[index] * len(hover_y_values),
            y=hover_y_values,
            mode="markers",
            marker=dict(color="rgba(0, 0, 0, 0.001)", size=18),
            hovertemplate=(
                f"{fiber['name']}<br>"
                f"Strain: {fiber['strain']:.1f}%<br>"
                f"Reference: {reference_length * 1000:.1f} mm<br>"
                f"Current: {current_length * 1000:.1f} mm<extra></extra>"
            ),
            showlegend=False,
        ))

    for bundle_name in ("ACLam", "ACLpl"):
        bundle_indices = [
            index
            for index, fiber in enumerate(display_fibers)
            if fiber["name"].startswith(bundle_name)
        ]
        if not bundle_indices:
            continue

        bundle_strains = [display_fibers[index]["strain"] for index in bundle_indices]
        mean_strain = float(bundle_mean_strains.get(bundle_name, np.mean(bundle_strains)))
        mean_display_length = 1 + (mean_strain / 100)
        max_display_length = max(max_display_length, max(mean_display_length, 1.0))
        x_start = min(bundle_indices) - 0.38
        x_end = max(bundle_indices) + 0.38
        color = acl_fiber_color(bundle_name)
        label_x = (x_start + x_end) / 2
        mean_annotations.append(dict(
            x=label_x,
            y=0.97,
            xref="x",
            yref="paper",
            text=f"{bundle_name} {mean_strain:+.1f}%",
            showarrow=False,
            font=dict(color=color, size=16),
            xanchor="center",
            yanchor="top",
        ))

        fig.add_trace(go.Scatter(
            x=[x_start, x_end],
            y=[mean_display_length, mean_display_length],
            mode="lines+markers",
            line=dict(color=color, width=4),
            marker=dict(size=6, color=color),
            opacity=0.86,
            hovertemplate=(
                f"{bundle_name} mean<br>"
                f"Mean strain: {mean_strain:.1f}%<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(text="ACL Fiber Strain (%)", font=dict(size=18), x=0.5),
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(display_fibers))),
            ticktext=[fiber["name"] for fiber in display_fibers],
            tickangle=-90,
            tickfont=dict(size=13),
            range=[-2.35, len(display_fibers) + 1.35],
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=[-0.06, max_display_length + 0.28],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
        ),
        margin=dict(l=34, r=12, t=62, b=82),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="closest",
        hoverdistance=40,
        uirevision="fiber-panel",
        annotations=mean_annotations,
    )
    return fig


def current_acl_fibers(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    femur_transform, femur_translation, tibia_transform, tibia_translation = knee_transforms(
        flexion,
        adduction,
        internal_rotation,
        anterior_translation,
        lateral_translation,
        proximal_translation,
    )
    return transformed_acl_fibers(
        femur_transform,
        femur_translation,
        tibia_transform,
        tibia_translation,
    )


def make_fiber_panel_figure(
    model_mode,
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
):
    fibers = current_acl_fibers(
        flexion,
        adduction,
        internal_rotation,
        anterior_translation,
        lateral_translation,
        proximal_translation,
    )
    if model_mode == "3DOF":
        modeled_strains = calculate_3dof_individual_fiber_strains(
            flexion=flexion,
            adduction=adduction,
            internal_rotation=internal_rotation,
        )
        bundle_mean_strains = {
            bundle_name: float(calculate_3dof_bundle_strain(
                bundle=bundle_name,
                flexion=flexion,
                adduction=adduction,
                internal_rotation=internal_rotation,
            ))
            for bundle_name in ("ACLpl", "ACLam")
        }
    else:
        modeled_strains = calculate_6dof_individual_fiber_strains(
            flexion=flexion,
            adduction=adduction,
            internal_rotation=internal_rotation,
            anterior_translation=anterior_translation,
            lateral_translation=lateral_translation,
            proximal_translation=proximal_translation,
        )
        bundle_mean_strains = {
            bundle_name: float(calculate_6dof_strain(
                target=bundle_name,
                flexion=flexion,
                adduction=adduction,
                internal_rotation=internal_rotation,
                anterior_translation=anterior_translation,
                lateral_translation=lateral_translation,
                proximal_translation=proximal_translation,
            ))
            for bundle_name in ("ACLpl", "ACLam")
        }

    for fiber in fibers:
        strain = float(modeled_strains[fiber["name"]])
        fiber["strain"] = strain
        fiber["current_length"] = fiber["reference_length"] * (1 + (strain / 100))

    return make_fiber_figure(fibers, bundle_mean_strains=bundle_mean_strains)


def make_anatomy_figure(
    flexion,
    adduction,
    internal_rotation,
    anterior_translation,
    lateral_translation,
    proximal_translation,
    camera,
):
    femur_transform, femur_translation, tibia_transform, tibia_translation = knee_transforms(
        flexion,
        adduction,
        internal_rotation,
        anterior_translation,
        lateral_translation,
        proximal_translation,
    )

    fig = go.Figure()
    fig.add_trace(mesh_trace(
        "Femur",
        ANATOMY_ASSETS["meshes"]["femur"],
        femur_transform,
        femur_translation,
    ))
    fig.add_trace(mesh_trace(
        "Tibia",
        ANATOMY_ASSETS["meshes"]["tibia"],
        tibia_transform,
        tibia_translation,
    ))
    fig.add_trace(mesh_trace(
        "Fibula",
        ANATOMY_ASSETS["meshes"]["fibula"],
        tibia_transform,
        tibia_translation,
    ))
    fibers = transformed_acl_fibers(
        femur_transform,
        femur_translation,
        tibia_transform,
        tibia_translation,
    )
    for trace in acl_traces(fibers):
        fig.add_trace(trace)
    fig.add_trace(orientation_label_traces())

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="data",
            camera=camera or ANTERIOR_ANATOMY_CAMERA,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        uirevision="anatomy-model",
    )
    return fig


app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H2(
        "ACL Strain Visualizer",
        style={"fontSize": "24px", "marginBottom": "10px", "textAlign": "center"},
    ),
    dcc.Store(id="camera-store", data=None),
    dcc.Store(id="anatomy-camera-store", data=None),
    dcc.Store(id="surface-selection-store", data=SURFACE_SELECTION_DEFAULT),
    dcc.Store(id="translation-store", data={
        "anterior": 0,
        "lateral": 0,
    }),
    dcc.Input(id="translation-input", value="0,0", type="text", className="pad-sync-input"),
    dcc.Input(id="rotation-input", value="0,0", type="text", className="pad-sync-input"),
    html.Div(id="pad-client-ready", style={"display": "none"}),
    html.Div([
        dcc.Loading(
            id="model-loading",
            type="default",
            color="rgba(0, 0, 0, 0)",
            children=[html.Div(id="model-loading-message", className="visual-loading-target")],
        ),
    ], className="visual-loading-overlay"),
    html.Div([
        html.Div([
            html.Label("Surface X Axis", style={"fontSize": "13px", "fontWeight": "600"}),
            dcc.Dropdown(
                id="surface-x-axis",
                options=SURFACE_DOF_DROPDOWN_OPTIONS,
                value="adduction",
                clearable=False,
                searchable=False,
                style={"fontSize": "13px"},
            ),
        ], style={"width": "220px"}),
        html.Div([
            html.Label("Surface Y Axis", style={"fontSize": "13px", "fontWeight": "600"}),
            dcc.Dropdown(
                id="surface-y-axis",
                options=SURFACE_DOF_DROPDOWN_OPTIONS,
                value="internal_rotation",
                clearable=False,
                searchable=False,
                style={"fontSize": "13px"},
            ),
        ], style={"width": "220px"}),
    ], className="surface-axis-controls", style={
        "display": "flex",
        "gap": "12px",
        "justifyContent": "center",
        "alignItems": "end",
        "margin": "0 auto 6px",
        "flexWrap": "wrap",
    }),
    html.Div([
        html.Div([
            html.Div([
                dcc.Graph(
                    id="surface-plot-pl",
                    style={
                        "width": "100%",
                        "height": "29.5vh",
                        "margin": "auto",
                        "marginTop": "0px",
                        "marginBottom": "0px",
                    },
                    config=INTERACTIVE_3D_GRAPH_CONFIG,
                ),
                dcc.Graph(
                    id="surface-plot-am",
                    style={
                        "width": "100%",
                        "height": "29.5vh",
                        "margin": "auto",
                        "marginTop": "4px",
                        "marginBottom": "0px",
                    },
                    config=INTERACTIVE_3D_GRAPH_CONFIG,
                ),
            ], className="surface-plots", style={"flex": "1 1 auto", "minWidth": "0"}),
            html.Div(id="surface-strain-legend", style={
                "flex": "0 0 58px",
                "height": "60vh",
                "padding": "4px 0",
                "boxSizing": "border-box",
            }),
        ], className="surface-panel", style={
            "flex": "0 1 calc(40% - 6px)",
            "minWidth": "430px",
            "display": "flex",
            "gap": "6px",
            "alignItems": "stretch",
        }),
        html.Div([
            html.Div([
                dcc.Graph(
                    id="anatomy-plot",
                    style={
                        "width": "100%",
                        "height": "60vh",
                        "margin": "auto",
                        "marginTop": "0px",
                        "marginBottom": "0px",
                    },
                    config=INTERACTIVE_3D_GRAPH_CONFIG,
                ),
            ], className="anatomy-panel", style={"flex": "1 1 0", "minWidth": "280px"}),
            html.Div([
                dcc.Graph(
                    id="fiber-plot",
                    style={
                        "width": "100%",
                        "height": "60vh",
                        "margin": "auto",
                        "marginTop": "0px",
                        "marginBottom": "0px",
                    },
                    config=STATIC_GRAPH_CONFIG,
                ),
            ], className="fiber-panel", style={"flex": "1 1 0", "minWidth": "280px"}),
        ], className="model-fiber-panel", style={
            "flex": "0 1 calc(60% - 6px)",
            "minWidth": "620px",
            "display": "flex",
            "gap": "8px",
            "alignItems": "stretch",
        }),
    ], className="visual-dashboard", style={
        "display": "flex",
        "gap": "12px",
        "alignItems": "stretch",
        "width": "100%",
        "margin": "auto",
        "padding": "0px",
        "marginTop": "0px",
        "marginBottom": "0px",
        "flexWrap": "wrap",
    }),
    html.Div([
        html.Label(scroll_bar1_label, style={"fontSize": "16px"}),
        dcc.Slider(
            id="flexion-slider",
            min=0,
            max=len(FLEXION_VALUES) - 1,
            value=0,
            step=1,
            marks={i: str(val) for i, val in enumerate(FLEXION_VALUES) if val % 10 == 0},
            included=False,
        ),
    ], className="flexion-control", style={
        "padding": "0px",
        "marginTop": "0px",
        "width": "50vw",
        "minWidth": "360px",
        "margin": "auto",
    }),
    html.Div(id="translation-readout", className="kinematic-readout", style={
        "margin": "10px auto 4px",
        "width": "72vw",
        "minWidth": "360px",
        "maxWidth": "860px",
    }),
    html.Div([
        html.Button(
            "Reset",
            id="reset-kinematics",
            n_clicks=0,
            style={
                "fontSize": "14px",
                "padding": "6px 14px",
                "border": "1px solid #8f8f8f",
                "background": "#ffffff",
                "borderRadius": "4px",
                "cursor": "pointer",
            },
        ),
    ], className="reset-row", style={
        "display": "flex",
        "justifyContent": "center",
        "margin": "4px auto 0",
    }),
    html.Div([
        html.Div([
            html.Div(translation_pad_y_label, className="pad-axis-label pad-axis-label-y"),
            html.Div(
                id="translation-pad-control",
                children=[
                    html.Div("-10", className="pad-label pad-label-left y-label-bottom"),
                    html.Div("0", className="pad-label pad-label-left y-label-middle"),
                    html.Div("10", className="pad-label pad-label-left y-label-top"),
                    html.Div("-10", className="pad-label x-label-bottom x-label-left"),
                    html.Div("0", className="pad-label x-label-bottom x-label-center"),
                    html.Div("10", className="pad-label x-label-bottom x-label-right"),
                    html.Div(id="translation-dot", className="translation-dot pad-dot"),
                ],
                className="kinematic-pad-control",
                **{
                    "data-pad-kind": "translation",
                    "data-input-id": "translation-input",
                    "data-store-id": "translation-store",
                    "data-dot-id": "translation-dot",
                    "data-x-key": "lateral",
                    "data-y-key": "anterior",
                    "data-input-order": "y,x",
                    "data-x-min": min(LATERAL_TRANSLATION_VALUES),
                    "data-x-max": max(LATERAL_TRANSLATION_VALUES),
                    "data-x-step": LATERAL_TRANSLATION_VALUES[1] - LATERAL_TRANSLATION_VALUES[0],
                    "data-y-min": min(ANTERIOR_TRANSLATION_VALUES),
                    "data-y-max": max(ANTERIOR_TRANSLATION_VALUES),
                    "data-y-step": ANTERIOR_TRANSLATION_VALUES[1] - ANTERIOR_TRANSLATION_VALUES[0],
                },
            ),
            html.Div(translation_pad_x_label, className="pad-axis-label pad-axis-label-x"),
        ], className="translation-pad-wrap", style={"flex": "0 0 320px"}),
        html.Div([
            html.Div(rotation_pad_y_label, className="pad-axis-label pad-axis-label-y"),
            html.Div(
                id="rotation-pad-control",
                children=[
                    html.Div("-20", className="pad-label pad-label-left y-label-bottom"),
                    html.Div("0", className="pad-label pad-label-left y-label-middle"),
                    html.Div("20", className="pad-label pad-label-left y-label-top"),
                    html.Div("-20", className="pad-label x-label-bottom x-label-left"),
                    html.Div("0", className="pad-label x-label-bottom x-label-center"),
                    html.Div("20", className="pad-label x-label-bottom x-label-right"),
                    html.Div(id="rotation-dot", className="translation-dot pad-dot rotation-dot"),
                ],
                className="kinematic-pad-control",
                **{
                    "data-pad-kind": "rotation",
                    "data-input-id": "rotation-input",
                    "data-store-id": "surface-selection-store",
                    "data-dot-id": "rotation-dot",
                    "data-x-key": "adduction",
                    "data-y-key": "rotation",
                    "data-input-order": "x,y",
                    "data-x-min": min(ADDUCTION_VALUES),
                    "data-x-max": max(ADDUCTION_VALUES),
                    "data-x-step": ADDUCTION_VALUES[1] - ADDUCTION_VALUES[0],
                    "data-y-min": min(INTERNAL_ROTATION_VALUES),
                    "data-y-max": max(INTERNAL_ROTATION_VALUES),
                    "data-y-step": INTERNAL_ROTATION_VALUES[1] - INTERNAL_ROTATION_VALUES[0],
                },
            ),
            html.Div(rotation_pad_x_label, className="pad-axis-label pad-axis-label-x"),
        ], className="translation-pad-wrap rotation-pad-wrap", style={"flex": "0 0 320px"}),
        html.Div([
            html.Label(proximal_slider_label, style={"fontSize": "16px"}),
            html.Div("Proximal (+)", style={"fontSize": "13px", "color": "#4f4f4f"}),
            dcc.Slider(
                id="proximal-slider",
                min=0,
                max=len(PROXIMAL_TRANSLATION_VALUES) - 1,
                value=PROXIMAL_TRANSLATION_VALUES.index(0),
                marks={i: str(val) for i, val in enumerate(PROXIMAL_TRANSLATION_VALUES)},
                step=None,
                included=False,
                vertical=True,
                verticalHeight=220,
            ),
            html.Div("Distal (-)", style={"fontSize": "13px", "color": "#4f4f4f"}),
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "gap": "8px",
            "flex": "0 0 240px",
            "padding": "8px 16px",
        }),
    ], id="translation-controls", style={
        "display": "flex",
        "gap": "28px",
        "alignItems": "center",
        "justifyContent": "center",
        "padding": "8px 0 0",
        "width": "100%",
        "margin": "auto",
        "flexWrap": "wrap",
    }),
    make_regression_equation_section(),
], className="app-root")


app.clientside_callback(
    """
    function(translationValue, rotationValue) {
        return "";
    }
    """,
    Output("pad-client-ready", "children"),
    Input("translation-input", "value"),
    Input("rotation-input", "value"),
)


@app.callback(
    Output("translation-store", "data"),
    Input("translation-input", "value"),
    Input("reset-kinematics", "n_clicks"),
    State("translation-store", "data"),
)
def update_translation_store(translation_value, reset_clicks, current_translation):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if trigger == "reset-kinematics":
        return {
            "anterior": 0,
            "lateral": 0,
        }

    if not translation_value:
        return normalized_translation(current_translation)

    try:
        anterior_value, lateral_value = [
            float(value)
            for value in translation_value.split(",", maxsplit=1)
        ]
    except ValueError:
        return normalized_translation(current_translation)

    return {
        "anterior": snap_to_values(anterior_value, ANTERIOR_TRANSLATION_VALUES),
        "lateral": snap_to_values(lateral_value, LATERAL_TRANSLATION_VALUES),
    }


@app.callback(
    Output("flexion-slider", "value"),
    Output("proximal-slider", "value"),
    Output("translation-input", "value"),
    Output("rotation-input", "value"),
    Input("reset-kinematics", "n_clicks"),
    prevent_initial_call=True,
)
def reset_kinematic_configuration(reset_clicks):
    return (
        FLEXION_VALUES.index(0),
        PROXIMAL_TRANSLATION_VALUES.index(0),
        "0,0",
        "0,0",
    )


@app.callback(
    Output("translation-readout", "children"),
    Output("translation-controls", "style"),
    Input("flexion-slider", "value"),
    Input("translation-store", "data"),
    Input("proximal-slider", "value"),
    Input("surface-selection-store", "data"),
)
def update_translation_controls(flexion_ix, translation, proximal_ix, surface_selection):
    flexion = FLEXION_VALUES[flexion_ix]
    translation = normalized_translation(translation)
    anterior_translation = translation["anterior"]
    lateral_translation = translation["lateral"]
    proximal_translation = PROXIMAL_TRANSLATION_VALUES[proximal_ix]
    surface_selection = surface_selection or SURFACE_SELECTION_DEFAULT
    adduction = surface_selection["adduction"]
    rotation = surface_selection["rotation"]

    style = {
        "display": "flex",
        "gap": "28px",
        "alignItems": "center",
        "justifyContent": "center",
        "padding": "8px 0 0",
        "width": "100%",
        "margin": "auto",
        "flexWrap": "wrap",
    }

    readout = html.Div([
        html.Div("Current Kinematics", style={
            "fontSize": "13px",
            "fontWeight": "650",
            "color": "#333333",
            "textAlign": "center",
            "marginBottom": "6px",
        }),
        html.Div([
            make_kinematic_readout_item("Flexion", flexion, "deg"),
            make_kinematic_readout_item("Anterior (+)", anterior_translation, "mm"),
            make_kinematic_readout_item("Lateral (+)", lateral_translation, "mm"),
            make_kinematic_readout_item("Proximal (+)", proximal_translation, "mm"),
            make_kinematic_readout_item("Adduction (+)", adduction, "deg"),
            make_kinematic_readout_item("Internal Rotation (+)", rotation, "deg"),
        ], style={
            "display": "flex",
            "gap": "8px",
            "justifyContent": "center",
            "alignItems": "stretch",
            "flexWrap": "wrap",
        }),
    ])

    return readout, style


@app.callback(
    Output("surface-selection-store", "data"),
    Input("rotation-input", "value"),
    Input("reset-kinematics", "n_clicks"),
    State("surface-selection-store", "data"),
)
def update_surface_selection(rotation_value, reset_clicks, current_selection):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if trigger == "reset-kinematics":
        return SURFACE_SELECTION_DEFAULT

    if not rotation_value:
        return current_selection or SURFACE_SELECTION_DEFAULT

    try:
        adduction_value, rotation_value = [
            float(value)
            for value in rotation_value.split(",", maxsplit=1)
        ]
    except ValueError:
        return current_selection or SURFACE_SELECTION_DEFAULT

    return {
        "adduction": snap_to_values(adduction_value, ADDUCTION_VALUES),
        "rotation": snap_to_values(rotation_value, INTERNAL_ROTATION_VALUES),
    }


def make_surface_figure(
    model_mode,
    bundle,
    current_values,
    x_axis,
    y_axis,
    camera,
    z_range,
    z_matrix,
    showscale,
):
    z_axis_label = "Strain (%)"
    global_min, global_max = z_range
    x_definition = SURFACE_DOF_OPTIONS[x_axis]
    y_definition = SURFACE_DOF_OPTIONS[y_axis]
    x_values = x_definition["values"]
    y_values = y_definition["values"]
    selected_x = current_values[x_axis]
    selected_y = current_values[y_axis]
    contour_values = surface_contour_values(z_range)
    contour_size = contour_values[1] - contour_values[0]
    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=x_values,
        y=y_values,
        z=z_matrix,
        colorscale="Balance",
        cmin=global_min,
        cmax=global_max,
        connectgaps=True,
        opacity=1.0,
        showscale=showscale,
        contours=dict(
            z=dict(
                show=True,
                usecolormap=True,
                highlightcolor="#ffffff",
                highlightwidth=4,
                start=contour_values[0],
                end=contour_values[-1],
                size=contour_size,
                width=3,
                project=dict(z=True),
            ),
        ),
        colorbar=dict(
            title=dict(text="Strain (%)", font=dict(size=11)),
            tickfont=dict(size=10),
            len=0.72,
            thickness=9,
            x=0.93,
            xpad=2,
        ),
    ))
    fig.add_trace(go.Surface(
        x=x_values,
        y=y_values,
        z=np.zeros_like(z_matrix, dtype=float),
        surfacecolor=np.zeros_like(z_matrix, dtype=float),
        colorscale=[[0.0, "#ffffff"], [1.0, "#ffffff"]],
        cmin=0,
        cmax=1,
        opacity=0.26,
        showscale=False,
        hoverinfo="skip",
        name="0% strain plane",
        contours=dict(z=dict(show=False)),
    ))
    selected_strain = calculate_placeholder_strain(
        model_mode=model_mode,
        bundle=bundle,
        **current_values,
    )
    fig.add_trace(go.Scatter3d(
        x=[selected_x],
        y=[selected_y],
        z=[selected_strain],
        mode="markers",
        marker=dict(size=5, color="#111111", line=dict(width=2, color="#ffffff")),
        name="Selected kinematics",
        hovertemplate=(
            f"{x_definition['label']}: %{{x}} {x_definition['unit']}<br>"
            f"{y_definition['label']}: %{{y}} {y_definition['unit']}<br>"
            "Strain: %{z:.2f}%<extra></extra>"
        ),
        showlegend=False,
    ))
    fig.update_layout(
        scene=dict(
            zaxis_title=z_axis_label,
            xaxis=dict(
                title=dict(text=surface_axis_title(x_axis), font=dict(size=10)),
                tickfont=dict(size=11),
                tickvals=list(x_definition["ticks"]),
                ticks="outside",
                ticklen=0,
                range=[min(x_values), max(x_values)],
            ),
            yaxis=dict(
                title=dict(text=surface_axis_title(y_axis), font=dict(size=10)),
                tickfont=dict(size=11),
                tickvals=list(y_definition["ticks"]),
                ticks="outside",
                ticklen=0,
                range=[min(y_values), max(y_values)],
            ),
            zaxis=dict(
                title=dict(text=z_axis_label, font=dict(size=10)),
                tickfont=dict(size=11),
                ticks="outside",
                ticklen=0,
                range=[global_min, global_max],
            ),
            aspectmode="cube",
            camera=camera,
        ),
        margin=dict(l=34, r=2, t=4, b=24),
        uirevision=f"surface-{bundle}",
        annotations=[
            dict(
                x=0,
                y=0.5,
                xref="paper",
                yref="paper",
                text=bundle,
                showarrow=False,
                textangle=-90,
                font=dict(size=16, color="#222222"),
                xanchor="left",
                yanchor="middle",
            )
        ],
    )
    return fig


@app.callback(
    Output("camera-store", "data"),
    Input("surface-plot-pl", "relayoutData"),
    Input("surface-plot-am", "relayoutData"),
    State("camera-store", "data"),
)
def store_surface_camera(pl_relayout_data, am_relayout_data, stored_camera):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    relayout_data = am_relayout_data if trigger == "surface-plot-am" else pl_relayout_data
    if relayout_data and "scene.camera" in relayout_data:
        return relayout_data["scene.camera"]
    return stored_camera


@app.callback(
    Output("surface-y-axis", "options"),
    Output("surface-y-axis", "value"),
    Input("surface-x-axis", "value"),
    State("surface-y-axis", "value"),
)
def update_surface_y_axis_options(x_axis, current_y_axis):
    if not x_axis:
        x_axis = "adduction"
    if not current_y_axis or current_y_axis == x_axis:
        current_y_axis = fallback_surface_axis(x_axis)
    return surface_dof_dropdown_options(disabled_axis=x_axis), current_y_axis


@app.callback(
    Output("surface-plot-pl", "figure"),
    Output("surface-plot-am", "figure"),
    Output("surface-strain-legend", "children"),
    [
        Input("flexion-slider", "value"),
        Input("translation-store", "data"),
        Input("proximal-slider", "value"),
        Input("surface-selection-store", "data"),
        Input("surface-x-axis", "value"),
        Input("surface-y-axis", "value"),
    ],
    State("camera-store", "data"),
)
def update_surface_plots(
    flexion_ix,
    translation,
    proximal_ix,
    surface_selection,
    x_axis,
    y_axis,
    stored_camera,
):
    flexion = FLEXION_VALUES[flexion_ix]
    translation = normalized_translation(translation)
    anterior_translation = translation["anterior"]
    lateral_translation = translation["lateral"]
    proximal_translation = PROXIMAL_TRANSLATION_VALUES[proximal_ix]
    model_mode = "6DOF"
    surface_selection = surface_selection or SURFACE_SELECTION_DEFAULT
    selected_adduction = surface_selection["adduction"]
    selected_rotation = surface_selection["rotation"]
    x_axis = x_axis if x_axis in SURFACE_DOF_OPTIONS else "adduction"
    y_axis = y_axis if y_axis in SURFACE_DOF_OPTIONS else "internal_rotation"
    if y_axis == x_axis:
        y_axis = fallback_surface_axis(x_axis)
    current_values = current_surface_values(
        flexion=flexion,
        adduction=selected_adduction,
        internal_rotation=selected_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )

    camera = stored_camera if stored_camera else SURFACE_CAMERA

    surface_pl_z = get_z_matrix(
        model_mode=model_mode,
        bundle="ACLpl",
        x_axis=x_axis,
        y_axis=y_axis,
        flexion=flexion,
        adduction=selected_adduction,
        internal_rotation=selected_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )
    surface_am_z = get_z_matrix(
        model_mode=model_mode,
        bundle="ACLam",
        x_axis=x_axis,
        y_axis=y_axis,
        flexion=flexion,
        adduction=selected_adduction,
        internal_rotation=selected_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )
    shared_z_range = shared_z_range_for_surfaces(surface_pl_z, surface_am_z)

    surface_pl_fig = make_surface_figure(
        model_mode=model_mode,
        bundle="ACLpl",
        current_values=current_values,
        x_axis=x_axis,
        y_axis=y_axis,
        camera=camera,
        z_range=shared_z_range,
        z_matrix=surface_pl_z,
        showscale=False,
    )
    surface_am_fig = make_surface_figure(
        model_mode=model_mode,
        bundle="ACLam",
        current_values=current_values,
        x_axis=x_axis,
        y_axis=y_axis,
        camera=camera,
        z_range=shared_z_range,
        z_matrix=surface_am_z,
        showscale=False,
    )
    surface_legend = make_surface_legend(shared_z_range)

    return surface_pl_fig, surface_am_fig, surface_legend


@app.callback(
    Output("anatomy-plot", "figure"),
    Output("fiber-plot", "figure"),
    Output("model-loading-message", "children"),
    [
        Input("flexion-slider", "value"),
        Input("translation-store", "data"),
        Input("proximal-slider", "value"),
        Input("surface-selection-store", "data"),
    ],
    State("anatomy-camera-store", "data"),
)
def update_anatomy_and_fibers(
    flexion_ix,
    translation,
    proximal_ix,
    surface_selection,
    stored_anatomy_camera,
):
    flexion = FLEXION_VALUES[flexion_ix]
    translation = normalized_translation(translation)
    anterior_translation = translation["anterior"]
    lateral_translation = translation["lateral"]
    proximal_translation = PROXIMAL_TRANSLATION_VALUES[proximal_ix]
    model_mode = "6DOF"
    surface_selection = surface_selection or SURFACE_SELECTION_DEFAULT
    selected_adduction = surface_selection["adduction"]
    selected_rotation = surface_selection["rotation"]
    anatomy_camera = stored_anatomy_camera if stored_anatomy_camera else ANTERIOR_ANATOMY_CAMERA

    anatomy_fig = make_anatomy_figure(
        flexion=flexion,
        adduction=selected_adduction,
        internal_rotation=selected_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
        camera=anatomy_camera,
    )
    fiber_fig = make_fiber_panel_figure(
        model_mode=model_mode,
        flexion=flexion,
        adduction=selected_adduction,
        internal_rotation=selected_rotation,
        anterior_translation=anterior_translation,
        lateral_translation=lateral_translation,
        proximal_translation=proximal_translation,
    )

    return anatomy_fig, fiber_fig, ""


@app.callback(
    Output("anatomy-camera-store", "data"),
    Input("anatomy-plot", "relayoutData"),
    State("anatomy-camera-store", "data"),
)
def store_anatomy_camera(anatomy_relayout_data, stored_anatomy_camera):
    if anatomy_relayout_data and "scene.camera" in anatomy_relayout_data:
        return anatomy_relayout_data["scene.camera"]
    return stored_anatomy_camera


if __name__ == "__main__":
    app.run(debug=True)
