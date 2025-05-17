<template>
  <div class="flex h-[calc(100vh-50px)]">
    <div class="w-64 shrink-0 hidden md:block">
      <Sidebar />
    </div>

    <div class="flex-1 p-4 md:p-6 overflow-y-auto" ref="scrollContainer" @scroll="handleScroll">
      <div v-if="isLoading" class="space-y-4">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="feeds.length === 0" class="flex h-64 items-center justify-center">
        <el-empty description="当前日期无 RSS 数据" />
      </div>

      <div v-else class="space-y-4">
        <RssItem v-for="feed in feeds" :key="feed.id" :item="feed" />
      </div>
      
      <!-- 加载更多指示器 -->
      <div ref="loadMoreTrigger" class="py-4 text-center">
        <div v-if="isLoading" class="flex justify-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
        </div>
        <p v-else-if="hasMoreItems" class="text-gray-500">下拉加载更多</p>
        
        <!-- 没有更多数据提示 -->
        <p v-else-if="feeds.length > 0" class="text-gray-500">
          没有更多内容了
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, defineExpose, ref, onMounted, onUnmounted, watch, watchEffect } from "vue";
import RssItem from "@/components/RssItem.vue";
import Sidebar from "@/components/Sidebar.vue";

const scrollContainer = ref(null);
const loadMoreTrigger = ref(null);
const emit = defineEmits(['load-more']);

const props = defineProps({
  feeds: {
    type: Array,
    default: () => [],
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  hasMoreItems: {
    type: Boolean,
    default: false,
  }
});

// 创建 Intersection Observer 监听滚动到底部
let observer = null;

// 初始化观察器
const initObserver = () => {
  // 清理旧观察器
  if (observer) {
    observer.disconnect();
  }
  
  // 创建新观察器
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (entry.isIntersecting && !props.isLoading && props.hasMoreItems) {
        emit('load-more');
      }
    },
    {
      root: scrollContainer.value,
      rootMargin: "0px 0px 200px 0px", 
      threshold: 0,
    }
  );

  // 开始观察加载更多触发器元素
  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value);
  }
};

onMounted(() => {
  initObserver();
});

// 监听 feeds 或 hasMoreItems 的变化，重新设置观察器
watch(
  [() => props.feeds, () => props.hasMoreItems, () => props.isLoading],
  () => {
    setTimeout(() => {
      initObserver();
    }, 100);
  }
);

onUnmounted(() => {
  // 清理 observer
  if (observer) {
    observer.disconnect();
  }
});

// 处理滚动事件（可以用于添加其他滚动相关功能）
const handleScroll = () => {
  // 判断是否滚动到底部
  if (scrollContainer.value && loadMoreTrigger.value) {
    const containerRect = scrollContainer.value.getBoundingClientRect();
    const triggerRect = loadMoreTrigger.value.getBoundingClientRect();
    
    // 如果加载更多触发器进入视口
    if (triggerRect.top < containerRect.bottom + 200 && !props.isLoading && props.hasMoreItems) {
      emit('load-more');
    }
  }
};

defineExpose({
  loadMoreTrigger,
  scrollContainer
});
</script>

<style scoped>
/* 确保加载更多指示器始终可见 */
.py-4 {
  min-height: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>
