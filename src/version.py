"""
RigX Pipeline Version Information
"""

import subprocess
import os

# Version information
VERSION = "2.0.0"
VERSION_NAME = "RigX Pipeline"

# Cache for git date to avoid repeated calls
_git_date_cache = None

def get_git_commit_date():
    """Get the date of the latest git commit (cached)"""
    global _git_date_cache
    
    if _git_date_cache is not None:
        return _git_date_cache
    
    try:
        # Suppress command prompt window on Windows
        startupinfo = None
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Use timeout to prevent hanging
        result = subprocess.run(
            ['git', 'show', '-s', '--format=%ad', '--date=short', 'HEAD'],
            capture_output=True, text=True, timeout=2, 
            cwd=os.path.dirname(__file__),
            startupinfo=startupinfo
        )
        _git_date_cache = result.stdout.strip()
        return _git_date_cache
    except:
        _git_date_cache = "2025-09-22"  # Fallback date
        return _git_date_cache

# Lazy load the date - only get it when needed
def get_build_date():
    """Get build date (lazy loaded)"""
    return get_git_commit_date()
# Version details
VERSION_INFO = {
    "version": VERSION,
    "name": VERSION_NAME,
    "build_date": get_build_date(),
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
    return f"{VERSION_NAME} v{VERSION}"

def get_detailed_version():
    """Get detailed version information for logging"""
    info = get_version_info()
    return f"""
────────────────────────────────────────────────────────────────────────
                           {VERSION_NAME}                               
                                                                        
  Version: {VERSION:<10} Date: {get_build_date()}   
  Description: Professional Rigging Pipeline for Maya                   
  Author: RigX Team                                                     
  Website: https://github.com/rigx/pipeline                             
────────────────────────────────────────────────────────────────────────
"""
