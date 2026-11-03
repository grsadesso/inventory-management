<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div
          class="modal-container"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          @click.stop
          @keydown.esc="close"
        >
          <div class="modal-header">
            <h3 :id="titleId" class="modal-title">
              {{ isView ? 'Purchase Order' : 'Create Purchase Order' }}
            </h3>
            <button class="close-button" type="button" aria-label="Close" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- View mode: read-only details of the existing PO -->
          <template v-if="isView">
            <div class="modal-body">
              <div v-if="loading" class="state-message">Loading purchase order...</div>
              <div v-else-if="loadError" class="state-error" role="alert">{{ loadError }}</div>
              <template v-else-if="purchaseOrder">
                <div class="item-summary">
                  <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                  <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO Number</div>
                    <div class="info-value mono">{{ purchaseOrder.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">
                      <span class="badge info">{{ purchaseOrder.status }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ purchaseOrder.quantity }} units</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <div class="info-value">{{ money(purchaseOrder.unit_cost, 2) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total Cost</div>
                    <div class="info-value">{{ money(purchaseOrder.quantity * purchaseOrder.unit_cost, 2) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                  </div>
                  <div v-if="purchaseOrder.notes" class="info-item info-item-wide">
                    <div class="info-label">Notes</div>
                    <div class="info-value notes">{{ purchaseOrder.notes }}</div>
                  </div>
                </div>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn-secondary" type="button" @click="close">Close</button>
            </div>
          </template>

          <!-- Create mode: form with client-side validation -->
          <form v-else novalidate @submit.prevent="submit">
            <div class="modal-body">
              <div class="item-summary">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }} &middot; Shortage: {{ shortage }} units</div>
              </div>

              <div v-if="submitError" class="state-error" role="alert">{{ submitError }}</div>

              <div class="form-grid">
                <div class="form-field form-field-wide">
                  <label :for="`${uid}-supplier`">Supplier</label>
                  <input
                    :id="`${uid}-supplier`"
                    v-model.trim="form.supplier_name"
                    type="text"
                    autocomplete="off"
                    :class="{ invalid: errors.supplier_name }"
                    :aria-invalid="!!errors.supplier_name"
                    :aria-describedby="errors.supplier_name ? `${uid}-supplier-err` : null"
                  />
                  <span v-if="errors.supplier_name" :id="`${uid}-supplier-err`" class="field-error">{{ errors.supplier_name }}</span>
                </div>

                <div class="form-field">
                  <label :for="`${uid}-quantity`">Quantity (units)</label>
                  <input
                    :id="`${uid}-quantity`"
                    v-model="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    inputmode="numeric"
                    :class="{ invalid: errors.quantity }"
                    :aria-invalid="!!errors.quantity"
                    :aria-describedby="errors.quantity ? `${uid}-quantity-err` : null"
                  />
                  <span v-if="errors.quantity" :id="`${uid}-quantity-err`" class="field-error">{{ errors.quantity }}</span>
                </div>

                <div class="form-field">
                  <label :for="`${uid}-cost`">Unit cost (USD)</label>
                  <input
                    :id="`${uid}-cost`"
                    v-model="form.unit_cost"
                    type="number"
                    min="0"
                    step="0.01"
                    inputmode="decimal"
                    :class="{ invalid: errors.unit_cost }"
                    :aria-invalid="!!errors.unit_cost"
                    :aria-describedby="errors.unit_cost ? `${uid}-cost-err` : null"
                  />
                  <span v-if="errors.unit_cost" :id="`${uid}-cost-err`" class="field-error">{{ errors.unit_cost }}</span>
                </div>

                <div class="form-field form-field-wide">
                  <label :for="`${uid}-date`">Expected delivery date</label>
                  <input
                    :id="`${uid}-date`"
                    v-model="form.expected_delivery_date"
                    type="date"
                    :min="today"
                    :class="{ invalid: errors.expected_delivery_date }"
                    :aria-invalid="!!errors.expected_delivery_date"
                    :aria-describedby="errors.expected_delivery_date ? `${uid}-date-err` : null"
                  />
                  <span v-if="errors.expected_delivery_date" :id="`${uid}-date-err`" class="field-error">{{ errors.expected_delivery_date }}</span>
                </div>

                <div class="form-field form-field-wide">
                  <label :for="`${uid}-notes`">Notes (optional)</label>
                  <textarea :id="`${uid}-notes`" v-model="form.notes" rows="3"></textarea>
                </div>
              </div>

              <div class="total-row">
                <span class="total-label">Estimated total</span>
                <span class="total-value">{{ estimatedTotal === null ? '-' : money(estimatedTotal, 2) }}</span>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn-secondary" type="button" :disabled="submitting" @click="close">Cancel</button>
              <button class="btn-primary" type="submit" :disabled="submitting">
                {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  // 'create' shows the form, 'view' shows the existing PO read-only
  mode: { type: String, default: 'create', validator: (v) => ['create', 'view'].includes(v) }
})

const emit = defineEmits(['close', 'po-created'])

const { translateProductName, currentCurrency } = useI18n()

// Unique per instance so label/id pairs never collide if the modal is mounted twice.
let uidCounter = 0
const uid = `po-modal-${++uidCounter}`
const titleId = `${uid}-title`

const isView = computed(() => props.mode === 'view')

const money = (value, decimals = 0) => formatCurrencyWithDecimals(value, currentCurrency.value, decimals)

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 0)
})

// Local-date YYYY-MM-DD (toISOString would shift the day for timezones ahead of/behind UTC).
const toLocalDateString = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
const today = computed(() => toLocalDateString(new Date()))

const emptyForm = () => ({
  supplier_name: '',
  quantity: shortage.value || 1,
  unit_cost: '',
  expected_delivery_date: '',
  notes: ''
})

const form = reactive(emptyForm())
const errors = reactive({})
const submitting = ref(false)
const submitError = ref(null)

const purchaseOrder = ref(null)
const loading = ref(false)
const loadError = ref(null)

const estimatedTotal = computed(() => {
  const qty = Number(form.quantity)
  const cost = Number(form.unit_cost)
  if (form.unit_cost === '' || !Number.isFinite(qty) || !Number.isFinite(cost)) return null
  return qty * cost
})

const validate = () => {
  Object.keys(errors).forEach((k) => delete errors[k])

  if (!form.supplier_name) errors.supplier_name = 'Supplier is required.'

  const qty = Number(form.quantity)
  if (form.quantity === '' || !Number.isInteger(qty) || qty < 1) {
    errors.quantity = 'Enter a whole number of at least 1.'
  }

  const cost = Number(form.unit_cost)
  if (form.unit_cost === '' || !Number.isFinite(cost) || cost <= 0) {
    errors.unit_cost = 'Enter a unit cost greater than 0.'
  }

  if (!form.expected_delivery_date) {
    errors.expected_delivery_date = 'Expected delivery date is required.'
  } else if (form.expected_delivery_date < today.value) {
    // Both values are YYYY-MM-DD, so string comparison is a valid date comparison.
    errors.expected_delivery_date = 'Delivery date cannot be in the past.'
  }

  return Object.keys(errors).length === 0
}

const submit = async () => {
  if (submitting.value || !validate()) return

  submitting.value = true
  submitError.value = null
  try {
    const created = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name,
      quantity: Number(form.quantity),
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes.trim() || null
    })
    emit('po-created', created)
  } catch (err) {
    console.error('Failed to create purchase order:', err)
    submitError.value = err?.response?.data?.detail && typeof err.response.data.detail === 'string'
      ? err.response.data.detail
      : 'Failed to create the purchase order. Please try again.'
  } finally {
    submitting.value = false
  }
}

const loadPurchaseOrder = async () => {
  loading.value = true
  loadError.value = null
  purchaseOrder.value = null
  // Guard against a stale response if the modal was reopened for another item meanwhile.
  const requestedId = props.backlogItem.id
  try {
    const result = await api.getPurchaseOrderByBacklogItem(requestedId)
    if (props.backlogItem?.id === requestedId) purchaseOrder.value = result
  } catch (err) {
    console.error('Failed to load purchase order:', err)
    if (props.backlogItem?.id === requestedId) loadError.value = 'Failed to load the purchase order.'
  } finally {
    if (props.backlogItem?.id === requestedId) loading.value = false
  }
}

// Reset state every time the modal opens (or switches item/mode).
watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  ([open]) => {
    if (!open || !props.backlogItem) return
    Object.assign(form, emptyForm())
    Object.keys(errors).forEach((k) => delete errors[k])
    submitError.value = null
    submitting.value = false
    if (isView.value) loadPurchaseOrder()
  },
  { immediate: true }
)

const close = () => {
  if (submitting.value) return
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-container form {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.close-button:hover {
  background: var(--color-bg);
  color: var(--color-text);
}

.close-button:focus-visible,
.btn-secondary:focus-visible,
.btn-primary:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
}

.item-summary {
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}

.item-name {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.item-sku {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.state-message {
  text-align: center;
  padding: var(--space-6) 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.state-error {
  background: var(--color-danger-soft);
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
}

/* View mode */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-5);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-item-wide {
  grid-column: 1 / -1;
}

.info-label,
.form-field label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--text-base);
  color: var(--color-text);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--color-primary);
}

.info-value.notes {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  background: #dbeafe;
  color: var(--color-primary-strong);
}

/* Create mode */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.form-field-wide {
  grid-column: 1 / -1;
}

.form-field input,
.form-field textarea {
  min-height: var(--control-height);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-field textarea {
  resize: vertical;
}

.form-field input:focus-visible,
.form-field textarea:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.form-field input.invalid {
  border-color: var(--color-danger);
}

.field-error {
  font-size: var(--text-xs);
  color: var(--color-danger);
}

.total-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.total-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.total-value {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.modal-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary,
.btn-primary {
  height: var(--control-height);
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  color: var(--color-text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg);
}

.btn-primary {
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-surface);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-strong);
  border-color: var(--color-primary-strong);
}

.btn-secondary:disabled,
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 479px) {
  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}

@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal-container,
  .modal-leave-active .modal-container {
    transition: none;
  }
}
</style>
