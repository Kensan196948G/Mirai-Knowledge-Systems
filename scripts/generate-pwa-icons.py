#!/usr/bin/env python3
"""
PWA Icon Generator for Mirai Knowledge Systems
Generates 9 PWA icons (72x72 to 512x512) + maskable icon

Requirements:
  pip install pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Icon sizes
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Output directory
OUTPUT_DIR = '../webui/icons'

# Colors
BG_COLOR = '#2f4b52'  # Theme color
TEXT_COLOR = '#f1ece4'  # Background color
ACCENT_COLOR = '#c8a882'  # Accent color

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_icon(size, output_path, is_maskable=False):
    """
    Create a single icon

    Args:
        size: Icon size (width = height)
        output_path: Output file path
        is_maskable: Whether to create maskable icon (with safe zone)
    """
    # Create image
    img = Image.new('RGB', (size, size), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    if is_maskable:
        # Maskable icon: 80% safe zone (40% margin)
        safe_zone = size * 0.8
        margin = (size - safe_zone) / 2
        logo_size = safe_zone
    else:
        # Regular icon: 90% of size
        logo_size = size * 0.9
        margin = (size - logo_size) / 2

    # Draw circle background (accent color)
    circle_margin = margin + logo_size * 0.1
    circle_size = logo_size * 0.8
    circle_box = [
        circle_margin,
        circle_margin,
        circle_margin + circle_size,
        circle_margin + circle_size
    ]
    draw.ellipse(circle_box, fill=hex_to_rgb(ACCENT_COLOR))

    # Draw "MKS" text
    try:
        # Try to load a font (fallback to default if not available)
        font_size = int(size * 0.25)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    text = "MKS"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2 - text_height * 0.1

    draw.text((text_x, text_y), text, fill=hex_to_rgb(TEXT_COLOR), font=font)

    # Add small subtitle for larger icons
    if size >= 192 and not is_maskable:
        subtitle = "建設土木"
        try:
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(size * 0.08))
        except:
            subtitle_font = ImageFont.load_default()

        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (size - subtitle_width) / 2
        subtitle_y = text_y + text_height + size * 0.05

        draw.text((subtitle_x, subtitle_y), subtitle, fill=hex_to_rgb(TEXT_COLOR), font=subtitle_font)

    # Save image
    img.save(output_path, 'PNG', optimize=True)
    print(f'✅ Created: {output_path} ({size}x{size})')

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print('🎨 Generating PWA icons...')
    print(f'Output directory: {OUTPUT_DIR}')
    print()

    # Generate regular icons
    for size in SIZES:
        output_path = os.path.join(OUTPUT_DIR, f'icon-{size}x{size}.png')
        create_icon(size, output_path, is_maskable=False)

    # Generate maskable icon (512x512)
    maskable_path = os.path.join(OUTPUT_DIR, 'maskable-icon-512x512.png')
    create_icon(512, maskable_path, is_maskable=True)

    # Generate shortcut icons (96x96)
    shortcuts = [
        ('icon-search-96.png', '🔍'),
        ('icon-new-96.png', '➕'),
        ('icon-notifications-96.png', '🔔')
    ]

    for filename, emoji in shortcuts:
        img = Image.new('RGB', (96, 96), hex_to_rgb(BG_COLOR))
        draw = ImageDraw.Draw(img)

        # Draw emoji (simplified - actual emoji rendering needs proper font)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        except:
            font = ImageFont.load_default()

        # Draw circle background
        draw.ellipse([10, 10, 86, 86], fill=hex_to_rgb(ACCENT_COLOR))

        # Draw emoji or text
        text_bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (96 - text_width) / 2
        text_y = (96 - text_height) / 2

        draw.text((text_x, text_y), emoji, fill=hex_to_rgb(TEXT_COLOR), font=font)

        output_path = os.path.join(OUTPUT_DIR, filename)
        img.save(output_path, 'PNG', optimize=True)
        print(f'✅ Created shortcut icon: {filename}')

    print()
    print('🎉 Icon generation complete!')
    print(f'Total icons: {len(SIZES) + 1 + len(shortcuts)} files')
    print()
    print('Next steps:')
    print('  1. Verify icons in webui/icons/')
    print('  2. Test manifest.json in browser')
    print('  3. Run Lighthouse audit')

if __name__ == '__main__':
    main()
