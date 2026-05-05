#!/usr/bin/env python3
"""Adjust template coordinates for different image sizes."""

import yaml
import sys
from pathlib import Path

def adjust_template_coordinates(template_path: str, original_size: list, new_size: list):
    """
    Adjust template coordinates when image size changes.

    Args:
        template_path: Path to YAML template file
        original_size: Original image size [width, height]
        new_size: New image size [width, height]
    """
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)

    # Calculate adjustment factors
    width_factor = new_size[0] / original_size[0]
    height_factor = new_size[1] / original_size[1]

    print(f"📐 Adjusting template from {original_size} to {new_size}")
    print(f"   Width factor: {width_factor:.3f}")
    print(f"   Height factor: {height_factor:.3f}")

    # Update image_size
    template['image_size'] = new_size

    # Adjust logo_region if present
    if 'detection' in template and 'logo_region' in template['detection']:
        logo = template['detection']['logo_region']
        print(f"\n🎯 Logo Region (original):")
        print(f"   x_percent: {logo.get('x_percent')}")
        print(f"   y_percent: {logo.get('y_percent')}")
        print(f"   width_percent: {logo.get('width_percent')}")
        print(f"   height_percent: {logo.get('height_percent')}")

        # Logo regions typically stay at same percentages, but may need adjustment
        # depending on the image resizing method

    # Adjust zones
    if 'zones' in template:
        print(f"\n📍 Adjusting {len(template['zones'])} zones:")
        for zone_name, zone_config in template['zones'].items():
            print(f"   {zone_name}:")
            print(f"     Before: x={zone_config.get('x_percent', 0):.2f}%, y={zone_config.get('y_percent', 0):.2f}%")

            # No adjustment needed for percentages - they automatically scale!
            # But let's verify they're reasonable values

            x = zone_config.get('x_percent', 0)
            y = zone_config.get('y_percent', 0)
            w = zone_config.get('width_percent', 0)
            h = zone_config.get('height_percent', 0)

            # Check if zone fits within image
            if x + w > 100 or y + h > 100:
                print(f"     ⚠️  WARNING: Zone extends beyond image bounds!")
            elif x < 0 or y < 0:
                print(f"     ⚠️  WARNING: Zone has negative coordinates!")

            print(f"     After:  x={x:.2f}%, y={y:.2f}% (same - percentages scale automatically)")

    # Save adjusted template
    backup_path = template_path + '.backup'
    with open(backup_path, 'w') as f:
        yaml.dump(template, f, allow_unicode=True)
    print(f"\n💾 Backup saved to: {backup_path}")

    with open(template_path, 'w') as f:
        yaml.dump(template, f, allow_unicode=True)
    print(f"💾 Template updated: {template_path}")

    print(f"\n✅ Template adjusted for new image size!")
    print(f"   Old size: {original_size}")
    print(f"   New size: {new_size}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python adjust_template.py <template.yaml> <old_width> <old_height> <new_width> <new_height>")
        print("Example: python adjust_template.py Kasikorn.yaml 990 1409 860 1428")
        sys.exit(1)

    template_path = sys.argv[1]
    old_width = int(sys.argv[2])
    old_height = int(sys.argv[3])
    new_width = int(sys.argv[4])
    new_height = int(sys.argv[5])

    adjust_template_coordinates(template_path, [old_width, old_height], [new_width, new_height])
