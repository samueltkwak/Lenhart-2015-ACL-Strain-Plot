import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_ROOT = WORKSPACE_ROOT / "Geometry"
MODEL_PATH = WORKSPACE_ROOT / "lenhart2015_bilateral_V3D_mod.osim"
OUTPUT_PATH = APP_ROOT / "data" / "anatomy_assets.json"

MESH_SPECS = {
    "femur": ("lenhart2015-R-femur-bone.stl", None, "#e8e2d6", 0.74),
    "tibia": ("lenhart2015-R-tibia-bone.stl", None, "#ded6c8", 0.78),
    "fibula": ("lenhart2015-R-fibula-bone.stl", None, "#d8d0c4", 0.78),
}


def read_binary_stl(path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path} is too small to be a binary STL")

    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if expected_size > len(data):
        raise ValueError(f"{path} does not look like a complete binary STL")

    triangles = []
    offset = 84
    for _ in range(triangle_count):
        offset += 12
        vertices = []
        for _ in range(3):
            vertices.append(struct.unpack_from("<fff", data, offset))
            offset += 12
        offset += 2
        triangles.append(vertices)

    return triangles


def read_ascii_stl(path):
    triangles = []
    current = []

    with path.open("r", encoding="utf-8", errors="ignore") as stl_file:
        for line in stl_file:
            stripped = line.strip()
            if not stripped.startswith("vertex "):
                continue

            current.append(tuple(float(value) for value in stripped.split()[1:4]))
            if len(current) == 3:
                triangles.append(current)
                current = []

    if not triangles:
        raise ValueError(f"{path} does not contain ASCII STL vertices")

    return triangles


def read_stl(path):
    with path.open("rb") as stl_file:
        header = stl_file.read(80)

    if header.lstrip().lower().startswith(b"solid"):
        return read_ascii_stl(path)

    return read_binary_stl(path)


def simplify_triangles(triangles, target_count):
    if target_count is None:
        return triangles

    if len(triangles) <= target_count:
        return triangles

    step = len(triangles) / target_count
    return [
        triangles[min(int(i * step), len(triangles) - 1)]
        for i in range(target_count)
    ]


def mesh_payload(path, target_count, color, opacity):
    triangles = simplify_triangles(read_stl(path), target_count)
    x = []
    y = []
    z = []
    i = []
    j = []
    k = []
    vertex_index = {}

    def add_vertex(vertex):
        key = tuple(round(value, 6) for value in vertex)
        if key in vertex_index:
            return vertex_index[key]

        vertex_index[key] = len(x)
        x.append(key[0])
        y.append(key[1])
        z.append(key[2])
        return vertex_index[key]

    for triangle in triangles:
        triangle_indexes = [add_vertex(vertex) for vertex in triangle]
        i.append(triangle_indexes[0])
        j.append(triangle_indexes[1])
        k.append(triangle_indexes[2])

    return {
        "x": x,
        "y": y,
        "z": z,
        "i": i,
        "j": j,
        "k": k,
        "color": color,
        "opacity": opacity,
    }


def text(element, tag):
    child = element.find(tag)
    return (child.text or "").strip() if child is not None else ""


def vector(text_value):
    return [float(value) for value in text_value.split()]


def acl_payload():
    root = ET.parse(MODEL_PATH).getroot()
    fibers = []

    for ligament in root.findall(".//Blankevoort1991Ligament"):
        name = ligament.attrib.get("name", "")
        if not (name.startswith("ACL") and name.endswith("_r")):
            continue

        points = []
        for path_point in ligament.findall(".//PathPoint"):
            points.append({
                "frame": text(path_point, "socket_parent_frame").split("/")[-1],
                "location": vector(text(path_point, "location")),
            })

        if len(points) == 2:
            fibers.append({"name": name, "points": points})

    return fibers


def main():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    payload = {
        "meshes": {
            name: mesh_payload(GEOMETRY_ROOT / filename, target, color, opacity)
            for name, (filename, target, color, opacity) in MESH_SPECS.items()
        },
        "acl_fibers": acl_payload(),
    }
    OUTPUT_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
