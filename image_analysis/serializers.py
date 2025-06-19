from rest_framework import serializers
from django.conf import settings

class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload validation."""
    
    image = serializers.ImageField(
        required=True,
        help_text="Image file to analyze (max 10MB)"
    )
    
    def validate_image(self, value):
        """Validate uploaded image."""
        max_size = getattr(settings, 'MAX_IMAGE_SIZE_MB', 10) * 1024 * 1024
        
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image file too large. Maximum size: {settings.MAX_IMAGE_SIZE_MB}MB"
            )
        
        # Check file format
        allowed_formats = ['JPEG', 'JPG', 'PNG', 'GIF', 'BMP', 'WEBP']
        try:
            from PIL import Image
            img = Image.open(value)
            if img.format not in allowed_formats:
                raise serializers.ValidationError(
                    f"Unsupported image format. Allowed: {', '.join(allowed_formats)}"
                )
            value.seek(0)  # Reset file pointer
        except Exception:
            raise serializers.ValidationError("Invalid image file")
        
        return value

class ImageDescriptionResponseSerializer(serializers.Serializer):
    """Serializer for API response."""
    
    description = serializers.CharField(help_text="AI-generated description of the image")
    metadata = serializers.DictField(help_text="Extracted image metadata")
    model_info = serializers.DictField(help_text="Information about the model used")
    processing_time = serializers.FloatField(help_text="Processing time in seconds")
    status = serializers.CharField(help_text="Processing status")