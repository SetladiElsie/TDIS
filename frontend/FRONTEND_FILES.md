# Frontend Files Reference

Complete React frontend implementation for Tender Document Extraction Application.

## Directory Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Upload.js
│   │   └── Results.js
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   │   ├── App.css
│   │   ├── Upload.css
│   │   ├── Results.css
│   │   └── index.css
│   ├── utils/
│   │   └── helpers.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
├── .env
├── .gitignore
├── README.md
├── QUICKSTART.md
└── FRONTEND_FILES.md (this file)
```

## Core Application Files (3 files)

### `src/App.js`
Main application component
- **Purpose**: Entry point for the React app
- **Features**:
  - API health check
  - Page layout structure (header, main, footer)
  - Component orchestration
  - Error handling for API connection
- **Dependencies**: Upload, Results components
- **Size**: ~2KB

### `src/index.js`
Application entry point
- **Purpose**: Render React app to DOM
- **Content**: Minimal setup with ReactDOM
- **Dependencies**: React, App component

### `public/index.html`
HTML template
- **Purpose**: Main HTML file served by development server
- **Features**:
  - Root div for React
  - Responsive viewport settings
  - Google Fonts import
  - Meta tags

## Components (2 files)

### `src/components/Upload.js`
Document upload component
- **Purpose**: Handle file uploads and extraction
- **Features**:
  - Drag-and-drop interface
  - File selection dialog
  - Upload progress tracking
  - File type validation
  - Real-time status updates
  - Toast notifications
- **Props**:
  - `onExtractionStart` - Callback when extraction starts
  - `onExtractComplete` - Callback with results
- **State**:
  - `file` - Selected file object
  - `uploading` - Upload status
  - `extracting` - Extraction status
  - `uploadProgress` - Progress percentage

### `src/components/Results.js`
Results display and management component
- **Purpose**: Show and manage extraction results
- **Features**:
  - Results list with pagination
  - Search functionality
  - Status filtering
  - Detailed information view
  - Export to JSON/CSV
  - Delete results
  - Responsive layout
- **Props**:
  - `data` - Initial extraction data
  - `refreshTrigger` - Trigger to refresh list
- **State**:
  - `results` - Array of results
  - `selectedResult` - Currently selected result
  - `page` - Current page number
  - `loading` - Loading state
  - `search` - Search query
  - `statusFilter` - Status filter value

## Services (1 file)

### `src/services/api.js`
API service using Axios
- **Purpose**: Handle all backend API calls
- **Features**:
  - Request interceptor
  - Response error handling
  - Timeout configuration
  - Base URL configuration
- **Functions**:
  - `uploadDocument(file)` - Upload document
  - `extractInformation(uploadId)` - Start extraction
  - `getResults(extractionId)` - Get extraction results
  - `listResults(params)` - List all results with pagination
  - `exportResults(extractionId, format)` - Export results
  - `deleteResult(extractionId)` - Delete result
  - `healthCheck()` - Check API health
- **Error Handling**: Custom error objects with message, code, and details

## Utilities (1 file)

### `src/utils/helpers.js`
Helper functions and utilities
- **Purpose**: Reusable utility functions
- **Functions** (15+):
  - `formatDate(dateString)` - Format date to readable format
  - `formatDateRelative(dateString)` - Format as relative time
  - `isClosingDatePassed(dateString)` - Check if date has passed
  - `formatCurrency(amount, currency)` - Format currency with symbols
  - `truncateText(text, length)` - Truncate text with ellipsis
  - `formatFileSize(bytes)` - Convert bytes to human-readable size
  - `getStatusColor(status)` - Get CSS class for status
  - `getStatusIcon(status)` - Get icon for status
  - `downloadJSON(data, filename)` - Download JSON file
  - `isFileTypeAllowed(file, allowedTypes)` - Validate file type
  - `getConfidenceDisplay(score)` - Format confidence score
  - `parseExtractionData(data)` - Parse and validate extraction data
  - And more...

## Styles (4 files)

### `src/styles/App.css`
Main global styles (800+ lines)
- **Purpose**: Base styles and utility classes
- **Includes**:
  - CSS custom properties (variables)
  - Global typography
  - Spacing utilities
  - Flex utilities
  - Button styles (.btn, .btn-primary, .btn-outline, etc.)
  - Form styles (.form-control, .form-label, etc.)
  - Card styles (.card, .card-header, .card-body, etc.)
  - Badge styles
  - Alert styles
  - Loading spinner animation
  - Text utilities
  - Grid layouts
  - Responsive breakpoints

### `src/styles/Upload.css`
Upload component styles
- **Purpose**: Styles specific to Upload component
- **Includes**:
  - Dropzone styling (active, hover states)
  - File preview layout
  - Progress bar animation
  - Status messages
  - Responsive design
  - Upload status indicators

### `src/styles/Results.css`
Results component styles
- **Purpose**: Styles for Results component
- **Includes**:
  - Two-column grid layout
  - Results list scrollable container
  - Result item cards
  - Search and filter bar
  - Pagination controls
  - Details section layout
  - Detail grid for information display
  - Lists with checkmarks
  - Responsive design
  - Tab/section styling

### `src/styles/index.css`
Additional global styles
- **Purpose**: Header, footer, and app layout
- **Includes**:
  - Header styling with gradient
  - Status badge and pulse animation
  - Main content area
  - Footer with columns
  - Code block styling
  - Responsive header/footer

## Configuration Files

### `package.json`
NPM configuration and dependencies
- **Main dependencies**:
  - react (18.2.0)
  - react-dom (18.2.0)
  - axios (1.4.0)
  - react-dropzone (14.2.3)
  - react-hook-form (7.44.4)
  - date-fns (2.30.0)
  - react-icons (4.10.1)
  - react-toastify (9.1.3)
  - lucide-react (0.263.1)
- **Scripts**: start, build, test, eject
- **Metadata**: name, version, description

### `.env`
Environment variables
- `REACT_APP_API_URL` - Backend API URL
- `REACT_APP_API_TIMEOUT` - API timeout in milliseconds

### `.gitignore`
Git ignore rules
- Node modules
- Build artifacts
- Environment files
- IDE settings
- OS-specific files

## Documentation Files

### `README.md`
Comprehensive frontend documentation (500+ lines)
- **Sections**:
  - Project structure
  - Prerequisites and installation
  - Available scripts
  - Features overview
  - API integration details
  - Component descriptions
  - Services documentation
  - Utilities reference
  - Styling architecture
  - Responsive design info
  - Browser support
  - Dependencies listing
  - Development workflow
  - Testing instructions
  - Production build
  - Deployment options
  - Troubleshooting
  - Contributing guidelines

### `QUICKSTART.md`
Quick start guide for developers
- **Content**:
  - Prerequisites
  - 3-step quick start (install, verify, start)
  - Expected behavior
  - Configuration
  - Common issues and solutions
  - Testing the application
  - File format support
  - File size limits
  - Browser support
  - Production build instructions

### `FRONTEND_FILES.md`
This file - Complete file manifest

## File Statistics

| Category | Count | Files |
|----------|-------|-------|
| Components | 2 | Upload.js, Results.js |
| Services | 1 | api.js |
| Utilities | 1 | helpers.js |
| Styles | 4 | App.css, Upload.css, Results.css, index.css |
| Config | 3 | package.json, .env, .gitignore |
| App Root | 3 | App.js, index.js, index.html |
| Docs | 3 | README.md, QUICKSTART.md, FRONTEND_FILES.md |
| **Total** | **20** | **Files** |

## Setup Instructions

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Edit `.env` file if backend is on different URL

### 3. Start Development Server
```bash
npm start
```

### 4. Open Application
Visit http://localhost:3000

## Key Features

✓ **Responsive Design** - Works on desktop, tablet, mobile  
✓ **Real-time Upload** - Progress tracking and instant feedback  
✓ **Advanced Search** - Find tenders by name, ID, or status  
✓ **Export Options** - Download as JSON or CSV  
✓ **Error Handling** - User-friendly error messages  
✓ **Toast Notifications** - Success, error, and info messages  
✓ **Professional UI** - Modern design with smooth animations  
✓ **Accessibility** - Semantic HTML and proper ARIA labels  
✓ **Performance** - Optimized rendering and lazy loading  
✓ **Mobile-Friendly** - Touch-friendly interface  

## API Integration Points

### Upload Flow
1. User selects file
2. `Upload.js` calls `uploadDocument()`
3. API returns `upload_id`
4. `extractInformation()` is called with `upload_id`
5. Results polling begins

### Results Flow
1. `Results.js` calls `listResults()` on mount
2. Results displayed in list
3. User clicks on result to view details
4. Export or delete options available

### Search & Filter
1. User types in search or changes filter
2. `listResults()` is called with parameters
3. Results update dynamically

## Styling System

### Color Variables
```css
--primary: #3b82f6
--secondary: #10b981
--danger: #ef4444
--warning: #f59e0b
--info: #06b6d4
--light: #f3f4f6
--dark: #1f2937
```

### Spacing Scale
```
1: 0.5rem (8px)
2: 1rem (16px)
3: 1.5rem (24px)
4: 2rem (32px)
5: 3rem (48px)
```

### Responsive Breakpoints
```
Mobile: < 768px
Tablet: 768px - 1024px
Desktop: > 1024px
```

## Performance Optimizations

- Lazy loading of components
- Efficient state updates
- Pagination for large datasets
- Debounced search input
- Optimized API calls
- Minimal re-renders
- CSS animations instead of JavaScript
- Image optimization

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome | ✅ Latest |
| Firefox | ✅ Latest |
| Safari | ✅ Latest |
| Edge | ✅ Latest |
| IE 11 | ❌ Not supported |

## Security Considerations

- Input validation on file upload
- XSS protection through React
- CSRF token in API calls (if needed)
- Secure API URL configuration
- No sensitive data in local storage

## Next Steps

1. **Run Frontend**: `npm start`
2. **Run Backend**: `python app.py`
3. **Test Upload**: Upload sample tender document
4. **Review Results**: Examine extracted information
5. **Export Data**: Download JSON or CSV
6. **Deploy**: Use production build

---

**Version**: 1.0.0  
**Created**: July 9, 2026  
**Status**: Ready for Development & Testing
