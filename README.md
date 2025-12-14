# Media-dw

Media-dw is a Python command-line application for downloading videos and multimedia content from multiple platforms in an easy, interactive, and organized way.

## Features
- Download from multiple platforms: YouTube, Instagram, TikTok, X (Twitter), Facebook, Reddit, and Twitch.
- Automatic platform detection from a URL.
- Video/audio quality selection.
- Batch downloads from .txt or .csv files.
- Download history stored in JSON.
- Automatic organization by platform folders.
- Interactive console interface with colored output.

## Requirements
- Python 3.8+
- ffmpeg (required by yt-dlp for post-processing; install via your package manager)
- Python packages:
  - yt-dlp
  - instaloader
  - colorama

## Installation (Quick install)
1. Clone the repository:
   ```
   git clone https://github.com/eliasdev-1/Media-dw.git
   cd Media-dw
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
   If you don't have a requirements.txt, install directly:
   ```
   pip install yt-dlp instaloader colorama
   ```

3. Run the program:
   ```
   python main.py
   ```

## Usage
When you start the program, an interactive menu will appear with options to:
- Download a single video by pasting a URL.
- Download multiple URLs from a file (.txt or .csv).
- Select video/audio quality.
- View download history.
- Open the downloads folder automatically.

Downloaded files are saved in a `downloads/` folder organized by platform.

## Batch downloads
Create a text file with one URL per line:
```
https://www.youtube.com/watch?v=xxxx
https://www.instagram.com/reel/xxxx
https://www.tiktok.com/@user/video/xxxx
```
Then select the batch download option from the menu.

## Notes and caveats
- Some platforms may require authentication to download certain content (private videos, age-restricted, etc.). The tool may require cookies or credentials for those cases.
- ffmpeg is required for format conversion and some yt-dlp post-processing.
- Respect each platform's Terms of Service and local laws. Download only content you have the right to access.

## Contributing
Contributions are welcome! Please:
- Open issues for bugs or feature requests.
- Fork the repo and create pull requests for fixes/features.
- Add tests where appropriate and keep changes small and focused.

## License
Add a LICENSE file (e.g., MIT) to make the project's license explicit.

## Support
If you find this project useful and want to support development:
https://ko-fi.com/eliasdev

## Contact
For questions, open an issue or contact the maintainer via the repository.
