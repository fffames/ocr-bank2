import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Edit, Download, RefreshCw, Grid3x3, Search } from 'lucide-react';
import { API_URL } from '../../services/api';
import '../../styles/developer.css';

interface Template {
  template_id: string;
  bank_name: string;
  description: string;
  num_zones: number;
  image_size: [number, number];
}

export default function TemplateManagement() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialog, setDeleteDialog] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('${API_URL}/api/templates/');
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (templateId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/templates/${templateId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setTemplates(prev => prev.filter(t => t.template_id !== templateId));
        setDeleteDialog(null);
      } else {
        alert('Failed to delete template');
      }
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  const exportTemplate = async (templateId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/templates/${templateId}`);
      const template = await response.json();

      const yaml = `
template_id: "${template.template_id}"
bank_name: "${template.bank_name}"
description: "${template.description}"
image_size: [${template.image_size.join(', ')}]
version: "1.0"

detection:
  primary_method: "keywords"
  keywords:
${template.detection.keywords.map((k: string) => `    - "${k}"`).join('\n')}

zones:
${Object.entries(template.zones).map(([name, zone]: [string, any]) => `  ${name}:
    x_percent: ${zone.x_percent}
    y_percent: ${zone.y_percent}
    width_percent: ${zone.width_percent}
    height_percent: ${zone.height_percent}
    parser: "${zone.parser}"
    required: ${zone.required}
    preprocessor: "${zone.preprocessor || 'grayscale'}"`).join('\n\n')}
`.trim();

      const blob = new Blob([yaml], { type: 'text/yaml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${templateId}.yaml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(`Failed to export: ${error}`);
    }
  };

  const filteredTemplates = templates.filter(t =>
    t.template_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.bank_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="dev-mode dev-grid-bg min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--dev-border)] bg-[var(--dev-bg-secondary)]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[var(--dev-text-primary)] flex items-center gap-2">
                <Grid3x3 className="w-6 h-6 text-[var(--dev-accent)]" />
                Template Management
              </h1>
              <p className="text-sm text-[var(--dev-text-secondary)] mt-1">
                Manage OCR templates for different bank receipt formats
              </p>
            </div>
            <button
              onClick={() => navigate('/developer/template-builder')}
              className="dev-btn flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Template
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filters */}
        <div className="dev-card p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--dev-text-muted)]" />
              <input
                type="text"
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="dev-input w-full pl-10"
              />
            </div>
            <button
              onClick={fetchTemplates}
              className="dev-btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Templates Grid */}
        {loading ? (
          <div className="dev-card p-12 text-center">
            <RefreshCw className="w-8 h-8 text-[var(--dev-accent)] animate-spin mx-auto mb-4" />
            <p className="text-[var(--dev-text-secondary)]">Loading templates...</p>
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="dev-card p-12 text-center">
            <Grid3x3 className="w-12 h-12 text-[var(--dev-text-muted)] mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-[var(--dev-text-primary)] mb-2">
              {searchQuery ? 'No templates found' : 'No templates yet'}
            </h3>
            <p className="text-[var(--dev-text-secondary)] mb-6">
              {searchQuery
                ? 'Try a different search term'
                : 'Create your first OCR template to get started'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => navigate('/developer/template-builder')}
                className="dev-btn flex items-center gap-2 mx-auto"
              >
                <Plus className="w-4 h-4" />
                Create Template
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((template) => (
              <div
                key={template.template_id}
                className="dev-card p-6 hover:border-[var(--dev-accent)] transition-all duration-200 group"
              >
                {/* Template Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-[var(--dev-text-primary)] mb-1">
                      {template.bank_name}
                    </h3>
                    <p className="text-xs text-[var(--dev-text-secondary)] font-mono">
                      {template.template_id}
                    </p>
                  </div>
                  <span className="dev-badge">{template.num_zones} zones</span>
                </div>

                {/* Description */}
                <p className="text-sm text-[var(--dev-text-secondary)] mb-4 line-clamp-2">
                  {template.description || 'No description'}
                </p>

                {/* Image Size */}
                <div className="flex items-center gap-2 mb-4">
                  <div className="dev-coordinate text-xs">
                    {template.image_size[0]} × {template.image_size[1]}px
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-[var(--dev-border)]">
                  <button
                    onClick={() => navigate(`/developer/template-builder/${template.template_id}`)}
                    className="dev-btn-secondary flex-1 flex items-center justify-center gap-2 text-xs"
                  >
                    <Edit className="w-3 h-3" />
                    Edit
                  </button>
                  <button
                    onClick={() => exportTemplate(template.template_id)}
                    className="dev-btn-secondary flex items-center justify-center gap-2 px-3"
                    title="Export YAML"
                  >
                    <Download className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => setDeleteDialog(template.template_id)}
                    className="dev-btn-danger flex items-center justify-center gap-2 px-3"
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="dev-card p-6 max-w-md w-full slide-in-animation">
            <h3 className="text-lg font-semibold text-[var(--dev-text-primary)] mb-2">
              Delete Template?
            </h3>
            <p className="text-sm text-[var(--dev-text-secondary)] mb-6">
              Are you sure you want to delete template "{deleteDialog}"? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteDialog(null)}
                className="dev-btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteDialog)}
                className="dev-btn-danger flex-1"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
