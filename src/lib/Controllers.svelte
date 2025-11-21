<script lang="ts">
  type Props = {
    speakers: string[];
    speakerColorMap: Map<string, string>;
    speakerVisibility: Map<string, boolean>;
    speakerFontWeight: Map<string, number>;
  };

  let {
    speakers,
    speakerColorMap = $bindable(),
    speakerVisibility = $bindable(),
    speakerFontWeight = $bindable(),
  }: Props = $props();

  function handleVisibilityChange(speaker: string, event: Event) {
    const checkbox = event.target as HTMLInputElement;
    speakerVisibility.set(speaker, checkbox.checked);
    // Trigger reactivity by reassigning the map
    speakerVisibility = new Map(speakerVisibility);
  }

  function handleColorChange(speaker: string, event: Event) {
    const speakerColorMapBefore = new Map(speakerColorMap);
    console.log("Color change event triggered", speakerColorMapBefore);
    const input = event.target as HTMLInputElement;
    const selectedColor = input.value;
    speakerColorMap.set(speaker, selectedColor);
    // Trigger reactivity by reassigning the map
    speakerColorMap = new Map(speakerColorMap);
    console.log("Color change event", speakerColorMap);
  }

  function handleFontWeightChange(speaker: string, event: Event) {
    const checkbox = event.target as HTMLInputElement;
    const fontWeight = checkbox.checked ? 600 : 400;
    speakerFontWeight.set(speaker, fontWeight);
    // Trigger reactivity by reassigning the map
    speakerFontWeight = new Map(speakerFontWeight);
  }

  function getSpeakerColor(speaker: string): string {
    const color = speakerColorMap.get(speaker);
    return color || "#f9f9f9"; // default color
  }
</script>

<div class="speaker-controllers">
  <h3>Speaker Controls</h3>

  {#if speakers.length > 0}
    <div class="controllers-list">
      {#each speakers as speaker}
        <div class="speaker-control-group">
          <!-- Visibility Control -->
          <div class="control-row">
            <label class="speaker-checkbox-label">
              <input
                type="checkbox"
                checked={speakerVisibility.get(speaker) ?? true}
                onchange={(e) => handleVisibilityChange(speaker, e)}
              />
              <span
                class="speaker-name"
                style="background-color: {getSpeakerColor(
                  speaker
                )}; font-weight: {speakerFontWeight.get(speaker) ?? 400};"
              >
                {speaker}
              </span>
            </label>
          </div>

          <!-- Color Control -->
          <div class="control-row">
            <span class="control-label">Color:</span>
            <input
              type="color"
              class="color-picker"
              value={getSpeakerColor(speaker)}
              oninput={(e) => handleColorChange(speaker, e)}
              aria-label="Color picker for {speaker}"
            />
          </div>

          <!-- Font Weight Control -->
          <div class="control-row">
            <label class="speaker-bold-toggle">
              <input
                type="checkbox"
                class="speaker-bold-checkbox"
                checked={(speakerFontWeight.get(speaker) ?? 400) > 500}
                onchange={(e) => handleFontWeightChange(speaker, e)}
              />
              Bold text
            </label>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <p class="no-speakers">No speakers available</p>
  {/if}
</div>

<style>
  .speaker-controllers {
    padding: 12px 15px;
    background-color: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e9ecef;
    margin-bottom: 15px;
    /* border-left: 4px solid #3498db; */
  }

  .speaker-controllers h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #2c3e50;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 6px;
  }

  .controllers-list {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 12px;
  }

  .speaker-control-group {
    padding: 8px 12px;
    background-color: white;
    border-radius: 4px;
    border: 1px solid #dee2e6;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    min-width: 180px;
    flex: 0 1 auto;
  }

  .control-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
    gap: 8px;
  }

  .control-row:last-child {
    margin-bottom: 0;
  }

  .speaker-checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    flex: 1;
  }

  .speaker-name {
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 13px;
    border: 1px solid #ddd;
    min-width: 80px;
    text-align: center;
  }

  .control-label {
    font-size: 12px;
    color: #666;
    min-width: 50px;
  }

  .color-picker {
    width: 40px;
    height: 30px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    background: none;
  }

  .speaker-bold-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-size: 12px;
    color: #666;
  }

  .speaker-bold-checkbox {
    margin: 0;
  }

  .no-speakers {
    text-align: center;
    color: #666;
    font-style: italic;
    margin: 20px 0;
    font-size: 14px;
  }
</style>
