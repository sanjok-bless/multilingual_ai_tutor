<template>
  <div id="app" class="min-h-screen bg-brand-bg">
    <ChatView />
  </div>
</template>

<script>
import ChatView from './views/ChatView.vue'

export default {
  name: 'App',
  components: {
    ChatView,
  },
}
</script>
