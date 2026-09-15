import { ref } from 'vue'
export function usePaneSelection(count) {
  const active = ref(0)
  function keydown(event, buttons) {
    const moves = { ArrowRight: 1, ArrowLeft: -1 }
    if (event.key in moves) active.value = (active.value + moves[event.key] + count) % count
    else if (event.key === 'Home') active.value = 0
    else if (event.key === 'End') active.value = count - 1
    else return
    event.preventDefault()
    buttons[active.value].focus()
  }
  return { active, keydown }
}
