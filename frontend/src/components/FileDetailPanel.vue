<script setup>
import Button from 'primevue/button'
import Card from 'primevue/card'
import Fieldset from 'primevue/fieldset'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
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

function updateDetailView(view) {
  if (!view) return
  emit('switch-detail-view', view)
}

function updateTraceBinWidth(value, fileId) {
  emit('update:selectedDetailBinWidthMs', value)
  emit('load-detail-trace', fileId)
}
</script>

<template>
  <Card class="panel-card panel-card--main-detail">
    <template #title>
      <div class="panel-title-row">
        <span>File Details</span>
        <div class="panel-actions">
          <Tag value="Selected file" severity="info" rounded />
          <Button
            label="Back"
            icon="pi pi-arrow-left"
            size="small"
            severity="secondary"
            variant="outlined"
            @click="emit('back')"
          />
        </div>
      </div>
    </template>

    <template #content>
      <div class="panel-content file-detail-main-column">
        <Fieldset legend="File Info">
          <div class="file-info-stack">
            <div>
              <h3 class="file-title">{{ selectedFile.filename }}</h3>
              <p class="file-meta">{{ selectedFile.object_key }}</p>
            </div>

            <div v-if="selectedFile.tags?.length" class="file-tags">
              <Tag
                v-for="tag in selectedFile.tags"
                :key="tag.id"
                :value="`${tag.name} ×`"
                severity="info"
                rounded
                class="removable-tag"
                @click="emit('remove-tag', selectedFile, tag)"
              />
            </div>

            <div class="tag-input-row">
              <InputText
                :model-value="newTagName"
                placeholder="Add tag"
                @update:model-value="emit('update:newTagName', $event)"
                @keyup.enter="emit('add-tag', selectedFile)"
              />
              <Button
                label="Add tag"
                icon="pi pi-plus"
                severity="secondary"
                @click="emit('add-tag', selectedFile)"
              />
            </div>
          </div>
        </Fieldset>

        <Fieldset legend="Analysis" class="file-analysis-fieldset">
          <div class="panel-content">
            <Tabs
              :value="selectedDetailView"
              scrollable
              class="analysis-tabs"
              @update:value="updateDetailView"
            >
              <TabList>
                <Tab value="trace">
                  <i class="pi pi-chart-line"></i>
                  <span>Trace</span>
                </Tab>
                <Tab value="acf">
                  <i class="pi pi-wave-pulse"></i>
                  <span>ACF</span>
                </Tab>
              </TabList>

              <TabPanels>
                <TabPanel value="trace">
                  <div class="tab-panel-content">
                    <div class="detail-controls">
                      <label class="field">
                        <span>Bin width</span>
                        <Select
                          :model-value="selectedDetailBinWidthMs"
                          :options="detailBinWidthOptions"
                          optionLabel="label"
                          optionValue="value"
                          @update:model-value="updateTraceBinWidth($event, selectedFile.id)"
                        />
                      </label>
                    </div>

                    <TracePreview
                      v-if="fileDetailTrace"
                      :preview="fileDetailTrace"
                      variant="detail"
                    />

                    <div v-else-if="loadingFileDetailTrace" class="loading-inline">
                      <ProgressSpinner class="inline-spinner" stroke-width="4" />
                      <span>Loading Detail-Trace ...</span>
                    </div>

                    <Message v-else severity="secondary" :closable="false">
                      No trace data available.
                    </Message>
                  </div>
                </TabPanel>

                <TabPanel value="acf">
                  <div class="tab-panel-content">
                    <div class="detail-controls-grid">
                      <label class="field">
                        <span>Bins/dec</span>
                        <InputNumber
                          :model-value="acfBinsPerDec"
                          :min="1"
                          :use-grouping="false"
                          @update:model-value="emit('update:acfBinsPerDec', $event ?? 1)"
                        />
                      </label>

                      <label class="field">
                        <span>Lag min exp</span>
                        <InputNumber
                          :model-value="acfLagMinExp"
                          :use-grouping="false"
                          @update:model-value="emit('update:acfLagMinExp', $event ?? 0)"
                        />
                      </label>

                      <label class="field">
                        <span>Lag max exp</span>
                        <InputNumber
                          :model-value="acfLagMaxExp"
                          :use-grouping="false"
                          @update:model-value="emit('update:acfLagMaxExp', $event ?? 0)"
                        />
                      </label>

                      <label class="field">
                        <span>Cut points</span>
                        <InputNumber
                          :model-value="acfCutPoints"
                          :min="0"
                          :use-grouping="false"
                          @update:model-value="emit('update:acfCutPoints', $event ?? 0)"
                        />
                      </label>

                      <label class="field">
                        <span>τ min (µs)</span>
                        <InputNumber
                          :model-value="acfTauMinUs"
                          :min="0"
                          :min-fraction-digits="0"
                          :max-fraction-digits="3"
                          @update:model-value="emit('update:acfTauMinUs', $event ?? 0)"
                        />
                      </label>

                      <label class="field">
                        <span>τ max (µs, 0 = none)</span>
                        <InputNumber
                          :model-value="acfTauMaxUs"
                          :min="0"
                          :min-fraction-digits="0"
                          :max-fraction-digits="3"
                          @update:model-value="emit('update:acfTauMaxUs', $event ?? 0)"
                        />
                      </label>

                      <Button
                        label="Update ACF"
                        icon="pi pi-refresh"
                        :loading="loadingFileAcfTrace"
                        :disabled="loadingFileAcfTrace"
                        @click="emit('load-acf-trace', selectedFile.id)"
                      />
                    </div>

                    <TracePreview
                      v-if="fileAcfTrace"
                      :preview="fileAcfTrace"
                      variant="detail"
                    />

                    <div v-else-if="loadingFileAcfTrace" class="loading-inline">
                      <ProgressSpinner class="inline-spinner" stroke-width="4" />
                      <span>Loading ACF/CCF ...</span>
                    </div>

                    <Message v-else severity="secondary" :closable="false">
                      No ACF data available.
                    </Message>
                  </div>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </div>
        </Fieldset>
      </div>
    </template>
  </Card>

  <Card class="panel-card panel-card--side-detail">
    <template #title>Notes & Metadata</template>
    <template #content>
      <div class="panel-content">
        <label class="field">
          <span>File notes</span>
          <Textarea
            :model-value="fileNotesDraft"
            auto-resize
            rows="5"
            placeholder="Add notes for this file"
            @update:model-value="emit('update:fileNotesDraft', $event)"
          />
        </label>

        <Fieldset legend="Metadata">
          <div class="file-metadata-grid">
            <label class="field">
              <span>Measurement date</span>
              <InputText
                :model-value="fileMeasurementDateDraft"
                type="datetime-local"
                @update:model-value="emit('update:fileMeasurementDateDraft', $event)"
              />
            </label>

            <label class="field">
              <span>Excitation power (µW)</span>
              <InputNumber
                :model-value="fileExcitationPowerDraft === '' ? null : Number(fileExcitationPowerDraft)"
                :min="0"
                :min-fraction-digits="0"
                :max-fraction-digits="3"
                placeholder="e.g. 5"
                @update:model-value="emit('update:fileExcitationPowerDraft', $event ?? '')"
              />
            </label>

            <label class="field">
              <span>Objective</span>
              <InputText
                :model-value="fileObjectiveDraft"
                placeholder="e.g. Plan Apo"
                @update:model-value="emit('update:fileObjectiveDraft', $event)"
              />
            </label>
          </div>
        </Fieldset>

        <Button
          label="Save notes"
          icon="pi pi-save"
          class="save-notes-button"
          :loading="savingFileNotes"
          :disabled="savingFileNotes"
          @click="emit('save-notes')"
        />
      </div>
    </template>
  </Card>
</template>

<style scoped>
.panel-title-row,
.panel-actions,
.tag-input-row,
.file-tags,
.loading-inline {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.panel-title-row {
  justify-content: space-between;
  flex-wrap: wrap;
}

.panel-actions {
  flex-wrap: wrap;
}

.panel-content,
.file-detail-main-column,
.file-info-stack,
.tab-panel-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-detail-main-column,
.file-analysis-fieldset,
.panel-card--main-detail,
.panel-card--side-detail {
  min-width: 0;
}

.panel-card--side-detail {
  position: sticky;
  top: 1rem;
}

.file-title {
  margin: 0 0 0.35rem;
  overflow-wrap: anywhere;
}

.file-meta {
  margin: 0;
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
  word-break: break-word;
}

.file-tags {
  flex-wrap: wrap;
}

.removable-tag {
  cursor: pointer;
}

.tag-input-row {
  align-items: stretch;
}

.detail-controls-grid,
.file-metadata-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  align-items: end;
}

.detail-controls-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.detail-controls {
  max-width: 260px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}

.save-notes-button {
  align-self: flex-start;
}

.inline-spinner {
  width: 1.5rem;
  height: 1.5rem;
}

:deep(.p-fieldset) {
  border-radius: 8px;
}

:deep(.analysis-tabs .p-tab) {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

:deep(.analysis-tabs .p-tabpanels) {
  padding: 1rem 0 0;
}

:deep(.p-inputtext),
:deep(.p-textarea),
:deep(.p-inputnumber),
:deep(.p-inputnumber-input),
:deep(.p-select),
:deep(.analysis-tabs) {
  width: 100%;
}

@media (max-width: 1200px) {
  .panel-card--side-detail {
    position: static;
  }

  .file-metadata-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}
</style>
