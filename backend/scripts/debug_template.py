#!/usr/bin/env python3
"""Visual debugging tool for template zones - shows what's being extracted."""

import cv2
import numpy as np
import yaml
from pathlib import Path
from PIL import Image

def visualize_template_zones(image_path: str, template_path: str):
    """
    Create a visual overlay showing where template zones are located on the image.

    Args:
        image_path: Path to the receipt image
        template_path: Path to the YAML template file
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    height, width = image.shape[:2]
    print(f"📸 Image size: {width}x{height}")

    # Load template
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)

    template_id = template.get('template_id', 'Unknown')
    expected_size = template.get('image_size', [0, 0])

    print(f"📋 Template: {template_id}")
    print(f"📐 Expected size: {expected_size[0]}x{expected_size[1]}")
    print(f"📊 Size mismatch: {width/expected_size[0]:.2f}x, {height/expected_size[1]:.2f}y")

    # Create a copy for visualization
    vis_image = image.copy()

    # Draw each zone
    zones = template.get('zones', {})
    colors = [
        (0, 0, 255),    # Blue
        (0, 255, 0),    # Green
        (255, 0, 0),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
    ]

    for idx, (zone_name, zone_config) in enumerate(zones.items()):
        # Calculate zone coordinates
        x = int(zone_config.get('x_percent', 0) * width / 100)
        y = int(zone_config.get('y_percent', 0) * height / 100)
        w = int(zone_config.get('width_percent', 0) * width / 100)
        h = int(zone_config.get('height_percent', 0) * height / 100)

        # Draw rectangle
        color = colors[idx % len(colors)]
        cv2.rectangle(vis_image, (x, y), (x + w, y + h), color, 3)

        # Add label
        label = f"{idx+1}. {zone_name}"
        cv2.putText(vis_image, label, (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Extract and show zone content
        zone_img = image[y:y+h, x:x+w]
        zone_info = {
            'name': zone_name,
            'coords': f"({x}, {y}, {w}, {h})",
            'parser': zone_config.get('parser', 'text'),
            'size': f"{w}x{h} pixels"
        }

        print(f"\n📍 Zone {idx+1}: {zone_name}")
        print(f"   Coordinates: {zone_info['coords']}")
        print(f"   Size: {zone_info['size']}")
        print(f"   Parser: {zone_info['parser']}")

        # Save individual zone image
        zone_path = Path(f"debug_zone_{idx+1}_{zone_name}.jpg")
        cv2.imwrite(str(zone_path), zone_img)
        print(f"   Saved zone image: {zone_path}")

    # Save visualization
    output_path = "debug_visualization.jpg"
    cv2.imwrite(output_path, vis_image)
    print(f"\n🎨 Visualization saved: {output_path}")

    # Also create a version with zone numbers only
    simple_vis = image.copy()
    for idx, (zone_name, zone_config) in enumerate(zones.items()):
        x = int(zone_config.get('x_percent', 0) * width / 100)
        y = int(zone_config.get('y_percent', 0) * height / 100)
        w = int(zone_config.get('width_percent', 0) * width / 100)
        h = int(zone_config.get('height_percent', 0) * height / 100)

        cv2.rectangle(simple_vis, (x, y), (x + w, y + h), (255, 255, 255), 2)
        cv2.putText(simple_vis, str(idx+1), (x + w//2 - 10, y + h//2 + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

    cv2.imwrite("debug_simple.jpg", simple_vis)
    print(f"🎨 Simple visualization saved: debug_simple.jpg")

    print(f"\n💡 Next steps:")
    print(f"   1. Open debug_visualization.jpg to see where zones are located")
    print(f"   2. Open debug_zone_*.jpg files to see what each zone contains")
    print(f"   3. If zones are wrong, adjust coordinates in {template_path}")
    print(f"   4. Re-run this script to verify changes")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python debug_template.py <image.jpg> <template.yaml>")
        sys.exit(1)

    visualize_template_zones(sys.argv[1], sys.argv[2])
