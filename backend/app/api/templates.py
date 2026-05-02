"""Template CRUD API endpoints."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Optional
import yaml
from pathlib import Path
import shutil
import logging

router = APIRouter()
TEMPLATES_DIR = Path("app/templates")
logger = logging.getLogger(__name__)


class Zone(BaseModel):
    """Zone configuration for a template field."""
    id: str
    field_name: str
    parser_type: str
    x_percent: float
    y_percent: float
    width_percent: float
    height_percent: float
    required: bool

    @field_validator('x_percent', 'y_percent', 'width_percent', 'height_percent')
    @classmethod
    def validate_percentages(cls, v):
        """Validate that percentage values are between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError('Percentage values must be between 0 and 100')
        return v


class TemplateCreate(BaseModel):
    """Request model for creating a template."""
    template_id: str
    bank_name: str
    description: str
    image_size: List[int]
    detection_keywords: List[str]
    zones: List[Zone]

    @field_validator('template_id')
    @classmethod
    def validate_template_id(cls, v):
        """Validate that template_id is not empty and contains only valid characters."""
        if not v or not v.strip():
            raise ValueError('template_id cannot be empty')
        # Allow alphanumeric, underscore, and hyphen
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError('template_id can only contain alphanumeric characters, underscores, and hyphens')
        return v

    @field_validator('image_size')
    @classmethod
    def validate_image_size(cls, v):
        """Validate that image_size has exactly 2 positive integers."""
        if len(v) != 2:
            raise ValueError('image_size must be a list of 2 integers [width, height]')
        if v[0] <= 0 or v[1] <= 0:
            raise ValueError('image_size values must be positive integers')
        return v

    @field_validator('zones')
    @classmethod
    def validate_zones(cls, v):
        """Validate that there is at least one zone."""
        if not v or len(v) == 0:
            raise ValueError('At least one zone must be defined')
        return v


@router.get("/templates/")
async def list_templates():
    """
    List all available templates.

    Returns:
        List of template info dictionaries
    """
    templates = []
    templates_dir = Path(TEMPLATES_DIR)

    if not templates_dir.exists():
        return templates

    for yaml_file in templates_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                templates.append({
                    'template_id': data.get('template_id', yaml_file.stem),
                    'bank_name': data.get('bank_name', 'Unknown'),
                    'description': data.get('description', ''),
                    'num_zones': len(data.get('zones', {})),
                    'image_size': data.get('image_size', [0, 0])
                })
        except Exception as e:
            print(f"Error reading template {yaml_file}: {e}")

    return templates


@router.post("/templates/")
async def create_template(template: TemplateCreate):
    """
    Save a new template from developer mode.

    Args:
        template: Template data from frontend

    Returns:
        Success message with template_id

    Raises:
        HTTPException: If template already exists or validation fails
    """
    try:
        logger.info(f"Received template data: {template.model_dump()}")

        templates_dir = Path(TEMPLATES_DIR)
        templates_dir.mkdir(parents=True, exist_ok=True)

        template_path = templates_dir / f"{template.template_id}.yaml"

        if template_path.exists():
            raise HTTPException(status_code=400, detail="Template already exists")

        # Convert to YAML format
        yaml_data = {
            'template_id': template.template_id,
            'bank_name': template.bank_name,
            'description': template.description,
            'image_size': template.image_size,
            'version': '1.0',
            'detection': {
                'primary_method': 'keywords',
                'keywords': template.detection_keywords
            },
            'zones': {}
        }

        for zone in template.zones:
            yaml_data['zones'][zone.field_name] = {
                'x_percent': zone.x_percent,
                'y_percent': zone.y_percent,
                'width_percent': zone.width_percent,
                'height_percent': zone.height_percent,
                'parser': zone.parser_type,
                'required': zone.required,
                'preprocessor': 'grayscale'
            }

        # Save YAML file
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)

        return {"message": "Template saved successfully", "template_id": template.template_id}

    except Exception as e:
        logger.error(f"Error saving template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Failed to save template: {str(e)}")


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Get a specific template by ID.

    Args:
        template_id: Template identifier

    Returns:
        Template data

    Raises:
        HTTPException: If template not found
    """
    template_path = Path(TEMPLATES_DIR) / f"{template_id}.yaml"

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")

    with open(template_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """
    Delete a template.

    Args:
        template_id: Template identifier

    Returns:
        Success message

    Raises:
        HTTPException: If template not found
    """
    template_path = Path(TEMPLATES_DIR) / f"{template_id}.yaml"

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")

    template_path.unlink()

    return {"message": f"Template '{template_id}' deleted successfully"}


@router.post("/templates/test-zone")
async def test_zone_ocr(request: dict):
    """
    Test OCR on a specific zone.

    Args:
        request: Dictionary containing image_data (base64) and zone configuration

    Returns:
        Extracted text from the zone
    """
    from app.services.zone_extractor import ZoneExtractor
    from PIL import Image
    from io import BytesIO
    import base64
    import tempfile
    import os

    try:
        # Extract image data and zone from request
        image_data = request.get('image_data', '')
        zone_data = request.get('zone')

        if not image_data or not zone_data:
            raise HTTPException(status_code=400, detail="Missing image_data or zone")

        # Parse zone data
        zone = Zone(**zone_data)

        # Handle base64 image data
        if image_data.startswith('data:image'):
            # Extract base64 data
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            try:
                extractor = ZoneExtractor()
                image = Image.open(temp_path)
                image_size = image.size

                zone_dict = {
                    'x_percent': zone.x_percent,
                    'y_percent': zone.y_percent,
                    'width_percent': zone.width_percent,
                    'height_percent': zone.height_percent,
                    'preprocessor': 'grayscale'
                }

                text = extractor.extract_zone_text(temp_path, zone_dict, image_size)

                return {'extracted_text': text}

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        else:
            # Assume it's a file path
            extractor = ZoneExtractor()
            image = Image.open(image_data)
            image_size = image.size

            zone_dict = {
                'x_percent': zone.x_percent,
                'y_percent': zone.y_percent,
                'width_percent': zone.width_percent,
                'height_percent': zone.height_percent,
                'preprocessor': 'grayscale'
            }

            text = extractor.extract_zone_text(image_data, zone_dict, image_size)

            return {'extracted_text': text}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR test failed: {str(e)}")
