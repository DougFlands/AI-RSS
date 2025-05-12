<template>
  <div class="flex h-[calc(100vh-140px)]">
    <div class="w-64 shrink-0 hidden md:block">
      <Sidebar />
    </div>

    <div class="flex-1 p-4 md:p-6 overflow-y-auto" ref="scrollContainer" @scroll="handleScroll">
      <div v-if="isLoading" class="space-y-4">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="feeds.length === 0" class="flex h-64 items-center justify-center">
        <el-empty description="暂无RSS数据" />
      </div>

      <div v-else class="space-y-4">
        <RssItem v-for="feed in feeds" :key="feed.id" :item="feed" />
      </div>
      
      <!-- 加载更多指示器 -->
      <div ref="loadMoreTrigger" class="py-4 text-center" v-if="hasMoreItems">
        <div v-if="isLoading" class="flex justify-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
        </div>
        <p v-else class="text-gray-500">下拉加载更多</p>
      </div>
      
      <!-- 没有更多数据提示 -->
      <div v-if="!hasMoreItems && feeds.length > 0" class="py-4 text-center text-gray-500">
        没有更多内容了
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, defineExpose, ref, onMounted, onUnmounted } from "vue";
import RssItem from "@/components/RssItem.vue";

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

onMounted(() => {
  // 创建 Intersection Observer
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (entry.isIntersecting && !props.isLoading) {
        emit('load-more');
      }
    },
    {
      rootMargin: "0px 0px 200px 0px", // 提前200px触发
      threshold: 0.1,
    }
  );

  // 开始观察加载更多触发器元素
  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value);
  }
});

onUnmounted(() => {
  // 清理 observer
  if (observer) {
    observer.disconnect();
  }
});

// 处理滚动事件（可以用于添加其他滚动相关功能）
const handleScroll = () => {
  // 可以添加额外的滚动处理逻辑
};

defineExpose({
  loadMoreTrigger,
  scrollContainer
});
</script>

<style scoped>
/* 可以添加自定义样式 */
</style>
