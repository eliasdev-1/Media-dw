#!/usr/bin/env python3

import os
import sys
import logging
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from yt_dlp import YoutubeDL
import instaloader
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constants and Configuration
# -------------------------------------------------------------------------
class Config:
    """Application configuration."""
    APP_NAME = "Media-dw"
    VERSION = "1.0.0"
    SUPPORTED_PLATFORMS = ["instagram", "tiktok", "twitter", "youtube", "facebook", "reddit", "twitch"]
    
    # Rate limiting settings
    REQUEST_DELAY = 1  # seconds between requests
    
    # Quality settings
    DEFAULT_QUALITY = "best"
    AVAILABLE_QUALITIES = ["best", "worst", "720p", "480p", "360p"]

# -------------------------------------------------------------------------
# Console Utilities
# -------------------------------------------------------------------------
def clear_console():
    """Clear console based on operating system."""
    os.system("cls" if os.name == "nt" else "clear")

def print_colored(text: str, color: str = Fore.WHITE, style: str = ""):
    """Print colored text with optional style."""
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def print_header(text: str):
    """Print section header."""
    print_colored(f"\n{'='*60}", Fore.CYAN)
    print_colored(f" {text}", Fore.CYAN, Style.BRIGHT)
    print_colored(f"{'='*60}", Fore.CYAN)

def print_success(message: str):
    """Print success message."""
    print_colored(f"{message}", Fore.GREEN)

def print_error(message: str):
    """Print error message."""
    print_colored(f"{message}", Fore.RED)

def print_warning(message: str):
    """Print warning message."""
    print_colored(f"{message}", Fore.YELLOW)

def print_info(message: str):
    """Print info message."""
    print_colored(f"{message}", Fore.BLUE)

# -------------------------------------------------------------------------
# Banner
# -------------------------------------------------------------------------
def display_banner():
    """Display application banner."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      UNIVERSAL MEDIA DOWNLOADER v1.0                     ║
║                                                          ║
║      Download videos from multiple platforms             ║
║      Made by Elias                                       ║
║      https://ko-fi.com/eliasdev                          ║
╚══════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)

# -------------------------------------------------------------------------
# Download Path Management
# -------------------------------------------------------------------------
def setup_download_path() -> Path:
    """Setup and return download path."""
    # Try multiple possible download locations
    possible_paths = [
        Path.home() / "Downloads",
        Path.home() / "downloads",
        Path.home() / "storage" / "downloads",  # Termux
        Path.cwd() / "downloads",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Create default download directory
    default_path = Path.cwd() / "downloads"
    default_path.mkdir(exist_ok=True)
    return default_path

def create_platform_folder(platform: str) -> Path:
    """Create platform-specific folder."""
    platform_path = DOWNLOAD_PATH / platform.capitalize()
    platform_path.mkdir(exist_ok=True)
    return platform_path

# -------------------------------------------------------------------------
# URL Validation and Processing
# -------------------------------------------------------------------------
def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def extract_video_id(url: str, platform: str) -> Optional[str]:
    """Extract video ID from URL based on platform."""
    try:
        parsed = urlparse(url)
        
        if platform == "youtube":
            if "youtu.be" in url:
                return parsed.path[1:]
            elif "youtube.com" in url:
                query = parse_qs(parsed.query)
                return query.get('v', [None])[0]
        
        elif platform == "instagram":
            # Extract shortcode from Instagram URL
            match = re.search(r'/(p|reel|tv)/([A-Za-z0-9_-]+)', url)
            return match.group(2) if match else None
        
        elif platform == "tiktok":
            # Extract video ID from TikTok URL
            match = re.search(r'/video/(\d+)', url)
            return match.group(1) if match else None
        
        elif platform == "twitter":
            # Extract tweet ID from Twitter URL
            match = re.search(r'/status/(\d+)', url)
            return match.group(1) if match else None
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
    
    return None

# -------------------------------------------------------------------------
# Platform Detection
# -------------------------------------------------------------------------
def detect_platform(url: str) -> Optional[str]:
    """Automatically detect platform from URL."""
    domain_patterns = {
        "youtube": r"(youtube\.com|youtu\.be)",
        "instagram": r"instagram\.com",
        "tiktok": r"tiktok\.com",
        "twitter": r"(twitter\.com|x\.com)",
        "facebook": r"facebook\.com",
        "reddit": r"reddit\.com",
        "twitch": r"twitch\.tv",
    }
    
    url_lower = url.lower()
    for platform, pattern in domain_patterns.items():
        if re.search(pattern, url_lower):
            return platform
    return None

# -------------------------------------------------------------------------
# Download Functions
# -------------------------------------------------------------------------
def get_ydl_options(platform: str, quality: str = None, output_path: Path = None) -> Dict:
    """Get yt-dlp options for specific platform."""
    options = {
        "outtmpl": str((output_path or DOWNLOAD_PATH) / "%(title)s.%(ext)s"),
        "quiet": False,
        "no_warnings": False,
        "noplaylist": True,
        "ignoreerrors": True,
        "no_color": True,
        "progress": True,
        "format": quality or Config.DEFAULT_QUALITY,
        "writethumbnail": True,
        "writeinfojson": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "subtitleslangs": ["en"],
    }
    
    # Platform-specific options
    if platform == "youtube":
        options.update({
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "merge_output_format": "mp4",
        })
    elif platform == "instagram":
        options.update({
            "cookiefile": "cookies.txt",  # Optional: for private content
        })
    
    return options

def download_with_ytdlp(url: str, platform: str, quality: str = None) -> bool:
    """Download content using yt-dlp."""
    try:
        platform_path = create_platform_folder(platform)
        options = get_ydl_options(platform, quality, platform_path)
        
        print_info(f"Starting download from {platform.capitalize()}...")
        print_info(f"Quality: {quality or Config.DEFAULT_QUALITY}")
        print_info(f"Save location: {platform_path}")
        
        start_time = time.time()
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if info:
                duration = time.time() - start_time
                print_success(f"Download completed successfully!")
                print_info(f"Title: {info.get('title', 'Unknown')}")
                print_info(f"Duration: {info.get('duration', 0)} seconds")
                print_info(f"Download time: {duration:.2f} seconds")
                print_info(f"File size: {info.get('filesize', 0) or 'Unknown'} bytes")
                return True
            else:
                print_error("Failed to extract video information")
                return False
                
    except Exception as e:
        print_error(f"Download failed: {str(e)}")
        logger.error(f"yt-dlp error for {url}: {e}", exc_info=True)
        return False

def download_instagram(url: str) -> bool:
    """Download Instagram content using instaloader."""
    try:
        print_info("Attempting Instagram download...")
        
        # Suppress instaloader logs
        logging.getLogger("instaloader").setLevel(logging.ERROR)
        
        # Create Instagram folder
        instagram_path = create_platform_folder("instagram")
        
        # Configure instaloader
        L = instaloader.Instaloader(
            download_videos=True,
            download_comments=False,
            save_metadata=False,
            quiet=True,
            dirname_pattern=str(instagram_path),
            filename_pattern="{shortcode}",
        )
        
        # Extract shortcode
        shortcode = extract_video_id(url, "instagram")
        if not shortcode:
            print_error("Could not extract Instagram shortcode from URL")
            return False
        
        print_info(f"Downloading Instagram post: {shortcode}")
        
        # Download post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=str(instagram_path))
        
        print_success(f"Instagram download completed: {post.title or shortcode}")
        return True
        
    except instaloader.exceptions.InstaloaderException as e:
        print_error(f"Instagram download failed: {e}")
        print_warning("This might be due to platform restrictions or private content.")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.error(f"Instagram download error: {e}", exc_info=True)
        return False

# -------------------------------------------------------------------------
# Batch Download Functions
# -------------------------------------------------------------------------
def download_from_file(filepath: str, platform: Optional[str] = None):
    """Download multiple URLs from a text file."""
    try:
        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print_error("No URLs found in file")
            return
        
        print_info(f"Found {len(urls)} URLs in file")
        
        success_count = 0
        for i, url in enumerate(urls, 1):
            print_header(f"Processing URL {i}/{len(urls)}")
            
            if not is_valid_url(url):
                print_error(f"Invalid URL: {url}")
                continue
            
            detected_platform = platform or detect_platform(url)
            if not detected_platform:
                print_error(f"Could not detect platform for: {url}")
                continue
            
            print_info(f"URL: {url}")
            print_info(f"Platform: {detected_platform}")
            
            if detected_platform == "instagram":
                success = download_instagram(url)
            else:
                success = download_with_ytdlp(url, detected_platform)
            
            if success:
                success_count += 1
            
            # Rate limiting
            if i < len(urls):
                print_info(f"Waiting {Config.REQUEST_DELAY} seconds before next download...")
                time.sleep(Config.REQUEST_DELAY)
        
        print_success(f"Batch download completed: {success_count}/{len(urls)} successful")
        
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")
    except Exception as e:
        print_error(f"Batch download failed: {e}")

# -------------------------------------------------------------------------
# History Management
# -------------------------------------------------------------------------
class DownloadHistory:
    """Manage download history."""
    
    def __init__(self):
        self.history_file = DOWNLOAD_PATH / "download_history.json"
        self.history = self.load_history()
    
    def load_history(self) -> List[Dict]:
        """Load download history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save download history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_entry(self, url: str, platform: str, success: bool, filename: str = None):
        """Add entry to download history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "platform": platform,
            "success": success,
            "filename": filename,
        }
        self.history.append(entry)
        
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self.save_history()
    
    def show_history(self, limit: int = 10):
        """Show recent download history."""
        if not self.history:
            print_info("No download history found")
            return
        
        recent = self.history[-limit:]
        
        print_header("Download History")
        for entry in reversed(recent):
            status = "Success" if entry["success"] else "Failed"
            color = Fore.GREEN if entry["success"] else Fore.RED
            print(f"{color}{status} {entry['timestamp']} - {entry['platform']}: {entry['url'][:50]}...")
        print()

# -------------------------------------------------------------------------
# Menu System
# -------------------------------------------------------------------------
def display_main_menu():
    """Display main menu."""
    print_colored("\n" + "="*60, Fore.CYAN)
    print_colored(f" {Config.APP_NAME} v{Config.VERSION}", Fore.CYAN, Style.BRIGHT)
    print_colored("="*60, Fore.CYAN)
    
    print(f"""
{Fore.YELLOW}Main Menu:{Style.RESET_ALL}

1. Single URL Download
2. Batch Download from File
3. Set Download Quality
4. View Download History
5. Open Downloads Folder
6. Clear Console
7. About
8. Exit

Supported Platforms: {', '.join(Config.SUPPORTED_PLATFORMS)}
Download Folder: {DOWNLOAD_PATH}
""")

def display_platform_menu():
    """Display platform selection menu."""
    print(f"""
{Fore.YELLOW}Select Platform:{Style.RESET_ALL}

1. Auto-detect
2. YouTube
3. Instagram
4. TikTok
5. Twitter/X
6. Other (yt-dlp)
7. Back to Main Menu
""")

def display_quality_menu():
    """Display quality selection menu."""
    print(f"""
{Fore.YELLOW}Select Quality:{Style.RESET_ALL}

1. Best (default)
2. 1080p
3. 720p
4. 480p
5. 360p
6. Worst (smallest size)
7. Back
""")

def get_menu_choice(prompt: str = "Enter your choice: ", min_val: int = 1, max_val: int = 8) -> int:
    """Get and validate menu choice."""
    while True:
        try:
            choice = input(f"{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()
            
            if choice.lower() in ['exit', 'quit', 'q']:
                return -1
            
            choice_int = int(choice)
            if min_val <= choice_int <= max_val:
                return choice_int
            else:
                print_error(f"Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print_error("Please enter a valid number")
        except KeyboardInterrupt:
            return -1

def get_url_input() -> Optional[str]:
    """Get URL input from user."""
    try:
        url = input(f"{Fore.CYAN}Enter video URL (or 'back' to return): {Style.RESET_ALL}").strip()
        
        if url.lower() in ['back', 'exit', 'quit']:
            return None
        
        if not url:
            print_warning("No URL entered")
            return None
        
        if not is_valid_url(url):
            print_error("Invalid URL format. Please include http:// or https://")
            return get_url_input()
        
        return url
    except KeyboardInterrupt:
        return None

def get_file_input() -> Optional[str]:
    """Get file path input from user."""
    try:
        filepath = input(f"{Fore.CYAN}Enter path to text file with URLs: {Style.RESET_ALL}").strip()
        
        if not filepath:
            print_warning("No file path entered")
            return None
        
        filepath = Path(filepath).expanduser()
        
        if not filepath.exists():
            print_error(f"File not found: {filepath}")
            return None
        
        if filepath.suffix.lower() not in ['.txt', '.csv']:
            print_warning("File should be a text file (.txt) or CSV file")
        
        return str(filepath)
    except KeyboardInterrupt:
        return None

# -------------------------------------------------------------------------
# Quality Settings
# -------------------------------------------------------------------------
class QualityManager:
    """Manage download quality settings."""
    
    def __init__(self):
        self.quality = Config.DEFAULT_QUALITY
        self.quality_map = {
            1: "best",
            2: "1080p",
            3: "720p",
            4: "480p",
            5: "360p",
            6: "worst",
        }
    
    def set_quality(self):
        """Set download quality."""
        display_quality_menu()
        choice = get_menu_choice("Select quality: ", 1, 7)
        
        if choice == 7 or choice == -1:
            return
        
        if choice in self.quality_map:
            self.quality = self.quality_map[choice]
            print_success(f"Quality set to: {self.quality}")
        else:
            print_error("Invalid quality choice")
    
    def get_quality(self) -> str:
        """Get current quality setting."""
        return self.quality

# -------------------------------------------------------------------------
# Main Application
# -------------------------------------------------------------------------
class MediaDownloaderApp:
    """Main application class."""
    
    def __init__(self):
        self.history = DownloadHistory()
        self.quality_manager = QualityManager()
        self.running = True
    
    def handle_single_download(self):
        """Handle single URL download."""
        display_platform_menu()
        platform_choice = get_menu_choice("Select platform: ", 1, 7)
        
        if platform_choice == -1:
            return
        
        if platform_choice == 7:  # Back
            return
        
        url = get_url_input()
        if not url:
            return
        
        # Determine platform
        if platform_choice == 1:  # Auto-detect
            platform = detect_platform(url)
            if not platform:
                print_error("Could not detect platform. Using yt-dlp...")
                platform = "other"
        else:
            platform_map = {
                2: "youtube",
                3: "instagram",
                4: "tiktok",
                5: "twitter",
                6: "other",
            }
            platform = platform_map.get(platform_choice, "other")
        
        print_info(f"Platform: {platform}")
        print_info(f"Quality: {self.quality_manager.get_quality()}")
        
        # Download
        if platform == "instagram":
            success = download_instagram(url)
        else:
            success = download_with_ytdlp(url, platform, self.quality_manager.get_quality())
        
        # Record in history
        self.history.add_entry(url, platform, success)
        
        if success:
            print_success("Download completed successfully!")
        else:
            print_error("Download failed. Check the error messages above.")
    
    def handle_batch_download(self):
        """Handle batch download from file."""
        filepath = get_file_input()
        if not filepath:
            return
        
        display_platform_menu()
        platform_choice = get_menu_choice("Select platform (or 1 for auto-detect): ", 1, 7)
        
        if platform_choice == -1 or platform_choice == 7:
            return
        
        platform = None
        if platform_choice != 1:  # Not auto-detect
            platform_map = {
                2: "youtube",
                3: "instagram",
                4: "tiktok",
                5: "twitter",
                6: "other",
            }
            platform = platform_map.get(platform_choice, "other")
        
        download_from_file(filepath, platform)
    
    def handle_open_downloads_folder(self):
        """Open downloads folder."""
        try:
            if os.name == "nt":  # Windows
                os.startfile(DOWNLOAD_PATH)
            elif os.name == "posix":  # macOS or Linux
                if sys.platform == "darwin":
                    os.system(f"open '{DOWNLOAD_PATH}'")
                else:
                    os.system(f"xdg-open '{DOWNLOAD_PATH}'")
            print_success(f"Opened downloads folder: {DOWNLOAD_PATH}")
        except Exception as e:
            print_error(f"Could not open folder: {e}")
    
    def handle_about(self):
        """Display about information."""
        print_header("About")
        print(f"{Fore.CYAN}{Config.APP_NAME} v{Config.VERSION}{Style.RESET_ALL}")
        print(f"Developed by Elias")
        print(f"Support here:")
        print(f" https://ko-fi.com/eliasdev")
        print(f"\n{Fore.YELLOW}Features:{Style.RESET_ALL}")
        print("• Download from multiple platforms")
        print("• Automatic platform detection")
        print("• Quality selection")
        print("• Batch downloads")
        print("• Download history")
        print(f"\n{Fore.YELLOW}Supported Platforms:{Style.RESET_ALL}")
        for platform in Config.SUPPORTED_PLATFORMS:
            print(f"  • {platform.capitalize()}")
        print(f"\n{Fore.YELLOW}Download Folder:{Style.RESET_ALL}")
        print(f"  {DOWNLOAD_PATH}")
        print()
    
    def run(self):
        """Main application loop."""
        clear_console()
        display_banner()
        
        print_info(f"Download folder: {DOWNLOAD_PATH}")
        print_info(f"Supported platforms: {', '.join(Config.SUPPORTED_PLATFORMS)}")
        
        while self.running:
            try:
                display_main_menu()
                choice = get_menu_choice()
                
                if choice == -1:  # Exit via keyboard
                    choice = 8
                
                if choice == 1:
                    self.handle_single_download()
                elif choice == 2:
                    self.handle_batch_download()
                elif choice == 3:
                    self.quality_manager.set_quality()
                elif choice == 4:
                    self.history.show_history()
                elif choice == 5:
                    self.handle_open_downloads_folder()
                elif choice == 6:
                    clear_console()
                    display_banner()
                elif choice == 7:
                    self.handle_about()
                elif choice == 8:
                    print_success("Thank you for using Media Downloader!")
                    self.running = False
                
                # Pause between operations
                if self.running and choice not in [6, 8]:
                    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
                    clear_console()
                    display_banner()
                    
            except KeyboardInterrupt:
                print_warning("\nInterrupted by user")
                confirm = input(f"{Fore.YELLOW}Do you want to exit? (y/n): {Style.RESET_ALL}").lower()
                if confirm in ['y', 'yes']:
                    print_success("Goodbye!")
                    self.running = False
            except Exception as e:
                print_error(f"Unexpected error: {e}")
                logger.error(f"Application error: {e}", exc_info=True)
                if self.running:
                    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

# -------------------------------------------------------------------------
# Global Variables
# -------------------------------------------------------------------------
DOWNLOAD_PATH = setup_download_path()

# -------------------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------------------
def main():
    """Application entry point."""
    try:
        app = MediaDownloaderApp()
        app.run()
    except Exception as e:
        print_error(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
