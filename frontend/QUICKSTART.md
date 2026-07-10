# Frontend Quick Start Guide

Get the React frontend running in minutes!

## Prerequisites

- Node.js 14+ and npm
- Backend API running on port 5000

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Verify Backend API

Ensure the backend is running:

```bash
# In another terminal
cd backend
python app.py
```

You should see: `* Running on http://127.0.0.1:5000`

### 3. Start Frontend

```bash
npm start
```

The app will automatically open at: **http://localhost:3000**

---

## What to Expect

### First Load
- Green "API Connected" status in header
- Upload area ready for files
- Empty results section

### Upload Flow
1. **Select a File**: Drag & drop or click to browse
2. **Upload**: Click "Upload & Extract"
3. **Processing**: Watch the progress indicator
4. **Results**: View extracted information on the right

### View Results
- **Search**: Find tenders by name or ID
- **Filter**: Filter by status (Completed, Processing, Failed)
- **Details**: Click any result to see full information
- **Export**: Download as JSON or CSV
- **Delete**: Remove unwanted results

---

## Configuration

Edit `frontend/.env` if needed:

```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_API_TIMEOUT=30000
```

---

## Common Issues

### "API is not running" Message
- Start the backend: `python app.py` in the backend folder
- Verify it's running on port 5000
- Refresh the browser

### Port 3000 Already in Use
```bash
PORT=3001 npm start
```

### Module Not Found Errors
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
npm start
```

### Blank Page
- Check browser console (F12)
- Ensure backend is running
- Clear browser cache (Ctrl+Shift+Delete)

---

## Testing the Application

### Test File Formats
The app supports:
- 📄 PDF files
- 📝 Word documents (.docx, .doc)
- 📋 Text files (.txt)
- 📊 Excel spreadsheets (.xlsx)
- 🗂️ CSV files

### Sample Test Flow
1. Prepare a sample tender document
2. Upload through drag-and-drop
3. Wait for extraction (usually 2-5 seconds)
4. Review extracted information
5. Export and download results

---

## Available Commands

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject configuration (irreversible)
npm eject
```

---

## What Gets Extracted?

The application automatically extracts:

✓ Tender ID  
✓ Tender Name  
✓ Organization  
✓ Scope of Work  
✓ Closing Date  
✓ Budget  
✓ Contact Information  
✓ Location  
✓ Evaluation Criteria  
✓ Deliverables  
✓ Required Documents  

---

## File Size Limits

- **Maximum**: 50 MB per file
- **Recommended**: Under 10 MB for faster processing

---

## Browser Support

- ✅ Chrome (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Edge (Latest)

---

## Next Steps

1. **Upload Documents**: Test with various tender documents
2. **Review Results**: Examine extracted information
3. **Export Data**: Download in JSON or CSV format
4. **Integration**: Integrate into your workflow

---

## Need Help?

### Check These Files
- `README.md` - Full documentation
- `src/services/api.js` - API calls
- `src/utils/helpers.js` - Utility functions
- `src/components/` - Component source code

### Common Paths
- Frontend files: `frontend/src/`
- Styles: `frontend/src/styles/`
- Services: `frontend/src/services/`
- Components: `frontend/src/components/`

---

## Production Build

When ready to deploy:

```bash
npm run build
```

This creates an optimized `build/` folder ready for deployment.

---

**Happy Extracting!** 🚀
