# TranscriptAnnotator
A lightweight fullstack application for annotating transcripts.

## Quick Start

### Prerequisites

- [List required software versions]
- Node.js [version]
- Python [version]
- [Other dependencies]

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd TranscriptAnnotator
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Set up the backend:
   ```bash
    cd server
    # Create a virtual environment (recommended):
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    # install dependencies
    pip install -r requirements.txt
    ```

4. Download segmented transcript data from https://drive.google.com/drive/folders/1PIczCcO-nnndowr-JzVw50csUXgSBT_E?usp=sharing,
Then copy the segmented transcript data to `server/segmented/...`
### Running the Application

1. Start the backend server:
   ```bash
   cd server
   python app.py
   ```

2. In a new terminal, start the frontend:
   ```bash
   npm run dev
   ```

3. Open your browser to `http://localhost:[port]` (typically 5173)
## Project Structure

```
TranscriptAnnotator/
├── README.md                    # This file
├── package.json                 # Frontend dependencies
├── svelte.config.js            # Svelte configuration
├── vite.config.ts              # Vite build configuration
├── tsconfig.json               # TypeScript configuration
├── index.html                  # Main HTML entry point
├── public/                     # Static assets
├── src/                        # Frontend source code
│   ├── App.svelte             # Main Svelte component
│   ├── main.ts                # Application entry point
│   ├── app.css                # Global styles
│   ├── constants.ts           # Application constants
│   └── lib/                   # Reusable components
├── server/                     # Backend API server
│   ├── README.md              # Server documentation
│   ├── app.py                 # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── segmentation.ipynb     # Data processing notebook
│   ├── transcripts/           # Raw transcript files
│   ├── segmented/             # Processed transcript segments
│   └── annotations/           # Saved annotations
└── pure_html/                  # Alternative HTML implementation
    └── index.html
```