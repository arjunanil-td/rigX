"""Generate simple controller icons (circle, square, cube) as transparent PNGs.

Outputs will be written to the repository's `config/icons` directory with
filenames like `rigX_ctrl_{shape}_{size}.png` for sizes 32 and 64.

Usage:
  python scripts/generate_controller_icons.py
"""

from __future__ import annotations

import os
from typing import Tuple

try:
    from PIL import Image, ImageDraw
except Exception as import_error:  # pragma: no cover
    raise SystemExit(
        "Pillow (PIL) is required. Install with: python -m pip install --user pillow\n"
        f"Original import error: {import_error}"
    )


def ensure_directory(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def create_blank_image(size: int) -> Image.Image:
    # RGBA image with full transparency
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def draw_circle(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.12)))
    bbox = (margin, margin, size - margin, size - margin)
    draw.ellipse(bbox, outline=stroke_rgba, width=stroke_width)


def draw_square(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.18)))
    bbox = (margin, margin, size - margin, size - margin)
    draw.rectangle(bbox, outline=stroke_rgba, width=stroke_width)


def draw_triangle(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    """Draw an upright isosceles triangle outline."""
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.18)))
    width = size - 2 * margin
    height = size - 2 * margin
    # Points: apex top-center, base left and right
    apex = (margin + width // 2, margin)
    left = (margin, margin + height)
    right = (margin + width, margin + height)
    draw.line([left, apex, right, left], fill=stroke_rgba, width=stroke_width)


def draw_sphere(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    """Draw a sphere suggestion: circle with latitude/longitude arcs."""
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.12)))
    bbox = (margin, margin, size - margin, size - margin)
    # Outer circle
    draw.ellipse(bbox, outline=stroke_rgba, width=stroke_width)
    # Horizontal (equator) ellipse
    equator_margin_y = int(round((size - 2 * margin) * 0.3))
    equator_bbox = (margin, margin + equator_margin_y, size - margin, size - margin - equator_margin_y)
    draw.ellipse(equator_bbox, outline=stroke_rgba, width=stroke_width)
    # Vertical (meridian) ellipse
    equator_margin_x = int(round((size - 2 * margin) * 0.3))
    meridian_bbox = (margin + equator_margin_x, margin, size - margin - equator_margin_x, size - margin)
    draw.ellipse(meridian_bbox, outline=stroke_rgba, width=stroke_width)


def draw_pyramid(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    """Draw a simple pyramid (triangular) front with back edge hint."""
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.16)))
    width = size - 2 * margin
    height = size - 2 * margin
    apex = (margin + width // 2, margin)
    left_base = (margin, margin + height)
    right_base = (margin + width, margin + height)
    # Front face triangle
    draw.line([left_base, apex, right_base, left_base], fill=stroke_rgba, width=stroke_width)
    # Interior edges to suggest depth
    mid_base = (margin + width // 2, margin + height)
    draw.line([apex, mid_base], fill=stroke_rgba, width=stroke_width)


def draw_cube(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    """Draw a simple isometric cube wireframe.

    The geometry is proportionally scaled to the icon size.
    """
    stroke_width = 2 if size >= 64 else 1

    # Margins and offset tuned for a recognizable cube silhouette at small sizes
    margin = max(2, int(round(size * 0.16)))
    offset = max(3, int(round(size * 0.22)))

    w = size

    # Front face square
    a = (margin, margin + offset)
    b = (w - margin - offset, margin + offset)
    c = (w - margin - offset, w - margin)
    d = (margin, w - margin)

    # Top face points (projected upwards/right)
    a_top = (a[0] + offset, a[1] - offset)
    b_top = (b[0] + offset, b[1] - offset)
    # Right face vertical extent matches front's height
    c_top = (b_top[0], b_top[1] + (c[1] - b[1]))

    # Front face
    draw.line([a, b], fill=stroke_rgba, width=stroke_width)
    draw.line([b, c], fill=stroke_rgba, width=stroke_width)
    draw.line([c, d], fill=stroke_rgba, width=stroke_width)
    draw.line([d, a], fill=stroke_rgba, width=stroke_width)

    # Top face
    draw.line([a, a_top], fill=stroke_rgba, width=stroke_width)
    draw.line([b, b_top], fill=stroke_rgba, width=stroke_width)
    draw.line([a_top, b_top], fill=stroke_rgba, width=stroke_width)

    # Right face
    draw.line([b_top, c_top], fill=stroke_rgba, width=stroke_width)
    draw.line([c, c_top], fill=stroke_rgba, width=stroke_width)


def save_icon(image: Image.Image, output_dir: str, shape_name: str, size: int, prefix: str = "ctrl") -> str:
    ensure_directory(output_dir)
    filename = f"rigX_{prefix}_{shape_name}_{size}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath, format="PNG")
    return filepath


# ========== Additional shapes for "More" dialog ==========
def draw_fatcross(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    # Use thick bars (filled rectangles) to form a cross
    margin = max(2, int(round(size * 0.12)))
    bar = max(3, int(round(size * 0.28)))
    # Horizontal bar
    left = margin
    right = size - margin
    cy = size // 2
    draw.rectangle([left, cy - bar // 2, right, cy + bar // 2], outline=stroke_rgba, fill=None, width=2)
    # Vertical bar
    cx = size // 2
    draw.rectangle([cx - bar // 2, margin, cx + bar // 2, size - margin], outline=stroke_rgba, fill=None, width=2)


def draw_cone(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.16)))
    width = size - 2 * margin
    height = size - 2 * margin
    apex = (margin + width // 2, margin)
    left = (margin, margin + height - 1)
    right = (margin + width, margin + height - 1)
    # Triangle sides
    draw.line([left, apex, right], fill=stroke_rgba, width=stroke_width)
    # Base arc (ellipse segment)
    base_bbox = (margin, margin + height - height // 6, margin + width, margin + height + height // 6)
    draw.ellipse(base_bbox, outline=stroke_rgba, width=stroke_width)


def draw_rombus(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    # Diamond shape
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.18)))
    cx = size // 2
    cy = size // 2
    dx = size // 2 - margin
    dy = size // 2 - margin
    pts = [(cx, cy - dy), (cx + dx, cy), (cx, cy + dy), (cx - dx, cy), (cx, cy - dy)]
    draw.line(pts, fill=stroke_rgba, width=stroke_width)


def draw_singlenormal(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    # Upward arrow from center-bottom
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.18)))
    cx = size // 2
    bottom = size - margin
    top = margin
    draw.line([ (cx, bottom), (cx, top) ], fill=stroke_rgba, width=stroke_width)
    # Arrow head
    head_w = max(4, int(round(size * 0.16)))
    draw.line([ (cx, top), (cx - head_w//2, top + head_w) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, top), (cx + head_w//2, top + head_w) ], fill=stroke_rgba, width=stroke_width)


def draw_fournormal(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    # Arrows up/down/left/right from center
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.20)))
    cx = size // 2
    cy = size // 2
    # Up
    draw.line([ (cx, cy), (cx, margin) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, margin), (cx - 5, margin + 8) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, margin), (cx + 5, margin + 8) ], fill=stroke_rgba, width=stroke_width)
    # Down
    draw.line([ (cx, cy), (cx, size - margin) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, size - margin), (cx - 5, size - margin - 8) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, size - margin), (cx + 5, size - margin - 8) ], fill=stroke_rgba, width=stroke_width)
    # Left
    draw.line([ (cx, cy), (margin, cy) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (margin, cy), (margin + 8, cy - 5) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (margin, cy), (margin + 8, cy + 5) ], fill=stroke_rgba, width=stroke_width)
    # Right
    draw.line([ (cx, cy), (size - margin, cy) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (size - margin, cy), (size - margin - 8, cy - 5) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (size - margin, cy), (size - margin - 8, cy + 5) ], fill=stroke_rgba, width=stroke_width)


def draw_dumbell(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.18)))
    r = max(3, int(round(size * 0.14)))
    y = size // 2
    left_x = margin + r
    right_x = size - margin - r
    # Connect bar
    draw.line([ (left_x, y), (right_x, y) ], fill=stroke_rgba, width=stroke_width)
    # End circles
    draw.ellipse([left_x - r, y - r, left_x + r, y + r], outline=stroke_rgba, width=stroke_width)
    draw.ellipse([right_x - r, y - r, right_x + r, y + r], outline=stroke_rgba, width=stroke_width)


def draw_arrowonball(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    margin = max(2, int(round(size * 0.14)))
    bbox = (margin, margin, size - margin, size - margin)
    draw.ellipse(bbox, outline=stroke_rgba, width=stroke_width)
    # Arrow pointing northeast
    cx = size // 2
    cy = size // 2
    tip = (size - margin, margin)
    draw.line([ (cx, cy), tip ], fill=stroke_rgba, width=stroke_width)
    draw.line([ tip, (tip[0] - 10, tip[1] + 4) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ tip, (tip[0] - 4, tip[1] + 10) ], fill=stroke_rgba, width=stroke_width)


def draw_pin(draw: ImageDraw.ImageDraw, size: int, stroke_rgba: Tuple[int, int, int, int]) -> None:
    stroke_width = 2 if size >= 64 else 1
    cx = size // 2
    margin = max(2, int(round(size * 0.18)))
    # Head (circle)
    r = max(4, int(round(size * 0.16)))
    head_center = (cx, margin + r)
    draw.ellipse([head_center[0] - r, head_center[1] - r, head_center[0] + r, head_center[1] + r], outline=stroke_rgba, width=stroke_width)
    # Body (triangle-ish)
    tip_y = size - margin
    draw.line([ (cx, head_center[1] + r), (cx, tip_y) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, tip_y), (cx - 5, tip_y - 8) ], fill=stroke_rgba, width=stroke_width)
    draw.line([ (cx, tip_y), (cx + 5, tip_y - 8) ], fill=stroke_rgba, width=stroke_width)


def generate_icons() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    output_dir = os.path.join(repo_root, "config", "icons")

    sizes = [64]

    # A bright cyan commonly used in rig UIs, readable on dark/neutral backgrounds
    stroke = (0, 200, 255, 255)  # RGBA

    draw_ops = {
        "circle": draw_circle,
        "square": draw_square,
        "triangle": draw_triangle,
        "sphere": draw_sphere,
        "pyramid": draw_pyramid,
        "cube": draw_cube,
        # More dialog shapes
        "fatcross": draw_fatcross,
        "cone": draw_cone,
        "rombus": draw_rombus,
        "singlenormal": draw_singlenormal,
        "fournormal": draw_fournormal,
        "dumbell": draw_dumbell,
        "arrowonball": draw_arrowonball,
        "pin": draw_pin,
    }

    written: list[str] = []
    for size in sizes:
        for shape_name, drawer in draw_ops.items():
            img = create_blank_image(size)
            draw = ImageDraw.Draw(img)
            drawer(draw, size, stroke)
            path = save_icon(img, output_dir, shape_name, size, prefix="ctrl")
            written.append(os.path.relpath(path, repo_root))

    # Quick tool icons for joints section
    def draw_curve_to_joint(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        stroke_width = 2 if size >= 64 else 1
        margin = max(2, int(round(size * 0.14)))
        # Curvy path
        points = [
            (margin, size - margin),
            (size * 0.35, size * 0.6),
            (size * 0.55, size * 0.4),
            (size - margin, margin),
        ]
        # Approximate smooth curve using polyline segments
        draw.line(points, fill=color, width=stroke_width)
        # Small joints along the path
        r = max(2, int(round(size * 0.06)))
        for (x, y) in points:
            x = int(x)
            y = int(y)
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=stroke_width)

    def draw_inbetween_joints(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        stroke_width = 2 if size >= 64 else 1
        margin = max(2, int(round(size * 0.14)))
        y = size // 2
        r = max(3, int(round(size * 0.10)))
        left_x = margin + r
        right_x = size - margin - r
        # End joints
        draw.ellipse([left_x - r, y - r, left_x + r, y + r], outline=color, width=stroke_width)
        draw.ellipse([right_x - r, y - r, right_x + r, y + r], outline=color, width=stroke_width)
        # Connector line
        draw.line([(left_x + r, y), (right_x - r, y)], fill=color, width=stroke_width)
        # Plus at center
        cx = size // 2
        plus = max(3, int(round(size * 0.12)))
        draw.line([(cx - plus, y), (cx + plus, y)], fill=color, width=stroke_width)
        draw.line([(cx, y - plus), (cx, y + plus)], fill=color, width=stroke_width)

    def _draw_axes(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int], center: Tuple[int, int]) -> None:
        stroke_width = 2 if size >= 64 else 1
        cx, cy = center
        arm = max(6, int(round(size * 0.18)))
        draw.line([(cx, cy), (cx + arm, cy)], fill=color, width=stroke_width)  # X
        draw.line([(cx, cy), (cx, cy - arm)], fill=color, width=stroke_width)  # Y
        draw.line([(cx, cy), (cx + int(arm * 0.6), cy + int(arm * 0.6))], fill=color, width=stroke_width)  # Z

    def _draw_circular_arrow(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int], center: Tuple[int, int]) -> None:
        stroke_width = 2 if size >= 64 else 1
        cx, cy = center
        r = max(8, int(round(size * 0.28)))
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.arc(bbox, start=30, end=300, fill=color, width=stroke_width)
        # Arrow head at approx 30 degrees
        import math
        angle = math.radians(30)
        tip = (int(cx + r * math.cos(angle)), int(cy - r * math.sin(angle)))
        head = max(5, int(round(size * 0.10)))
        draw.line([tip, (tip[0] - head, tip[1] + int(head * 0.4))], fill=color, width=stroke_width)
        draw.line([tip, (tip[0] - int(head * 0.4), tip[1] + head)], fill=color, width=stroke_width)

    def draw_rotation_to_orient(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        # Left: circular arrow, Right: axes, center arrow ->
        _draw_circular_arrow(draw, size, color, (int(size * 0.32), int(size * 0.52)))
        _draw_axes(draw, size, color, (int(size * 0.75), int(size * 0.52)))
        stroke_width = 2 if size >= 64 else 1
        draw.line([(int(size * 0.46), int(size * 0.52)), (int(size * 0.64), int(size * 0.52))], fill=color, width=stroke_width)
        draw.line([(int(size * 0.64), int(size * 0.52)), (int(size * 0.60), int(size * 0.48))], fill=color, width=stroke_width)
        draw.line([(int(size * 0.64), int(size * 0.52)), (int(size * 0.60), int(size * 0.56))], fill=color, width=stroke_width)

    def draw_orient_to_rotation(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        # Left: axes, Right: circular arrow, center arrow ->
        _draw_axes(draw, size, color, (int(size * 0.28), int(size * 0.52)))
        _draw_circular_arrow(draw, size, color, (int(size * 0.72), int(size * 0.52)))
        stroke_width = 2 if size >= 64 else 1
        draw.line([(int(size * 0.40), int(size * 0.52)), (int(size * 0.58), int(size * 0.52))], fill=color, width=stroke_width)
        draw.line([(int(size * 0.58), int(size * 0.52)), (int(size * 0.54), int(size * 0.48))], fill=color, width=stroke_width)
        draw.line([(int(size * 0.58), int(size * 0.52)), (int(size * 0.54), int(size * 0.56))], fill=color, width=stroke_width)

    def draw_joint_at_center(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        # Bounding box with crosshair and a center joint dot
        stroke_width = 2 if size >= 64 else 1
        margin = max(3, int(round(size * 0.16)))
        # Bounding rectangle
        bbox = (margin, margin, size - margin, size - margin)
        draw.rectangle(bbox, outline=color, width=stroke_width)
        # Crosshair
        cx = size // 2
        cy = size // 2
        cross = max(6, int(round(size * 0.20)))
        draw.line([(cx - cross, cy), (cx + cross, cy)], fill=color, width=stroke_width)
        draw.line([(cx, cy - cross), (cx, cy + cross)], fill=color, width=stroke_width)
        # Center joint (filled circle)
        r = max(3, int(round(size * 0.10)))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, fill=None, width=stroke_width)

    def draw_modules(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        """Draw a modules icon - stacked boxes representing modular components."""
        stroke_width = 2 if size >= 64 else 1
        margin = max(3, int(round(size * 0.12)))
        
        # Three stacked boxes with slight offset to show modularity
        box_height = max(8, int(round(size * 0.20)))
        box_width = max(12, int(round(size * 0.40)))
        
        # Bottom box
        bottom_y = size - margin - box_height
        bottom_x = margin
        draw.rectangle([bottom_x, bottom_y, bottom_x + box_width, bottom_y + box_height], 
                      outline=color, width=stroke_width)
        
        # Middle box (slightly offset)
        middle_y = bottom_y - box_height - 2
        middle_x = bottom_x + 4
        draw.rectangle([middle_x, middle_y, middle_x + box_width, middle_y + box_height], 
                      outline=color, width=stroke_width)
        
        # Top box (more offset)
        top_y = middle_y - box_height - 2
        top_x = middle_x + 4
        draw.rectangle([top_x, top_y, top_x + box_width, top_y + box_height], 
                      outline=color, width=stroke_width)
        
        # Add small connector dots
        dot_r = max(1, int(round(size * 0.03)))
        # Between bottom and middle
        draw.ellipse([bottom_x + box_width//2 - dot_r, bottom_y - 1 - dot_r, 
                     bottom_x + box_width//2 + dot_r, bottom_y - 1 + dot_r], 
                    outline=color, fill=color, width=stroke_width)
        # Between middle and top
        draw.ellipse([middle_x + box_width//2 - dot_r, middle_y - 1 - dot_r, 
                     middle_x + box_width//2 + dot_r, middle_y - 1 + dot_r], 
                    outline=color, fill=color, width=stroke_width)

    def draw_joint_to_curve(draw: ImageDraw.ImageDraw, size: int, color: Tuple[int, int, int, int]) -> None:
        # Small joint nodes connected by a curve path
        stroke_width = 2 if size >= 64 else 1
        margin = max(2, int(round(size * 0.14)))
        # Joint points roughly diagonal
        points = [
            (margin + int(size * 0.12), size - margin - int(size * 0.18)),
            (int(size * 0.40), int(size * 0.70)),
            (int(size * 0.62), int(size * 0.48)),
            (size - margin - int(size * 0.14), margin + int(size * 0.16)),
        ]
        # Draw joints (small circles)
        r = max(3, int(round(size * 0.08)))
        for (x, y) in points:
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=stroke_width)
        # Connect joints with a polyline to suggest a curve
        draw.line(points, fill=color, width=stroke_width)

    quick_draw_ops = {
        "curveToJoint": draw_curve_to_joint,
        "jointToCurve": draw_joint_to_curve,
        "inbetweenJoints": draw_inbetween_joints,
        "rotationToOrient": draw_rotation_to_orient,
        "orientToRotation": draw_orient_to_rotation,
        "jointAtCenter": draw_joint_at_center,
        "modules": draw_modules,
    }

    for size in sizes:
        for quick_name, drawer in quick_draw_ops.items():
            img = create_blank_image(size)
            draw = ImageDraw.Draw(img)
            drawer(draw, size, stroke)
            path = save_icon(img, output_dir, quick_name, size, prefix="quick")
            written.append(os.path.relpath(path, repo_root))

    # === UI-style icons (solid/gradient bg + white glyph) ===
    def _draw_vertical_gradient(bg_img: Image.Image, top_color: Tuple[int, int, int, int], bottom_color: Tuple[int, int, int, int]) -> None:
        width, height = bg_img.size
        draw_bg = ImageDraw.Draw(bg_img)
        for y in range(height):
            t = y / max(1, height - 1)
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            a = int(top_color[3] * (1 - t) + bottom_color[3] * t)
            draw_bg.line([(0, y), (width, y)], fill=(r, g, b, a))

    def _rounded_paste(base: Image.Image, src: Image.Image, radius: int) -> Image.Image:
        mask = Image.new("L", base.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([1, 1, base.width - 2, base.height - 2], radius=max(2, radius), fill=255)
        out = Image.new("RGBA", base.size, (0, 0, 0, 0))
        out.paste(src, (0, 0), mask)
        return out

    def _draw_utils_glyph_white(draw: ImageDraw.ImageDraw, size: int) -> None:
        """Crossed wrench and screwdriver for a clearer 'Tools' icon."""
        white = (255, 255, 255, 255)
        shaft_w = max(4, int(size * 0.07))

        # Wrench (diagonal bottom-left to top-right)
        wx1, wy1 = int(size * 0.20), int(size * 0.74)
        wx2, wy2 = int(size * 0.72), int(size * 0.22)
        draw.line([(wx1, wy1), (wx2, wy2)], fill=white, width=shaft_w)
        # Wrench open head near (wx2, wy2)
        head_r = int(size * 0.10)
        head_box = [wx2 - head_r, wy2 - head_r, wx2 + head_r, wy2 + head_r]
        # Two short arcs to suggest the open-end
        draw.arc(head_box, start=320, end=30, fill=white, width=shaft_w - 1)
        draw.arc(head_box, start=150, end=210, fill=white, width=shaft_w - 1)

        # Screwdriver (diagonal top-left to bottom-right)
        sx1, sy1 = int(size * 0.26), int(size * 0.22)
        sx2, sy2 = int(size * 0.78), int(size * 0.66)
        # Handle (thicker segment near top-left)
        handle_w = shaft_w + 2
        draw.line([(sx1, sy1), (int(sx1 + (sx2 - sx1) * 0.25), int(sy1 + (sy2 - sy1) * 0.25))], fill=white, width=handle_w)
        # Shaft
        draw.line([(int(sx1 + (sx2 - sx1) * 0.25), int(sy1 + (sy2 - sy1) * 0.25)), (sx2, sy2)], fill=white, width=shaft_w - 1)
        # Flat head tip triangle at (sx2, sy2)
        tip = (sx2, sy2)
        tip_w = max(4, int(size * 0.06))
        tip_h = max(4, int(size * 0.05))
        # Oriented approx perpendicular to the shaft direction
        tip_poly = [(tip[0], tip[1]), (tip[0] - tip_w, tip[1] - tip_h), (tip[0] - tip_w, tip[1] + tip_h)]
        draw.polygon(tip_poly, fill=white)

    def _draw_validator_glyph_white(draw: ImageDraw.ImageDraw, size: int) -> None:
        """Circular badge with white ring and bold tick for high legibility."""
        white = (255, 255, 255, 255)
        # Outer ring
        ring_width = max(3, int(round(size * 0.06)))
        margin = int(round(size * 0.18))
        bbox = [margin, margin, size - margin, size - margin]
        draw.ellipse(bbox, outline=white, width=ring_width)

        # Bold tick
        stroke_width = max(5, int(round(size * 0.10)))
        x1 = int(size * 0.28)
        y1 = int(size * 0.54)
        x2 = int(size * 0.44)
        y2 = int(size * 0.70)
        x3 = int(size * 0.76)
        y3 = int(size * 0.32)
        draw.line([(x1, y1), (x2, y2)], fill=white, width=stroke_width)
        draw.line([(x2, y2), (x3, y3)], fill=white, width=stroke_width)

    def _draw_skin_glyph_white(draw: ImageDraw.ImageDraw, size: int) -> None:
        """Bone + brush + target dot (inspired by common weight-paint icons)."""
        white = (255, 255, 255, 255)
        # Bone: angled shaft with rounded ends (thicker for clarity at 64px)
        bx1, by1 = int(size * 0.26), int(size * 0.62)
        bx2, by2 = int(size * 0.64), int(size * 0.36)
        draw.line([(bx1, by1), (bx2, by2)], fill=white, width=7)
        r_knob = int(size * 0.09)
        draw.ellipse([bx1 - r_knob, by1 - r_knob, bx1 + r_knob, by1 + r_knob], fill=white)
        draw.ellipse([bx2 - r_knob, by2 - r_knob, bx2 + r_knob, by2 + r_knob], fill=white)

        # Target dot near mid-bone
        tx, ty = int(size * 0.48), int(size * 0.46)
        r_dot = int(size * 0.04)
        r_ring = int(size * 0.09)
        draw.ellipse([tx - r_dot, ty - r_dot, tx + r_dot, ty + r_dot], fill=white)
        draw.ellipse([tx - r_ring, ty - r_ring, tx + r_ring, ty + r_ring], outline=white, width=2)

        # Brush crossing the bone with clear bristle triangle and ferrule
        hx1, hy1 = int(size * 0.22), int(size * 0.40)
        hx2, hy2 = int(size * 0.52), int(size * 0.70)
        draw.line([(hx1, hy1), (hx2, hy2)], fill=white, width=4)
        # Ferrule (small rectangle at brush head)
        ferrule_w = int(size * 0.05)
        ferrule_h = int(size * 0.02)
        draw.rectangle([hx2 - ferrule_w, hy2 - ferrule_h, hx2, hy2 + ferrule_h], fill=white)
        # Bristles as triangle
        br_w = int(size * 0.12)
        br_h = int(size * 0.07)
        draw.polygon([(hx2, hy2), (hx2 + br_w, hy2 - br_h), (hx2 + br_w, hy2 + br_h)], fill=white)

    # Utility Tools icon
    ui_size = 64
    bg_img = Image.new("RGBA", (ui_size, ui_size), (0, 0, 0, 0))
    # Utils: brand green gradient to match Modules/Skin
    _draw_vertical_gradient(bg_img, (27, 67, 50, 255), (64, 145, 108, 255))
    bg_img = _rounded_paste(bg_img, bg_img, 8)
    glyph = ImageDraw.Draw(bg_img)
    _draw_utils_glyph_white(glyph, ui_size)
    utils_icon_path = os.path.join(output_dir, "rigX_icon_utils.png")
    bg_img.save(utils_icon_path, format="PNG")
    written.append(os.path.relpath(utils_icon_path, repo_root))

    # Validator icon
    bg2 = Image.new("RGBA", (ui_size, ui_size), (0, 0, 0, 0))
    # Validator: brand green gradient
    _draw_vertical_gradient(bg2, (27, 67, 50, 255), (64, 145, 108, 255))
    bg2 = _rounded_paste(bg2, bg2, 8)
    glyph2 = ImageDraw.Draw(bg2)
    _draw_validator_glyph_white(glyph2, ui_size)
    validator_icon_path = os.path.join(output_dir, "rigX_icon_validator.png")
    bg2.save(validator_icon_path, format="PNG")
    written.append(os.path.relpath(validator_icon_path, repo_root))

    # Skin Toolkit icon
    bg3 = Image.new("RGBA", (ui_size, ui_size), (0, 0, 0, 0))
    # Brand green gradient for consistency
    _draw_vertical_gradient(bg3, (27, 67, 50, 255), (64, 145, 108, 255))
    bg3 = _rounded_paste(bg3, bg3, 8)
    glyph3 = ImageDraw.Draw(bg3)
    _draw_skin_glyph_white(glyph3, ui_size)
    skin_icon_path = os.path.join(output_dir, "rigX_icon_skinTools.png")
    bg3.save(skin_icon_path, format="PNG")
    written.append(os.path.relpath(skin_icon_path, repo_root))

    print("Generated icons:")
    for rel in written:
        print(f" - {rel}")


if __name__ == "__main__":
    generate_icons()


