import io
from PIL import Image
from collections import Counter
import colorsys

def extract_image_metadata(image_file):
    """
    Extract metadata from image using Pillow.
    Returns dimensions and dominant colors.
    """
    try:
        # Open image from file-like object
        image = Image.open(image_file)
        
        # Get dimensions
        width, height = image.size
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract dominant colors
        dominant_colors = get_dominant_colors(image, num_colors=5)
        
        return {
            'width': width,
            'height': height,
            'dominant_colors': dominant_colors,
            'aspect_ratio': round(width / height, 2),
            'total_pixels': width * height
        }
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")

def get_color_name(r, g, b):
    """
    Get approximate color name from RGB values.
    """
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = h * 360
    
    if v < 0.2:
        return "black"
    elif v > 0.8 and s < 0.2:
        return "white"
    elif s < 0.2:
        return "gray"
    elif h < 15 or h > 345:
        return "red"
    elif h < 45:
        return "orange"
    elif h < 75:
        return "yellow"
    elif h < 150:
        return "green"
    elif h < 150:
        return "blue"
    elif h < 270:
        return "purple"
    elif h < 330:
        return "pink"
    else:
        return "red"

def get_dominant_colors(image, num_colors=5):
    """
    Extract dominant colors from PIL Image with improved algorithm.
    Returns list of colors in hex format.
    """
    # Resize image for faster processing but keep aspect ratio
    image.thumbnail((200, 200))
    
    # Convert to RGB if not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get all pixels
    pixels = list(image.getdata())
    
    # Filter out very similar colors to get more diverse palette
    filtered_pixels = []
    color_threshold = 30  # Minimum difference between colors
    
    for pixel in pixels:
        r, g, b = pixel
        # Skip if very similar to already added colors
        is_unique = True
        for existing in filtered_pixels[-100:]:  # Check last 100 to avoid too much computation
            er, eg, eb = existing
            if abs(r - er) + abs(g - eg) + abs(b - eb) < color_threshold:
                is_unique = False
                break
        if is_unique:
            filtered_pixels.append(pixel)
    
    # Use filtered pixels if we have enough, otherwise use all
    pixels_to_analyze = filtered_pixels if len(filtered_pixels) > num_colors * 10 else pixels
    
    # Count color frequencies
    color_counter = Counter(pixels_to_analyze)
    
    # Get most common colors
    most_common = color_counter.most_common(num_colors * 2)  # Get more to filter
    
    # Filter for diverse colors
    diverse_colors = []
    for color, count in most_common:
        r, g, b = color
        # Check if this color is significantly different from already selected
        is_diverse = True
        for selected_color in diverse_colors:
            sr, sg, sb = selected_color[0]
            color_distance = abs(r - sr) + abs(g - sg) + abs(b - sb)
            if color_distance < 60:  # Colors too similar
                is_diverse = False
                break
        
        if is_diverse:
            diverse_colors.append((color, count))
            if len(diverse_colors) >= num_colors:
                break
    
    # Convert to hex and include color names
    dominant_colors = []
    total_pixels = len(pixels)
    
    for color, count in diverse_colors:
        r, g, b = color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        color_name = get_color_name(r, g, b)
        
        dominant_colors.append({
            'hex': hex_color,
            'rgb': {'r': r, 'g': g, 'b': b},
            'name': color_name,
            'percentage': round((count / total_pixels) * 100, 1)
        })
    
    return dominant_colors

def validate_image_file(image_file, max_size_mb=10):
    """
    Validate uploaded image file.
    """
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if image_file.size > max_size_bytes:
        raise ValueError(f"Image file too large. Maximum size: {max_size_mb}MB")
    
    # Check if it's a valid image
    try:
        image = Image.open(image_file)
        image.verify()  # Verify it's a valid image
        image_file.seek(0)  # Reset file pointer after verify
        return True
    except Exception:
        raise ValueError("Invalid image file format")

def generate_description_prompt(metadata):
    """
    Generate prompt for LLM based on image metadata.
    """
    colors_desc = ", ".join([color['name'] for color in metadata['dominant_colors'][:3]])
    
    prompt = f"""Describe this image based on the following visual analysis:

Image Properties:
- Dimensions: {metadata['width']} x {metadata['height']} pixels
- Aspect ratio: {metadata['aspect_ratio']}
- Dominant colors: {colors_desc}

Please provide a detailed, coherent description of what this image likely contains, considering its dimensions, proportions, and color palette. Focus on the overall composition, mood, and potential subject matter that would align with these visual characteristics."""

    return prompt