import { reactive } from 'vue'
export const queue = reactive({ title: '', owner: '' })
export function applyQueue(response) {
  queue.title = response.title
  queue.owner = response.owner
}
