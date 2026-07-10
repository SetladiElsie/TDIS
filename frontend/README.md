# Tender Document Extraction - Frontend

React-based frontend for the Tender Document Extraction Application.

## Project Structure

```
frontend/
├── public/
│   └── index.html              # Main HTML file
├── src/
│   ├── components/
│   │   ├── Upload.js           # Document upload component
│   │   └── Results.js          # Results display component
│   ├── services/
│   │   └── api.js              # API service with axios
│   ├── styles/
│   │   ├── App.css             # Main styles
│   │   ├── Upload.css          # Upload component styles
│   │   ├── Results.css         # Results component styles
│   │   └── index.css           # Additional styles
│   ├── utils/
│   │   └── helpers.js          # Utility functions
│   ├── App.js                  # Main app component
│   ├── index.js                # Entry point
│   └── index.css               # Global styles
├── package.json                # Dependencies
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Prerequisites

- Node.js 14+ and npm
- Backend API running on http://localhost:5000
- Git

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Edit `.env` file:

```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_API_TIMEOUT=30000
```

### 3. Start Development Server

```bash
npm start
```

The app will open at: **http://localhost:3000**

## Available Scripts

### `npm start`
Runs the app in development mode.

### `npm build`
Builds the app for production to the `build` folder.

### `npm test`
Launches the test runner.

### `npm eject`
Exposes all configuration files and dependencies.

## Features

### 📄 Document Upload
- Drag and drop file upload
- Support for PDF, DOCX, TXT, CSV, XLSX
- Maximum file size: 50MB
- Real-time upload progress tracking
- Automatic extraction after upload

### 📊 Results Display
- Beautiful card-based layout
- Search and filter functionality
- Paginated results list
- Detailed information view

### 📋 Extracted Information
- Tender ID and Name
- Organization and Location
- Scope of Work
- Closing Date (with formatting)
- Budget Information
- Contact Details
- Evaluation Criteria
- Deliverables
- Compulsory Documents
- And more...

### 💾 Export Options
- Download as JSON
- Download as CSV
- View in application

### 🔍 Search & Filter
- Search by tender name or ID
- Filter by extraction status
- Pagination support

## API Integration

The frontend communicates with the backend API at `http://localhost:5000/api`.

### Available Endpoints

- `POST /api/upload` - Upload document
- `POST /api/extract` - Extract information
- `GET /api/results/<id>` - Get results
- `GET /api/results` - List results
- `GET /api/export/<id>` - Export results
- `DELETE /api/results/<id>` - Delete result
- `GET /api/health` - Health check

## Components

### App.js
Main application component. Handles:
- API health check
- Page layout and structure
- State management
- Component orchestration

### Upload.js
Document upload component. Features:
- Drag and drop interface
- File selection dialog
- Upload progress tracking
- Automatic extraction

### Results.js
Results display component. Features:
- Results list with pagination
- Search functionality
- Detailed view
- Export options
- Delete functionality

## Services

### api.js
API service using Axios. Provides:
- Request/response interceptors
- Error handling
- All API endpoints as functions
- File download utilities

## Utilities

### helpers.js
Utility functions for:
- Date formatting (absolute and relative)
- Currency formatting
- File size formatting
- Text truncation
- Status color mapping
- File type validation
- Data parsing and validation

## Styling

### CSS Architecture
- Global styles in `App.css`
- Component-specific styles in separate CSS files
- CSS custom properties (variables) for theming
- Responsive design with media queries
- Utility classes for spacing and alignment

### Color Scheme
```
Primary:   #3b82f6 (Blue)
Secondary: #10b981 (Green)
Danger:    #ef4444 (Red)
Warning:   #f59e0b (Amber)
```

### Responsive Design
- Mobile-first approach
- Breakpoints: 768px, 1024px
- Flexible grid layout
- Touch-friendly buttons and inputs

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | http://localhost:5000/api |
| `REACT_APP_API_TIMEOUT` | API request timeout (ms) | 30000 |

## Error Handling

- Network errors
- File validation errors
- API errors with custom messages
- Toast notifications for user feedback

## Performance

- Lazy loading components
- Optimized re-renders
- Efficient API calls
- Pagination for large datasets

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Dependencies

### Main Dependencies
- **react** (18.2.0) - UI framework
- **react-dom** (18.2.0) - React DOM rendering
- **axios** (1.4.0) - HTTP client
- **react-dropzone** (14.2.3) - File upload
- **react-hook-form** (7.44.4) - Form handling
- **date-fns** (2.30.0) - Date utilities
- **react-toastify** (9.1.3) - Notifications
- **react-icons** (4.10.1) - Icon library

### Development Dependencies
- **react-scripts** (5.0.1) - Build tools
- **@testing-library/react** - Testing utilities

## Development Workflow

1. **Start Backend**
   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm start
   ```

3. **Open Application**
   Visit http://localhost:3000

## Testing

To test the application:

1. Upload a sample PDF/DOCX file
2. Wait for extraction to complete
3. View extracted information
4. Test search and filters
5. Test export functionality

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deployment

### Using a web server (Nginx)
```nginx
location / {
  root /path/to/frontend/build;
  try_files $uri /index.html;
}

location /api {
  proxy_pass http://backend:5000;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}
```

### Using Docker
See docker-compose.yml in the root directory

## Troubleshooting

### API Connection Failed
- Ensure backend is running on port 5000
- Check `REACT_APP_API_URL` in .env
- Check browser console for error details

### Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
npm start
```

### Port 3000 Already in Use
```bash
# Use a different port
PORT=3001 npm start
```

### Blank Screen
- Check browser console for errors
- Clear browser cache
- Verify API is running

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## Support

For issues or questions:
- Check the main README.md
- Review API documentation
- Check console for error messages

## License

Proprietary - 2026

---

**Version**: 1.0.0  
**Last Updated**: July 9, 2026
