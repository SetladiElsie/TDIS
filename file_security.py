"""
Enhanced File Security Module for TDIS
======================================

Provides comprehensive file validation and security scanning:
- MIME type validation (prevents file extension spoofing)
- Virus/malware scanning with ClamAV
- Secure file storage outside web root
- File content analysis

Setup Requirements:
------------------
1. Install dependencies:
   pip install python-magic python-magic-bin clamd

2. Install ClamAV (Antivirus):
   
   Windows:
   - Download from: https://www.clamav.net/downloads
   - Or use Chocolatey: choco install clamav
   - Start daemon: clamd
   
   Linux:
   - Ubuntu/Debian: sudo apt-get install clamav clamav-daemon
   - CentOS/RHEL: sudo yum install clamav clamav-update clamd
   - Start: sudo systemctl start clamavd
   
   macOS:
   - brew install clamav
   - Start: brew services start clamav

3. Update virus definitions:
   - Windows: freshclam
   - Linux/macOS: sudo freshclam

Usage:
------
from file_security import validate_file_security, scan_for_viruses

# Validate uploaded file
result = validate_file_security(file_path, filename)
if not result['valid']:
    raise SecurityError(result['error'])

# Scan for viruses
scan_result = scan_for_viruses(file_path)
if scan_result['infected']:
    raise SecurityError(f"Virus detected: {scan_result['virus']}")
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from werkzeug.utils import secure_filename
from logger import get_logger

logger = get_logger(__name__)

# Try to import python-magic (with graceful fallback)
try:
    import magic
    MAGIC_AVAILABLE = True
    logger.info("python-magic loaded successfully")
except ImportError as e:
    MAGIC_AVAILABLE = False
    logger.warning(f"python-magic not available: {str(e)}")
    logger.warning("MIME validation will be disabled. Install with: pip install python-magic python-magic-bin")

# Allowed MIME types for uploads
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/msword',  # .doc
    'text/plain',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'application/rtf',
    'application/vnd.oasis.opendocument.text',  # .odt
}

# Mapping of MIME types to expected extensions
MIME_TO_EXTENSION = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'text/plain': ['.txt'],
    'text/csv': ['.csv'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/rtf': ['.rtf'],
    'application/vnd.oasis.opendocument.text': ['.odt'],
}


def get_mime_type(file_path: str) -> Optional[str]:
    """
    Get actual MIME type of file by analyzing its content
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string or None if detection fails
    """
    if not MAGIC_AVAILABLE:
        logger.warning("python-magic not available, cannot detect MIME type")
        return None
    
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        logger.debug(f"Detected MIME type for {file_path}: {mime_type}")
        return mime_type
    except Exception as e:
        logger.error(f"Failed to detect MIME type for {file_path}: {str(e)}")
        return None


def validate_mime_type(file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that file's actual MIME type matches its extension
    
    Args:
        file_path: Path to the file
        filename: Original filename with extension
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Get actual MIME type from file content
        actual_mime = get_mime_type(file_path)
        
        if not actual_mime:
            return False, "Could not determine file type"
        
        # Check if MIME type is allowed
        if actual_mime not in ALLOWED_MIME_TYPES:
            logger.warning(f"Rejected file {filename} with MIME type: {actual_mime}")
            return False, f"File type not allowed: {actual_mime}"
        
        # Verify extension matches MIME type
        file_ext = Path(filename).suffix.lower()
        expected_extensions = MIME_TO_EXTENSION.get(actual_mime, [])
        
        if expected_extensions and file_ext not in expected_extensions:
            logger.warning(
                f"File extension mismatch for {filename}: "
                f"extension={file_ext}, mime={actual_mime}, expected={expected_extensions}"
            )
            return False, f"File extension does not match content type"
        
        logger.info(f"File {filename} passed MIME validation: {actual_mime}")
        return True, None
        
    except Exception as e:
        logger.error(f"MIME validation error for {filename}: {str(e)}")
        return False, f"File validation failed: {str(e)}"


def scan_for_viruses(file_path: str) -> Dict[str, any]:
    """
    Scan file for viruses using ClamAV
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        Dict with keys:
        - scanned: bool (whether scan was performed)
        - infected: bool (whether virus was found)
        - virus: str (virus name if found)
        - error: str (error message if scan failed)
    """
    result = {
        'scanned': False,
        'infected': False,
        'virus': None,
        'error': None
    }
    
    try:
        import clamd
        
        # Try to connect to ClamAV daemon
        try:
            # Try Unix socket first (Linux/macOS)
            cd = clamd.ClamdUnixSocket()
            cd.ping()
        except Exception:
            try:
                # Try network socket (Windows or remote)
                cd = clamd.ClamdNetworkSocket()
                cd.ping()
            except Exception as e:
                logger.warning(f"ClamAV not available: {str(e)}")
                result['error'] = "Virus scanning not available"
                return result
        
        # Scan the file
        scan_result = cd.scan(file_path)
        result['scanned'] = True
        
        if scan_result:
            # scan_result format: {'/path/to/file': ('FOUND', 'Virus.Name')}
            file_result = scan_result.get(file_path)
            
            if file_result and file_result[0] == 'FOUND':
                result['infected'] = True
                result['virus'] = file_result[1]
                logger.error(f"🦠 VIRUS DETECTED in {file_path}: {file_result[1]}")
            else:
                logger.info(f"✅ File {file_path} is clean (no viruses)")
        else:
            logger.info(f"✅ File {file_path} is clean")
            
    except ImportError:
        logger.warning("clamd module not installed. Virus scanning disabled.")
        result['error'] = "Virus scanning module not installed"
    except Exception as e:
        logger.error(f"Virus scan error for {file_path}: {str(e)}")
        result['error'] = str(e)
    
    return result


def validate_file_security(file_path: str, filename: str, scan_viruses: bool = True) -> Dict[str, any]:
    """
    Comprehensive file security validation
    
    Args:
        file_path: Path to the uploaded file
        filename: Original filename
        scan_viruses: Whether to perform virus scanning (default: True)
        
    Returns:
        Dict with validation results:
        - valid: bool
        - mime_type: str
        - virus_scanned: bool
        - virus_found: bool
        - error: str (if validation failed)
    """
    result = {
        'valid': False,
        'mime_type': None,
        'virus_scanned': False,
        'virus_found': False,
        'error': None
    }
    
    # Step 1: Validate MIME type
    mime_valid, mime_error = validate_mime_type(file_path, filename)
    if not mime_valid:
        result['error'] = mime_error
        logger.warning(f"File security validation failed for {filename}: {mime_error}")
        return result
    
    result['mime_type'] = get_mime_type(file_path)
    
    # Step 2: Virus scan (if enabled)
    if scan_viruses:
        scan_result = scan_for_viruses(file_path)
        result['virus_scanned'] = scan_result['scanned']
        result['virus_found'] = scan_result['infected']
        
        if scan_result['infected']:
            result['error'] = f"Virus detected: {scan_result['virus']}"
            logger.error(f"🦠 Rejecting infected file {filename}: {scan_result['virus']}")
            return result
        
        if not scan_result['scanned'] and scan_result['error']:
            # Virus scanning failed, but we can continue with a warning
            logger.warning(f"Virus scan unavailable for {filename}: {scan_result['error']}")
    
    # All checks passed
    result['valid'] = True
    logger.info(f"✅ File {filename} passed all security validations")
    return result


def get_secure_upload_path(base_folder: str, filename: str) -> str:
    """
    Generate secure path for file upload outside web root
    
    Args:
        base_folder: Base upload folder path
        filename: Original filename
        
    Returns:
        Secure absolute path for storing the file
    """
    # Sanitize filename
    safe_filename = secure_filename(filename)
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(base_folder)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate full path
    file_path = upload_dir / safe_filename
    
    # Handle duplicates by adding number suffix
    counter = 1
    original_path = file_path
    while file_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        file_path = original_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    
    return str(file_path)


def is_clamav_available() -> bool:
    """
    Check if ClamAV is available and running
    
    Returns:
        True if ClamAV can be reached
    """
    try:
        import clamd
        
        try:
            cd = clamd.ClamdUnixSocket()
            cd.ping()
            return True
        except Exception:
            try:
                cd = clamd.ClamdNetworkSocket()
                cd.ping()
                return True
            except Exception:
                return False
    except ImportError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Testing and Diagnostics
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    """Test file security features"""
    
    print("🔒 TDIS File Security Module - Diagnostic Test\n")
    print("=" * 70)
    
    # Check python-magic
    print("\n1. Testing MIME Type Detection:")
    print("-" * 70)
    if MAGIC_AVAILABLE:
        try:
            mime = magic.Magic(mime=True)
            print(f"✅ python-magic loaded successfully")
            print(f"✅ Magic instance created: {mime}")
        except Exception as e:
            print(f"❌ Error creating magic instance: {str(e)}")
    else:
        print("❌ python-magic not available")
        print("   Install: pip install python-magic python-magic-bin")
    
    # Check ClamAV
    print("\n2. Testing Virus Scanning (ClamAV):")
    print("-" * 70)
    clamav_available = is_clamav_available()
    if clamav_available:
        print("✅ ClamAV is available and running")
    else:
        print("❌ ClamAV not available")
        print("\nInstallation Instructions:")
        print("  Windows:  choco install clamav  (or download from clamav.net)")
        print("  Linux:    sudo apt-get install clamav clamav-daemon")
        print("  macOS:    brew install clamav")
        print("\nStart daemon:")
        print("  Windows:  clamd")
        print("  Linux:    sudo systemctl start clamav-daemon")
        print("  macOS:    brew services start clamav")
        print("\nUpdate virus definitions:")
        print("  freshclam")
    
    # Test with sample file if available
    print("\n3. Testing File Validation:")
    print("-" * 70)
    
    # Look for a test file
    test_files = ['README.md', 'requirements.txt', '.env.example']
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
    
    if test_file:
        print(f"\nTesting with file: {test_file}")
        
        # Test MIME detection
        mime_type = get_mime_type(test_file)
        print(f"  Detected MIME type: {mime_type}")
        
        # Test full validation
        result = validate_file_security(test_file, test_file, scan_viruses=clamav_available)
        print(f"\nValidation Result:")
        print(f"  Valid: {result['valid']}")
        print(f"  MIME Type: {result['mime_type']}")
        print(f"  Virus Scanned: {result['virus_scanned']}")
        print(f"  Virus Found: {result['virus_found']}")
        if result['error']:
            print(f"  Error: {result['error']}")
    else:
        print("No test files found in current directory")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    
    features = {
        'MIME Type Validation': MAGIC_AVAILABLE,
        'Virus Scanning': clamav_available,
    }
    
    for feature, available in features.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {feature}: {status}")
    
    if all(features.values()):
        print("\n🎉 All security features are operational!")
    else:
        print("\n⚠️  Some security features need configuration")
        print("   See installation instructions above")
