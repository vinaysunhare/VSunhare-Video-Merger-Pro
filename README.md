# SunhareTech Video Studio - Pro Merger 🎬

A professional, lightning-fast GUI desktop application to merge multiple video files without losing quality or re-encoding. Built with Python, PyQt5, and FFmpeg, this tool is designed to handle heavy video files (like long gameplay recordings) in seconds.

## ✨ Key Features

* **Zero-Loss Merging:** Uses FFmpeg's `-c copy` method to stitch videos together instantly without rendering or quality degradation.
* **Premium Dark UI:** A sleek, modern interface inspired by professional studio software.
* **Drag & Drop Workflow:** Directly drag videos from your file manager into the application to add them.
* **Real-Time Metadata:** Automatically extracts and displays video duration, resolution, and file size using `ffprobe` before merging.
* **Anti-Freeze Tech:** Runs the FFmpeg merging process on a background `QThread` so the UI remains smooth and responsive.
* **Total Duration Calculator:** Instantly calculates the total estimated length of the final merged video as you add or remove clips.

## 🛠️ Prerequisites

Before running this application, ensure you have the following installed on your system:
1. **Python 3.x**
2. **FFmpeg & FFprobe:** Must be installed and added to your system's Environment Variables (PATH).
   * **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`
   * **Windows:** Download from the official FFmpeg site and add the `bin` folder to your PATH.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YourUsername/VSunhare-Video-Merger-Pro.git](https://github.com/YourUsername/VSunhare-Video-Merger-Pro.git)
   cd VSunhare-Video-Merger-Pro
