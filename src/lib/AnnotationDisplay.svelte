<script lang="ts">
  import { type Annotation } from "../constants.js";

  type Props = {
    annotation: Annotation & {
      top: number;
      height: number;
      width: number;
      rightOffset: number;
    };
    onDelete: (annotationId: number) => Promise<void>;
    onEdit: (
      annotationId: number,
      label: string,
      description: string
    ) => Promise<void>;
  };

  let { annotation, onDelete, onEdit }: Props = $props();

  let isEditing = $state(false);
  let editLabel = $state("");
  let editDescription = $state("");

  function startEditing() {
    isEditing = true;
    editLabel = annotation.label;
    editDescription = annotation.description;
  }

  function cancelEditing() {
    isEditing = false;
    editLabel = "";
    editDescription = "";
  }

  async function saveEditing() {
    await onEdit(annotation.id, editLabel, editDescription);
    isEditing = false;
  }

  function handleMouseEnter() {
    // Highlight corresponding messages
    annotation.messageIndices.forEach((index) => {
      const messageEl = document.querySelector(
        `[data-message-index="${index}"]`
      );
      if (messageEl) messageEl.classList.add("annotation-hover-highlight");
    });
  }

  function handleMouseLeave() {
    // Remove highlight from messages
    document.querySelectorAll(".annotation-hover-highlight").forEach((el) => {
      el.classList.remove("annotation-hover-highlight");
    });
  }

  function getMessageRange() {
    const minIndex = Math.min(...annotation.messageIndices);
    const maxIndex = Math.max(...annotation.messageIndices);

    if (minIndex === maxIndex) {
      return `Message ${minIndex}`;
    } else {
      return `Messages ${minIndex}-${maxIndex}`;
    }
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="annotation-display"
  style="top: {annotation.top}px; min-height: {annotation.height}px; width: {annotation.width}px; right: {annotation.rightOffset}px;"
  onmouseenter={handleMouseEnter}
  onmouseleave={handleMouseLeave}
>
  <div class="annotation-header">
    {#if isEditing}
      <div class="edit-header">
        <div class="annotation-actions">
          <button
            class="annotation-save-btn"
            title="Save changes"
            onclick={saveEditing}
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
            title="Cancel editing"
            onclick={cancelEditing}
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
        </div>
        <textarea
          class="edit-label-textarea"
          bind:value={editLabel}
          placeholder="Enter label"
          rows="2"
        ></textarea>
        <textarea
          class="edit-textarea"
          bind:value={editDescription}
          placeholder="Enter description"
          rows="3"
        ></textarea>
      </div>
    {:else}
      <div class="annotation-label">{annotation.label}</div>
      {#if annotation.description}
        <div class="annotation-description">{annotation.description}</div>
      {/if}
      <div class="annotation-meta">
        <div class="annotation-messages">
          {getMessageRange()}
        </div>
        <div class="annotation-timestamp">
          {new Date(annotation.timestamp).toLocaleString()}
        </div>
      </div>
      <div class="annotation-actions">
        <button
          class="annotation-edit-btn"
          title="Edit annotation"
          onclick={startEditing}
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
        <button
          class="annotation-delete-btn"
          title="Delete annotation"
          onclick={async () => {
            await onDelete(annotation.id);
          }}
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
    {/if}
  </div>
</div>

<style>
  .annotation-display {
    background-color: rgba(179, 224, 255, 0.4);
    border: 1px solid #3498db;
    border-radius: 5px;
    padding: 10px;
    margin: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    position: absolute;
    z-index: 50;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 20px;
  }

  .annotation-display:hover {
    background-color: rgba(179, 224, 255, 0.6);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .annotation-header {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    gap: 6px;
  }

  .annotation-label {
    font-weight: bold;
    font-size: 14px;
    color: #2c3e50;
    flex: 1;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .edit-header {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .edit-label-textarea {
    width: 100%;
    padding: 4px 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 12px;
    background-color: white;
    color: #2c3e50;
    font-family: inherit;

    /* CSS-only auto-expanding */
    field-sizing: content;
    resize: none;
    /* min-height: 2lh; minimum 2 lines */
    max-height: 10lh; /* maximum 10 lines, then scroll */
    overflow-y: auto;

    /* Fallback for browsers that don't support field-sizing */
    height: 10rem;
    min-height: 2.4em;
  }

  .edit-label-textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .annotation-actions {
    display: flex;
    gap: 2px;
    align-items: center;
    justify-content: flex-end;
  }

  .annotation-edit-btn {
    background: transparent;
    color: #28a745;
    border: none;
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
  }

  .annotation-edit-btn:hover {
    background-color: rgba(40, 167, 69, 0.1);
  }

  .annotation-save-btn {
    background: transparent;
    color: #007bff;
    border: none;
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
  }

  .annotation-save-btn:hover {
    background-color: rgba(0, 123, 255, 0.1);
  }

  .annotation-cancel-btn {
    background: transparent;
    color: #6c757d;
    border: none;
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
  }

  .annotation-cancel-btn:hover {
    background-color: rgba(108, 117, 125, 0.1);
  }

  .annotation-delete-btn {
    background: transparent;
    color: #dc3545;
    border: none;
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
  }

  .annotation-delete-btn:hover {
    background-color: rgba(220, 53, 69, 0.1);
  }

  .edit-textarea {
    width: 100%;
    padding: 4px 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 12px;
    background-color: white;
    color: #333;
    font-family: inherit;
    margin-bottom: 8px;

    /* CSS-only auto-expanding */
    field-sizing: content;
    resize: none;
    min-height: 3lh; /* minimum 3 lines */
    max-height: 15lh; /* maximum 15 lines, then scroll */
    overflow-y: auto;

    /* Fallback for browsers that don't support field-sizing */
    height: auto;
    min-height: 3.6em;
  }

  .edit-textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .annotation-description {
    font-size: 12px;
    color: #555;
    margin-bottom: 8px;
    line-height: 1.4;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .annotation-meta {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #666;
    flex-wrap: wrap;
    gap: 4px;
  }

  .annotation-messages {
    font-weight: bold;
  }

  .annotation-timestamp {
    font-style: italic;
  }

  /* Compact styling for narrow annotations */
  .annotation-display[style*="width: 120px"],
  .annotation-display[style*="width: 140px"] {
    padding: 6px;
    font-size: 11px;
  }

  .annotation-display[style*="width: 120px"] .annotation-label,
  .annotation-display[style*="width: 140px"] .annotation-label {
    font-size: 12px;
  }

  .annotation-display[style*="width: 120px"] .annotation-description,
  .annotation-display[style*="width: 140px"] .annotation-description {
    font-size: 10px;
  }

  .annotation-display[style*="width: 120px"] .annotation-meta,
  .annotation-display[style*="width: 140px"] .annotation-meta {
    font-size: 9px;
    flex-direction: column;
    gap: 2px;
  }
</style>
