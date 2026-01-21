<script lang="ts">
  import { onMount } from "svelte";
  import { server_address } from "../constants";
  import { slide } from "svelte/transition";

  import { categoriesState } from "./categories.svelte";
  interface TranscriptMessage {
    speaker: string;
    timestamp: string;
    content: string;
  }

  interface Category {
    label: string;
    annotations: { transcriptFile: string; annotationId: number }[];
  }

  interface Props {
    annotation: {
      id: number;
      label: string;
      description: string;
      messageIndices: number[];
      annotated_messages: any[];
      timestamp: string;
      x?: number;
      y?: number;
    };
    transcriptName: string;
    onPositionChange: (
      id: number,
      x: number,
      y: number,
      transcriptName?: string
    ) => void;
    onDelete?: (transcriptName: string, annotationId: number) => void;
  }

  let { annotation, transcriptName, onPositionChange, onDelete }: Props =
    $props();

  let isDragging = $state(false);
  let dragOffsetX = $state(0);
  let dragOffsetY = $state(0);
  let currentX = $state(annotation.x ?? 0);
  let currentY = $state(annotation.y ?? 0);
  let isMessagesExpanded = $state(false);
  let messages: TranscriptMessage[] = $state([]);
  let messagesLoading = $state(false);
  let messagesError = $state<string | null>(null);
  let isEditing = $state(false);
  let editLabel = $state(annotation.label);
  let editDescription = $state(annotation.description);
  let isSaving = $state(false);
  let saveError = $state<string | null>(null);
  let showCategoryDropdown = $state(false);
  let addingToCategory = $state(false);

  const categories = $derived.by(() => {
    const key = `${transcriptName}-${annotation.id}`;
    return categoriesState.categoriesMap[key] || [];
  });

  //   async function fetchCategories() {
  //     try {
  //       const response = await fetch(`${server_address}/categories`);
  //       if (!response.ok) throw new Error("Failed to fetch categories");
  //       const categories_list = await response.json();
  //       return categories_list;
  //     } catch (err) {
  //       console.error("Error fetching categories:", err);
  //     }
  //   }

  function handleMouseDown(e: MouseEvent) {
    if (e.button !== 0) return; // Only left click
    if (isEditing) return; // Don't drag while editing

    isDragging = true;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    dragOffsetX = e.clientX - rect.left;
    dragOffsetY = e.clientY - rect.top;

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging) return;

    const parentRect = (
      document.querySelector(".annotations-canvas") as HTMLElement
    )?.getBoundingClientRect();
    if (!parentRect) return;

    currentX = e.clientX - parentRect.left - dragOffsetX;
    currentY = e.clientY - parentRect.top - dragOffsetY;

    // Constrain to parent bounds
    currentX = Math.max(0, Math.min(currentX, parentRect.width - 300));
    currentY = Math.max(0, Math.min(currentY, parentRect.height - 100));
  }

  function handleMouseUp() {
    if (isDragging) {
      isDragging = false;
      onPositionChange(annotation.id, currentX, currentY, transcriptName);
    }

    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
  }

  async function toggleMessages() {
    isMessagesExpanded = !isMessagesExpanded;

    if (isMessagesExpanded && messages.length === 0) {
      await fetchMessages();
    }
  }

  async function fetchMessages() {
    if (annotation.messageIndices.length === 0) {
      messagesError = "No message indices associated with this annotation";
      return;
    }

    messagesLoading = true;
    messagesError = null;

    try {
      const indicesString = annotation.messageIndices.join(",");
      const response = await fetch(
        `${server_address}/transcripts/${transcriptName}/messages?indices=${indicesString}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch messages: ${response.statusText}`);
      }

      messages = await response.json();
    } catch (err) {
      messagesError =
        err instanceof Error ? err.message : "Failed to load messages";
    } finally {
      messagesLoading = false;
    }
  }

  function startEdit() {
    isEditing = true;
    editLabel = annotation.label;
    editDescription = annotation.description;
    saveError = null;
  }

  function cancelEdit() {
    isEditing = false;
    saveError = null;
  }

  async function saveEdit() {
    isSaving = true;
    saveError = null;

    try {
      const response = await fetch(
        `${server_address}/annotations/${transcriptName}/${annotation.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...annotation,
            label: editLabel,
            description: editDescription,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save changes");
      }

      // Update annotation object
      annotation.label = editLabel;
      annotation.description = editDescription;
      isEditing = false;
    } catch (err) {
      saveError = err instanceof Error ? err.message : "Failed to save changes";
    } finally {
      isSaving = false;
    }
  }

  async function deleteAnnotation() {
    if (!confirm(`Delete annotation "${annotation.label}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `${server_address}/annotations/${transcriptName}/${annotation.id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete annotation");
      }

      if (onDelete) {
        onDelete(transcriptName, annotation.id);
      }
    } catch (err) {
      console.error("Error deleting annotation:", err);
    }
  }

  //   function toggleCategoryDropdown() {
  //     showCategoryDropdown = !showCategoryDropdown;
  //     if (showCategoryDropdown) {
  //       fetchCategories();
  //     }
  //   }

  async function addToCategory(
    categoryLabel: string,
    categories_list: Category[]
  ) {
    addingToCategory = true;
  }
  //   onMount(() => {
  //     console.log("categories:", categories, annotation);
  //   });
</script>

<div
  class="annotation-card"
  style="left: {currentX}px; top: {currentY}px;"
  onmousedown={handleMouseDown}
>
  <div class="card-header">
    {#if isEditing}
      <input
        type="text"
        bind:value={editLabel}
        placeholder="Label"
        class="edit-input"
      />
      <div class="button-group">
        <button
          class="icon-btn annotation-save-btn"
          onclick={saveEdit}
          disabled={isSaving}
          title="Save"
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
          class="icon-btn annotation-cancel-btn"
          onclick={cancelEdit}
          disabled={isSaving}
          title="Cancel"
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
    {:else}
      <span>{annotation.label}</span>
      <div class="button-group">
        <button
          class="icon-btn annotation-category-btn"
          onclick={() => (showCategoryDropdown = !showCategoryDropdown)}
          title="Add to category"
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
              d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
            />
          </svg>
        </button>
        <button
          class="icon-btn annotation-edit-btn"
          onclick={startEdit}
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
            <path d="M12 20h9" />
            <path
              d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"
            />
          </svg>
        </button>
        <button
          class="icon-btn annotation-delete-btn"
          onclick={deleteAnnotation}
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
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            <line x1="10" y1="11" x2="10" y2="17" />
            <line x1="14" y1="11" x2="14" y2="17" />
          </svg>
        </button>
      </div>
    {/if}
  </div>

  {#if showCategoryDropdown}
    {#if categoriesState.categories.length === 0}
      <p class="dropdown-message">No categories available</p>
    {:else}
      <div in:slide>
        {#each categoriesState.categories as category}
          <button
            class="category-option"
            onclick={() => {
              categoriesState.addAnnotationToCategory(
                category.label,
                transcriptName,
                annotation
              );
              showCategoryDropdown = false;
            }}
            disabled={addingToCategory}
          >
            {category.label}
          </button>
        {/each}
      </div>
    {/if}
  {/if}

  {#if !isEditing && categories && categories.length > 0}
    <div class="categories-display">
      {#each categories as categoryLabel}
        <div class="category-badge-container">
          <span class="category-badge">{categoryLabel}</span>
          <button
            class="category-delete-btn"
            onclick={() =>
              categoriesState.removeCategoryFromAnnotation(
                categoryLabel,
                transcriptName,
                annotation.id
              )}
            title="Remove from category"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      {/each}
    </div>
  {/if}

  {#if saveError}
    <p class="save-error">{saveError}</p>
  {/if}

  {#if isEditing}
    <textarea
      bind:value={editDescription}
      placeholder="Description"
      class="edit-textarea"
    />
  {:else if annotation.description}
    <p class="description">{annotation.description}</p>
  {/if}

  {#if !isEditing}
    <div class="toggle-messages-btn" onclick={toggleMessages}>
      Messages ({annotation.messageIndices.length})
    </div>

    {#if isMessagesExpanded}
      <div class="messages-container">
        {#if messagesLoading}
          <p class="loading">Loading messages...</p>
        {:else if messagesError}
          <p class="error">{messagesError}</p>
        {:else if messages.length > 0}
          <div class="messages-list">
            {#each messages as message, index}
              <div class="message-item">
                <div class="message-header">
                  <strong>{message.speaker}</strong>
                  <span class="timestamp">{message.timestamp}</span>
                </div>
                <div class="message-content">{message.content}</div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="no-messages">No messages found</p>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .annotation-card {
    position: absolute;
    width: 250px;
    background-color: rgba(179, 224, 255, 0.4);
    border: 2px solid #007bff;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    cursor: move;
    user-select: none;
    padding: 0;
    overflow: hidden;
    transition: box-shadow 0.2s;
    color: #666;
  }

  .annotation-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .card-header {
    background-color: rgba(179, 224, 255, 0.4);
    padding: 0.5rem;
    font-weight: 500;
    font-size: 0.8rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    /* align-items: center; */
    gap: 0.5rem;
  }

  .card-header span {
    flex: 1;
    /* white-space: nowrap; */
    /* overflow: hidden;
    text-overflow: ellipsis; */
  }

  .button-group {
    display: flex;
    gap: 0.25rem;
    flex-shrink: 0;
  }

  .icon-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
    color: #333;
  }

  .icon-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .annotation-edit-btn {
    color: #007bff;
  }

  .annotation-edit-btn:hover:not(:disabled) {
    background-color: rgba(0, 123, 255, 0.1);
  }

  .annotation-save-btn {
    color: #007bff;
  }

  .annotation-save-btn:hover:not(:disabled) {
    background-color: rgba(0, 123, 255, 0.1);
  }

  .annotation-cancel-btn {
    color: #6c757d;
  }

  .annotation-cancel-btn:hover:not(:disabled) {
    background-color: rgba(108, 117, 125, 0.1);
  }

  .annotation-delete-btn {
    color: #dc3545;
  }

  .annotation-delete-btn:hover:not(:disabled) {
    background-color: rgba(220, 53, 69, 0.1);
  }

  .annotation-category-btn {
    color: #28a745;
  }

  .annotation-category-btn:hover:not(:disabled) {
    background-color: rgba(40, 167, 69, 0.1);
  }

  .category-dropdown {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin: 0.5rem;
    max-height: 200px;
    overflow-y: auto;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .category-option {
    display: block;
    width: 100%;
    padding: 0.5rem;
    border: none;
    background: white;
    text-align: left;
    cursor: pointer;
    font-size: 0.85rem;
    transition: background-color 0.2s ease;
  }

  .category-option:hover:not(:disabled) {
    background-color: rgba(0, 123, 255, 0.08);
  }

  .category-option:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .dropdown-message {
    padding: 0.5rem;
    margin: 0;
    font-size: 0.85rem;
    color: #666;
    text-align: center;
  }

  .categories-display {
    padding: 0.25rem 0.5rem 0.5rem 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .category-badge-container {
    display: inline-flex;
    align-items: center;
  }

  .category-badge {
    display: inline-block;
    padding: 0.15rem 0.4rem;
    background-color: rgba(40, 167, 69, 0.15);
    border: 1px solid rgba(40, 167, 69, 0.3);
    border-radius: 3px;
    font-size: 0.7rem;
    color: #28a745;
    font-weight: 500;
  }

  .category-badge-container:hover .category-badge {
    /* display: none; */
  }

  .category-delete-btn {
    display: none;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    padding: 0;
    background-color: rgba(220, 53, 69, 0.2);
    border: 1px solid rgba(220, 53, 69, 0.4);
    border-radius: 3px;
    cursor: pointer;
    color: #dc3545;
    transition: background-color 0.2s ease;
  }

  .category-badge-container:hover .category-delete-btn {
    display: inline-flex;
  }

  .category-delete-btn:hover {
    background-color: rgba(220, 53, 69, 0.3);
    border-color: rgba(220, 53, 69, 0.6);
  }

  .category-delete-btn svg {
    display: block;
  }

  .edit-input,
  .edit-textarea {
    width: 100%;
    padding: 6px;
    margin: 0;
    border: 1px solid #ccc;
    border-radius: 3px;
    font-size: 0.8rem;
    font-family: inherit;
    resize: none;
  }

  .edit-input {
    height: 2rem;
  }

  .edit-textarea {
    height: 3rem;
    field-sizing: content;
    min-height: 3lh;
    max-height: 12lh;
  }

  .edit-input:focus,
  .edit-textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .save-error {
    color: #d32f2f;
    font-size: 0.75rem;
    padding: 0.5rem;
    margin: 0;
    background-color: rgba(211, 47, 47, 0.1);
  }

  .description {
    padding: 0.5rem;
    margin: 0;
    font-size: 0.7rem;
    font-style: italic;
  }

  .toggle-messages-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.7rem;
    padding: 0.5rem 0.5rem;
    text-align: left;
    font-weight: 500;
    width: 100%;
  }

  .toggle-messages-btn:hover {
    background: #ddd;
  }

  .messages-container {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
  }

  .messages-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 10rem;
    overflow-y: auto;
  }

  .message-item {
    background-color: rgba(255, 255, 255, 0.6);
    padding: 0.5rem;
    border-radius: 2px;
    font-size: 0.8rem;
  }

  .message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
  }

  .message-header strong {
    font-weight: bold;
    color: #333;
  }

  .timestamp {
    font-size: 0.75rem;
    color: #999;
  }

  .message-content {
    color: #555;
    line-height: 1.3;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .loading,
  .error,
  .no-messages {
    font-size: 0.85rem;
    padding: 0.5rem;
    margin: 0;
  }

  .loading {
    color: #666;
    font-style: italic;
  }

  .error {
    color: #d32f2f;
  }

  .no-messages {
    color: #999;
  }
</style>
