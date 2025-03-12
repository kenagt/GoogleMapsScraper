# Setup Instructions for GoogleMapsScraper

Follow the steps below to set up the project on your system.

## 1. Install Visual Studio Code
Download and install [Visual Studio Code](https://code.visualstudio.com/) for your platform:
- **Windows**: [Download for Windows](https://code.visualstudio.com/download)
- **Mac**: [Download for Mac](https://code.visualstudio.com/download)

## 2. Set Up the Environment

Open the **Terminal** and execute the following commands:

```bash
# Check if Python is installed
python -v

# Install virtualenv
pip install virtualenv

# Change directory to the desired folder
cd path/to/your/folder

# Clone the repository
git clone https://github.com/kenagt/GoogleMapsScraper

# Navigate into the project folder
cd GoogleMapsScraper

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# Install required dependencies
python -m pip install -r requirements.txt

python google_maps_scraper.py
