import { useState, useEffect } from 'react';
import { receiptService } from '../services/receiptService';

interface Zone {
  field_name: string;
  x_percent: number;
  y_percent: number;
  width_percent: number;
  height_percent: number;
  parser: string;
  required: boolean;
}

interface TemplateZones {
  template_id: string;
  template_name: string;
  image_size: number[];
  zones: Zone[];
}

interface ZoneOverlayProps {
  templateId: string | null;
  imageWidth: number;
  imageHeight: number;
}

// Color scheme for different field types (CAD/technical aesthetic)
const ZONE_COLORS = {
  date: '#06b6d4',      // Cyan
  time: '#0891b2',      // Darker cyan
  sender_name: '#8b5cf6', // Purple
  receiver_name: '#ec4899', // Pink
  amount: '#10b981',     // Emerald green
  fee: '#f59e0b',       // Amber
  note: '#6366f1',      // Indigo
  reference: '#f97316', // Orange
  default: '#94a3b8'     // Slate gray
};

export default function ZoneOverlay({ templateId, imageWidth, imageHeight }: ZoneOverlayProps) {
  const [zones, setZones] = useState<TemplateZones | null>(null);
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);

  useEffect(() => {
    if (templateId) {
      receiptService.getTemplateZones(templateId).then(setZones).catch(() => {
        setZones(null);
      });
    } else {
      setZones(null);
    }
  }, [templateId]);

  if (!zones || !zones.zones.length) {
    return null;
  }

  const getZoneColor = (fieldName: string): string => {
    if (fieldName in ZONE_COLORS) {
      return ZONE_COLORS[fieldName as keyof typeof ZONE_COLORS];
    }
    return ZONE_COLORS.default;
  };

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${imageWidth} ${imageHeight}`}
      preserveAspectRatio="none"
      style={{ mixBlendMode: 'multiply' }}
    >
      {zones.zones.map((zone) => {
        const x = (zone.x_percent / 100) * imageWidth;
        const y = (zone.y_percent / 100) * imageHeight;
        const width = (zone.width_percent / 100) * imageWidth;
        const height = (zone.height_percent / 100) * imageHeight;
        const color = getZoneColor(zone.field_name);
        const isHovered = hoveredZone === zone.field_name;

        return (
          <g key={zone.field_name}>
            {/* Zone box */}
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              fill={color}
              fillOpacity={isHovered ? 0.3 : 0.15}
              stroke={color}
              strokeWidth={isHovered ? 3 : 2}
              strokeDasharray={zone.required ? '0' : '5,5'}
              className="transition-all duration-200"
              onMouseEnter={() => setHoveredZone(zone.field_name)}
              onMouseLeave={() => setHoveredZone(null)}
            />

            {/* Zone label (shown on hover) */}
            {isHovered && (
              <>
                {/* Label background */}
                <rect
                  x={x}
                  y={y - 24}
                  width={120}
                  height={24}
                  fill="rgba(0, 0, 0, 0.85)"
                  rx="4"
                />
                {/* Label text */}
                <text
                  x={x + 8}
                  y={y - 8}
                  fill="white"
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="monospace"
                >
                  {zone.field_name}
                  {zone.required && ' *'}
                </text>
                {/* Coordinates */}
                <text
                  x={x + 8}
                  y={y - 8 + 14}
                  fill="#94a3b8"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {zone.x_percent.toFixed(0)}%, {zone.y_percent.toFixed(0)}%
                </text>
              </>
            )}
          </g>
        );
      })}

      {/* Legend */}
      <g transform={`translate(${imageWidth - 150}, 10)`}>
        <rect
          x={-10}
          y={-10}
          width={150}
          height={Object.keys(ZONE_COLORS).length * 20 + 20}
          fill="rgba(0, 0, 0, 0.8)"
          rx="4"
        />
        <text
          x="0"
          y="5"
          fill="white"
          fontSize="11"
          fontWeight="700"
          fontFamily="monospace"
        >
          ZONES
        </text>

        {Object.entries(ZONE_COLORS).map(([key, color], index) => (
          <g key={key} transform={`translate(0, ${20 + index * 18})`}>
            <rect
              x="0"
              y="-6"
              width="12"
              height="12"
              fill={color}
              rx="2"
            />
            <text
              x="18"
              y="4"
              fill="#cbd5e1"
              fontSize="10"
              fontFamily="monospace"
            >
              {key}
            </text>
          </g>
        ))}
      </g>
    </svg>
  );
}
