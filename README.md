# Doccle Document Downloader

Automated document downloader for Doccle.be (Belgium). Runs on Windows with a simple GUI interface.

## Features

- ✅ Automatic login to Doccle.be
- ✅ Downloads all available documents
- ✅ Simple GUI interface (no technical knowledge required)
- ✅ Run on-demand (not scheduled)
- ✅ Saves credentials securely in local config file
- ✅ Detailed logging of all operations
- ✅ Option to run in background (headless mode)

## Requirements

### For End Users:
- Windows PC
- Google Chrome browser (installed)
- Internet connection

## Installation

1. **Install Python:**
   - Download from: https://www.python.org/downloads/
   - **IMPORTANT:** During installation, check the box "Add Python to PATH"
   - Click "Install Now"

2. **Extract this folder** to a location on your PC (e.g., `C:\Tools\DoccleDownloader`)

3. **Run the installer:**
   - Double-click `install.bat`
   - Wait for installation to complete (may take a few minutes)

4. **Configure your credentials:**
   - Open `config.json` with Notepad
   - Fill in your Doccle username and password
   - Optionally change the download folder
   - Save and close

5. **Run the downloader:**
   - Double-click `launcher.pyw`
   - The GUI will open - click "Download Documents"

## Configuration

Edit `config.json`:

```json
{
    "username": "your_email@example.com",
    "password": "your_password",
    "download_folder": "C:\\Users\\YourName\\Downloads\\Doccle",
    "wait_timeout": 20,
    "headless": false
}
```

- **username**: Your Doccle login email
- **password**: Your Doccle password
- **download_folder**: Where to save downloaded documents (use `\\` for Windows paths)
- **wait_timeout**: How long to wait for page elements (in seconds)
- **headless**: `true` = run browser in background, `false` = show browser window

## Usage

### With GUI (Recommended)

1. Double-click `launcher.pyw`
2. Verify/update your credentials in the GUI
3. Click "Download Documents"
4. Wait for completion (progress shown in log window)
5. Documents will be saved to your configured download folder

### Without GUI (Command Line)

```bash
python doccle_downloader.py
```

## Troubleshooting

### "Python is not recognized"
- Reinstall Python and make sure to check "Add Python to PATH"
- Or add Python to PATH manually

### "Chrome driver not found"
- The script automatically downloads the Chrome driver
- Make sure Google Chrome is installed
- If issues persist, check your internet connection

### "Login failed"
- Verify credentials in `config.json` are correct
- Try logging in manually at https://secure.doccle.be to verify account works
- Check if Doccle website structure has changed (may need script updates)

### "No documents found"
- The script may need adjustment for Doccle's current HTML structure
- Check `page_source.html` (automatically saved) to debug
- Contact script maintainer for updates

### Script runs but doesn't download anything
- Try setting `"headless": false` to see what's happening
- Check the `logs/` folder for detailed error messages
- Doccle may have updated their website structure

## File Structure

```
doccle/
├── doccle_downloader.py   # Main automation script
├── launcher.pyw            # GUI launcher (no console window)
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── install.bat            # Windows installer
├── README.md              # This file
└── logs/                  # Log files (created automatically)
```

## Security Notes

⚠️ **Important Security Information:**

- Your credentials are stored in plain text in `config.json`
- Keep this folder secure and don't share it
- Only run this on a trusted PC

## License

This is a personal automation tool. Use at your own risk.

## Changelog

### v1.0 (Initial Release)
- Basic login and download functionality
- GUI launcher
- Configuration management
- Logging system
