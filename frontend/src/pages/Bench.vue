<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const boxes = ref([])
const bid = ref(1)
const out = ref(null)
const ticket = ref(null)
const confirmed = ref(null)
const err = ref('')
const busy = ref(false)

onMounted(async () => {
  try {
    boxes.value = (await getJSON('/api/boxes')).items.filter((b) => b.data_quality === 'clean')
    if (boxes.value.length) bid.value = boxes.value[0].id
  } catch (e) {
    err.value = String(e.message || e)
  }
})

function resetFlow() {
  out.value = null
  ticket.value = null
  confirmed.value = null
  err.value = ''
}

function switchBox() {
  resetFlow()
}

async function preview() {
  resetFlow()
  busy.value = true
  try {
    out.value = await getJSON(`/api/estimate?box_id=${bid.value}`)
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}

async function issue() {
  err.value = ''
  confirmed.value = null
  busy.value = true
  try {
    ticket.value = await postJSON('/api/tickets/issue', { box_id: bid.value })
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}

async function confirmTicket() {
  err.value = ''
  busy.value = true
  try {
    confirmed.value = await postJSON('/api/tickets/confirm', { code: ticket.value.code })
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>算纸</h1>
    <p class="lede">先试算看面积，再签发一次性估纸条，票面数字经服务端登记；确认时只认票面，不按现场重算。</p>
    <div class="row">
      <select v-model.number="bid" @change="switchBox">
        <option v-for="b in boxes" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <button :disabled="busy" @click="preview">① 试算面积</button>
      <button class="ghost" :disabled="busy || !out" @click="issue">② 签发估纸条</button>
    </div>
    <p v-if="err" class="bad">{{ err }}</p>

    <div v-if="out" class="result-board">
      <div class="figure">{{ out.paper_m2 }}<span>m²</span></div>
      <p class="stat-line" v-if="out.ribbon">
        十字丝带约 {{ out.ribbon.ribbon_m ?? out.ribbon }} m
      </p>
      <BoxUnfold
        :l="out.box.length"
        :w="out.box.width"
        :h="out.box.height"
        :paper-m2="out.paper_m2"
      />
    </div>

    <div v-if="ticket && !confirmed" class="ticket-card">
      <div class="ticket-head">
        <span class="ticket-label">一次性估纸条（待确认）</span>
        <span class="ticket-code">{{ ticket.code }}</span>
      </div>
      <dl class="ticket-face">
        <div><dt>礼盒</dt><dd>{{ ticket.box_name }} #{{ ticket.box_id }}</dd></div>
        <div><dt>票面三边 (m)</dt><dd>{{ ticket.length }} × {{ ticket.width }} × {{ ticket.height }}</dd></div>
        <div><dt>票面折边</dt><dd>× {{ ticket.overlap }}</dd></div>
        <div><dt>展开面积</dt><dd>{{ ticket.box_surface }} m²</dd></div>
        <div class="ticket-total"><dt>票面用纸</dt><dd>{{ ticket.paper_m2 }} m²</dd></div>
      </dl>
      <p class="ticket-note">纸条已在服务端登记、未核销。确认后写入一行用纸档并立即核销；若盒边或折边系数在此期间变动，确认将失败。</p>
      <div class="row">
        <button class="ribbon" :disabled="busy" @click="confirmTicket">③ 确认写入用纸档</button>
        <button class="ghost" :disabled="busy" @click="resetFlow">放弃本票</button>
      </div>
    </div>

    <div v-if="confirmed" class="ticket-card done">
      <div class="ticket-head">
        <span class="ticket-label">已核销 · 用纸档 #{{ confirmed.run_id }}</span>
        <span class="ticket-code">{{ confirmed.code }}</span>
      </div>
      <dl class="ticket-face">
        <div><dt>礼盒</dt><dd>{{ confirmed.box_name }} #{{ confirmed.box_id }}</dd></div>
        <div><dt>票面三边 (m)</dt><dd>{{ confirmed.length }} × {{ confirmed.width }} × {{ confirmed.height }}</dd></div>
        <div><dt>票面折边</dt><dd>× {{ confirmed.overlap }}</dd></div>
        <div class="ticket-total"><dt>入账用纸</dt><dd>{{ confirmed.paper_m2 }} m²</dd></div>
      </dl>
      <p class="ticket-note">入账数字与票面完全一致，钉住签发当时的三边与折边。</p>
      <div class="row">
        <button :disabled="busy" @click="resetFlow">再算一单</button>
        <router-link class="btn ghost" to="/history">查看用纸档</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ticket-card {
  margin-top: 1.4rem;
  padding: 1.1rem 1.2rem 0.6rem;
  border: 1px solid rgba(184, 151, 59, 0.55);
  border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(243, 247, 244, 0.95));
}
.ticket-card.done {
  border-color: rgba(26, 122, 92, 0.5);
}
.ticket-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin-bottom: 0.75rem;
}
.ticket-label {
  font-size: 0.8rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-soft);
}
.ticket-code {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--ribbon);
}
.ticket-card.done .ticket-code {
  color: var(--ok);
}
.ticket-face {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem 1.5rem;
  margin: 0 0 0.6rem;
}
.ticket-face div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--line);
}
.ticket-face dt {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.88rem;
}
.ticket-face dd {
  margin: 0;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.ticket-total dd {
  color: var(--wash-b);
  font-size: 1.05rem;
}
.ticket-note {
  margin: 0.5rem 0 0.9rem;
  color: var(--ink-soft);
  font-size: 0.85rem;
  line-height: 1.5;
}
</style>
