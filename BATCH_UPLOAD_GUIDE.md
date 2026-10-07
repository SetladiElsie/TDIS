# Batch Upload Feature - User Guide

## 🎯 Overview

The TDIS app now supports **batch/multiple document upload**, allowing you to upload and extract multiple tender documents at once. This is perfect for processing entire folders of tender documents.

---

## ✨ Key Features

### 1. **Two Upload Modes**

**Single Upload Mode** (Default)
- Upload one document at a time
- Suitable for individual tender processing
- Simple, focused interface

**Batch Upload Mode** (New!)
- Upload multiple documents simultaneously
- Process entire folders of tender documents
- Track progress for each file individually
- Automatic extraction queue

### 2. **Batch Processing Capabilities**

✅ Upload multiple PDF, DOCX, TXT, CSV, or XLSX files  
✅ Process up to 50MB per file  
✅ Automatic extraction queue (processes one by one)  
✅ Real-time status tracking for each file  
✅ Drag & drop folder support  
✅ Individual file removal before upload  
✅ Skip unsupported files automatically  

---

## 🚀 How to Use Batch Upload

### Step 1: Switch to Batch Mode

1. Open the TDIS app: `http://localhost:3000`
2. Click the **"Batch Upload (Multiple Files)"** button
3. The interface switches to batch mode

### Step 2: Add Files

**Option A: Drag & Drop**
- Open your tender documents folder in File Explorer
- Select multiple files (or entire folder)
- Drag them into the upload area
- Valid files will be added to the queue

**Option B: Click to Browse**
- Click the upload area
- Hold `Ctrl` and click to select multiple files
- Or select an entire folder
- Click "Open"

### Step 3: Review Files

Before uploading, you can:
- ✅ See the list of files to be uploaded
- ✅ Check file sizes
- ✅ Remove individual files (click ✕ button)
- ✅ Click "Clear All" to start over

### Step 4: Upload & Extract

1. Click **"Upload & Extract All (X)"** button
2. Watch the progress:
   - 🟡 **Uploading...** - File being uploaded
   - 🔵 **Uploaded** - Upload complete
   - 🟣 **Extracting...** - Information being extracted
   - 🟢 **✓ Done** - Extraction complete
   - 🔴 **✗ Failed** - Error occurred

### Step 5: View Results

- All completed extractions appear in the Results section below
- Click on any tender to view extracted information
- Use filters to find specific tenders

---

## 📊 Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| **Uploading...** | 🟡 Yellow | File is being uploaded to server |
| **Uploaded** | 🔵 Blue | Upload complete, waiting for extraction |
| **Extracting...** | 🟣 Purple | Extraction in progress |
| **✓ Done** | 🟢 Green | Successfully completed |
| **✗ Failed** | 🔴 Red | Error occurred (hover for details) |

---

## 🎨 User Interface

### Batch Upload Screen

```
┌─────────────────────────────────────────────────────┐
│ Batch Upload Documents                      3 files │
├─────────────────────────────────────────────────────┤
│                                                     │
│             📁 Upload Multiple Documents             │
│         Drag and drop or click to browse            │
│    PDF, DOCX, TXT, CSV, XLSX (Max 50MB each)       │
│                                                     │
├─────────────────────────────────────────────────────┤
│ 📄 tender_rfq_001.pdf  (2.3 MB)  ✓ Done        ✕  │
│ 📄 tender_rfp_002.pdf  (1.8 MB)  Extracting... ✕  │
│ 📄 tender_bid_003.pdf  (3.1 MB)  Uploading...  ✕  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Clear All]              [Upload & Extract All (3)]│
└─────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints (Backend)

### 1. Batch Upload Endpoint

**POST** `/api/upload/batch`

Upload multiple files at once.

**Request:**
```
Content-Type: multipart/form-data

files: [File, File, File, ...]
assigned_user_id: <optional-user-id>
```

**Response:**
```json
{
  "message": "Uploaded 3 file(s)",
  "uploaded": [
    {
      "upload_id": "uuid-1",
      "filename": "tender_001.pdf",
      "file_size": 2356789,
      "status": "uploaded"
    },
    ...
  ],
  "skipped": [
    {
      "filename": "invalid.txt",
      "reason": "Unsupported format"
    }
  ],
  "total_uploaded": 3,
  "total_skipped": 0
}
```

### 2. Batch Extraction Endpoint

**POST** `/api/extract/batch`

Trigger extraction for multiple uploads.

**Request:**
```json
{
  "upload_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**Response:**
```json
{
  "message": "Started extraction for 3 file(s)",
  "extractions": [
    {
      "extraction_id": "extraction-uuid-1",
      "upload_id": "uuid-1",
      "status": "processing",
      "filename": "tender_001.pdf"
    },
    ...
  ],
  "errors": [],
  "total_started": 3,
  "total_errors": 0
}
```

---

## 💡 Use Cases

### 1. **Process Daily Tender Submissions**
Upload all tender documents received today in one batch.

### 2. **Bulk Historical Import**
Import an entire archive of old tender documents.

### 3. **Department-wide Upload**
Upload all tenders assigned to a specific department.

### 4. **Project-based Processing**
Upload all documents related to a specific project or RFQ batch.

---

## ⚙️ Configuration

### File Size Limits
- **Per file:** 50MB (configurable in backend)
- **Total batch:** No hard limit (limited by server memory)

### Supported Formats
- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)
- CSV Files (`.csv`)
- Excel Files (`.xlsx`, `.xls`)

### Concurrent Processing
- Files are extracted **sequentially** to avoid overwhelming the server
- Each extraction runs in a background thread
- Multiple batches can run simultaneously

---

## 🐛 Troubleshooting

### Problem: "File type not supported"
**Solution:** Only upload PDF, DOCX, TXT, CSV, or XLSX files.

### Problem: Files stuck at "Uploading..."
**Solution:** 
- Check your internet connection
- Ensure file size is under 50MB
- Try uploading fewer files at once

### Problem: Extraction shows "Failed"
**Solution:**
- Check if the document is corrupted
- Ensure the document contains extractable text
- Check backend logs for specific errors

### Problem: Some files skipped during upload
**Solution:**
- Check the error message for each skipped file
- Verify file format is supported
- Ensure files aren't corrupted

---

## 📁 Files Modified/Added

### Backend (`routes.py`)
- **Added:** `/api/upload/batch` endpoint
- **Added:** `/api/extract/batch` endpoint

### Frontend
- **Added:** `UploadBatch.js` component
- **Modified:** `App.js` - Added mode toggle
- **Modified:** `api.js` - Added batch API functions
- **Modified:** `App.css` - Added batch upload styles

---

## 🎯 Testing the Feature

### Test Single Upload
1. Switch to "Single Upload" mode
2. Upload one file
3. Verify extraction completes

### Test Batch Upload
1. Switch to "Batch Upload" mode
2. Drag 3-5 tender documents
3. Click "Upload & Extract All"
4. Verify all files process successfully
5. Check Results section for all extractions

### Test Error Handling
1. Try uploading an unsupported file (e.g., `.jpg`)
2. Verify it's skipped with error message
3. Try uploading a very large file (>50MB)
4. Verify appropriate error message

---

## 🚀 Current Status

✅ **Backend**: Both endpoints implemented and tested  
✅ **Frontend**: Batch upload UI complete  
✅ **Integration**: Mode toggle working  
✅ **Error Handling**: Comprehensive error messages  
✅ **Status Tracking**: Real-time progress indicators  

**The batch upload feature is fully functional!** 🎉

### How to Test Right Now

1. **Refresh browser**: `Ctrl + Shift + R`
2. **Click "Batch Upload (Multiple Files)"** button
3. **Drag multiple PDF files** into the upload area
4. **Click "Upload & Extract All"**
5. **Watch the magic happen!** ✨

---

## 📊 Performance Notes

- **Upload Speed**: Depends on file size and internet connection
- **Extraction Speed**: ~5-15 seconds per document
- **Recommended Batch Size**: 5-20 files for optimal performance
- **Large Batches**: 50+ files may take several minutes

---

**Questions or Issues?** Check the browser console (F12) for detailed logs and error messages.
