<script lang="ts">
  import { onMount } from "svelte";
  import { server_address } from "../constants";
  import AnnotationCard from "./AnnotationCard.svelte";
  import CategoryPanel from "./CategoryPanel.svelte";
  import { categoriesState } from "./categories.svelte";

  interface Annotation {
    id: number;
    label: string;
    description: string;
    messageIndices: number[];
    annotated_messages: any[];
    timestamp: string;
    x?: number;
    y?: number;
    transcriptName?: string; // Track which transcript this annotation belongs to
  }

  interface TranscriptAnnotations {
    transcriptFile: string;
    annotations: Annotation[];
    lastModified: string;
  }

  interface Category {
    label: string;
    annotations: { transcriptFile: string; annotationId: number }[];
  }

  let allAnnotations: Record<string, TranscriptAnnotations> = {};
  let loading = true;
  let error: string | null = null;
  let allDisplayAnnotations: Annotation[] = [];
  let selectedTranscript: string | null = null;
  let transcriptNames: string[] = [];

  const CANVAS_WIDTH = 1000;
  const CANVAS_HEIGHT = 600;
  const CARD_WIDTH = 300;
  const CARD_HEIGHT = 120;

  function getRandomCoordinates(): { x: number; y: number } {
    const x = Math.random() * (1 - CARD_WIDTH / CANVAS_WIDTH);
    const y = Math.random() * (1 - CARD_HEIGHT / CANVAS_HEIGHT);
    return { x: Math.max(0, x), y: Math.max(0, y) };
  }

  function denormalizeCoordinates(
    x: number | undefined,
    y: number | undefined
  ): { x: number; y: number } {
    return {
      x: (x ?? 0) * CANVAS_WIDTH,
      y: (y ?? 0) * CANVAS_HEIGHT,
    };
  }

  function normalizeCoordinates(
    x: number,
    y: number
  ): { x: number; y: number } {
    return {
      x: x / CANVAS_WIDTH,
      y: y / CANVAS_HEIGHT,
    };
  }

  function assignMissingCoordinates(annotations: Annotation[]): Annotation[] {
    return annotations.map((annotation) => {
      if (annotation.x === undefined || annotation.y === undefined) {
        const coords = getRandomCoordinates();
        return { ...annotation, x: coords.x, y: coords.y };
      }
      return annotation;
    });
  }

  onMount(async () => {
    try {
      const response = await fetch(`${server_address}/annotations/all`);
      if (!response.ok) {
        throw new Error(`Failed to fetch annotations: ${response.statusText}`);
      }
      const data = await response.json();
      allAnnotations = data.annotations;

      // Get list of transcript names
      transcriptNames = Object.keys(allAnnotations).sort();

      // Select first transcript by default
      if (transcriptNames.length > 0) {
        selectedTranscript = transcriptNames[0];
        updateDisplayedAnnotations();
      }
    } catch (err) {
      error = err instanceof Error ? err.message : "Unknown error occurred";
    } finally {
      loading = false;
    }
  });

  function updateDisplayedAnnotations() {
    if (!selectedTranscript || !allAnnotations[selectedTranscript]) {
      allDisplayAnnotations = [];
      return;
    }

    const transcriptData = allAnnotations[selectedTranscript];
    const annotationsWithTranscript = transcriptData.annotations.map(
      (annotation) => ({
        ...annotation,
        transcriptName: selectedTranscript,
      })
    );

    allDisplayAnnotations = assignMissingCoordinates(annotationsWithTranscript);
  }

  function handleTranscriptChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedTranscript = target.value;
    updateDisplayedAnnotations();
  }

  async function handlePositionChange(
    annotationId: number,
    x: number,
    y: number,
    transcriptName?: string
  ) {
    if (!transcriptName) return;

    try {
      const annotation = allDisplayAnnotations.find(
        (a) => a.id === annotationId && a.transcriptName === transcriptName
      );
      if (!annotation) return;

      // Normalize coordinates before sending to backend
      const normalized = normalizeCoordinates(x, y);

      const response = await fetch(
        `${server_address}/annotations/${transcriptName}/${annotationId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...annotation,
            x: normalized.x,
            y: normalized.y,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update annotation position");
      }

      // Update local state with normalized values
      annotation.x = normalized.x;
      annotation.y = normalized.y;
    } catch (err) {
      console.error("Error updating annotation position:", err);
    }
  }

  function handleAnnotationDelete(
    transcriptName: string,
    annotationId: number
  ) {
    // Remove the annotation from the display array
    allDisplayAnnotations = allDisplayAnnotations.filter(
      (a) => !(a.id === annotationId && a.transcriptName === transcriptName)
    );
  }
</script>

<div class="annotations-canvas-container">
  {#if loading}
    <p>Loading annotations...</p>
  {:else if error}
    <p class="error">Error: {error}</p>
  {:else}
    {#key selectedTranscript}
      <div class="canvas-section">
        <div class="transcript-selector">
          <label for="transcript-select">Transcript:</label>
          <select
            id="transcript-select"
            value={selectedTranscript}
            onchange={handleTranscriptChange}
          >
            {#each transcriptNames as name}
              <option value={name}>{name}</option>
            {/each}
          </select>
        </div>
        {#key categoriesState.categoriesMap}
          <div class="annotations-canvas">
            {#each allDisplayAnnotations as annotation}
              {@const denormalized = denormalizeCoordinates(
                annotation.x,
                annotation.y
              )}
              <AnnotationCard
                annotation={{
                  ...annotation,
                  x: denormalized.x,
                  y: denormalized.y,
                }}
                transcriptName={annotation.transcriptName || ""}
                onPositionChange={handlePositionChange}
                onDelete={handleAnnotationDelete}
              />
            {/each}
          </div>
        {/key}
        <CategoryPanel></CategoryPanel>
      </div>
    {/key}
  {/if}
</div>

<style>
  .annotations-canvas-container {
    height: 100%;
    display: flex;
    /* flex-direction: column; */
    padding: 1rem;
    gap: 1rem;
  }

  .canvas-section {
    flex: 1;
    display: flex;
    /* flex-direction: column; */
    gap: 0.5rem;
    position: relative;
  }

  .transcript-selector {
    position: absolute;
    bottom: 100%;
    left: 0px;
    transform: translateY(50%);
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
  }

  .transcript-selector label {
    font-weight: 500;
    color: #333;
    font-size: 0.9rem;
  }

  .transcript-selector select {
    flex: 1;
    padding: 6px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
    background: white;
    cursor: pointer;
  }

  .transcript-selector select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
  }

  .annotations-canvas {
    position: relative;
    flex: 1;
    border: 2px solid #ddd;
    border-radius: 8px;
    background-color: #fafafa;
    overflow: hidden;
  }

  .error {
    color: red;
    font-weight: bold;
  }
</style>
