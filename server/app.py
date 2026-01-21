from fastapi import FastAPI, HTTPException, Request
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
    x: Optional[float] = 0
    y: Optional[float] = 0
    categories: List[str] = []


class CategoryAssignment(BaseModel):
    transcriptFile: str
    annotationId: int


class Category(BaseModel):
    label: str
    annotations: List[CategoryAssignment] = []


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
CATEGORIES_FILE = ANNOTATIONS_DIR / "categories.json"


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


def load_categories() -> List[Category]:
    """Load categories from disk, creating file if missing"""
    if not CATEGORIES_FILE.exists():
        CATEGORIES_FILE.write_text("[]", encoding="utf-8")
        return []
    with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Category(**c) for c in raw]


def save_categories(categories: List[Category]) -> None:
    CATEGORIES_FILE.write_text(
        json.dumps([c.dict() for c in categories], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def ensure_annotation_file(transcript_name: str) -> Path:
    annotation_filename = transcript_name + ".json"
    file_path = ANNOTATIONS_DIR / annotation_filename
    if not file_path.exists():
        empty = {
            "transcriptFile": transcript_name,
            "annotations": [],
            "lastModified": None,
        }
        file_path.write_text(json.dumps(empty, indent=2), encoding="utf-8")
    return file_path


def add_category_to_annotation(transcript_name: str, annotation_id: int, category_label: str):
    file_path = ensure_annotation_file(transcript_name)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for ann in data.get("annotations", []):
        if ann.get("id") == annotation_id:
            ann.setdefault("categories", [])
            if category_label not in ann["categories"]:
                ann["categories"].append(category_label)
                updated = True
            break

    if updated:
        data["lastModified"] = datetime.now().isoformat()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def remove_category_from_annotation(transcript_name: str, annotation_id: int, category_label: str):
    file_path = ensure_annotation_file(transcript_name)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for ann in data.get("annotations", []):
        if ann.get("id") == annotation_id:
            if "categories" in ann and category_label in ann["categories"]:
                ann["categories"] = [c for c in ann["categories"] if c != category_label]
                updated = True
            break

    if updated:
        data["lastModified"] = datetime.now().isoformat()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def rename_category_in_annotations(old_label: str, new_label: str):
    """Replace category label across all annotations files."""
    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        if ann_file.name == "categories.json":
            continue
        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        for ann in data.get("annotations", []):
            if "categories" in ann:
                if old_label in ann["categories"]:
                    ann["categories"] = [new_label if c == old_label else c for c in ann["categories"]]
                    changed = True

        if changed:
            data["lastModified"] = datetime.now().isoformat()
            with open(ann_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)


def remove_category_globally(label: str):
    """Remove category label from all annotations files."""
    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        if ann_file.name == "categories.json":
            continue
        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        for ann in data.get("annotations", []):
            if "categories" in ann and label in ann["categories"]:
                ann["categories"] = [c for c in ann["categories"] if c != label]
                changed = True

        if changed:
            data["lastModified"] = datetime.now().isoformat()
            with open(ann_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)


def sync_category_assignments(label: str, assignments: List[CategoryAssignment]):
    """Ensure annotations' category lists match the provided assignments for this label."""
    # Map transcript -> set of annotation IDs that should have this label
    assignment_map = {}
    for a in assignments:
        assignment_map.setdefault(a.transcriptFile, set()).add(a.annotationId)

    for ann_file in ANNOTATIONS_DIR.glob("*.json"):
        if ann_file.name == "categories.json":
            continue
        transcript_name = ann_file.stem
        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        for ann in data.get("annotations", []):
            ann.setdefault("categories", [])
            should_have = ann.get("id") in assignment_map.get(transcript_name, set())
            has_label = label in ann["categories"]

            if should_have and not has_label:
                ann["categories"].append(label)
                changed = True
            elif not should_have and has_label:
                ann["categories"] = [c for c in ann["categories"] if c != label]
                changed = True

        if changed:
            data["lastModified"] = datetime.now().isoformat()
            with open(ann_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)


@app.get("/api/categories", response_model=List[Category])
async def list_categories():
    try:
        return load_categories()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading categories: {str(e)}")


@app.post("/api/categories", response_model=Category)
async def create_category(category: Category):
    try:
        categories = load_categories()

        # Ensure label is unique
        if any(c.label == category.label for c in categories):
            raise HTTPException(status_code=400, detail="Category label already exists")

        # Persist category
        categories.append(category)
        save_categories(categories)

        # Add category label to referenced annotations
        for assignment in category.annotations:
            add_category_to_annotation(
                assignment.transcriptFile, assignment.annotationId, category.label
            )

        return category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")


@app.put("/api/categories", response_model=Category)
async def update_category(request: Request):
    """Update a category's label and assignments. Renames will propagate to annotations."""
    try:
        categories = load_categories()
        request = await request.json()
        label = request.get("label")
        category = Category(**request.get("category"))
        print(label, category.annotations)
        target_idx = next((i for i, c in enumerate(categories) if c.label == label), None)
        if target_idx is None:
            raise HTTPException(status_code=404, detail="Category not found")

        # If renaming, ensure new label is unique
        if category.label != label and any(c.label == category.label for c in categories):
            raise HTTPException(status_code=400, detail="Category label already exists")

        # Apply rename in annotations if needed
        if category.label != label:
            rename_category_in_annotations(label, category.label)

        # Sync assignments to annotations
        sync_category_assignments(category.label, category.annotations)

        # Persist category definition
        categories[target_idx] = category
        save_categories(categories)

        return category
    except HTTPException as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")


@app.delete("/api/categories/{label}")
async def delete_category(label: str):
    """Delete a category and remove it from all annotations."""
    try:
        categories = load_categories()
        remaining = [c for c in categories if c.label != label]

        if len(remaining) == len(categories):
            raise HTTPException(status_code=404, detail="Category not found")

        # Remove label from annotations
        remove_category_globally(label)

        # Persist categories
        save_categories(remaining)

        return {"message": "Category deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting category: {str(e)}")


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


@app.get("/api/transcripts/{transcript_id}/messages", response_model=List[TranscriptMessage])
async def get_transcript_messages(transcript_id: str, indices: str = ""):
    """Get transcript messages by transcript id and message indices
    
    Args:
        transcript_id: The transcript ID
        indices: Comma-separated message indices (e.g., "0,1,2,5")
    
    Returns:
        List of TranscriptMessage objects in the order requested
    """
    try:
        # Parse the indices from the query parameter
        if not indices:
            raise HTTPException(status_code=400, detail="indices parameter is required")
        
        try:
            message_indices = [int(idx.strip()) for idx in indices.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="indices must be comma-separated integers")

        segment_dir = SEGMENTED_DIR / transcript_id

        if not segment_dir.exists():
            raise HTTPException(
                status_code=404, detail="Transcript not found"
            )

        # Find all segment files in the directory
        segment_files = sorted(segment_dir.glob(f"*.json"))

        if not segment_files:
            raise HTTPException(status_code=404, detail="No segment files found")

        # Load all messages into a map for quick access
        messages_map: dict[int, TranscriptMessage] = {}
        
        for segment_file in segment_files:
            with open(segment_file, "r", encoding="utf-8") as f:
                segment_data = json.load(f)
                messages = segment_data.get("messages", [])
                segment_start = segment_data.get("start_index", 0)

                # Map each message by its index
                for i, msg in enumerate(messages):
                    message_idx = segment_start + i
                    messages_map[message_idx] = TranscriptMessage(
                        speaker=msg["speaker"],
                        timestamp=msg["timestamp"],
                        content=msg["content"].strip(),
                    )

        # Collect messages in the order requested
        result = []
        missing_indices = []
        
        for idx in message_indices:
            if idx in messages_map:
                result.append(messages_map[idx])
            else:
                missing_indices.append(idx)
        
        # If some indices were missing, include a warning in the response
        if missing_indices:
            # Still return the found messages, but log the missing ones
            # This allows partial results which may be useful
            pass

        return result

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid segment file format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading transcript messages: {str(e)}"
        )


@app.get("/api/transcripts/{transcript_id}/message/{message_index}", response_model=TranscriptMessage)
async def get_transcript_message(transcript_id: str, message_index: int):
    """Get a specific transcript message by transcript id and message index"""
    try:
        segment_dir = SEGMENTED_DIR / transcript_id

        if not segment_dir.exists():
            raise HTTPException(
                status_code=404, detail="Transcript not found"
            )

        # Find all segment files in the directory
        segment_files = sorted(segment_dir.glob(f"*.json"))

        if not segment_files:
            raise HTTPException(status_code=404, detail="No segment files found")

        # Search through all segments to find the message at the given index
        current_index = 0
        for segment_file in segment_files:
            with open(segment_file, "r", encoding="utf-8") as f:
                segment_data = json.load(f)
                messages = segment_data.get("messages", [])
                segment_start = segment_data.get("start_index", current_index)
                segment_end = segment_data.get("end_index", current_index + len(messages) - 1)

                # Check if the requested index is in this segment
                if segment_start <= message_index <= segment_end:
                    # Calculate the position within this segment
                    position_in_segment = message_index - segment_start
                    if 0 <= position_in_segment < len(messages):
                        msg = messages[position_in_segment]
                        return TranscriptMessage(
                            speaker=msg["speaker"],
                            timestamp=msg["timestamp"],
                            content=msg["content"].strip(),
                        )

        raise HTTPException(status_code=404, detail="Message not found at the specified index")

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid segment file format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading transcript message: {str(e)}"
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

        # Ensure categories field exists on each annotation
        for ann in data.get("annotations", []):
            ann.setdefault("categories", [])

        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid annotation file format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading annotations: {str(e)}"
        )


@app.get("/api/annotations/all")
async def get_all_annotations():
    """Get all annotations from all transcript files"""
    try:
        all_annotations = {}
        annotation_files = sorted([f for f in ANNOTATIONS_DIR.glob("*.json") if f.name != "categories.json"])
        
        for annotation_file in annotation_files:
            try:
                with open(annotation_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Use the transcript file name (without .json) as the key
                    transcript_name = annotation_file.stem
                    # Ensure categories field exists on each annotation
                    # for ann in data.get("annotations", []):
                    #     if "categories" not in ann:
                    #         ann['categories'] = []
                    all_annotations[transcript_name] = data
            except (json.JSONDecodeError, IOError):
                # Skip files that can't be read or parsed
                continue
        
        return {
            "totalTranscripts": len(all_annotations),
            "annotations": all_annotations
        }
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

        # Ensure categories defaults exist
        for ann in annotation_data.annotations:
            if ann.categories is None:
                ann.categories = []

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
                if updated_annotation.categories is None:
                    updated_annotation.categories = []
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
