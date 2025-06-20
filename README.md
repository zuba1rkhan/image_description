# Django Image Description API

A Django REST API that analyzes uploaded images and generates AI-powered descriptions using Pillow for metadata extraction and intelligent visual analysis.

![Django](https://img.shields.io/badge/Django-4.0+-green) ![Python](https://img.shields.io/badge/Python-3.10+-blue)

## Features

- **Single REST endpoint** for image upload and analysis
- **Intelligent visual analysis** based on colors, composition, and metadata
- **Dual LLM support** - Local analysis or remote APIs (OpenAI, Claude)
- **Fast processing** - 0.3-1 second typical response time
- **Universal support** - Works with any image type
- **Production ready** - Comprehensive error handling and testing

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd image_description

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux

# Setup Django
python manage.py migrate
python manage.py check

# Start server
python manage.py runserver
```

## Usage

### Health Check
```bash
curl http://localhost:8000/api/health/
```

### Analyze Image
```bash
curl -X POST http://localhost:8000/api/describe/ \
  -F "image=@your_image.jpg"
```

### Example Response
```json
{
  "description": "This is a 4426 x 2951 pixel image captured in standard landscape orientation. This appears to be artistic photography with dramatic contrast and minimalist aesthetics.",
  "metadata": {
    "dimensions": {
      "width": 4426,
      "height": 2951,
      "aspect_ratio": 1.5
    },
    "colors": [
      {
        "hex": "#0d1313",
        "rgb": {"r": 13, "g": 19, "b": 19},
        "name": "black",
        "percentage": 6.8
      }
    ],
    "total_pixels": 13061126
  },
  "model_info": {
    "model_used": "intelligent_visual_analyzer",
    "model_type": "local",
    "local_mode": true
  },
  "processing_time": 0.33,
  "status": "success"
}
```

## Configuration

### Environment Variables (.env)
```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# LLM Configuration
USE_LOCAL_LLM=True                    # Set to False for remote APIs
OPENAI_API_KEY=sk-your-openai-key     # Optional
ANTHROPIC_API_KEY=your-claude-key     # Optional

# Processing Limits
MAX_IMAGE_SIZE_MB=10
REQUEST_TIMEOUT_SECONDS=20
```

### Local vs Remote Analysis

**Local Mode (Default)**
```bash
USE_LOCAL_LLM=True
```
- Fast (0.3-1 second)
- No API costs
- Always available
- Intelligent rule-based analysis

**Remote Mode (AI APIs)**
```bash
USE_LOCAL_LLM=False
OPENAI_API_KEY=your-key    # For GPT models
# OR
ANTHROPIC_API_KEY=your-key # For Claude models
```
- Advanced AI descriptions
- Requires API keys and internet
- Higher quality but costs money

## API Reference

### Endpoints
- `GET /api/health/` - Health check
- `POST /api/describe/` - Analyze image

### POST /api/describe/
- **Content-Type:** `multipart/form-data`
- **Parameter:** `image` (file)
- **Supported formats:** JPEG, PNG, GIF, BMP, WEBP
- **Max size:** 10MB

### Response Fields
- `description` - AI-generated description
- `metadata` - Image dimensions, colors, technical info
- `model_info` - Analysis method used
- `processing_time` - Duration in seconds
- `status` - "success" or "error"

## Project Structure
```
image_description/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── image_describe_api/         # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── image_analysis/             # Main app
    ├── views.py               # API endpoints
    ├── serializers.py         # Request/response handling
    ├── services.py            # LLM integration
    ├── utils.py               # Image processing
    ├── urls.py                # URL patterns
    └── tests.py               # Test suite
```

## Testing
```bash
# Run all tests
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2
```

## How It Works

1. **Image Upload** - Validates format and size
2. **Metadata Extraction** - Uses Pillow to extract dimensions and colors
3. **Visual Analysis** - Analyzes composition, mood, and subject matter
4. **Description Generation** - Creates contextual descriptions
5. **Response** - Returns JSON with description and metadata

## Troubleshooting

### Common Issues

**"Module not found"**
```bash
# Activate virtual environment
venv\Scripts\activate
pip install -r requirements.txt
```

**"Port already in use"**
```bash
python manage.py runserver 8001
```

**"Invalid image file"**
- Check file format (JPEG, PNG, etc.)
- Ensure file size under 10MB
- Verify file isn't corrupted

**Remote API errors**
- Check API key validity
- Verify internet connection
- Switch to local mode temporarily

## Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

```bash
docker build -t image-api .
docker run -p 8000:8000 image-api
```

## Security Notes
- Keep API keys in environment variables
- Use HTTPS in production
- Set DEBUG=False for production
- Configure proper ALLOWED_HOSTS

## License
MIT License


**Quick Commands:**
```bash
# Setup and run
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt && copy .env.example .env
python manage.py migrate && python manage.py runserver

# Test API
curl http://localhost:8000/api/health/
curl -X POST http://localhost:8000/api/describe/ -F "image=@test.jpg"
```
