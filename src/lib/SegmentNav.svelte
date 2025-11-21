<script lang="ts">
  import { type Transcript } from "../constants.js";

  type Props = {
    currentTranscript: Transcript | null;
    activeSegmentIndex: number;
    onSegmentClick: (segmentIndex: number) => void;
  };

  let { currentTranscript, activeSegmentIndex, onSegmentClick }: Props =
    $props();

  function getSegmentColor(index: number): string {
    const colors = [
      "#F3AEA6",
      "#CAE6C1",
      "#D6C5DE",
      "#FAD4A2",
      "#F8D7E8",
      "#FFFECB",
      "#E0D2B8",
      "#F0F0F0",
      "#ADC6DD",
    ];
    return colors[index % colors.length];
  }
</script>

{#if currentTranscript && currentTranscript.segments.length > 1}
  <div class="segment-nav">
    <div class="segment-nav-items">
      {#each currentTranscript.segments as segment, index}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="segment-nav-item"
          class:active={activeSegmentIndex === index}
          onclick={() => onSegmentClick(index)}
          role="button"
          tabindex="0"
          style="background-color: {getSegmentColor(index)};"
        >
          <div class="segment-nav-title">
            {segment.title || `Segment ${index + 1}`}
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  /* Segment Navigation */
  .segment-nav {
    position: absolute;
    left: 0px; /* Account for annotations panel width */
    top: 50%;
    transform: translateX(-100%);
    /* transform: translateY(-50%); */
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 60;
    max-height: 60vh;
    overflow-y: auto;
  }

  .segment-nav-items {
    display: flex;
    flex-direction: column;
  }

  .segment-nav-item {
    padding: 4px 8px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    transition: background 0.2s;
    min-width: 120px;
  }

  .segment-nav-item:hover {
    outline: 2px solid #ffffff;
    background-color: #f8f9fa;
  }

  .segment-nav-item.active {
    background: #e3f2fd;
    border-left: 4px solid #2196f3;
  }

  .segment-nav-title {
    font-size: 10px;
    color: black;
    font-weight: bold;
  }
</style>
