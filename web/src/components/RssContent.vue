<template>
  <div class="p-4 md:p-6">
    <div v-if="isLoading" class="space-y-4">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="feeds.length === 0" class="flex h-64 items-center justify-center">
      <el-empty description="暂无RSS数据" />
    </div>

    <div v-else class="space-y-4">
      <RssItem v-for="feed in feeds" :key="feed.id" :item="feed" />
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import RssItem from "@/components/RssItem.vue";

const props = defineProps({
  feeds: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
/* 可以添加自定义样式 */
</style> 