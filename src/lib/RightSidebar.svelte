<script lang="ts">
  import { type Annotation } from "../constants.js";

  type Props = {
    annotations: Annotation[];
    onDeleteAnnotation: (annotationId: number) => Promise<void>;
  };

  let { annotations, onDeleteAnnotation }: Props = $props();

  // Sort annotations by their start index
  let sortedAnnotations = $derived(
    annotations.slice().sort((a, b) => {
      const aStartIndex = Math.min(...a.messageIndices);
      const bStartIndex = Math.min(...b.messageIndices);
      return aStartIndex - bStartIndex;
    })
  );

  async function handleDeleteAnnotation(annotationId: number) {
    await onDeleteAnnotation(annotationId);
  }

  function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  function truncateText(text: string, maxLength: number = 100): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  }
</script>

<div class="right-sidebar sidebar">
  <h2>Annotations</h2>
  <div class="saved-annotations">
    {#each sortedAnnotations as annotation (annotation.id)}
      <div class="annotation-display">
        <div class="annotation-header">
          <span class="annotation-timestamp">
            {formatTimestamp(annotation.timestamp)}
          </span>
          <button
            class="annotation-delete-btn"
            onclick={() => handleDeleteAnnotation(annotation.id)}
            aria-label="Delete annotation"
            title="Delete annotation"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M10 11v6" /><path d="M14 11v6" /><path
                d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"
              /><path d="M3 6h18" /><path
                d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
              />
            </svg>
          </button>
        </div>
        <div class="annotation-text">
          <strong>Label:</strong>
          <div class="selected-text">
            {annotation.label}
          </div>
        </div>
        {#if annotation.description}
          <div class="annotation-note">
            <strong>Description:</strong>
            <div class="note-content">
              {truncateText(annotation.description)}
            </div>
          </div>
        {/if}
        <div class="annotation-meta">
          Messages: {annotation.messageIndices.join(", ")}
        </div>
      </div>
    {/each}

    {#if sortedAnnotations.length === 0}
      <div class="no-annotations">
        <p>No annotations yet.</p>
        <p>Select text in the transcript to create annotations.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .sidebar {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    overflow-y: auto;
  }

  .right-sidebar {
    width: 300px;
    background-color: #ecf0f1;
    color: #2c3e50;
    border-left: 2px solid #bdc3c7;
  }

  .sidebar h2 {
    margin-bottom: 20px;
    font-size: 18px;
    border-bottom: 2px solid #34495e;
    padding-bottom: 10px;
  }

  .right-sidebar h2 {
    border-bottom: 2px solid #bdc3c7;
    color: #2c3e50;
  }

  .saved-annotations {
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding-right: 12px;
  }

  .annotation-display {
    background-color: rgba(179, 224, 255, 0.4);
    border: 1px solid #3498db;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: static;
    width: auto;
    margin-bottom: 15px;
  }

  .annotation-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0;
  }

  .annotation-timestamp {
    font-size: 11px;
    color: #666;
    font-weight: normal;
  }

  .annotation-delete-btn {
    background: transparent;
    color: #dc3545;
    border: none;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: bold;
    transition: background-color 0.2s;
  }

  .annotation-delete-btn:hover {
    background-color: rgba(220, 53, 69, 0.1);
  }

  .annotation-text {
    font-size: 12px;
  }

  .selected-text {
    margin-top: 4px;
    font-style: italic;
    color: #555;
    padding: 4px;
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    border-left: 3px solid #3498db;
  }

  .annotation-note {
    font-size: 12px;
  }

  .note-content {
    margin-top: 4px;
    color: #2c3e50;
    padding: 4px;
    background-color: rgba(255, 255, 255, 0.5);
    border-radius: 3px;
  }

  .annotation-meta {
    font-size: 10px;
    color: #666;
    margin-top: 4px;
    font-style: italic;
  }

  .no-annotations {
    text-align: center;
    color: #666;
    font-style: italic;
    margin-top: 40px;
  }

  .no-annotations p {
    margin-bottom: 8px;
    font-size: 14px;
  }
</style>
