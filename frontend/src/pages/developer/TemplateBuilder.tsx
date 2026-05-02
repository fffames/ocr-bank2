import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Save, Trash2, TestTube, ArrowLeft, Grid3x3 } from 'lucide-react';
import '../../styles/developer.css';

interface Zone {
  id: string;
  fieldName: string;
  parserType: string;
  xPercent: number;
  yPercent: number;
  widthPercent: number;
  heightPercent: number;
  required: boolean;
}

interface Template {
  templateId: string;
  bankName: string;
  description: string;
  imageSize: [number, number];
  detectionKeywords: string[];
  zones: Zone[];
}

const FIELD_NAMES = [
  'date', 'time', 'sender_name', 'sender_account',
  'receiver_name', 'receiver_account', 'amount',
  'fee', 'reference', 'note'
];

const PARSER_TYPES = [
  { value: 'thai_date', label: 'Thai Date (Buddhist Era)' },
  { value: 'time', label: 'Time (HH:MM)' },
  { value: 'thai_amount', label: 'Thai Amount' },
  { value: 'thai_name', label: 'Thai Name' },
  { value: 'account_number', label: 'Account Number' },
  { value: 'text', label: 'Plain Text' }
];

export default function TemplateBuilder() {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const [template, setTemplate] = useState<Partial<Template>>({
    templateId: '',
    bankName: '',
    description: '',
    imageSize: [0, 0],
    detectionKeywords: [],
    zones: []
  });

  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 });
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Logo cropping state
  const [mode, setMode] = useState<'zones' | 'logo'>('zones');
  const [logoCrop, setLogoCrop] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);

  // Handle image upload
  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageSrc(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  // Handle image load to get dimensions
  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
    setTemplate(prev => ({ ...prev, imageSize: [img.naturalWidth, img.naturalHeight] }));
  }, []);

  // Convert pixel coordinates to percentages
  const pixelsToPercent = useCallback((pixels: number, dimension: number) => {
    return (pixels / dimension) * 100;
  }, []);

  // Convert percentage coordinates to pixels
  const percentToPixels = useCallback((percent: number, dimension: number) => {
    return (percent / 100) * dimension;
  }, []);

  // Handle mouse down on canvas
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!imageRef.current || !imageSrc || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (mode === 'logo') {
      // Logo cropping mode - start drawing logo crop
      setIsDrawing(true);
      setDrawStart({ x, y });
      setLogoCrop(null);
      return;
    }

    // Check if clicking on existing zone
    const clickedZone = zones.find(zone => {
      const zoneX = percentToPixels(zone.xPercent, rect.width);
      const zoneY = percentToPixels(zone.yPercent, rect.height);
      const zoneW = percentToPixels(zone.widthPercent, rect.width);
      const zoneH = percentToPixels(zone.heightPercent, rect.height);

      return x >= zoneX && x <= zoneX + zoneW && y >= zoneY && y <= zoneY + zoneH;
    });

    if (clickedZone) {
      setSelectedZoneId(clickedZone.id);
      setIsDragging(true);
      setDragOffset({
        x: x - percentToPixels(clickedZone.xPercent, rect.width),
        y: y - percentToPixels(clickedZone.yPercent, rect.height)
      });
    } else {
      // Start drawing new zone
      setIsDrawing(true);
      setDrawStart({ x, y });
      setSelectedZoneId(null);
    }
  }, [zones, imageSrc, percentToPixels, mode]);

  // Handle mouse move for drawing/dragging
  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!imageRef.current || !imageSrc || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (mode === 'logo' && isDrawing) {
      // Logo cropping mode - update logo crop rectangle
      const cropX = Math.min(drawStart.x, x);
      const cropY = Math.min(drawStart.y, y);
      const cropWidth = Math.abs(x - drawStart.x);
      const cropHeight = Math.abs(y - drawStart.y);

      setLogoCrop({ x: cropX, y: cropY, width: cropWidth, height: cropHeight });
      return;
    }

    if (isDragging && selectedZoneId) {
      // Dragging existing zone
      setZones(prev => prev.map(zone => {
        if (zone.id === selectedZoneId) {
          return {
            ...zone,
            xPercent: Math.max(0, Math.min(100, pixelsToPercent(x - dragOffset.x, rect.width))),
            yPercent: Math.max(0, Math.min(100, pixelsToPercent(y - dragOffset.y, rect.height)))
          };
        }
        return zone;
      }));
    }
  }, [isDragging, selectedZoneId, imageSrc, pixelsToPercent, dragOffset, mode, isDrawing, drawStart]);

  // Handle mouse up to finish drawing/dragging
  const handleCanvasMouseUp = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!imageRef.current || !imageSrc || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (mode === 'logo' && isDrawing) {
      // Logo cropping mode - finalize logo crop
      const cropX = Math.min(drawStart.x, x);
      const cropY = Math.min(drawStart.y, y);
      const cropWidth = Math.abs(x - drawStart.x);
      const cropHeight = Math.abs(y - drawStart.y);

      // Only set logo crop if it's big enough
      if (cropWidth > 20 && cropHeight > 20) {
        setLogoCrop({ x: cropX, y: cropY, width: cropWidth, height: cropHeight });
      } else {
        setLogoCrop(null);
      }
      setIsDrawing(false);
      return;
    }

    if (isDrawing) {
      // Finish drawing new zone
      const xPercent = Math.min(drawStart.x, x);
      const yPercent = Math.min(drawStart.y, y);
      const widthPercent = Math.abs(x - drawStart.x);
      const heightPercent = Math.abs(y - drawStart.y);

      if (widthPercent > 1 && heightPercent > 1) {
        const newZone: Zone = {
          id: `zone-${Date.now()}`,
          fieldName: FIELD_NAMES[zones.length % FIELD_NAMES.length],
          parserType: 'text',
          xPercent: pixelsToPercent(xPercent, rect.width),
          yPercent: pixelsToPercent(yPercent, rect.height),
          widthPercent: pixelsToPercent(widthPercent, rect.width),
          heightPercent: pixelsToPercent(heightPercent, rect.height),
          required: false
        };

        setZones(prev => [...prev, newZone]);
        setSelectedZoneId(newZone.id);
      }

      setIsDrawing(false);
    }

    setIsDragging(false);
  }, [isDrawing, drawStart, imageSrc, zones.length, pixelsToPercent, mode]);

  // Delete zone
  const deleteZone = useCallback((zoneId: string) => {
    setZones(prev => prev.filter(z => z.id !== zoneId));
    if (selectedZoneId === zoneId) {
      setSelectedZoneId(null);
    }
  }, [selectedZoneId]);

  // Update zone properties
  const updateZone = useCallback((zoneId: string, updates: Partial<Zone>) => {
    setZones(prev => prev.map(zone =>
      zone.id === zoneId ? { ...zone, ...updates } : zone
    ));
  }, []);

  // Save template
  const saveTemplate = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/templates/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: template.templateId,
          bank_name: template.bankName,
          description: template.description,
          image_size: template.imageSize,
          detection_keywords: template.detectionKeywords,
          zones: zones.map(zone => ({
            id: zone.id,
            field_name: zone.fieldName,  // Convert to snake_case
            parser_type: zone.parserType,  // Convert to snake_case
            x_percent: zone.xPercent,  // Convert to snake_case
            y_percent: zone.yPercent,  // Convert to snake_case
            width_percent: zone.widthPercent,  // Convert to snake_case
            height_percent: zone.heightPercent,  // Convert to snake_case
            required: zone.required
          }))
        })
      });

      if (response.ok) {
        alert('Template saved successfully!');
        navigate('/developer/templates');
      } else {
        const error = await response.json();
        alert(`Failed to save: ${error.detail}`);
      }
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  // Test OCR on a zone
  const testZoneOCR = async (zone: Zone) => {
    if (!imageSrc) return;

    try {
      const response = await fetch('http://localhost:8000/api/templates/test-zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: imageSrc,
          zone: {
            id: zone.id,
            field_name: zone.fieldName,
            parser_type: zone.parserType,
            x_percent: zone.xPercent,
            y_percent: zone.yPercent,
            width_percent: zone.widthPercent,
            height_percent: zone.heightPercent,
            required: zone.required
          }
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'OCR test failed');
      }

      const result = await response.json();

      // Show result in a nicer dialog
      const text = result.extracted_text || '(no text detected)';
      alert(`📝 OCR Result for "${zone.fieldName}":\n\n${text}`);
    } catch (error: any) {
      alert(`❌ OCR Test failed: ${error.message}`);
    }
  };

  const selectedZone = zones.find(z => z.id === selectedZoneId);

  // Handle logo upload
  const handleUploadLogo = async () => {
    if (!logoCrop || !imageSrc || !template.templateId) {
      alert('Please set template ID and crop a logo region first');
      return;
    }

    setIsUploadingLogo(true);

    try {
      // Create canvas to crop the logo
      const canvas = document.createElement('canvas');
      const img = imageRef.current;
      if (!img) throw new Error('Image not loaded');

      // Calculate crop coordinates in actual image dimensions
      const scaleX = img.naturalWidth / img.width;
      const scaleY = img.naturalHeight / img.height;

      const cropX = logoCrop.x * scaleX;
      const cropY = logoCrop.y * scaleY;
      const cropWidth = logoCrop.width * scaleX;
      const cropHeight = logoCrop.height * scaleY;

      canvas.width = cropWidth;
      canvas.height = cropHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Failed to get canvas context');

      // Crop the logo region
      ctx.drawImage(
        img,
        cropX, cropY, cropWidth, cropHeight,
        0, 0, cropWidth, cropHeight
      );

      // Convert to blob
      canvas.toBlob(async (blob) => {
        if (!blob) {
          setIsUploadingLogo(false);
          throw new Error('Failed to create blob');
        }

        const formData = new FormData();
        formData.append('template_id', template.templateId || 'unknown');
        formData.append('logo_image', blob, 'logo.png');

        const response = await fetch('http://localhost:8000/api/templates/upload-logo', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const error = await response.json();
          setIsUploadingLogo(false);
          throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        alert(`✅ Logo uploaded successfully!\n\nSaved to: ${result.logo_path}`);
        setIsUploadingLogo(false);
      }, 'image/png');
    } catch (error: any) {
      alert(`❌ Logo upload failed: ${error.message}`);
      setIsUploadingLogo(false);
    }
  };

  const handleSaveAsHeaderTemplate = async () => {
    if (!imageSrc || !imageRef.current || !template.templateId) {
      alert('Please upload an image and set template ID first');
      return;
    }

    try {
      // Get the image dimensions
      const img = imageRef.current;
      const naturalWidth = img.naturalWidth;
      const naturalHeight = img.naturalHeight;

      // Calculate header region (top 25% of FULL image, full width)
      const headerHeight = Math.floor(naturalHeight * 0.25);
      const headerWidth = naturalWidth;  // FULL WIDTH!

      // Create canvas with EXACT header dimensions
      const canvas = document.createElement('canvas');
      canvas.width = headerWidth;
      canvas.height = headerHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Failed to get canvas context');

      // Extract the header region (top 25%, full width)
      ctx.drawImage(
        img,
        0, 0, headerWidth, headerHeight,     // Source: top-left (0,0) to (width, 25% height)
        0, 0, headerWidth, headerHeight      // Destination: full canvas
      );

      // Convert to blob for upload
      canvas.toBlob(async (blob) => {
        if (!blob) throw new Error('Failed to create blob');

        const formData = new FormData();
        formData.append('template_id', (template.templateId || 'unknown') + '_header');
        formData.append('logo_image', blob, 'header.png');

        const response = await fetch('http://localhost:8000/api/templates/upload-logo', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }

        await response.json();

        // Show success with dimensions
        alert(`✅ Header template saved!\n\nTemplate ID: ${template.templateId}\nHeader size: ${headerWidth}x${headerHeight}px\n\nThis captures the full width of your receipt header!\n\n🔄 Restart the backend to apply changes.`);

      }, 'image/png');
    } catch (error: any) {
      alert(`❌ Failed to save header template: ${error.message}`);
    }
  };

  return (
    <div className="dev-mode dev-grid-bg min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--dev-border)] bg-[var(--dev-bg-secondary)]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/developer/templates')}
                className="p-2 hover:bg-[var(--dev-bg-tertiary)] rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[var(--dev-text-secondary)]" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-[var(--dev-text-primary)] flex items-center gap-2">
                  <Grid3x3 className="w-6 h-6 text-[var(--dev-accent)]" />
                  Template Builder
                </h1>
                <p className="text-sm text-[var(--dev-text-secondary)] mt-1">
                  Create OCR templates by drawing zones on receipt images
                </p>
              </div>
            </div>
            <button
              onClick={saveTemplate}
              disabled={!template.templateId || !template.bankName || zones.length === 0}
              className="dev-btn flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              Save Template
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Canvas */}
          <div className="lg:col-span-2 space-y-4">
            {/* Template Metadata */}
            <div className="dev-card p-6 space-y-4">
              <h2 className="text-lg font-semibold text-[var(--dev-text-primary)]">Template Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Template ID</label>
                  <input
                    type="text"
                    value={template.templateId}
                    onChange={(e) => setTemplate(prev => ({ ...prev, templateId: e.target.value }))}
                    placeholder="e.g., krungthai_kplus"
                    className="dev-input w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Bank Name</label>
                  <input
                    type="text"
                    value={template.bankName}
                    onChange={(e) => setTemplate(prev => ({ ...prev, bankName: e.target.value }))}
                    placeholder="e.g., Krungthai Bank"
                    className="dev-input w-full"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Description</label>
                <input
                  type="text"
                  value={template.description}
                  onChange={(e) => setTemplate(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of this template"
                  className="dev-input w-full"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Detection Keywords (comma-separated)</label>
                <input
                  type="text"
                  value={template.detectionKeywords?.join(', ')}
                  onChange={(e) => setTemplate(prev => ({ ...prev, detectionKeywords: e.target.value.split(',').map(k => k.trim()) }))}
                  placeholder="K+, Krungthai, เลขที่ใบสำคัญ"
                  className="dev-input w-full"
                />
              </div>
            </div>

            {/* Canvas */}
            <div className="dev-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <h2 className="text-lg font-semibold text-[var(--dev-text-primary)]">Receipt Image</h2>
                  {imageSrc && (
                    <div className="flex items-center gap-2 bg-[var(--dev-bg-tertiary)] rounded-lg p-1">
                      <button
                        onClick={() => setMode('zones')}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${
                          mode === 'zones'
                            ? 'bg-[var(--dev-accent)] text-[var(--dev-bg-primary)]'
                            : 'text-[var(--dev-text-secondary)] hover:text-[var(--dev-text-primary)]'
                        }`}
                      >
                        Zones
                      </button>
                      <button
                        onClick={() => setMode('logo')}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${
                          mode === 'logo'
                            ? 'bg-[var(--dev-accent)] text-[var(--dev-bg-primary)]'
                            : 'text-[var(--dev-text-secondary)] hover:text-[var(--dev-text-primary)]'
                        }`}
                      >
                        Logo
                      </button>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {mode === 'logo' && logoCrop && (
                    <button
                      onClick={handleUploadLogo}
                      disabled={isUploadingLogo || !template.templateId}
                      className="dev-btn flex items-center gap-2 disabled:opacity-50"
                    >
                      {isUploadingLogo ? 'Uploading...' : 'Upload Logo'}
                    </button>
                  )}
                  {imageSrc && template.templateId && (
                    <button
                      onClick={() => handleSaveAsHeaderTemplate()}
                      className="dev-btn-secondary flex items-center gap-2"
                      title="Save entire image as header template"
                    >
                      💾 Save as Header
                    </button>
                  )}
                  <label className="dev-btn-secondary flex items-center gap-2 cursor-pointer">
                    <Upload className="w-4 h-4" />
                    Upload Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>

              {/* Mode-specific instructions */}
              {imageSrc && template.templateId && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                  <div className="text-blue-600 text-xl mt-0.5">🎯</div>
                  <div className="text-sm text-blue-800 flex-1">
                    <strong>💡 Quick Start - Create Header Template:</strong>
                    <ul className="mt-2 space-y-1">
                      <li>1. Make sure Template ID is set (e.g., "SCB")</li>
                      <li>2. Upload a clear sample receipt image</li>
                      <li>3. Click <strong>"💾 Save as Header"</strong> button above</li>
                      <li>4. System automatically extracts top 25% as template</li>
                    </ul>
                    <p className="mt-2 text-xs text-blue-600">
                      ⚡ Header templates are much more reliable than logo-only matching!
                    </p>
                  </div>
                </div>
              )}

              {mode === 'logo' && imageSrc && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
                  <div className="text-green-600 mt-0.5">📌</div>
                  <div className="text-sm text-green-800">
                    <strong>Logo Cropping Mode:</strong>
                    <ul className="mt-1 list-disc list-inside space-y-1">
                      <li>Draw a rectangle around the bank logo</li>
                      <li>Click "Upload Logo" to save it</li>
                      <li>Saved to: <code>app/templates/logos/{template.templateId || 'TEMPLATE_ID'}.png</code></li>
                    </ul>
                  </div>
                </div>
              )}

              {imageSrc ? (
                <div className="dev-canvas-container" ref={canvasRef}>
                  <img
                    ref={imageRef}
                    src={imageSrc}
                    alt="Receipt"
                    onLoad={handleImageLoad}
                    className="w-full h-auto"
                    style={{ display: 'block' }}
                  />

                  {/* Zones SVG Overlay */}
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    style={{ zIndex: 10 }}
                  >
                    {/* Logo Crop Rectangle */}
                    {mode === 'logo' && logoCrop && (
                      <g>
                        <rect
                          x={logoCrop.x}
                          y={logoCrop.y}
                          width={logoCrop.width}
                          height={logoCrop.height}
                          fill="rgba(0, 255, 0, 0.2)"
                          stroke="#00ff00"
                          strokeWidth="2"
                          strokeDasharray="5,5"
                        />
                        <text
                          x={logoCrop.x + 5}
                          y={logoCrop.y + 15}
                          fill="#00ff00"
                          fontSize="12"
                          fontWeight="600"
                        >
                          LOGO
                        </text>
                      </g>
                    )}

                    {mode === 'zones' && zones.map(zone => {
                      const container = canvasRef.current;
                      if (!container) return null;

                      const rect = container.getBoundingClientRect();
                      const x = (zone.xPercent / 100) * rect.width;
                      const y = (zone.yPercent / 100) * rect.height;
                      const w = (zone.widthPercent / 100) * rect.width;
                      const h = (zone.heightPercent / 100) * rect.height;

                      return (
                        <g key={zone.id} className={zone.id === selectedZoneId ? 'selected' : ''}>
                          <rect
                            x={x}
                            y={y}
                            width={w}
                            height={h}
                            className="zone-rect"
                            style={{ pointerEvents: 'all' }}
                            onClick={() => setSelectedZoneId(zone.id)}
                          />
                          {/* Zone Label */}
                          <text
                            x={x + 5}
                            y={y + 15}
                            fill="var(--dev-accent)"
                            fontSize="11"
                            fontFamily="var(--dev-font-mono)"
                            fontWeight="600"
                            pointerEvents="none"
                          >
                            {zone.fieldName}
                          </text>
                          {/* Coordinates Badge */}
                          <text
                            x={x + 5}
                            y={y + h - 5}
                            fill="var(--dev-text-secondary)"
                            fontSize="10"
                            fontFamily="var(--dev-font-mono)"
                            opacity={0.7}
                            pointerEvents="none"
                          >
                            {zone.xPercent.toFixed(1)}%, {zone.yPercent.toFixed(1)}%
                          </text>
                        </g>
                      );
                    })}

                    {/* Drawing preview for zones */}
                    {mode === 'zones' && isDrawing && (
                      <rect
                        x={Math.min(drawStart.x, drawStart.x)}
                        y={Math.min(drawStart.y, drawStart.y)}
                        width={Math.abs(drawStart.x - drawStart.x)}
                        height={Math.abs(drawStart.y - drawStart.y)}
                        fill="rgba(0, 212, 255, 0.1)"
                        stroke="var(--dev-accent)"
                        strokeWidth={2}
                        strokeDasharray="5,5"
                      />
                    )}
                  </svg>

                  {/* Interactive overlay for mouse events */}
                  <div
                    className="absolute inset-0"
                    style={{ zIndex: 5 }}
                    onMouseDown={handleCanvasMouseDown}
                    onMouseMove={handleCanvasMouseMove}
                    onMouseUp={handleCanvasMouseUp}
                    onMouseLeave={handleCanvasMouseUp}
                  />
                </div>
              ) : (
                <div className="border-2 border-dashed border-[var(--dev-border)] rounded-lg p-12 text-center">
                  <Upload className="w-12 h-12 text-[var(--dev-text-muted)] mx-auto mb-4" />
                  <p className="text-[var(--dev-text-secondary)] mb-2">No image uploaded</p>
                  <p className="text-sm text-[var(--dev-text-muted)]">Upload a receipt image to start creating zones</p>
                </div>
              )}

              {/* Instructions */}
              {imageSrc && (
                <div className="mt-4 p-4 bg-[var(--dev-bg-tertiary)] rounded-lg border border-[var(--dev-border)]">
                  <p className="text-sm text-[var(--dev-text-secondary)]">
                    <span className="font-semibold text-[var(--dev-accent)]">Instructions:</span> Click and drag on the image to draw zones.
                    Click on a zone to select it. Drag zones to reposition.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Zone Properties */}
          <div className="space-y-4">
            {/* Selected Zone Properties */}
            {selectedZone && (
              <div className="dev-card p-6 slide-in-animation">
                <h3 className="text-lg font-semibold text-[var(--dev-text-primary)] mb-4">Zone Properties</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Field Name</label>
                    <select
                      value={selectedZone.fieldName}
                      onChange={(e) => updateZone(selectedZone.id, { fieldName: e.target.value })}
                      className="dev-input w-full"
                    >
                      {FIELD_NAMES.map(name => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm text-[var(--dev-text-secondary)] mb-2">Parser Type</label>
                    <select
                      value={selectedZone.parserType}
                      onChange={(e) => updateZone(selectedZone.id, { parserType: e.target.value })}
                      className="dev-input w-full"
                    >
                      {PARSER_TYPES.map(({ value, label }) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="text-sm text-[var(--dev-text-secondary)]">Required Field</label>
                    <button
                      onClick={() => updateZone(selectedZone.id, { required: !selectedZone.required })}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        selectedZone.required ? 'bg-[var(--dev-accent)]' : 'bg-[var(--dev-bg-secondary)]'
                      }`}
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                          selectedZone.required ? 'translate-x-6' : 'translate-x-0.5'
                        }`}
                      />
                    </button>
                  </div>

                  <div className="pt-4 border-t border-[var(--dev-border)]">
                    <div className="dev-coordinate mb-2">
                      X: {selectedZone.xPercent.toFixed(1)}%
                    </div>
                    <div className="dev-coordinate mb-2">
                      Y: {selectedZone.yPercent.toFixed(1)}%
                    </div>
                    <div className="dev-coordinate mb-2">
                      W: {selectedZone.widthPercent.toFixed(1)}%
                    </div>
                    <div className="dev-coordinate">
                      H: {selectedZone.heightPercent.toFixed(1)}%
                    </div>
                  </div>

                  <div className="flex gap-2 pt-4">
                    <button
                      onClick={() => testZoneOCR(selectedZone)}
                      className="dev-btn-secondary flex-1 flex items-center justify-center gap-2"
                    >
                      <TestTube className="w-4 h-4" />
                      Test OCR
                    </button>
                    <button
                      onClick={() => deleteZone(selectedZone.id)}
                      className="dev-btn-danger flex-1 flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Zones List */}
            <div className="dev-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-[var(--dev-text-primary)]">Zones ({zones.length})</h3>
                <span className="dev-badge">{zones.length} defined</span>
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {zones.length === 0 ? (
                  <p className="text-sm text-[var(--dev-text-muted)] text-center py-8">
                    No zones yet. Draw on the image to create zones.
                  </p>
                ) : (
                  zones.map(zone => (
                    <div
                      key={zone.id}
                      onClick={() => setSelectedZoneId(zone.id)}
                      className={`zone-list-item cursor-pointer ${zone.id === selectedZoneId ? 'selected' : ''}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-[var(--dev-accent)]" />
                        <div>
                          <p className="font-medium text-[var(--dev-text-primary)]">{zone.fieldName}</p>
                          <p className="text-xs text-[var(--dev-text-secondary)] font-mono">
                            {zone.parserType}
                          </p>
                        </div>
                      </div>
                      {zone.required && (
                        <span className="dev-badge text-[10px]">Required</span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="dev-card p-6">
              <h3 className="text-sm font-semibold text-[var(--dev-text-secondary)] mb-3">Image Size</h3>
              {imageSize.width > 0 ? (
                <div className="dev-coordinate">
                  {imageSize.width} × {imageSize.height}px
                </div>
              ) : (
                <p className="text-sm text-[var(--dev-text-muted)]">No image loaded</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
