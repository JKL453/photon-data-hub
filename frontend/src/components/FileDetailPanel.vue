<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
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

const showMetadataSection = ref(true)

defineProps({
  selectedFile: { type: Object, required: true },
  newTagName: { type: String, required: true },
  fileNotesDraft: { type: String, required: true },
  fileMeasurementDateDraft: { type: String, required: true },
  fileExcitationPowerDraft: { type: [String, Number], required: true },
  fileObjectiveDraft: { type: String, required: true },
  savingFileNotes: { type: Boolean, required: true },
  selectedDetailView: { type: String, required: true },
  selectedDetailBinWidthMs: { type: Number, required: true },
  detailBinWidthOptions: { type: Array, required: true },
  fileDetailTrace: { type: Object, default: null },
  fileAcfTrace: { type: Object, default: null },
  loadingFileDetailTrace: { type: Boolean, required: true },
  loadingFileAcfTrace: { type: Boolean, required: true },
  acfBinsPerDec: { type: Number, required: true },
  acfLagMinExp: { type: Number, required: true },
  acfLagMaxExp: { type: Number, required: true },
  acfCutPoints: { type: Number, required: true },
  acfTauMinUs: { type: Number, required: true },
  acfTauMaxUs: { type: Number, required: true },
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
  <!-- ── Main analysis panel ──────────────────────────────────────── -->
  <Card class="panel-card panel-card--main-detail">
    <template #title>
      <div class="panel-title-row">
        <div class="panel-title-left">
          <Button
            icon="pi pi-arrow-left"
            size="small"
            severity="secondary"
            variant="text"
            rounded
            aria-label="Back"
            @click="emit('back')"
          />
          <div class="panel-title-text">
            <span class="panel-title-label">File Details</span>
            <span class="panel-title-filename" :title="selectedFile.object_key">{{ selectedFile.filename }}</span>
          </div>
        </div>
        <Tag value="Selected" severity="info" rounded />
      </div>
    </template>

    <template #content>
      <div class="panel-content file-detail-main-column">

        <!-- File info: object key + tags -->
        <div class="file-info-block">
          <p class="file-meta">{{ selectedFile.object_key }}</p>

          <div class="tag-row">
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
                placeholder="Add tag …"
                @update:model-value="emit('update:newTagName', $event)"
                @keyup.enter="emit('add-tag', selectedFile)"
              />
              <Button
                icon="pi pi-plus"
                aria-label="Add tag"
                severity="secondary"
                @click="emit('add-tag', selectedFile)"
              />
            </div>
          </div>
        </div>

        <!-- Analysis tabs -->
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
              <span>ACF / CCF</span>
            </Tab>
          </TabList>

          <TabPanels>
            <!-- Trace tab -->
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

                <TracePreview v-if="fileDetailTrace" :preview="fileDetailTrace" variant="detail" />

                <div v-else-if="loadingFileDetailTrace" class="loading-inline">
                  <ProgressSpinner class="inline-spinner" stroke-width="4" />
                  <span>Loading trace …</span>
                </div>

                <Message v-else severity="secondary" :closable="false">
                  No trace data available.
                </Message>
              </div>
            </TabPanel>

            <!-- ACF tab -->
            <TabPanel value="acf">
              <div class="tab-panel-content">
                <div class="detail-controls-grid">
                  <label class="field">
                    <span>Bins / dec</span>
                    <InputNumber :model-value="acfBinsPerDec" :min="1" :use-grouping="false" @update:model-value="emit('update:acfBinsPerDec', $event ?? 1)" />
                  </label>
                  <label class="field">
                    <span>Lag min exp</span>
                    <InputNumber :model-value="acfLagMinExp" :use-grouping="false" @update:model-value="emit('update:acfLagMinExp', $event ?? 0)" />
                  </label>
                  <label class="field">
                    <span>Lag max exp</span>
                    <InputNumber :model-value="acfLagMaxExp" :use-grouping="false" @update:model-value="emit('update:acfLagMaxExp', $event ?? 0)" />
                  </label>
                  <label class="field">
                    <span>Cut points</span>
                    <InputNumber :model-value="acfCutPoints" :min="0" :use-grouping="false" @update:model-value="emit('update:acfCutPoints', $event ?? 0)" />
                  </label>
                  <label class="field">
                    <span>τ min (µs)</span>
                    <InputNumber :model-value="acfTauMinUs" :min="0" :min-fraction-digits="0" :max-fraction-digits="3" @update:model-value="emit('update:acfTauMinUs', $event ?? 0)" />
                  </label>
                  <label class="field">
                    <span>τ max (µs, 0 = none)</span>
                    <InputNumber :model-value="acfTauMaxUs" :min="0" :min-fraction-digits="0" :max-fraction-digits="3" @update:model-value="emit('update:acfTauMaxUs', $event ?? 0)" />
                  </label>
                  <Button
                    label="Update ACF"
                    icon="pi pi-refresh"
                    :loading="loadingFileAcfTrace"
                    :disabled="loadingFileAcfTrace"
                    @click="emit('load-acf-trace', selectedFile.id)"
                  />
                </div>

                <TracePreview v-if="fileAcfTrace" :preview="fileAcfTrace" variant="detail" />

                <div v-else-if="loadingFileAcfTrace" class="loading-inline">
                  <ProgressSpinner class="inline-spinner" stroke-width="4" />
                  <span>Loading ACF / CCF …</span>
                </div>

                <Message v-else severity="secondary" :closable="false">
                  No ACF data available.
                </Message>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>

      </div>
    </template>
  </Card>

  <!-- ── Side panel ───────────────────────────────────────────────── -->
  <Card class="panel-card panel-card--side-detail">
    <template #title>
      <div class="side-panel-title">
        <i class="pi pi-sliders-h side-panel-icon"></i>
        <span>Notes &amp; Metadata</span>
      </div>
    </template>

    <template #content>
      <div class="panel-content">
        <label class="field">
          <span>File notes</span>
          <Textarea
            :model-value="fileNotesDraft"
            auto-resize
            rows="4"
            placeholder="Add notes for this file …"
            @update:model-value="emit('update:fileNotesDraft', $event)"
          />
        </label>

        <!-- Metadata section (collapsible) -->
        <div class="section-block">
          <button class="section-toggle" @click="showMetadataSection = !showMetadataSection">
            <i class="pi pi-tag section-toggle-icon"></i>
            <span>Measurement Metadata</span>
            <i :class="['pi section-chevron', showMetadataSection ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
          </button>
          <div v-if="showMetadataSection" class="section-body">
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
          </div>
        </div>

        <Button
          label="Save"
          icon="pi pi-save"
          class="save-button"
          :loading="savingFileNotes"
          :disabled="savingFileNotes"
          @click="emit('save-notes')"
        />
      </div>
    </template>
  </Card>
</template>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────── */
.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.panel-title-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
  flex: 1;
}

.panel-title-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.panel-title-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
  line-height: 1.2;
}

.panel-title-filename {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--p-text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.side-panel-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.9rem;
  font-weight: 700;
}

.side-panel-icon {
  color: var(--p-primary-color);
  font-size: 0.9rem;
}

.panel-content,
.file-detail-main-column,
.file-info-block,
.tab-panel-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-card--main-detail,
.panel-card--side-detail {
  min-width: 0;
}

.panel-card--side-detail {
  position: sticky;
  top: 1rem;
}

/* ── File info ───────────────────────────────────────────────────── */
.file-meta {
  margin: 0;
  font-size: 0.79rem;
  color: var(--p-text-muted-color);
  word-break: break-word;
  font-family: ui-monospace, Consolas, monospace;
  opacity: 0.75;
}

.tag-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.removable-tag {
  cursor: pointer;
  transition: opacity 0.12s ease;
}

.removable-tag:hover {
  opacity: 0.7;
}

.tag-input-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── Field labels ────────────────────────────────────────────────── */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

/* ── Analysis controls ───────────────────────────────────────────── */
.detail-controls {
  max-width: 240px;
}

.detail-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  align-items: end;
}

.file-metadata-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* ── Loading ─────────────────────────────────────────────────────── */
.loading-inline {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 0;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
}

.inline-spinner {
  width: 1.4rem;
  height: 1.4rem;
}

/* ── Save button ─────────────────────────────────────────────────── */
.save-button {
  align-self: flex-start;
}

/* ── Custom collapsible sections ─────────────────────────────────── */
.section-block {
  border: 1px solid var(--p-content-border-color);
  border-radius: 10px;
  overflow: hidden;
}

.section-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 0.9rem;
  background: color-mix(in srgb, var(--p-content-background) 97%, var(--p-text-color) 3%);
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--p-text-color);
  font-size: 0.85rem;
  font-weight: 600;
  font-family: inherit;
  transition: background 0.12s ease;
}

.section-toggle:hover {
  background: color-mix(in srgb, var(--p-content-background) 91%, var(--p-text-color) 9%);
}

.section-toggle-icon {
  color: var(--p-primary-color);
  font-size: 0.85rem;
}

.section-chevron {
  margin-left: auto;
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
}

.section-body {
  padding: 1rem;
  border-top: 1px solid var(--p-content-border-color);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Deep overrides ──────────────────────────────────────────────── */
:deep(.analysis-tabs .p-tab) {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}

:deep(.analysis-tabs .p-tabpanels) {
  padding: 1.1rem 0 0;
}

:deep(.p-inputtext),
:deep(.p-textarea),
:deep(.p-inputnumber),
:deep(.p-inputnumber-input),
:deep(.p-select),
:deep(.analysis-tabs) {
  width: 100%;
}

/* ── Responsive ──────────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .panel-card--side-detail {
    position: static;
  }

  .file-metadata-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
</style>
