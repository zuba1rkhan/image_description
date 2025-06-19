import time
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.conf import settings

from .serializers import ImageUploadSerializer, ImageDescriptionResponseSerializer
from .utils import extract_image_metadata, validate_image_file, generate_description_prompt
from .services import LLMService

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def describe_image(request):
    """
    Single endpoint that receives an image, extracts metadata,
    generates a description using LLM, and returns structured response.
    """
    start_time = time.time()
    
    try:
        # Validate input
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid input',
                    'details': serializer.errors,
                    'status': 'error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = serializer.validated_data['image']
        
        # Validate image file
        try:
            validate_image_file(image_file, settings.MAX_IMAGE_SIZE_MB)
        except ValueError as e:
            return Response(
                {
                    'error': str(e),
                    'status': 'error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract metadata using Pillow
        try:
            metadata = extract_image_metadata(image_file)
        except ValueError as e:
            return Response(
                {
                    'error': f'Failed to process image: {str(e)}',
                    'status': 'error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate prompt based on metadata
        prompt = generate_description_prompt(metadata)
        
        # Get description from LLM service
        try:
            llm_service = LLMService()
            llm_response = llm_service.get_description(prompt)
        except Exception as e:
            return Response(
                {
                    'error': f'LLM service unavailable: {str(e)}',
                    'status': 'error',
                    'metadata': metadata  # Still return metadata if available
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        # Prepare response
        response_data = {
            'description': llm_response['description'],
            'metadata': {
                'dimensions': {
                    'width': metadata['width'],
                    'height': metadata['height'],
                    'aspect_ratio': metadata['aspect_ratio']
                },
                'colors': metadata['dominant_colors'],
                'total_pixels': metadata['total_pixels']
            },
            'model_info': {
                'model_used': llm_response['model_used'],
                'model_type': llm_response['model_type'],
                'local_mode': settings.USE_LOCAL_LLM
            },
            'processing_time': processing_time,
            'status': 'success'
        }
        
        # Add error info if present (for fallback scenarios)
        if 'error' in llm_response:
            response_data['model_info']['fallback_reason'] = llm_response['error']
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        processing_time = round(time.time() - start_time, 2)
        return Response(
            {
                'error': f'Unexpected error: {str(e)}',
                'status': 'error',
                'processing_time': processing_time
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return Response(
        {
            'status': 'healthy',
            'service': 'Image Description API',
            'version': '1.0.0',
            'llm_mode': 'local' if settings.USE_LOCAL_LLM else 'remote'
        },
        status=status.HTTP_200_OK
    )