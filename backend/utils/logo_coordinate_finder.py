#!/usr/bin/env python3
"""
Utility to help find logo region coordinates for template configuration.

This script displays an image and allows you to select the logo region,
then outputs the percentage-based coordinates for the template YAML.
"""

import cv2
import numpy as np
from pathlib import Path

class LogoRegionSelector:
    """Interactive logo region selector."""

    def __init__(self, image_path: str):
        """Initialize with image path."""
        self.image_path = Path(image_path)
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"Could not load image: {image_path}")

        self.height, self.width = self.image.shape[:2]
        self.selecting = False
        self.start_point = None
        self.end_point = None
        self.clone = self.image.copy()
        self.region = None

        print(f"\nImage loaded: {self.image_path.name}")
        print(f"Dimensions: {self.width}x{self.height}")
        print("\nInstructions:")
        print("  1. Click and drag to select the logo region")
        print("  2. Press 'r' to reset selection")
        print("  3. Press 'c' to confirm and get coordinates")
        print("  4. Press 'q' to quit")
        print("\n" + "="*60 + "\n")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for region selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.selecting = True
            self.start_point = (x, y)
            self.end_point = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selecting:
                self.end_point = (x, y)
                self.clone = self.image.copy()
                cv2.rectangle(self.clone, self.start_point, self.end_point, (0, 255, 0), 2)

        elif event == cv2.EVENT_LBUTTONUP:
            self.selecting = False
            self.end_point = (x, y)
            self.clone = self.image.copy()
            cv2.rectangle(self.clone, self.start_point, self.end_point, (0, 255, 0), 2)

    def get_region_coordinates(self):
        """Get region coordinates in percentage format."""
        if self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point

            # Ensure coordinates are ordered correctly
            x_min = min(x1, x2)
            x_max = max(x1, x2)
            y_min = min(y1, y2)
            y_max = max(y1, y2)

            # Calculate region dimensions
            region_width = x_max - x_min
            region_height = y_max - y_min

            # Calculate percentages
            x_percent = (x_min / self.width) * 100
            y_percent = (y_min / self.height) * 100
            width_percent = (region_width / self.width) * 100
            height_percent = (region_height / self.height) * 100

            return {
                'x_percent': round(x_percent, 2),
                'y_percent': round(y_percent, 2),
                'width_percent': round(width_percent, 2),
                'height_percent': round(height_percent, 2),
                'pixels': {
                    'x': x_min,
                    'y': y_min,
                    'width': region_width,
                    'height': region_height
                }
            }
        return None

    def display_image(self):
        """Display image and handle user interaction."""
        cv2.namedWindow('Select Logo Region')
        cv2.setMouseCallback('Select Logo Region', self.mouse_callback)

        while True:
            cv2.imshow('Select Logo Region', self.clone)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\nQuit without saving")
                break

            elif key == ord('r'):
                self.clone = self.image.copy()
                self.start_point = None
                self.end_point = None
                print("\nSelection reset")

            elif key == ord('c'):
                region = self.get_region_coordinates()
                if region:
                    print("\n" + "="*60)
                    print("LOGO REGION COORDINATES")
                    print("="*60)
                    print("\nAdd this to your template YAML:\n")
                    print("detection:")
                    print("  primary_method: logo")
                    print("  logo_region:")
                    print(f"    x_percent: {region['x_percent']}")
                    print(f"    y_percent: {region['y_percent']}")
                    print(f"    width_percent: {region['width_percent']}")
                    print(f"    height_percent: {region['height_percent']}")
                    print("\n" + "="*60)
                    print(f"\nPixel values:")
                    print(f"  Position: ({region['pixels']['x']}, {region['pixels']['y']})")
                    print(f"  Size: {region['pixels']['width']}x{region['pixels']['height']}")

                    # Draw preview
                    preview = self.image.copy()
                    x1 = region['pixels']['x']
                    y1 = region['pixels']['y']
                    x2 = x1 + region['pixels']['width']
                    y2 = y1 + region['pixels']['height']
                    cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Extract and display the region
                    logo_region = self.image[y1:y2, x1:x2]
                    cv2.imshow('Extracted Logo Region', logo_region)

                    print("\nPress any key to continue...")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    break
                else:
                    print("\nNo region selected. Please select a region first.")

        cv2.destroyAllWindows()

def main():
    """Main function."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python logo_coordinate_finder.py <path_to_image>")
        print("\nExample:")
        print("  python logo_coordinate_finder.py sample_receipt.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    try:
        selector = LogoRegionSelector(image_path)
        selector.display_image()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
