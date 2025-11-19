# Transcript Annotator

A web-based tool for annotating transcripts with a FastAPI backend for persistent storage.

## Setup Instructions

### 1. Create a Virtual Environment (Recommended)

#### Using venv (Python 3.3+):
```bash
python -m venv transcript-annotator-env
source transcript-annotator-env/bin/activate  # On Windows: transcript-annotator-env\Scripts\activate
```

#### Using conda:
```bash
conda create -n transcript-annotator python=3.9
conda activate transcript-annotator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Server

```bash
python app.py
```

Alternatively, you can run it directly with uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### 4. Open the Application

#### Option A: Using VS Code Live Server (Recommended)
1. Install the "Live Server" extension in VS Code
2. Right-click on `index.html` and select "Open with Live Server"
3. The application will open in your browser and automatically connect to the FastAPI server
4. **Note**: The project includes `.vscode/settings.json` with Live Server configuration to prevent auto-refresh when annotation files are saved

#### Option B: Direct Browser Access
1. Open `index.html` directly in your web browser
2. The application will connect to the FastAPI server at `http://localhost:8000`

## VS Code Configuration

This project includes a `.vscode/settings.json` file with the following configurations:
- **Live Server ignore patterns**: Prevents page refresh when annotation files are saved
- **Python interpreter path**: Points to the virtual environment
- **File exclusions**: Hides Python cache files from the explorer

These settings are automatically applied when you open the project in VS Code.

## Directory Structure

```
TranscriptAnnotator/
├── .vscode/
│   └── settings.json     # VS Code workspace settings (Live Server config)
├── app.py                 # FastAPI server
├── index.html            # Frontend application
├── requirements.txt      # Python dependencies
├── transcripts/          # Transcript files (.txt)
│   └── Alex.txt
└── annotations/         # Annotation files (.json)
    └── Alex.json
```

## API Endpoints

- `GET /api/transcripts` - List all transcript files
- `GET /api/transcripts/{filename}` - Get transcript content
- `GET /api/annotations/{transcript_name}` - Get annotations for a transcript
- `POST /api/annotations/{transcript_name}` - Save annotations for a transcript
- `DELETE /api/annotations/{transcript_name}` - Delete annotations for a transcript
- `GET /api/health` - Health check

## Usage

1. **Start the server**: Run `python app.py`
2. **Open the app**: Open `index.html` in your browser
3. **Load transcripts**: Transcripts are automatically loaded from the `transcripts/` directory
4. **Create annotations**: Select messages and annotate them
5. **Automatic saving**: Annotations are automatically saved to the server
6. **Export/Import**: Use the Export/Import buttons for manual backup

## Features

- **Real-time annotation**: Create annotations by selecting message ranges
- **Persistent storage**: Annotations are automatically saved to JSON files
- **Speaker filtering**: Filter messages by speaker
- **Custom colors**: Customize speaker colors
- **Export/Import**: Manual backup and restore functionality
- **Split panel layout**: Messages on the left, annotations on the right

## Troubleshooting

- **CORS errors**: Make sure the server is running on `http://localhost:8000`
- **File not found**: Ensure transcript files are in the `transcripts/` directory
- **Server connection**: Check that the FastAPI server is running and accessible