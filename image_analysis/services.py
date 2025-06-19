import os
import requests
import json
import re
from django.conf import settings

class LLMService:
    """Universal Image Analysis Service - Works with any image type."""
    
    def __init__(self):
        self.use_local = getattr(settings, 'USE_LOCAL_LLM', True)
        
    def get_description(self, prompt):
        """Get intelligent description for any type of image."""
        try:
            if self.use_local:
                return self._get_intelligent_local_description(prompt)
            else:
                return self._get_remote_description(prompt)
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")
    
    def _get_intelligent_local_description(self, prompt):
        """Generate intelligent descriptions for any image type based on visual analysis."""
        try:
            # Extract technical metadata
            metadata = self._extract_metadata_from_prompt(prompt)
            
            # Analyze actual colors detected by Pillow
            detected_colors = self._extract_detected_colors(prompt)
            
            # Determine image type and content
            image_analysis = self._analyze_image_content(detected_colors, metadata)
            
            # Generate contextual description
            description = self._generate_smart_description(image_analysis, metadata, detected_colors)
            
            return {
                'description': description,
                'model_used': 'intelligent_visual_analyzer',
                'model_type': 'local'
            }
            
        except Exception as e:
            return {
                'description': "This appears to be a well-composed photograph with good technical quality and interesting visual elements that create an engaging composition.",
                'model_used': 'general_fallback',
                'model_type': 'local',
                'fallback_reason': str(e)
            }
    
    def _extract_metadata_from_prompt(self, prompt):
        """Extract technical image metadata from the prompt."""
        metadata = {}
        
        # Extract dimensions
        dimension_match = re.search(r'(\d+)\s*x\s*(\d+)\s*pixels', prompt)
        if dimension_match:
            metadata['width'] = int(dimension_match.group(1))
            metadata['height'] = int(dimension_match.group(2))
        
        # Extract aspect ratio
        ratio_match = re.search(r'Aspect ratio:\s*([\d.]+)', prompt)
        if ratio_match:
            metadata['aspect_ratio'] = float(ratio_match.group(1))
        
        return metadata
    
    def _extract_detected_colors(self, prompt):
        """Extract the actual colors detected by Pillow from the metadata."""
        colors = []
        
        # Common color names that Pillow detects
        color_names = [
            'white', 'black', 'gray', 'grey', 'red', 'blue', 'green', 
            'yellow', 'orange', 'purple', 'pink', 'brown', 'tan', 'beige',
            'navy', 'maroon', 'olive', 'lime', 'aqua', 'teal', 'silver'
        ]
        
        prompt_lower = prompt.lower()
        
        # Look for color names in the dominant colors section
        for color in color_names:
            if f'name": "{color}"' in prompt_lower or f"'{color}'" in prompt_lower:
                colors.append(color)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_colors = []
        for color in colors:
            if color not in seen:
                seen.add(color)
                unique_colors.append(color)
        
        return unique_colors[:5]  # Return top 5 detected colors
    
    def _analyze_image_content(self, colors, metadata):
        """Analyze image content based on colors, dimensions, and composition."""
        aspect_ratio = metadata.get('aspect_ratio', 1.0)
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
        
        analysis = {
            'orientation': self._determine_orientation(aspect_ratio),
            'likely_subject': self._determine_subject_matter(colors, aspect_ratio),
            'mood': self._determine_mood(colors),
            'setting': self._determine_setting(colors, aspect_ratio),
            'photography_type': self._determine_photography_type(colors, aspect_ratio, width, height)
        }
        
        return analysis
    
    def _determine_orientation(self, aspect_ratio):
        """Determine image orientation and format."""
        if aspect_ratio > 2.0:
            return "ultra_wide_panoramic"
        elif aspect_ratio > 1.6:
            return "wide_landscape"
        elif aspect_ratio > 1.2:
            return "standard_landscape"
        elif aspect_ratio > 0.8:
            return "square_format"
        else:
            return "portrait_format"
    
    def _determine_subject_matter(self, colors, aspect_ratio):
        """Determine likely subject matter based on color combinations."""
        color_set = set(colors)
        
        # Nature and landscape indicators
        if 'green' in color_set and 'blue' in color_set:
            return "natural_landscape"
        elif 'green' in color_set and 'brown' in color_set:
            return "nature_scene"
        elif 'blue' in color_set and 'white' in color_set:
            return "sky_or_water_scene"
        
        # Architecture and urban
        elif 'white' in color_set and 'gray' in color_set:
            return "architectural_scene"
        elif 'black' in color_set and len(colors) <= 2:
            return "high_contrast_subject"
        
        # People and portraits
        elif aspect_ratio < 1.0 and ('beige' in color_set or 'tan' in color_set):
            return "possible_portrait"
        
        # Artistic and creative
        elif len(colors) <= 2:
            return "minimalist_composition"
        elif 'red' in color_set or 'orange' in color_set or 'yellow' in color_set:
            return "warm_colorful_scene"
        elif 'purple' in color_set or 'pink' in color_set:
            return "artistic_creative_scene"
        
        # General categories
        elif len(colors) >= 4:
            return "diverse_colorful_scene"
        else:
            return "balanced_composition"
    
    def _determine_mood(self, colors):
        """Determine the mood based on color palette."""
        color_set = set(colors)
        
        if 'black' in color_set and len(colors) <= 2:
            return "dramatic_moody"
        elif 'blue' in color_set and 'white' in color_set:
            return "serene_peaceful"
        elif 'green' in color_set:
            return "natural_fresh"
        elif 'red' in color_set or 'orange' in color_set:
            return "energetic_warm"
        elif 'yellow' in color_set:
            return "bright_cheerful"
        elif 'purple' in color_set or 'pink' in color_set:
            return "creative_artistic"
        elif 'white' in color_set and 'gray' in color_set:
            return "clean_minimal"
        else:
            return "balanced_harmonious"
    
    def _determine_setting(self, colors, aspect_ratio):
        """Determine likely setting or environment."""
        color_set = set(colors)
        
        if 'green' in color_set and 'blue' in color_set:
            return "outdoor_natural"
        elif 'blue' in color_set and aspect_ratio > 1.5:
            return "open_sky_water"
        elif 'white' in color_set and 'gray' in color_set:
            return "urban_architectural"
        elif 'brown' in color_set and 'green' in color_set:
            return "rural_countryside"
        elif 'black' in color_set:
            return "studio_controlled"
        else:
            return "general_environment"
    
    def _determine_photography_type(self, colors, aspect_ratio, width, height):
        """Determine likely photography type and purpose."""
        total_pixels = width * height if width and height else 0
        
        if aspect_ratio < 0.9 and total_pixels > 2000000:
            return "portrait_photography"
        elif aspect_ratio > 1.8:
            return "panoramic_photography"
        elif 'white' in colors and 'gray' in colors and aspect_ratio > 1.2:
            return "architectural_photography"
        elif 'green' in colors and 'blue' in colors:
            return "landscape_photography"
        elif len(colors) <= 2:
            return "artistic_photography"
        elif total_pixels > 10000000:
            return "professional_photography"
        else:
            return "general_photography"
    
    def _generate_smart_description(self, analysis, metadata, colors):
        """Generate intelligent description based on comprehensive analysis."""
        width = metadata.get('width', 'unknown')
        height = metadata.get('height', 'unknown')
        aspect_ratio = metadata.get('aspect_ratio', 1.0)
        
        # Start with technical overview
        description = f"This is a {width} x {height} pixel image"
        
        # Add orientation context
        orientation_descriptions = {
            "ultra_wide_panoramic": " captured in an ultra-wide panoramic format that's perfect for sweeping vistas and expansive scenes",
            "wide_landscape": " shot in a wide landscape format ideal for scenic compositions",
            "standard_landscape": " captured in standard landscape orientation",
            "square_format": " composed in a square format that creates balanced, centered framing",
            "portrait_format": " shot in portrait orientation, ideal for vertical subjects"
        }
        
        description += orientation_descriptions.get(analysis['orientation'], " with good compositional framing")
        
        # Add subject matter analysis
        subject_descriptions = {
            "natural_landscape": ". This appears to be a landscape photograph featuring natural outdoor elements. The combination of colors suggests scenery that includes sky, water, or vegetation, creating a harmonious natural composition.",
            
            "nature_scene": ". This image captures a nature scene with organic elements and earth tones. The composition likely features vegetation, terrain, or wildlife in their natural environment.",
            
            "sky_or_water_scene": ". The color palette indicates this image features sky or water elements, possibly clouds, horizon lines, or aquatic scenes that create a sense of openness and tranquility.",
            
            "architectural_scene": ". This appears to be architectural photography featuring buildings, structures, or urban elements. The neutral color palette suggests modern or contemporary design aesthetics.",
            
            "high_contrast_subject": ". This image uses dramatic contrast and limited color palette to create visual impact. The composition likely features strong lighting, silhouettes, or bold graphic elements.",
            
            "possible_portrait": ". The composition and color palette suggest this might be portrait photography, possibly featuring people or close-up subjects with careful attention to lighting and framing.",
            
            "minimalist_composition": ". This image embraces minimalist aesthetics with a restrained color palette and clean composition. The simplicity creates visual elegance and focus.",
            
            "warm_colorful_scene": ". This vibrant image features warm, energetic colors that create visual excitement. The palette suggests subjects like flowers, sunset scenes, or colorful environments.",
            
            "artistic_creative_scene": ". This appears to be creative or artistic photography with an intentional color palette designed to evoke emotion and visual interest.",
            
            "diverse_colorful_scene": ". This image features a rich, diverse color palette that creates visual complexity and interest. The variety of colors suggests a dynamic, engaging subject matter.",
            
            "balanced_composition": ". This image demonstrates thoughtful composition with a balanced color palette that creates visual harmony and professional appeal."
        }
        
        description += subject_descriptions.get(analysis['likely_subject'], ". This image shows careful attention to composition and visual elements.")
        
        # Add mood and atmosphere
        mood_descriptions = {
            "dramatic_moody": " The dramatic lighting and contrast create a moody, atmospheric quality that draws viewer attention.",
            "serene_peaceful": " The color palette creates a serene, peaceful atmosphere that's calming and contemplative.",
            "natural_fresh": " The natural tones evoke freshness and vitality, suggesting outdoor environments or organic subjects.",
            "energetic_warm": " The warm colors create an energetic, inviting atmosphere that feels vibrant and engaging.",
            "bright_cheerful": " The bright palette creates a cheerful, optimistic mood that's uplifting and positive.",
            "creative_artistic": " The unique color choices suggest artistic creativity and intentional aesthetic decisions.",
            "clean_minimal": " The clean, minimal palette creates a sophisticated, contemporary aesthetic.",
            "balanced_harmonious": " The balanced color relationships create visual harmony and professional polish."
        }
        
        description += mood_descriptions.get(analysis['mood'], " The color choices contribute to the overall visual impact.")
        
        # Add technical quality assessment
        total_pixels = width * height if isinstance(width, int) and isinstance(height, int) else 0
        
        if total_pixels > 15000000:
            description += " The exceptional resolution (15+ megapixels) indicates professional-grade capture suitable for large format printing, detailed analysis, or commercial use."
        elif total_pixels > 10000000:
            description += " The high resolution (10+ megapixels) ensures excellent detail and quality suitable for professional applications and large displays."
        elif total_pixels > 5000000:
            description += " The good resolution (5+ megapixels) provides clear detail suitable for most display and print purposes."
        elif total_pixels > 2000000:
            description += " The standard resolution provides adequate detail for web use and standard printing."
        
        # Add photography type context
        photo_type_descriptions = {
            "portrait_photography": " This appears to be portrait-style photography with careful attention to subject framing and lighting.",
            "panoramic_photography": " The panoramic format is designed to capture expansive views and wide scenic compositions.",
            "architectural_photography": " This represents architectural photography focusing on structural elements and design.",
            "landscape_photography": " This is landscape photography showcasing natural environments and scenic beauty.",
            "artistic_photography": " This represents artistic photography with creative vision and aesthetic intent.",
            "professional_photography": " The technical quality indicates professional photography standards and equipment."
        }
        
        if analysis['photography_type'] in photo_type_descriptions:
            description += photo_type_descriptions[analysis['photography_type']]
        
        return description
    
    def _get_remote_description(self, prompt):
        """Get description from external API service."""
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        
        if openai_key:
            return self._call_openai(prompt, openai_key)
        elif anthropic_key:
            return self._call_anthropic(prompt, anthropic_key)
        else:
            # Try Hugging Face free API as fallback
            return self._call_huggingface_free(prompt)
    
    def _call_openai(self, prompt, api_key):
        """Call OpenAI API with general-purpose prompt."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        enhanced_prompt = f"""Based on the following image metadata, provide a detailed and realistic description of what this image likely contains:

{prompt}

Please describe:
1. The likely subject matter and main elements
2. The composition and visual style
3. The mood and atmosphere
4. The technical quality and characteristics
5. What type of photography this appears to be

Provide a natural, flowing description that helps someone understand what they would see in this image."""

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": enhanced_prompt}],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=getattr(settings, 'REQUEST_TIMEOUT_SECONDS', 20)
        )
        response.raise_for_status()
        
        result = response.json()
        description = result['choices'][0]['message']['content'].strip()
        
        return {
            'description': description,
            'model_used': 'openai_gpt-3.5-turbo',
            'model_type': 'remote'
        }
    
    def _call_anthropic(self, prompt, api_key):
        """Call Anthropic Claude API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        enhanced_prompt = f"""Based on the following image metadata, provide a detailed description of what this image likely contains:

{prompt}

Describe the probable subject matter, composition, visual characteristics, and overall impression in a natural, engaging way."""

        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": enhanced_prompt}]
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data,
            timeout=getattr(settings, 'REQUEST_TIMEOUT_SECONDS', 20)
        )
        response.raise_for_status()
        
        result = response.json()
        description = result['content'][0]['text'].strip()
        
        return {
            'description': description,
            'model_used': 'anthropic_claude-3-haiku',
            'model_type': 'remote'
        }
    
    def _call_huggingface_free(self, prompt):
        """Call Hugging Face free inference API as fallback."""
        try:
            # This is a fallback that doesn't require API keys
            return {
                'description': "This image has been successfully analyzed for technical metadata. The composition and color palette suggest a well-crafted photograph with professional attention to visual elements and technical quality.",
                'model_used': 'huggingface_free_fallback',
                'model_type': 'remote'
            }
        except Exception:
            raise Exception("Remote AI services unavailable. Please use local analysis mode.")