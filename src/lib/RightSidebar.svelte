<script lang="ts">
  import { type Annotation } from "../constants.js";

  type Props = {
    annotations: Annotation[];
    onDeleteAnnotation: (annotationId: number) => Promise<void>;
    onEditAnnotation: (
      annotationId: number,
      label: string,
      description: string
    ) => Promise<void>;
  };

  let { annotations, onDeleteAnnotation, onEditAnnotation }: Props = $props();

  // Track which annotations are being edited
  let editingAnnotations = $state<Set<number>>(new Set());

  // Track temporary edit values
  let editValues = $state<Map<number, { label: string; description: string }>>(
    new Map()
  );

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

  function startEditing(annotation: Annotation) {
    editingAnnotations.add(annotation.id);
    editValues.set(annotation.id, {
      label: annotation.label,
      description: annotation.description,
    });
    editingAnnotations = new Set(editingAnnotations);
    editValues = new Map(editValues);
  }

  function cancelEditing(annotationId: number) {
    editingAnnotations.delete(annotationId);
    editValues.delete(annotationId);
    editingAnnotations = new Set(editingAnnotations);
    editValues = new Map(editValues);
  }

  async function saveEditing(annotationId: number) {
    const values = editValues.get(annotationId);
    if (!values) return;

    await onEditAnnotation(annotationId, values.label, values.description);

    editingAnnotations.delete(annotationId);
    editValues.delete(annotationId);
    editingAnnotations = new Set(editingAnnotations);
    editValues = new Map(editValues);
  }

  function updateEditValue(
    annotationId: number,
    field: "label" | "description",
    value: string
  ) {
    const current = editValues.get(annotationId) || {
      label: "",
      description: "",
    };
    editValues.set(annotationId, { ...current, [field]: value });
    editValues = new Map(editValues);
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
          <div class="annotation-actions">
            {#if !editingAnnotations.has(annotation.id)}
              <button
                class="annotation-edit-btn"
                onclick={() => startEditing(annotation)}
                aria-label="Edit annotation"
                title="Edit annotation"
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
                  <path
                    d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                  />
                  <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
            {:else}
              <button
                class="annotation-save-btn"
                onclick={() => saveEditing(annotation.id)}
                aria-label="Save changes"
                title="Save changes"
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
                  <polyline points="20,6 9,17 4,12" />
                </svg>
              </button>
              <button
                class="annotation-cancel-btn"
                onclick={() => cancelEditing(annotation.id)}
                aria-label="Cancel editing"
                title="Cancel editing"
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
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            {/if}
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
        </div>
        <div class="annotation-text">
          <strong>Label:</strong>
          {#if editingAnnotations.has(annotation.id)}
            <input
              type="text"
              class="edit-input"
              value={editValues.get(annotation.id)?.label || ""}
              oninput={(e) =>
                updateEditValue(annotation.id, "label", e.target.value)}
              placeholder="Enter label"
            />
          {:else}
            <div class="selected-text">
              {annotation.label}
            </div>
          {/if}
        </div>
        <div class="annotation-note">
          <strong>Description:</strong>
          {#if editingAnnotations.has(annotation.id)}
            <textarea
              class="edit-textarea"
              value={editValues.get(annotation.id)?.description || ""}
              oninput={(e) =>
                updateEditValue(annotation.id, "description", e.target.value)}
              placeholder="Enter description"
              rows="3"
            ></textarea>
          {:else}
            <div class="note-content">
              {annotation.description
                ? truncateText(annotation.description)
                : "No description"}
            </div>
          {/if}
        </div>
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

  .annotation-actions {
    display: flex;
    gap: 4px;
    align-items: center;
  }

  .annotation-edit-btn {
    background: transparent;
    color: #28a745;
    border: none;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: bold;
    transition: background-color 0.2s;
  }

  .annotation-edit-btn:hover {
    background-color: rgba(40, 167, 69, 0.1);
  }

  .annotation-save-btn {
    background: transparent;
    color: #007bff;
    border: none;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: bold;
    transition: background-color 0.2s;
  }

  .annotation-save-btn:hover {
    background-color: rgba(0, 123, 255, 0.1);
  }

  .annotation-cancel-btn {
    background: transparent;
    color: #6c757d;
    border: none;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: bold;
    transition: background-color 0.2s;
  }

  .annotation-cancel-btn:hover {
    background-color: rgba(108, 117, 125, 0.1);
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

  .edit-input {
    width: 100%;
    margin-top: 4px;
    padding: 4px 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 12px;
    background-color: white;
    color: #333;
  }

  .edit-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .edit-textarea {
    width: 100%;
    margin-top: 4px;
    padding: 4px 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 12px;
    background-color: white;
    color: #333;
    resize: vertical;
    font-family: inherit;
  }

  .edit-textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
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
