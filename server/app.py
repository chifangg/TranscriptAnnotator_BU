from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path

app = FastAPI(title="Transcript Annotator API")

# Enable CORS for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define data models
class TranscriptMessage(BaseModel):
    speaker: str
    timestamp: str
    content: str


class TranscriptSegment(BaseModel):
    start_index: int
    end_index: int
    title: str
    messages: List[TranscriptMessage]


class Annotation(BaseModel):
    id: int
    label: str
    description: Optional[str] = ""
    messageIndices: List[int]
    annotated_messages: Optional[List[TranscriptMessage]] = []
    timestamp: str


class AnnotationFile(BaseModel):
    transcriptFile: str
    annotations: List[Annotation]
    lastModified: str


# Ensure directories exist
TRANSCRIPTS_DIR = Path("transcripts")
ANNOTATIONS_DIR = Path("annotations")
# ANNOTATIONS_DIR = Path("annotation_offset")
SEGMENTED_DIR = Path("segmented")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)
ANNOTATIONS_DIR.mkdir(exist_ok=True)
SEGMENTED_DIR.mkdir(exist_ok=True)


def parse_transcript(content: str) -> List[TranscriptMessage]:
    """Parse transcript content into structured messages"""
    messages = []
    lines = content.split("\n")
    current_message = None

    for line in lines:
        line = line.strip()

        # Check if line matches speaker pattern: [Speaker Name] hh:mm:ss
        import re

        speaker_match = re.match(r"^\[([^\]]+)\]\s+(\d{1,2}:\d{2}:\d{2})$", line)

        if speaker_match:
            # If we were building a previous message, save it
            if current_message:
                # Join content lines and clean up extra empty lines
                content_text = "\n".join(current_message["content"]).strip()
                if content_text:  # Only add messages with actual content
                    messages.append(
                        TranscriptMessage(
                            speaker=current_message["speaker"],
                            timestamp=current_message["timestamp"],
                            content=content_text,
                        )
                    )

            # Start a new message
            current_message = {
                "speaker": speaker_match.group(1),
                "timestamp": speaker_match.group(2),
                "content": [],
            }
        elif current_message and line != "":
            # Add content line to current message
            current_message["content"].append(line)
        elif current_message and line == "":
            # Empty line - add spacing to content
            current_message["content"].append("")

    # Don't forget the last message
    if current_message:
        content_text = "\n".join(current_message["content"]).strip()
        if content_text:  # Only add messages with actual content
            messages.append(
                TranscriptMessage(
                    speaker=current_message["speaker"],
                    timestamp=current_message["timestamp"],
                    content=content_text,
                )
            )

    return messages


@app.get("/")
async def root():
    return {"message": "Transcript Annotator API"}


@app.get("/api/transcripts")
async def get_transcripts():
    """Get list of available transcript files"""
    try:
        transcript_files = []
        for folder_path in SEGMENTED_DIR.glob("*/"):
            if folder_path.is_dir():
                transcript_files.append(
                    {
                        "filename": folder_path.name,
                        "size": folder_path.stat().st_size,
                        "modified": folder_path.stat().st_mtime,
                    }
                )
        return transcript_files
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading transcripts: {str(e)}"
        )


@app.get("/api/transcripts/{filename}")
async def get_transcript_content(filename: str):
    """Get content of a specific transcript file"""
    try:
        file_path = TRANSCRIPTS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Transcript file not found")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"filename": filename, "content": content, "size": len(content)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript file not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading transcript: {str(e)}"
        )


@app.get("/api/transcripts/{filename}/parsed", response_model=List[TranscriptMessage])
async def get_parsed_transcript(filename: str):
    """Get parsed transcript content as structured messages"""
    try:
        file_path = TRANSCRIPTS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Transcript file not found")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parsed_messages = parse_transcript(content)
        return parsed_messages
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript file not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error parsing transcript: {str(e)}"
        )


@app.get(
    "/api/transcripts/{transcript_name}/segmented",
    response_model=List[TranscriptSegment],
)
async def get_segmented_transcript(transcript_name: str):
    """Get segmented transcript content as an array of segments"""
    try:
        # Remove .txt extension from filename to get the base name
        # base_name = transcript_name.replace(".txt", "")
        segment_dir = SEGMENTED_DIR / transcript_name

        if not segment_dir.exists():
            raise HTTPException(
                status_code=404, detail="Segmented transcript not found"
            )

        # Find all segment files in the directory
        segment_files = sorted(segment_dir.glob(f"*.json"))

        if not segment_files:
            raise HTTPException(status_code=404, detail="No segment files found")

        segments = []
        for segment_file in segment_files:
            with open(segment_file, "r", encoding="utf-8") as f:
                segment_data = json.load(f)

                # Convert the messages to TranscriptMessage objects
                messages = [
                    TranscriptMessage(
                        speaker=msg["speaker"],
                        timestamp=msg["timestamp"],
                        content=msg["content"].strip(),
                    )
                    for msg in segment_data["messages"]
                ]

                # Create the segment object
                segment = TranscriptSegment(
                    start_index=segment_data["start_index"],
                    end_index=segment_data["end_index"],
                    title=segment_data["title"],
                    messages=messages,
                )
                segments.append(segment)

        return segments

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Segmented transcript not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid segment file format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading segmented transcript: {str(e)}"
        )


@app.get("/api/annotations/get/{transcript_name}")
async def get_annotations(transcript_name: str):
    """Get annotations for a specific transcript"""
    try:
        # Convert transcript filename to annotation filename
        annotation_filename = transcript_name + ".json"
        file_path = ANNOTATIONS_DIR / annotation_filename

        if not file_path.exists():
            # Return empty annotations if file doesn't exist
            return {
                "transcriptFile": transcript_name,
                "annotations": [],
                "lastModified": None,
            }

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid annotation file format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading annotations: {str(e)}"
        )


@app.post("/api/annotations/save/{transcript_name}")
async def save_annotations(transcript_name: str, annotation_data: AnnotationFile):
    """Save annotations for a specific transcript"""
    try:
        # Convert transcript filename to annotation filename
        annotation_filename = transcript_name + ".json"
        file_path = ANNOTATIONS_DIR / annotation_filename

        # Ensure the annotation data has the correct transcript file name
        annotation_data.transcriptFile = transcript_name

        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(annotation_data.dict(), f, indent=2, ensure_ascii=False)

        return {
            "message": "Annotations saved successfully",
            "filename": annotation_filename,
            "annotationCount": len(annotation_data.annotations),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving annotations: {str(e)}"
        )


@app.delete("/api/annotations/{transcript_name}")
async def delete_annotations(transcript_name: str):
    """Delete annotations for a specific transcript"""
    try:
        annotation_filename = transcript_name + ".json"
        file_path = ANNOTATIONS_DIR / annotation_filename

        if file_path.exists():
            file_path.unlink()
            return {"message": "Annotations deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Annotation file not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting annotations: {str(e)}"
        )


@app.put("/api/annotations/{transcript_name}/{annotation_id}")
async def update_annotation_by_id(transcript_name: str, annotation_id: int, updated_annotation: Annotation):
    """Update a specific annotation by ID"""
    try:
        annotation_filename = transcript_name + ".json"
        file_path = ANNOTATIONS_DIR / annotation_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Annotation file not found")

        # Load existing annotations
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Find and update the annotation with the specified ID
        annotation_found = False
        for i, annotation in enumerate(data.get("annotations", [])):
            if annotation.get("id") == annotation_id:
                # Replace the entire annotation object but preserve the ID
                updated_annotation.id = annotation_id
                data["annotations"][i] = updated_annotation.dict()
                annotation_found = True
                break

        if not annotation_found:
            raise HTTPException(status_code=404, detail="Annotation not found")

        # Update lastModified timestamp
        data["lastModified"] = datetime.now().isoformat()

        # Save updated annotations
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "message": "Annotation updated successfully",
            "updatedId": annotation_id,
            "annotation": updated_annotation.dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating annotation: {str(e)}"
        )


@app.delete("/api/annotations/{transcript_name}/{annotation_id}")
async def delete_annotation_by_id(transcript_name: str, annotation_id: int):
    """Delete a specific annotation by ID"""
    try:
        annotation_filename = transcript_name + ".json"
        file_path = ANNOTATIONS_DIR / annotation_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Annotation file not found")

        # Load existing annotations
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Find and remove the annotation with the specified ID
        original_count = len(data.get("annotations", []))
        data["annotations"] = [
            annotation
            for annotation in data.get("annotations", [])
            if annotation.get("id") != annotation_id
        ]

        if len(data["annotations"]) == original_count:
            raise HTTPException(status_code=404, detail="Annotation not found")

        # Update lastModified timestamp
        data["lastModified"] = datetime.now().isoformat()

        # Save updated annotations
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "message": "Annotation deleted successfully",
            "deletedId": annotation_id,
            "remainingCount": len(data["annotations"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting annotation: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "transcripts_dir_exists": TRANSCRIPTS_DIR.exists(),
        "annotations_dir_exists": ANNOTATIONS_DIR.exists(),
        "transcript_files": len(list(TRANSCRIPTS_DIR.glob("*.txt"))),
        "annotation_files": len(list(ANNOTATIONS_DIR.glob("*.json"))),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
