"""
Aegis Vault Version Information
Made by Samar in India 🇮🇳
"""

__version__ = "3.0.0"
__app_name__ = "Aegis Vault"
__author__ = "Samar"
__country__ = "India"
__description__ = "Modern Cloud Storage with Zero-Knowledge Encryption"

# Version metadata
VERSION_INFO = {
    "version": __version__,
    "name": __app_name__,
    "author": __author__,
    "country": __country__,
    "description": __description__,
    "release_date": "2024-06-06",
    "features": [
        "Multi-threaded uploads/downloads (6 concurrent workers)",
        "12+ cloud provider support",
        "Enhanced folder discovery",
        "AES-256 encryption",
        "Zero-knowledge architecture",
        "Modern UI with drag & drop",
    ]
}

def get_version_string():
    """Returns formatted version string."""
    return f"{__app_name__} v{__version__}"

def get_attribution():
    """Returns attribution string."""
    return f"Made by {__author__} in {__country__} 🇮🇳"

def print_version_info():
    """Prints full version information."""
    print(f"{__app_name__} v{__version__}")
    print(f"Made by {__author__} in {__country__} 🇮🇳")
    print(f"\n{__description__}")
    print(f"\nRelease Date: {VERSION_INFO['release_date']}")
    print("\nFeatures:")
    for feature in VERSION_INFO['features']:
        print(f"  • {feature}")

if __name__ == "__main__":
    print_version_info()
