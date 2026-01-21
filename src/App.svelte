<script lang="ts">
  import LeftSidebar from "./lib/LeftSidebar.svelte";
  import MainContent from "./lib/MainContent.svelte";
  import RightSidebar from "./lib/RightSidebar.svelte";
  import {
    type Transcript,
    type Annotation,
    type Segment,
    server_address,
  } from "./constants.js";
  import AnnotationsCanvas from "./lib/AnnotationsCanvas.svelte";

  let transcripts = $state<Transcript[]>([]);
  let currentTranscript = $state<Transcript | null>(null);
  let annotations = $state<Annotation[]>([]);
  let selectedMessages = $state<number[]>([]);
  let isSelecting = $state(false);
  let showAnnotationForm = $state(false);
  let mode = $state("transcript"); // "transcript" or "annotations"

  const apiBaseUrl = server_address;

  async function loadTranscripts() {
    try {
      const response = await fetch(`${apiBaseUrl}/transcripts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const transcriptList = await response.json();
      console.log("transcript list:", transcriptList);
      transcripts = [];

      for (const transcriptInfo of transcriptList) {
        try {
          const contentResponse = await fetch(
            `${apiBaseUrl}/transcripts/${transcriptInfo.filename}/segmented`
          );
          if (contentResponse.ok) {
            const segments = await contentResponse.json();
            transcripts.push({
              filename: transcriptInfo.filename,
              segments: segments,
            });
            console.log("transcript loaded:", {
              filename: transcriptInfo.filename,
              segments: segments,
            });
          }
        } catch (error) {
          console.warn(`Could not load ${transcriptInfo.filename}:`, error);
        }
      }
    } catch (error) {
      console.error("Error loading transcripts:", error);
    }
  }

  async function selectTranscript(transcript: Transcript) {
    annotations = [];
    selectedMessages = [];
    showAnnotationForm = false;

    currentTranscript = transcript;

    await loadAnnotations();
  }

  async function loadAnnotations() {
    if (!currentTranscript) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/annotations/get/${currentTranscript.filename}`
      );
      if (response.ok) {
        const annotation_response = await response.json();
        annotations = annotation_response.annotations;
        console.log({ annotations });
      } else if (response.status !== 404) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error("Error loading annotations:", error);
    }
  }

  async function saveAnnotation(label: string, description: string) {
    if (!currentTranscript || selectedMessages.length === 0) return;

    try {
      // Generate a unique ID for the new annotation
      const newId =
        annotations.length > 0
          ? Math.max(...annotations.map((a) => a.id)) + 1
          : 1;

      const newAnnotation = {
        id: newId,
        messageIndices: [...selectedMessages],
        annotated_messages: selectedMessages.map(
          (index) =>
            currentTranscript?.segments.flatMap((segment) => segment.messages)[
              index
            ]
        ),
        label,
        description,
        timestamp: new Date().toISOString(),
      };

      // Create the annotation file structure expected by the backend
      const annotationFileData = {
        transcriptFile: currentTranscript.filename,
        annotations: [...annotations, newAnnotation],
        lastModified: new Date().toISOString(),
      };

      const response = await fetch(
        `${apiBaseUrl}/annotations/save/${currentTranscript.filename}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(annotationFileData),
        }
      );

      if (response.ok) {
        annotations = [...annotations, newAnnotation];
        selectedMessages = [];
        showAnnotationForm = false;
      }
    } catch (error) {
      console.error("Error saving annotation:", error);
    }
  }

  async function deleteAnnotation(annotationId: number) {
    if (!currentTranscript) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/annotations/${currentTranscript.filename}/${annotationId}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        annotations = annotations.filter((a) => a.id !== annotationId);
      }
    } catch (error) {
      console.error("Error deleting annotation:", error);
    }
  }

  async function editAnnotation(
    annotationId: number,
    label: string,
    description: string
  ) {
    if (!currentTranscript) return;

    try {
      // Find the existing annotation to preserve other properties
      const existingAnnotation = annotations.find((a) => a.id === annotationId);
      if (!existingAnnotation) {
        console.error("Annotation not found");
        return;
      }

      const updatedAnnotation = {
        ...existingAnnotation,
        label,
        description,
        timestamp: new Date().toISOString(),
      };

      const response = await fetch(
        `${apiBaseUrl}/annotations/${currentTranscript.filename}/${annotationId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updatedAnnotation),
        }
      );

      if (response.ok) {
        // Update the annotation in the local state
        annotations = annotations.map((a) =>
          a.id === annotationId ? updatedAnnotation : a
        );
      }
    } catch (error) {
      console.error("Error editing annotation:", error);
    }
  }

  // Load transcripts on mount
  loadTranscripts();
</script>

<div class="container">
  {#if mode === "transcript"}
    <div class="">
      <!-- svelte-ignore a11y_consider_explicit_label -->
      <button
        class="switch-button"
        onclick={() => {
          mode = "annotations";
        }}
      >
        Switch to Annotations Mode
      </button>
      <LeftSidebar {transcripts} onTranscriptSelect={selectTranscript} />
    </div>

    <MainContent
      {currentTranscript}
      {annotations}
      {selectedMessages}
      bind:isSelecting
      bind:showAnnotationForm
      onSaveAnnotation={saveAnnotation}
      onDeleteAnnotation={deleteAnnotation}
      onEditAnnotation={editAnnotation}
      onSelectedMessagesChange={(messages: number[]) =>
        (selectedMessages = messages)}
    />
    <RightSidebar
      {annotations}
      onDeleteAnnotation={deleteAnnotation}
      onEditAnnotation={editAnnotation}
    />
  {:else if mode === "annotations"}
    <!-- svelte-ignore a11y_consider_explicit_label -->
    <div class="annotations-mode-container">
      <button
        class="switch-button"
        onclick={() => {
          mode = "transcript";
        }}
      >
        Switch to Transcript Mode
      </button>

      <div class="annotations-container">
        <AnnotationsCanvas></AnnotationsCanvas>
      </div>
    </div>
  {/if}
</div>

<style>
  .container {
    display: flex;
    width: 100%;
    height: 100vh;
    background-color: #f5f5f5;
  }
  .switch-button {
    padding: 10px;
    margin: 10px;
    width: fit-content;
  }
  .annotations-mode-container {
    display: flex;
    flex-direction: column;
    width: 100%;
  }
  .annotations-container {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    align-self: stretch;
  }

  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: monospace, sans-serif;
    height: 100vh;
  }
</style>
