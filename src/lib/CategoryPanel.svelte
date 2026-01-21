<script lang="ts">
  "use runes";
  import { onMount } from "svelte";
  import { server_address } from "../constants";
  import type { Category, CategoryAssignment } from "../constants";
  import { categoriesState } from "./categories.svelte";

  let newLabel = $state("");
  let editingLabel: string | null = $state(null);
  let editDraft = $state("");
  let savingEdit = $state(false);
  let deletingLabel: string | null = $state(null);

  onMount(() => {
    categoriesState.fetchCategories();
  });

  function startEdit(label: string) {
    editingLabel = label;
    editDraft = label;
  }

  function cancelEdit() {
    editingLabel = null;
    editDraft = "";
  }
</script>

<div class="category-panel">
  <h3>Categories</h3>

  <div class="add-row">
    <input
      class="text-input"
      placeholder="New category label"
      bind:value={newLabel}
      onkeydown={(e) =>
        e.key === "Enter" && categoriesState.addCategory(newLabel)}
      aria-label="New category label"
    />
    <button
      class="icon-btn primary"
      onclick={() => {
        categoriesState.addCategory(newLabel);
        newLabel = "";
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
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
      Add
    </button>
  </div>
  {#if categoriesState.categories.length === 0}
    <p class="muted">No categories yet</p>
  {:else}
    <div class="category-list">
      {#each categoriesState.categories as category}
        <div class="category-card">
          {#if editingLabel === category.label}
            <input
              class="text-input"
              bind:value={editDraft}
              aria-label="Edit category label"
              onkeydown={(e) =>
                e.key === "Enter" &&
                categoriesState.saveEdit(category.label, editDraft)}
            />
            <div class="button-group">
              <button
                class="icon-btn primary"
                onclick={() => {
                  editingLabel = null;
                  categoriesState.saveEdit(category.label, editDraft);
                }}
                disabled={savingEdit}
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
                class="icon-btn"
                onclick={cancelEdit}
                disabled={savingEdit}
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
            <div class="card-main">
              <div>
                <div class="category-label">{category.label}</div>
                <div class="meta">
                  {category.annotations.length} annotations
                </div>
              </div>
              <div class="button-group">
                <button
                  class="icon-btn"
                  title="Edit category"
                  onclick={() => startEdit(category.label)}
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
                  class="icon-btn danger"
                  title="Delete category"
                  onclick={() => categoriesState.deleteCategory(category.label)}
                  disabled={deletingLabel === category.label}
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
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .category-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  h3 {
    margin: 0;
    font-size: 1rem;
    color: #333;
  }

  .add-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .text-input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .text-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
  }

  .icon-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 4px;
    background: white;
    cursor: pointer;
    color: #333;
    transition:
      background-color 0.2s ease,
      border-color 0.2s ease;
  }

  .icon-btn svg {
    display: block;
  }

  .icon-btn:hover:not(:disabled) {
    background-color: rgba(0, 123, 255, 0.08);
    border-color: rgba(0, 123, 255, 0.2);
  }

  .icon-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .icon-btn.primary {
    color: #007bff;
  }

  .icon-btn.danger {
    color: #dc3545;
  }

  .category-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .category-card {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: rgba(179, 224, 255, 0.25);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .card-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  .category-label {
    font-weight: 600;
    color: #333;
  }

  .meta {
    font-size: 0.8rem;
    color: #666;
  }

  .button-group {
    display: flex;
    gap: 0.35rem;
  }

  .error {
    color: #d32f2f;
    margin: 0;
    font-size: 0.85rem;
  }

  .muted {
    color: #777;
    margin: 0;
    font-size: 0.9rem;
  }
</style>
