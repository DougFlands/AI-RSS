<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<script>
import { computed } from "vue";
import { useRoute } from "vue-router";

export default {
  setup() {
    const route = useRoute();
    const activeRoute = computed(() => route.path);

    return {
      activeRoute,
    };
  },
};
</script>

<style>
body {
  margin: 0;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  background-color: #f5f7fa;
}

/* 禁止双击放大 */
* {
  touch-action: manipulation;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>
