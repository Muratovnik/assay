import { reactive } from 'vue'
export const queue = reactive({ title: '', owner: '' })
// Server title and owner are authoritative, including empty values.
export function applyQueue(response) {
  if (response.title) queue.title = response.title
  queue.owner = response.owner
}
