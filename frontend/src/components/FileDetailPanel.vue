<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import TracePreview from './TracePreview.vue'

defineProps({
  selectedFile: {
    type: Object,
    required: true,
  },
  newTagName: {
    type: String,
    required: true,
  },
  fileNotesDraft: {
    type: String,
    required: true,
  },
  fileMeasurementDateDraft: {
    type: String,
    required: true,
  },
  fileExcitationPowerDraft: {
    type: [String, Number],
    required: true,
  },
  fileObjectiveDraft: {
    type: String,
    required: true,
  },
  savingFileNotes: {
    type: Boolean,
    required: true,
  },
  selectedDetailView: {
    type: String,
    required: true,
  },
  selectedDetailBinWidthMs: {
    type: Number,
    required: true,
  },
  detailBinWidthOptions: {
    type: Array,
    required: true,
  },
  fileDetailTrace: {
    type: Object,
    default: null,
  },
  fileAcfTrace: {
    type: Object,
    default: null,
  },
  loadingFileDetailTrace: {
    type: Boolean,
    required: true,
  },
  loadingFileAcfTrace: {
    type: Boolean,
    required: true,
  },
  acfBinsPerDec: {
    type: Number,
    required: true,
  },
  acfLagMinExp: {
    type: Number,
    required: true,
  },
  acfLagMaxExp: {
    type: Number,
    required: true,
  },
  acfCutPoints: {
    type: Number,
    required: true,
  },
  acfTauMinUs: {
    type: Number,
    required: true,
  },
  acfTauMaxUs: {
    type: Number,
    required: true,
  },
})

const emit = defineEmits([
  'back',
  'update:newTagName',
  'add-tag',
  'remove-tag',
  'update:fileNotesDraft',
  'update:fileMeasurementDateDraft',
  'update:fileExcitationPowerDraft',
  'update:fileObjectiveDraft',
  'save-notes',
  'switch-detail-view',
  'update:selectedDetailBinWidthMs',
  'load-detail-trace',
  'load-acf-trace',
  'update:acfBinsPerDec',
  'update:acfLagMinExp',
  'update:acfLagMaxExp',
  'update:acfCutPoints',
  'update:acfTauMinUs',
  'update:acfTauMaxUs',
])
</script>

<template>
  <Card class="panel-card panel-card--main-detail">
    <template #title>File Details</template>
    <template #content>
      <div class="panel-content file-detail-main-column">
        <Button
          class="secondary-button small-button"
          label="← Back to dataset"
          @click="emit('back')"
        />

        <Card class="sub-card">
          <template #title>File Info</template>
          <template #content>
            <div class="panel-content">
              <h3>{{ selectedFile.filename }}</h3>
              <p class="file-meta">{{ selectedFile.object_key }}</p>

              <div class="file-tags" v-if="selectedFile.tags?.length">
                <span
                  v-for="tag in selectedFile.tags"
                  :key="tag.id"
                  class="tag-pill removable-tag"
                  @click="emit('remove-tag', selectedFile, tag)"
                >
                  {{ tag.name }} ×
                </span>
              </div>

              <div class="tag-input-row">
                <InputText
                  :model-value="newTagName"
                  placeholder="Add tag"
                  class="text-input"
                  @update:model-value="emit('update:newTagName', $event)"
                  @keyup.enter="emit('add-tag', selectedFile)"
                />
                <Button
                  class="secondary-button small-button"
                  label="Add tag"
                  @click="emit('add-tag', selectedFile)"
                />
              </div>
            </div>
          </template>
        </Card>

        <Card class="sub-card file-analysis-card">
          <template #title>Analysis</template>
          <template #content>
            <div class="panel-content">
              <div class="detail-view-toggle">
                <Button
                  class="secondary-button small-button"
                  :class="{ 'active-toggle': selectedDetailView === 'trace' }"
                  label="Trace"
                  @click="emit('switch-detail-view', 'trace')"
                />
                <Button
                  class="secondary-button small-button"
                  :class="{ 'active-toggle': selectedDetailView === 'acf' }"
                  label="ACF"
                  @click="emit('switch-detail-view', 'acf')"
                />
              </div>

              <div v-if="selectedDetailView === 'trace'" class="detail-controls">
                <label for="bin-width-select">Bin width:</label>
                <Select
                  id="bin-width-select"
                  :model-value="selectedDetailBinWidthMs"
                  :options="detailBinWidthOptions"
                  optionLabel="label"
                  optionValue="value"
                  class="text-input"
                  @update:model-value="emit('update:selectedDetailBinWidthMs', $event)"
                  @change="emit('load-detail-trace', selectedFile.id)"
                />
              </div>

              <div v-if="selectedDetailView === 'acf'" class="detail-controls detail-controls-grid">
                <label>
                  Bins/dec
                  <input
                    :value="acfBinsPerDec"
                    type="number"
                    min="1"
                    class="text-input"
                    @input="emit('update:acfBinsPerDec', Number($event.target.value))"
                  />
                </label>

                <label>
                  Lag min exp
                  <input
                    :value="acfLagMinExp"
                    type="number"
                    class="text-input"
                    @input="emit('update:acfLagMinExp', Number($event.target.value))"
                  />
                </label>

                <label>
                  Lag max exp
                  <input
                    :value="acfLagMaxExp"
                    type="number"
                    class="text-input"
                    @input="emit('update:acfLagMaxExp', Number($event.target.value))"
                  />
                </label>

                <label>
                  Cut points
                  <input
                    :value="acfCutPoints"
                    type="number"
                    min="0"
                    class="text-input"
                    @input="emit('update:acfCutPoints', Number($event.target.value))"
                  />
                </label>

                <label>
                  τ min (µs)
                  <input
                    :value="acfTauMinUs"
                    type="number"
                    min="0"
                    step="0.1"
                    class="text-input"
                    @input="emit('update:acfTauMinUs', Number($event.target.value))"
                  />
                </label>

                <label>
                  τ max (µs, 0 = none)
                  <input
                    :value="acfTauMaxUs"
                    type="number"
                    min="0"
                    step="0.1"
                    class="text-input"
                    @input="emit('update:acfTauMaxUs', Number($event.target.value))"
                  />
                </label>

                <Button
                  class="secondary-button small-button"
                  :label="loadingFileAcfTrace ? 'Loading...' : 'Update ACF'"
                  :loading="loadingFileAcfTrace"
                  :disabled="loadingFileAcfTrace"
                  @click="emit('load-acf-trace', selectedFile.id)"
                />
              </div>

              <TracePreview
                v-if="selectedDetailView === 'trace' && fileDetailTrace"
                :preview="fileDetailTrace"
                variant="detail"
              />

              <TracePreview
                v-else-if="selectedDetailView === 'acf' && fileAcfTrace"
                :preview="fileAcfTrace"
                variant="detail"
              />

              <p v-else-if="selectedDetailView === 'trace' && loadingFileDetailTrace" class="empty-state">
                Loading Detail-Trace ...
              </p>

              <p v-else-if="selectedDetailView === 'acf' && loadingFileAcfTrace" class="empty-state">
                Loading ACF/CCF ...
              </p>

              <p v-else class="empty-state">No data available for this view.</p>
            </div>
          </template>
        </Card>
      </div>
    </template>
  </Card>

  <Card class="panel-card panel-card--side-detail">
    <template #title>Notes & Metadata</template>
    <template #content>
      <div class="panel-content">
        <div class="file-notes-section">
          <label class="notes-label" for="file-notes-textarea">File notes</label>
          <Textarea
            id="file-notes-textarea"
            :model-value="fileNotesDraft"
            class="text-input textarea-input"
            placeholder="Add notes for this file"
            @update:model-value="emit('update:fileNotesDraft', $event)"
          />

          <div class="file-metadata-grid">
            <label>
              Measurement date
              <input
                :value="fileMeasurementDateDraft"
                type="datetime-local"
                class="text-input"
                @input="emit('update:fileMeasurementDateDraft', $event.target.value)"
              />
            </label>

            <label>
              Excitation power (µW)
              <input
                :value="fileExcitationPowerDraft"
                type="number"
                step="0.1"
                min="0"
                class="text-input"
                placeholder="e.g. 5"
                @input="emit('update:fileExcitationPowerDraft', $event.target.value)"
              />
            </label>

            <label>
              Objective
              <InputText
                :model-value="fileObjectiveDraft"
                class="text-input"
                placeholder="e.g. Plan Apo"
                @update:model-value="emit('update:fileObjectiveDraft', $event)"
              />
            </label>
          </div>

          <Button
            class="secondary-button small-button save-notes-button"
            :label="savingFileNotes ? 'Saving...' : 'Save notes'"
            :loading="savingFileNotes"
            :disabled="savingFileNotes"
            @click="emit('save-notes')"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.panel-content,
.file-detail-main-column,
.file-notes-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-detail-main-column {
  min-width: 0;
}

.sub-card {
  border-radius: 14px;
}

.file-analysis-card {
  min-width: 0;
}

.file-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: #eef2ff;
  color: #445;
  font-size: 0.75rem;
  font-weight: 600;
}

.removable-tag {
  cursor: pointer;
}

.tag-input-row {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.file-meta {
  font-size: 0.9rem;
  color: #666;
  word-break: break-word;
}

.detail-view-toggle {
  display: flex;
  gap: 0.5rem;
}

.active-toggle {
  background: #2f6fed;
}

.detail-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.detail-controls-grid label,
.file-metadata-grid label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.file-metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.textarea-input {
  min-height: 90px;
  resize: vertical;
}

.save-notes-button {
  align-self: flex-start;
}

.notes-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #555;
}
</style>