"""
Simple script to generate PWA icons for EDU AI app.
Requires PIL/Pillow: pip install Pillow
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call(["pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont
    import os

def create_icon(size, filename):
    """Create a simple icon with EDU AI branding"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "E" letter
    try:
        # Try to use a nice font
        font_size = size // 2
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    text = "E"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - text_height // 4)
    
    # Draw white "E"
    draw.text(position, text, fill='white', font=font)
    
    # Save icon
    os.makedirs('static', exist_ok=True)
    img.save(f'static/{filename}', 'PNG')
    print(f"✓ Created {filename} ({size}x{size})")

if __name__ == '__main__':
    print("Generating PWA icons for EDU AI...")
    create_icon(192, 'icon-192.png')
    create_icon(512, 'icon-512.png')
    print("\n✓ Icons generated successfully!")
    print("Place them in the static/ folder.")

