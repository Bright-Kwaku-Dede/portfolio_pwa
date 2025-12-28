from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
os.makedirs('static/icons', exist_ok=True)

def create_icon(size, filename):
    """Create a simple icon with text"""
    # Create blue background
    img = Image.new('RGB', (size, size), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", size // 4)
    except:
        font = ImageFont.load_default()
    
    # Add text
    text = "P"
    
    # Get text size and position it in center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    # Save the image
    img.save(filename)
    print(f"Created {filename}")

# Create both icon sizes
create_icon(192, 'static/icons/icon-192x192.png')
create_icon(512, 'static/icons/icon-512x512.png')

print("\nIcons created successfully!")