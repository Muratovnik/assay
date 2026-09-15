<script setup>
import { usePaneSelection } from './usePaneSelection.js'
import { queue } from './queue.js'
const { active, keydown } = usePaneSelection(2)
const buttons = []
</script>
<template>
  <div role="tablist" @keydown="keydown($event, buttons)">
    <button v-for="(name, i) in ['Active', 'Done']" :id="`tab-${i}`"
      :key="name" :ref="el => buttons[i] = el" role="tab"
      :aria-controls="`panel-${i}`" :aria-selected="active === i"
      :tabindex="active === i ? 0 : -1" @click="active = i">{{ name }}</button>
  </div>
  <section v-for="(_, i) in ['Active', 'Done']" :id="`panel-${i}`"
    :key="i" role="tabpanel" :aria-labelledby="`tab-${i}`" :hidden="active !== i">
    {{ queue.title }}
  </section>
</template>
