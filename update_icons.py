"""
Update app icons from EDU AI.png
Resizes the image to required PWA icon sizes
"""

try:
    from PIL import Image
    import os
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call(["pip", "install", "Pillow"])
    from PIL import Image
    import os

def resize_icon(input_path, output_path, size):
    """Resize image to specified size while maintaining aspect ratio"""
    try:
        # Open the original image
        img = Image.open(input_path)
        
        # Convert to RGB if necessary (handles RGBA, etc.)
        if img.mode != 'RGB':
            # Create white background for transparency
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            else:
                rgb_img.paste(img)
            img = rgb_img
        
        # Resize with high-quality resampling
        img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save the resized image
        os.makedirs('static', exist_ok=True)
        img_resized.save(output_path, 'PNG', optimize=True)
        print(f"✓ Created {output_path} ({size}x{size})")
        return True
    except Exception as e:
        print(f"✗ Error creating {output_path}: {e}")
        return False

if __name__ == '__main__':
    input_file = 'static/EDU AI.png'
    
    if not os.path.exists(input_file):
        print(f"✗ Error: {input_file} not found!")
        print("Please make sure 'EDU AI.png' is in the static/ folder")
        exit(1)
    
    print(f"Using source image: {input_file}")
    print("Generating PWA icons...")
    
    success = True
    success &= resize_icon(input_file, 'static/icon-192.png', 192)
    success &= resize_icon(input_file, 'static/icon-512.png', 512)
    
    if success:
        print("\n✓ Icons updated successfully!")
        print("The app will now use your EDU AI.png as the icon.")
    else:
        print("\n✗ Some icons failed to generate. Please check the errors above.")

