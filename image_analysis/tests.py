import io
import os
from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from .utils import extract_image_metadata, validate_image_file, generate_description_prompt
from .services import LLMService

class ImageUtilsTestCase(TestCase):
    """Test image processing utilities."""
    
    def setUp(self):
        # Create a test image
        self.test_image = Image.new('RGB', (100, 200), color='red')
        self.image_buffer = io.BytesIO()
        self.test_image.save(self.image_buffer, format='JPEG')
        self.image_buffer.seek(0)
    
    def test_extract_image_metadata(self):
        """Test metadata extraction from image."""
        self.image_buffer.seek(0)
        metadata = extract_image_metadata(self.image_buffer)
        
        self.assertEqual(metadata['width'], 100)
        self.assertEqual(metadata['height'], 200)
        self.assertEqual(metadata['aspect_ratio'], 0.5)
        self.assertIsInstance(metadata['dominant_colors'], list)
        self.assertGreaterEqual(len(metadata['dominant_colors']), 3)
    
    def test_validate_image_file_success(self):
        """Test successful image validation."""
        self.image_buffer.seek(0)
        # Should not raise exception
        validate_image_file(self.image_buffer, max_size_mb=10)
    
    def test_validate_image_file_too_large(self):
        """Test image file size validation."""
        self.image_buffer.seek(0)
        with self.assertRaises(ValueError) as context:
            validate_image_file(self.image_buffer, max_size_mb=0.001)  # Very small limit
        
        self.assertIn("too large", str(context.exception))
    
    def test_generate_description_prompt(self):
        """Test prompt generation."""
        metadata = {
            'width': 100,
            'height': 200,
            'aspect_ratio': 0.5,
            'dominant_colors': [
                {'name': 'red', 'hex': '#ff0000'},
                {'name': 'blue', 'hex': '#0000ff'},
                {'name': 'green', 'hex': '#00ff00'}
            ]
        }
        
        prompt = generate_description_prompt(metadata)
        
        self.assertIn('100 x 200', prompt)
        self.assertIn('red', prompt)
        self.assertIn('0.5', prompt)

class LLMServiceTestCase(TestCase):
    """Test LLM service functionality."""
    
    def setUp(self):
        self.llm_service = LLMService()
        self.test_prompt = "Describe an image that is 100x200 pixels with red, blue, and green colors."
    
    def test_local_llm_fallback(self):
        """Test local LLM with fallback when model unavailable."""
        # Force local mode
        self.llm_service.use_local = True
        
        response = self.llm_service.get_description(self.test_prompt)
        
        self.assertIsInstance(response, dict)
        self.assertIn('description', response)
        self.assertIn('model_used', response)
        self.assertEqual(response['model_type'], 'local')

class ImageDescriptionAPITestCase(APITestCase):
    """Test the main API endpoint."""
    
    def setUp(self):
        # Create test image
        self.test_image = Image.new('RGB', (100, 200), color='red')
        self.image_buffer = io.BytesIO()
        self.test_image.save(self.image_buffer, format='JPEG')
        self.image_buffer.seek(0)
        
        self.uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            self.image_buffer.getvalue(),
            content_type="image/jpeg"
        )
        
        self.url = reverse('describe_image')
    
    def test_successful_image_description(self):
        """Test successful image upload and description - happy path."""
        response = self.client.post(
            self.url,
            {'image': self.uploaded_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('description', data)
        self.assertIn('metadata', data)
        self.assertIn('model_info', data)
        self.assertIn('processing_time', data)
        
        # Check metadata structure
        metadata = data['metadata']
        self.assertIn('dimensions', metadata)
        self.assertIn('colors', metadata)
        self.assertEqual(metadata['dimensions']['width'], 100)
        self.assertEqual(metadata['dimensions']['height'], 200)
    
    def test_no_image_uploaded(self):
        """Test error handling when no image is uploaded."""
        response = self.client.post(self.url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
    
    def test_invalid_file_format(self):
        """Test error handling for invalid file format."""
        # Create a text file pretending to be an image
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"This is not an image",
            content_type="text/plain"
        )
        
        response = self.client.post(
            self.url,
            {'image': invalid_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        url = reverse('health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('service', data)
        self.assertIn('llm_mode', data)

class ImageFileSizeTestCase(APITestCase):
    """Test file size limitations."""
    
    def setUp(self):
        self.url = reverse('describe_image')
    
    def test_large_image_rejection(self):
        """Test rejection of oversized images."""
        # Create a large image (this is a mock - actual large file would be huge)
        large_image = Image.new('RGB', (1000, 1000), color='blue')
        buffer = io.BytesIO()
        large_image.save(buffer, format='JPEG', quality=100)
        buffer.seek(0)
        
        # Mock a file that appears larger than limit
        large_file = SimpleUploadedFile(
            "large_image.jpg",
            buffer.getvalue(),
            content_type="image/jpeg"
        )
        
        # Temporarily reduce max size for testing
        original_max_size = settings.MAX_IMAGE_SIZE_MB
        settings.MAX_IMAGE_SIZE_MB = 0.001  # Very small limit
        
        try:
            response = self.client.post(
                self.url,
                {'image': large_file},
                format='multipart'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.json()
            self.assertEqual(data['status'], 'error')
            self.assertIn('too large', data['error'])
            
        finally:
            # Restore original setting
            settings.MAX_IMAGE_SIZE_MB = original_max_size