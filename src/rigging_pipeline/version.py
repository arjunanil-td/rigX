"""
RigX Pipeline Version Information
"""

# Version information
VERSION = "1.0.0"
VERSION_NAME = "RigX Pipeline"
BUILD_DATE = "2024-01-15"
BUILD_NUMBER = "001"

# Version details
VERSION_INFO = {
    "version": VERSION,
    "name": VERSION_NAME,
    "build_date": BUILD_DATE,
    "build_number": BUILD_NUMBER,
    "description": "Professional Rigging Pipeline for Maya",
    "author": "RigX Team",
    "website": "https://github.com/rigx/pipeline"
}

def get_version():
    """Get the current version string"""
    return VERSION

def get_version_info():
    """Get complete version information dictionary"""
    return VERSION_INFO.copy()

def get_version_string():
    """Get formatted version string for display"""
    return f"{VERSION_NAME} v{VERSION} (Build {BUILD_NUMBER})"

def get_detailed_version():
    """Get detailed version information for logging"""
    info = get_version_info()
    return f"""
────────────────────────────────────────────────────────────────────────
                           {VERSION_NAME}                               
                                                                        
  Version: {VERSION:<10} Build: {BUILD_NUMBER:<10} Date: {BUILD_DATE}   
  Description: Professional Rigging Pipeline for Maya                   
  Author: RigX Team                                                     
  Website: https://github.com/rigx/pipeline                             
────────────────────────────────────────────────────────────────────────
"""
