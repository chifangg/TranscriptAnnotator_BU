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
  };

  let { annotation, onDelete }: Props = $props();

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
    <div class="annotation-label">{annotation.label}</div>
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
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }

  .annotation-label {
    font-weight: bold;
    font-size: 14px;
    color: #2c3e50;
    flex: 1;
    word-wrap: break-word;
    overflow-wrap: break-word;
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
