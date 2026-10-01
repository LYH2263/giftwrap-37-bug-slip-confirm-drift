<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])
const err = ref('')

onMounted(async () => {
  try {
    items.value = (await getJSON('/api/runs')).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="hint">列表读库内面积，与确认回包、票面纸积三者一致。</p>
    <p class="lede">凭一次性估纸条确认后落库。每行钉住票面：签发当时的三边、折边与用纸面积，不随后续改动重算。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸签发并确认一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id" class="run-row">
        <div class="run-main">
          <router-link :to="`/boxes/${r.box_id}`">{{ r.box_name }}</router-link>
          <span class="meta">{{ r.result?.paper_m2 ?? '—' }} m²</span>
        </div>
        <div class="run-face meta">
          <span>票面 {{ r.result?.length }} × {{ r.result?.width }} × {{ r.result?.height }} m</span>
          <span>折边 ×{{ r.result?.overlap }}</span>
          <span class="ticket-tag">{{ r.ticket_code }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.run-row {
  flex-direction: column;
  align-items: stretch;
  gap: 0.25rem;
}
.run-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.run-face {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.1rem;
  font-size: 0.82rem;
}
.ticket-tag {
  letter-spacing: 0.05em;
  color: var(--ribbon);
  font-weight: 600;
}
</style>
