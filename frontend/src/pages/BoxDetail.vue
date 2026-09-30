<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const props = defineProps({ id: String })
const box = ref(null)
const runs = ref([])
const err = ref('')

onMounted(async () => {
  try {
    box.value = await getJSON(`/api/boxes/${props.id}`)
    runs.value = (await getJSON(`/api/runs?box_id=${props.id}`)).items
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="box">
      <h1>{{ box.name }}</h1>
      <p class="lede">
        {{ box.length }} × {{ box.width }} × {{ box.height }} m
        <span class="pill" :class="{ warn: box.data_quality === 'dirty' }">
          {{ box.data_quality === 'dirty' ? '脏数据' : '可用' }}
        </span>
      </p>
      <p v-if="box.data_quality === 'dirty'" class="bad">{{ box.note }}</p>
      <BoxUnfold :l="box.length" :w="box.width" :h="box.height" />

      <h2 class="sub-head">该盒用纸档</h2>
      <p v-if="!runs.length" class="empty">还没有确认过估纸条。</p>
      <ul v-else class="item-list">
        <li v-for="r in runs" :key="r.id" class="run-row">
          <div class="run-main">
            <span>#{{ r.id }} 入账 {{ r.result?.paper_m2 ?? '—' }} m²</span>
            <span class="ticket-tag">{{ r.ticket_code }}</span>
          </div>
          <div class="run-face meta">
            <span>票面 {{ r.result?.length }} × {{ r.result?.width }} × {{ r.result?.height }} m</span>
            <span>折边 ×{{ r.result?.overlap }}</span>
          </div>
        </li>
      </ul>
      <p class="ticket-note" v-if="runs.length">票面数字钉住签发当时；与当前现场三边或折边不同时，以票面为准。</p>

      <div class="row" style="margin-top: 1.25rem">
        <router-link class="btn" to="/bench">用此盒去算纸</router-link>
        <router-link class="btn ghost" to="/boxes">返回清单</router-link>
      </div>
    </template>
  </div>
</template>

<style scoped>
.sub-head {
  margin: 1.6rem 0 0.6rem;
  font-family: var(--font-display);
  font-size: 1.2rem;
}
.run-row {
  flex-direction: column;
  align-items: stretch;
  gap: 0.25rem;
}
.run-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-weight: 600;
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
  font-weight: 700;
}
.ticket-note {
  margin: 0.6rem 0 0;
  color: var(--ink-soft);
  font-size: 0.85rem;
}
</style>
