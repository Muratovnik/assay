<script setup>
import { ref } from 'vue'
import { SwitchRoot, SwitchThumb } from 'reka-ui'
const enabled = ref(false)
const dialog = ref(null)
</script>
<template>
  <label>Queue name <input name="queue-name" /></label>
  <SwitchRoot v-model:checked="enabled" aria-label="Notifications" class="switch">
    <SwitchThumb class="thumb" />
  </SwitchRoot>
  <button @click="dialog.showModal()">About</button>
  <dialog ref="dialog" aria-label="About queue">
    <p>Queue settings</p><form method="dialog"><button>Close</button></form>
  </dialog>
  <aside class="static-help">Changes apply to this queue.</aside>
</template>
