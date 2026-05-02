# Developer Mode - OCR Template Builder

## 🎯 Overview

The Developer Mode provides a visual interface for creating and managing OCR templates for Thai bank receipts. Instead of manually calculating coordinates and editing YAML files, you can now draw zones directly on receipt images.

## 🚀 Features

### **Template Builder** (`/developer/template-builder`)
- **Visual Canvas**: Upload receipt images and draw zones by clicking and dragging
- **Real-time Coordinates**: See zone positions update in real-time as you draw
- **Zone Properties Panel**: Configure field names, parser types, and requirements
- **OCR Testing**: Test OCR on individual zones before saving
- **Template Metadata**: Define template ID, bank name, and detection keywords

### **Template Management** (`/developer/templates`)
- **Template Gallery**: View all created templates in a grid layout
- **Quick Actions**: Edit, export YAML, or delete templates
- **Search**: Find templates by ID or bank name
- **Template Stats**: See image size and zone count at a glance

### **Mode Toggle**
- Seamless switching between User Mode and Developer Mode
- Distinct visual themes for each mode
- Separate navigation and routing

## 🎨 Design Aesthetic

The developer interface uses a **"Precision Technical"** design language:
- **Dark theme** with cyan/teal accents (#00d4ff)
- **Grid overlay patterns** on canvas (CAD-like feel)
- **Monospace fonts** for coordinates and technical data
- **Glass morphism** cards with backdrop blur
- **Smooth animations** for zone creation and selection
- **High contrast** zones with glowing borders

## 📖 How to Use

### Creating a New Template

1. **Access Developer Mode**
   - Click "Developer Mode" button in the top-right of User Mode
   - Or navigate directly to `/developer/templates`

2. **Start Template Builder**
   - Click "New Template" button
   - Or navigate to `/developer/template-builder`

3. **Upload Receipt Image**
   - Click "Upload Image" button
   - Select a sample receipt image from your bank

4. **Fill Template Metadata**
   ```
   Template ID:   krungthai_kplus
   Bank Name:     Krungthai Bank (K+)
   Description:   K+ mobile banking receipt format
   Keywords:      K+, Krungthai, เลขที่ใบสำคัญ
   ```

5. **Draw Zones**
   - Click and drag on the image to create a rectangular zone
   - The zone will appear with a cyan border and label
   - Coordinates are displayed in real-time

6. **Configure Zone Properties**
   - Click on a zone to select it
   - Choose the **Field Name** (date, time, amount, etc.)
   - Select the **Parser Type** (Thai Date, Thai Amount, etc.)
   - Toggle **Required** if the field is mandatory

7. **Test OCR** (Optional)
   - Click "Test OCR" button on a selected zone
   - View the extracted text to verify the zone is correct

8. **Save Template**
   - Click "Save Template" button
   - The template is saved to the backend and ready to use

### Managing Templates

1. **View All Templates**
   - Navigate to `/developer/templates`
   - See all templates in a card grid layout

2. **Search Templates**
   - Use the search bar to filter by template ID or bank name

3. **Export Template**
   - Click the download icon on any template card
   - Downloads the template as a YAML file

4. **Delete Template**
   - Click the trash icon on any template card
   - Confirm deletion in the dialog

## 🎯 Available Field Types

| Field Name | Parser Type | Description |
|-----------|-------------|-------------|
| `date` | Thai Date | Date with Buddhist era conversion (2567 → 2024) |
| `time` | Time | Time in HH:MM format |
| `sender_name` | Thai Name | Sender name with title prefix (นาย, นาง, etc.) |
| `sender_account` | Account Number | Sender account number |
| `receiver_name` | Thai Name | Receiver name with title prefix |
| `receiver_account` | Account Number | Receiver account number |
| `amount` | Thai Amount | Transaction amount with currency |
| `fee` | Thai Amount | Transaction fee |
| `reference` | Plain Text | Reference number |
| `note` | Plain Text | Additional notes |

## 🧪 Testing

### Start the Frontend
```bash
cd frontend
npm run dev
```

### Start the Backend
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### Access the Application
- **User Mode**: http://localhost:5173/
- **Developer Mode**: http://localhost:5173/developer/templates

## 📁 File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── developer/
│   │       ├── TemplateBuilder.tsx      # Main template builder
│   │       └── TemplateManagement.tsx   # Template list/management
│   ├── styles/
│   │   └── developer.css                # Developer mode design system
│   └── App.tsx                          # Updated with mode toggle
```

## 🎨 CSS Variables

The developer mode uses these CSS custom properties:

```css
--dev-bg-primary: #0a0e27;      /* Main background */
--dev-bg-secondary: #151932;    /* Card background */
--dev-bg-tertiary: #1a1f3a;     /* Input background */
--dev-border: #2d3561;           /* Border color */
--dev-accent: #00d4ff;           /* Primary accent (cyan) */
--dev-text-primary: #e8eaf0;     /* Main text */
--dev-text-secondary: #9ca3af;   /* Secondary text */
```

## 🔧 Technical Details

### Zone Coordinates
- Zones are stored as **percentages** (not pixels)
- This makes templates scalable across different image sizes
- Example: `x_percent: 5.0` means 5% from the left edge

### Zone Creation
1. **MouseDown**: Start drawing at current position
2. **MouseMove**: Update zone dimensions in real-time
3. **MouseUp**: Finalize zone and open properties panel

### Zone Selection
- Click on any zone to select it
- Selected zones have:
  - Brighter cyan border
  - Glowing shadow effect
  - Coordinates highlighted in properties panel

## 🚀 Performance

- **Fast rendering**: Canvas-based zone overlay
- **Smooth animations**: CSS transitions for all interactions
- **Real-time feedback**: Coordinates update as you drag
- **Responsive**: Works on desktop and tablet screens

## 🎯 Next Steps

### Future Enhancements
- [ ] Zone resizing with corner handles
- [ ] Duplicate zone functionality
- [ ] Bulk zone creation from templates
- [ ] Template preview mode
- [ ] Import from YAML file
- [ ] Zone validation warnings
- [ ] Undo/redo for zone operations

## 📝 Notes

- Templates are saved to the backend at `/backend/app/templates/*.yaml`
- The frontend communicates with backend APIs at `http://localhost:8000/api/templates/`
- Zone coordinates are automatically validated (0-100% range)
- Image dimensions are displayed in pixels for reference

## 🐛 Troubleshooting

### Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS Issues
Ensure backend has CORS enabled for `http://localhost:5173`

### Canvas Not Responding
- Check browser console for errors
- Verify image is loaded before drawing zones
- Ensure canvas container has valid dimensions

## 🎉 Success!

You now have a fully functional developer mode for creating OCR templates visually. No more manual YAML editing or coordinate calculations!

---

**Built with** ❤️ **using React, TypeScript, Tailwind CSS, and the frontend-design skill**
