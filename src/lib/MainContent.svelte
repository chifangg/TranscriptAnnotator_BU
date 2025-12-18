<script lang="ts">
  import { type Transcript, type Annotation } from "../constants.js";
  import Controllers from "./Controllers.svelte";
  import AnnotationDisplay from "./AnnotationDisplay.svelte";
  import SegmentNav from "./SegmentNav.svelte";
  import { untrack } from "svelte";

  type Props = {
    currentTranscript: Transcript | null;
    annotations: Annotation[];
    selectedMessages: number[];
    isSelecting: boolean;
    showAnnotationForm: boolean;
    onSaveAnnotation: (label: string, description: string) => Promise<void>;
    onDeleteAnnotation: (annotationId: number) => Promise<void>;
    onSelectedMessagesChange: (messages: number[]) => void;
  };

  let {
    currentTranscript,
    annotations,
    selectedMessages,
    isSelecting = $bindable(),
    showAnnotationForm = $bindable(),
    onSaveAnnotation,
    onDeleteAnnotation,
    onSelectedMessagesChange,
  }: Props = $props();

  // Speaker states - now managed externally as bindable props
  //   let speakers = $state<string[]>([]);
  let speakers: string[] = $derived.by(() => {
    if (currentTranscript) {
      const allMessages = currentTranscript.segments.flatMap(
        (segment) => segment.messages
      );
      return [...new Set(allMessages.map((m) => m.speaker))];
    }
    return [];
  });

  let annotationNote = $state("");
  let annotationLabel = $state("");
  let annotationDescription = $state("");
  let startSelectionIndex = $state<number | null>(null);
  //   let messagesContainer = $state<HTMLElement | undefined>(undefined);
  let transcriptContent = $state<HTMLElement | undefined>(undefined);
  let annotationFormTop = $state(0);
  let positionedAnnotations = $state<
    Array<
      Annotation & {
        top: number;
        height: number;
        width: number;
        rightOffset: number;
      }
    >
  >([]);
  let activeSegmentIndex = $state(0);
  let segmentPositions = $state<Array<{ top: number; height: number }>>([]);

  let speakerColorMap: Map<string, string> = $state(new Map());
  let speakerVisibility: Map<string, boolean> = $state(new Map());
  let speakerFontWeight: Map<string, number> = $state(new Map());
  function getMessageIndex(element: HTMLElement): number {
    return parseInt(element.dataset.messageIndex || "0");
  }

  function positionAnnotations() {
    if (!currentTranscript || annotations.length === 0) {
      positionedAnnotations = [];
      return;
    }

    const annotationsPanel = document.querySelector(".annotations-panel");
    if (!annotationsPanel) {
      positionedAnnotations = [];
      return;
    }

    // First, calculate basic positions
    const basicPositioned = annotations
      .map((annotation) => {
        const startIndex = Math.min(...annotation.messageIndices);
        const endIndex = Math.max(...annotation.messageIndices);

        const startMessage = document.querySelector(
          `[data-message-index="${startIndex}"]`
        );
        const endMessage = document.querySelector(
          `[data-message-index="${endIndex}"]`
        );

        if (startMessage && endMessage) {
          const startRect = startMessage.getBoundingClientRect();
          const endRect = endMessage.getBoundingClientRect();
          const panelRect = annotationsPanel.getBoundingClientRect();

          const top = startRect.top - panelRect.top;
          const height = endRect.bottom - startRect.top;

          return {
            ...annotation,
            top: Math.max(0, top),
            height: Math.max(20, height),
            width: 280, // Default width
            rightOffset: 0, // Default offset from right
          };
        }
        return null;
      })
      .filter(Boolean) as Array<
      Annotation & {
        top: number;
        height: number;
        width: number;
        rightOffset: number;
      }
    >;

    // Now detect overlaps and adjust layout
    const layoutAdjusted = basicPositioned.map((current, index) => {
      // Find overlapping annotations
      const overlapping = basicPositioned.filter((other, otherIndex) => {
        if (index === otherIndex) return false;

        const currentBottom = current.top + current.height;
        const otherBottom = other.top + other.height;

        // Check if ranges overlap
        return !(
          currentBottom < other.top + 5 || current.top + 5 > otherBottom
        );
      });

      if (overlapping.length === 0) {
        return current; // No overlap, keep original layout
      }

      // Sort overlapping annotations by their original order (including current)
      const allOverlapping = [...overlapping, current].sort(
        (a, b) =>
          basicPositioned.findIndex((ann) => ann.id === a.id) -
          basicPositioned.findIndex((ann) => ann.id === b.id)
      );

      // Find current annotation's position in the overlap group
      const currentPositionInGroup = allOverlapping.findIndex(
        (ann) => ann.id === current.id
      );
      const totalInGroup = allOverlapping.length;

      // Calculate new width and offset
      const newWidth = Math.max(20, Math.floor(280 / totalInGroup)); // Minimum 60px width
      const rightOffset = currentPositionInGroup * newWidth;

      return {
        ...current,
        width: newWidth,
        rightOffset: rightOffset,
      };
    });

    positionedAnnotations = layoutAdjusted;
  }

  // Effect to position annotations when transcript or annotations change
  $effect(() => {
    if (currentTranscript && annotations.length > 0) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(positionAnnotations, 0);
    } else {
      positionedAnnotations = [];
    }
  });

  // Effect to reposition annotations when scrolling
  $effect(() => {
    if (!transcriptContent) return;

    const handleScroll = () => {
      if (annotations.length > 0) {
        positionAnnotations();
      }
    };

    transcriptContent.addEventListener("scroll", handleScroll);
    window.addEventListener("resize", handleScroll);

    return () => {
      transcriptContent?.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  });

  function handleMouseDown(event: MouseEvent) {
    const messageElement = (event.target as HTMLElement).closest(
      ".message"
    ) as HTMLElement;
    if (!messageElement) return;

    isSelecting = true;
    startSelectionIndex = getMessageIndex(messageElement);
    selectedMessages = [startSelectionIndex];
    onSelectedMessagesChange(selectedMessages);

    // Don't prevent default to allow click events to still work
    // event.preventDefault();
  }

  function handleMouseMove(event: MouseEvent) {
    if (!isSelecting || startSelectionIndex === null) return;

    const messageElement = (event.target as HTMLElement).closest(
      ".message"
    ) as HTMLElement;
    if (!messageElement) return;

    const currentIndex = getMessageIndex(messageElement);
    const start = Math.min(startSelectionIndex, currentIndex);
    const end = Math.max(startSelectionIndex, currentIndex);

    selectedMessages = [];
    for (let i = start; i <= end; i++) {
      selectedMessages.push(i);
    }
    onSelectedMessagesChange(selectedMessages);
  }

  function handleMouseUp(event: MouseEvent) {
    if (isSelecting && selectedMessages.length > 1) {
      // Only show annotation form for drag selections with multiple messages
      showAnnotationForm = true;
      annotationNote = "";

      // Calculate the position relative to the annotations panel
      const annotationsPanel = document.querySelector(".annotations-panel");
      if (annotationsPanel) {
        const panelRect = annotationsPanel.getBoundingClientRect();
        annotationFormTop = Math.max(0, event.clientY - panelRect.top - 200);
      }
    }
    isSelecting = false;
    startSelectionIndex = null;
  }

  // Effect to initialize speakers when transcript changes
  $effect(() => {
    if (currentTranscript) {
      const _speakers = untrack(() => speakers);
      const _speakerColorMap = untrack(() => speakerColorMap);
      const _speakerVisibility = untrack(() => speakerVisibility);
      const _speakerFontWeight = untrack(() => speakerFontWeight);
      // Initialize speaker settings
      _speakerColorMap.clear();
      _speakerVisibility.clear();
      _speakerFontWeight.clear();

      _speakers.forEach((speaker, index) => {
        const defaultColors = [
          "#f9f9f9",
          "#ffffff",
          "#f0f0f0",
          "#e8e8e8",
          "#f5f5f5",
        ];
        console.log("Initializing speaker:", speaker);
        _speakerColorMap.set(
          speaker,
          defaultColors[index % defaultColors.length]
        );
        _speakerVisibility.set(speaker, true);
        _speakerFontWeight.set(speaker, 400); // Default font weight
      });
    } else {
      // Clear everything if no transcript
      console.log("No current transcript, clearing speaker states");
      const _speakerColorMap = untrack(() => speakerColorMap);
      const _speakerVisibility = untrack(() => speakerVisibility);
      const _speakerFontWeight = untrack(() => speakerFontWeight);
      _speakerColorMap.clear();
      _speakerVisibility.clear();
      _speakerFontWeight.clear();
    }
  });

  function isMessageVisible(speaker: string): boolean {
    // Force reactivity by accessing the map in a derived context
    return speakerVisibility.get(speaker) ?? true;
  }

  function getSpeakerClass(speaker: string, index: number): string {
    const selectedClass = selectedMessages.includes(index) ? " selected" : "";
    const annotationClass = annotations.some((ann) =>
      ann.messageIndices.includes(index)
    )
      ? " annotation-highlight"
      : "";

    return `message${selectedClass}${annotationClass}`;
  }

  function getSpeakerBackgroundColor(speaker: string): string {
    const color = speakerColorMap.get(speaker);
    const defaultColors = [
      "#f9f9f9",
      "#ffffff",
      "#f0f0f0",
      "#e8e8e8",
      "#f5f5f5",
    ];
    return color || defaultColors[0];
  }

  function getSpeakerFontWeight(speaker: string): string {
    const weight = speakerFontWeight.get(speaker) ?? "normal";
    return typeof weight === "number" ? weight.toString() : weight;
  }

  function handleMessageClick(index: number) {
    console.log("Message clicked:", index, selectedMessages);
    // if (selectedMessages.includes(index)) {
    //   selectedMessages = selectedMessages.filter((i) => i !== index);
    // } else {
    //   selectedMessages = [...selectedMessages, index];
    // }

    showAnnotationForm = selectedMessages.length > 0;

    if (selectedMessages.length === 0) {
      annotationLabel = "";
      annotationDescription = "";
      annotationFormTop = 0;
    } else if (selectedMessages.length === 1) {
      // Position form near the clicked message
      const messageElement = document.querySelector(
        `[data-message-index="${index}"]`
      );
      if (messageElement) {
        const annotationsPanel = document.querySelector(".annotations-panel");
        if (annotationsPanel) {
          const panelRect = annotationsPanel.getBoundingClientRect();
          const messageRect = messageElement.getBoundingClientRect();
          annotationFormTop = Math.max(0, messageRect.top - panelRect.top);
        }
      }
    }
  }

  async function handleSaveAnnotation() {
    if (annotationLabel.trim()) {
      await onSaveAnnotation(annotationLabel.trim(), annotationNote.trim());
      annotationLabel = "";
      annotationNote = "";
      annotationFormTop = 0;
    }
  }

  function handleCancelAnnotation() {
    showAnnotationForm = false;
    selectedMessages = [];
    onSelectedMessagesChange(selectedMessages);
    annotationLabel = "";
    annotationNote = "";
    annotationFormTop = 0;
  }

  // Segment Navigation Functions
  function scrollToSegment(segmentIndex: number) {
    if (!transcriptContent) return;

    const messageGroup = transcriptContent.querySelector(
      `.message-group[data-segment-index="${segmentIndex}"]`
    );
    if (messageGroup) {
      const offset = 40; // Desired vertical offset in pixels
      const targetPosition = (messageGroup as HTMLElement).offsetTop - offset;

      transcriptContent.scrollTo({
        top: Math.max(0, targetPosition),
        behavior: "smooth",
      });
    }
  }

  function updateActiveSegment() {
    if (!currentTranscript || !transcriptContent) return;

    let maxVisibleArea = 0;

    currentTranscript.segments.forEach((segment, index) => {
      const messageGroup = transcriptContent!.querySelector(
        `.message-group[data-segment-index="${index}"]`
      ) as HTMLElement;
      if (messageGroup && transcriptContent) {
        // Calculate positions relative to the scroll container
        const groupTop = messageGroup.offsetTop;
        const groupBottom = groupTop + messageGroup.offsetHeight;

        // Calculate the currently visible viewport area within the scroll container
        const viewportTop = transcriptContent.scrollTop;
        const viewportBottom =
          transcriptContent.scrollTop + transcriptContent.clientHeight;

        // Only calculate visible area if the group intersects with the visible viewport
        let visibleArea = 0;
        if (groupBottom > viewportTop && groupTop < viewportBottom) {
          const visibleTop = Math.max(groupTop, viewportTop);
          const visibleBottom = Math.min(groupBottom, viewportBottom);
          visibleArea = visibleBottom - visibleTop;
        }

        if (visibleArea > maxVisibleArea) {
          maxVisibleArea = visibleArea;
          activeSegmentIndex = index;
        }
      }
    });
  }

  // Effect to set up scroll listener
  $effect(() => {
    const transcriptContent = document.querySelector(".transcript-content");
    if (!transcriptContent) return;

    const handleScroll = () => {
      updateActiveSegment();
    };

    transcriptContent.addEventListener("scroll", handleScroll);

    return () => {
      transcriptContent?.removeEventListener("scroll", handleScroll);
    };
  });

  // Segment visual bar functions
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

  function updateSegmentPositions() {
    if (!currentTranscript || !transcriptContent) {
      segmentPositions = [];
      return;
    }

    const totalHeight = transcriptContent.scrollHeight;
    if (totalHeight === 0) {
      segmentPositions = [];
      return;
    }

    const newPositions = currentTranscript.segments.map((_, segmentIndex) => {
      const messageGroup = transcriptContent!.querySelector(
        `.message-group[data-segment-index="${segmentIndex}"]`
      ) as HTMLElement;
      if (!messageGroup) return { top: 0, height: 0 };

      const segmentTop = (messageGroup.offsetTop / totalHeight) * 100;
      const segmentHeight = (messageGroup.offsetHeight / totalHeight) * 100;

      return { top: segmentTop, height: segmentHeight };
    });

    segmentPositions = newPositions;
  }

  function getSegmentTopPercentage(segmentIndex: number): number {
    return segmentPositions[segmentIndex]?.top || 0;
  }

  function getSegmentHeightPercentage(segmentIndex: number): number {
    return segmentPositions[segmentIndex]?.height || 0;
  }

  // Effect to update segment positions when content changes
  $effect(() => {
    if (currentTranscript && transcriptContent) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        updateSegmentPositions();
      }, 100);
    }
  });
</script>

<div class="main-content">
  <!-- Speaker Controls -->
  <Controllers
    {speakers}
    bind:speakerColorMap
    bind:speakerVisibility
    bind:speakerFontWeight
  />

  <!-- Segment Navigation -->
  <SegmentNav
    {currentTranscript}
    {activeSegmentIndex}
    onSegmentClick={scrollToSegment}
  />

  {#if currentTranscript}
    <div class="transcript-content" bind:this={transcriptContent}>
      <!-- Messages Panel -->
      <div class="messages-panel">
        <!-- Segment Visual Bar -->
        {#if currentTranscript.segments.length > 1}
          <div class="segment-visual-bar">
            {#each currentTranscript.segments as segment, index}
              {@const segmentColor = getSegmentColor(index)}
              <div
                class="segment-bar-section"
                class:active={activeSegmentIndex === index}
                style="background-color: {segmentColor}; top: {getSegmentTopPercentage(
                  index
                )}%; height: {getSegmentHeightPercentage(index)}%;"
                data-segment-index={index}
              ></div>
            {/each}
          </div>
        {/if}

        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
          class="messages-container"
          onmousedown={handleMouseDown}
          onmousemove={handleMouseMove}
          onmouseup={handleMouseUp}
          role="application"
          aria-label="Transcript messages - click and drag to select text for annotation"
        >
          {#each currentTranscript.segments as segment, segmentIndex}
            {#if segmentIndex >= 0}
              <div class="segment-divider">
                <div class="segment-title-marker">{segment.title}</div>
              </div>
            {/if}

            <div class="message-group" data-segment-index={segmentIndex}>
              {#each segment.messages as message, messageIndexInSegment}
                {@const globalMessageIndex =
                  currentTranscript.segments
                    .slice(0, segmentIndex)
                    .reduce((acc, s) => acc + s.messages.length, 0) +
                  messageIndexInSegment}

                {#if isMessageVisible(message.speaker)}
                  <div
                    class={getSpeakerClass(message.speaker, globalMessageIndex)}
                    data-message-index={globalMessageIndex}
                    data-speaker={message.speaker}
                    style="background-color: {getSpeakerBackgroundColor(
                      message.speaker
                    )}; font-weight: {getSpeakerFontWeight(message.speaker)};
                    z-index: {segment.messages.length - messageIndexInSegment};
                    "
                    role="button"
                    tabindex="0"
                    onclick={() => handleMessageClick(globalMessageIndex)}
                    onkeydown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleMessageClick(globalMessageIndex);
                      }
                    }}
                  >
                    <span>[{message.speaker}][{globalMessageIndex}]</span>
                    {message.content}
                    {#if message.timestamp}
                      <span class="message-time">{message.timestamp}</span>
                    {/if}
                  </div>
                {/if}
              {/each}
            </div>
          {/each}
        </div>
      </div>

      <!-- Annotations Panel -->
      <div class="annotations-panel">
        <!-- Positioned Annotations -->
        {#each positionedAnnotations as annotation (annotation.id)}
          <AnnotationDisplay {annotation} onDelete={onDeleteAnnotation} />
        {/each}

        <!-- Selection Annotation Form -->
        {#if showAnnotationForm}
          <div class="selection-annotation" style="top: {annotationFormTop}px;">
            <div class="selection-info">
              Selected {selectedMessages.length} message{selectedMessages.length !==
              1
                ? "s"
                : ""}
            </div>
            <div class="form-group">
              <label for="annotation-label">Label:</label>
              <input
                type="text"
                id="annotation-label"
                bind:value={annotationLabel}
                placeholder="Enter annotation label"
              />
            </div>
            <div class="form-group">
              <label for="annotation-description">Description:</label>
              <textarea
                id="annotation-description"
                bind:value={annotationNote}
                placeholder="Enter annotation description"
                rows="4"
              ></textarea>
            </div>
            <div class="annotation-actions">
              <button class="btn btn-primary" onclick={handleSaveAnnotation}
                >Save Annotation</button
              >
              <button class="btn btn-secondary" onclick={handleCancelAnnotation}
                >Cancel</button
              >
            </div>
          </div>
        {/if}
      </div>
    </div>
  {:else}
    <div class="loading">
      <p>Select a transcript to view its contents</p>
    </div>
  {/if}
</div>

<style>
  .main-content {
    flex: 1;
    background-color: white;
    padding: 20px;
    /* overflow-y: auto; */
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
  }

  .transcript-content {
    display: flex;
    position: relative;
    overflow-y: auto;
    flex: 1;
  }

  .messages-panel {
    flex: 1;
    border-right: 2px solid #e0e0e0;
    position: relative;
    height: fit-content;
  }

  /* Segment Visual Bar */
  .segment-visual-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 6px;
    background: white;
    z-index: 50;
  }

  .segment-bar-section {
    position: absolute;
    width: 100%;
    transition: all 0.3s ease;
    cursor: pointer;
  }

  .segment-bar-section:hover {
    width: 8px;
    left: -1px;
  }

  .segment-bar-section.active {
    width: 8px;
    left: -1px;
  }

  .annotations-panel {
    flex: 0 0 300px;
    padding-left: 15px;
    position: relative;
  }

  .messages-container {
    position: relative;
    user-select: none;
    /* overflow-y: auto; */
    padding-right: 12px;
    padding-left: 12px;
  }

  .message-group {
    position: relative;
  }

  .segment-divider {
    margin: 20px 0;
    border-top: 2px dashed #e0e0e0;
    position: relative;
  }

  .segment-title-marker {
    position: absolute;
    left: 0;
    top: -10px;
    background: white;
    padding: 0 10px;
    font-size: 12px;
    color: #666;
    font-weight: bold;
  }

  .message {
    padding: 10px;
    /* border-radius: 4px; */
    transition: all 0.2s ease;
    white-space: pre-wrap;
    line-height: 1.6;
    font-family: "Courier New", monospace;
    font-size: 14px;
    color: #2c3e50;
    border-bottom: 1px dashed #e0e0e0;
    cursor: pointer;
    user-select: none;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .message:hover {
    filter: brightness(0.9);
    transform: translateX(2px);
  }

  .message.selected {
    /* border-left: 2px solid #3498db; */
    border-right: 4px solid #3498db;
    transform: translateX(12px);
    box-shadow: 0 2px 5px 2px rgba(14, 42, 61, 0.3);
  }
  /* .selected:last-of-type {
    border-left: 4px solid #3498db;
  } */

  /* .message.annotation-highlight {
    border-right: 3px solid #3498db;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.4);
  } */
  .message.annotation-hover-highlight {
    border-right: 3px solid #3498db;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.4);
  }

  /* .message.annotation-hover-highlight { */
  /* background-color: rgba(52, 152, 219, 0.2) !important; */
  /* border: 2px solid #3498db; */
  /* } */

  .message.speaker-0 {
    background-color: #f9f9f9;
  }

  .message.speaker-1 {
    background-color: #ffffff;
  }

  .message.speaker-2 {
    background-color: #f0f0f0;
  }

  .message.speaker-3 {
    background-color: #e8e8e8;
  }

  .message.speaker-4 {
    background-color: #f5f5f5;
  }

  .selection-annotation {
    background-color: #e8f4fd;
    border: 1px solid #3498db;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    position: absolute;
    width: 280px;
    z-index: 100;
  }

  .selection-info {
    font-size: 12px;
    color: #2980b9;
    margin-bottom: 15px;
    font-weight: bold;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 12px;
    color: #2c3e50;
  }

  .form-group input,
  .form-group textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    font-size: 12px;
    font-family: inherit;
  }

  .form-group textarea {
    resize: vertical;
    min-height: 80px;
  }

  .message-time {
    float: right;
    font-size: 11px;
    color: #666;
    font-style: italic;
    position: absolute;
    right: 10px;
    top: 10px;
  }

  .message.hidden {
    display: none;
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
    font-style: italic;
  }

  .annotation-actions {
    display: flex;
    gap: 10px;
    margin-top: 10px;
  }

  .btn {
    padding: 6px 12px;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
  }

  .btn-primary {
    background-color: #3498db;
    color: white;
  }

  .btn-secondary {
    background-color: #95a5a6;
    color: white;
  }

  .btn:hover {
    opacity: 0.9;
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
    font-style: italic;
  }
</style>
