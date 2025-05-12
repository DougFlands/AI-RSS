<template>
  <div class="flex h-screen bg-gray-50 overflow-hidden">
    <div
      class="flex-1 overflow-auto md:ml-0 transition-all duration-300"
      ref="scrollContainer"
    >
      <!-- 使用封装的头部组件 -->
      <RssHeader
        :available-dates="availableDates"
        :initial-filter-type="filterType"
        :initial-selected-date="selectedDate"
        @filter-change="handleFilterChange"
        @date-change="handleDateSelected"
        @toggle-sidebar="toggleSidebar"
      />

      <!-- 使用封装的内容组件 -->
      <RssContent :feeds="displayedFeeds" :is-loading="rssQuery.isLoading.value" />

      <!-- 加载更多指示器 -->
      <div ref="loadMoreTrigger" class="py-4 text-center" v-if="hasMoreItems">
        <div v-if="rssQuery.isLoading.value" class="flex justify-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
        </div>
        <p v-else class="text-gray-500">下拉加载更多</p>
      </div>

      <!-- 没有更多数据提示 -->
      <div
        v-if="!hasMoreItems && feeds.length > 0"
        class="py-4 text-center text-gray-500"
      >
        没有更多内容了
      </div>
    </div>

    <!-- 使用 Drawer 组件替换原来的右侧边栏 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="70%"
      :with-header="false"
      :show-close="false"
      :close-on-press-escape="true"
      :close-on-click-modal="true"
    >
      <div class="flex flex-col h-full w-full">
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-800">订阅源设置</h3>

          <div class="flex-1 overflow-hidden">
            <Sidebar @date-selected="handleDateSelected" />
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import Sidebar from "@/components/Sidebar.vue";
import { server } from "@/server";

// 导入封装的组件
import RssHeader from "@/components/RssHeader.vue";
import RssContent from "@/components/RssContent.vue";

// 数据状态
const filterType = ref("all");
const selectedDate = ref("all");
const keywordFilter = ref("");

// 使用 Drawer 组件的状态
const drawerVisible = ref(false);

// 无限滚动相关
const scrollContainer = ref(null);
const loadMoreTrigger = ref(null);

const currentPage = ref(1);
const pageSize = ref(20);

// 判断是否还有更多项目可加载
const hasMoreItems = computed(() => {
  return filteredFeeds.value.length > displayedFeeds.value.length;
});

// 使用 TanStack Query 获取日期列表
const datesQuery = server.rss.useRssDatesQuery();

// 按日期排序（降序）
const sortedDates = computed(() => {
  const dates = datesQuery.data?.value || [];
  return [...dates].sort((a, b) => {
    // 统一格式为 YYYYMMDD 进行比较
    const dateA = a.date.includes("-") ? a.date.replace(/-/g, "") : a.date;
    const dateB = b.date.includes("-") ? b.date.replace(/-/g, "") : b.date;
    return dateB.localeCompare(dateA);
  });
});

// 切换左侧边栏
const toggleSidebar = () => {
  drawerVisible.value = !drawerVisible.value;
};

// 使用 TanStack Query 获取 RSS 数据
const rssQuery = server.rss.useRssQuery(
  selectedDate.value === "all" ? undefined : selectedDate.value
);

// 处理日期选择
const handleDateSelected = (date) => {
  selectedDate.value = date;
  resetPagination();
};

// 可用日期集合
const availableDates = computed(() => {
  return new Set(sortedDates.value.map((d) => d.date));
});

// 处理筛选变化
const handleFilterChange = (type) => {
  filterType.value = type;
  resetPagination();
};

// 重置分页状态
const resetPagination = () => {
  currentPage.value = 1;
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0;
    }
  });
};

// 获取原始 feeds 数据
const feeds = computed(() => {
  if (!rssQuery.data.value || !rssQuery.data.value.ids || !rssQuery.data.value.ids[0]) {
    return [];
  }

  return rssQuery.data.value.ids[0].map((id, index) => ({
    id,
    document: rssQuery.data.value.documents[0][index],
    metadata: rssQuery.data.value.metadatas[0][index],
  }));
});

// 过滤后的数据（未分页）
const filteredFeeds = computed(() => {
  let result = feeds.value;

  // 应用过滤
  if (filterType.value !== "all") {
    result = feeds.value.filter((feed) => {
      const pref = feed.metadata.user_preference;
      if (filterType.value === "liked") return pref && pref.is_liked;
      if (filterType.value === "disliked") return pref && !pref.is_liked;
      if (filterType.value === "unmarked") return !pref;
      return true;
    });
  }

  // 应用关键词过滤
  if (keywordFilter.value.trim()) {
    const keyword = keywordFilter.value.trim().toLowerCase();
    result = result.filter((feed) => {
      return (
        (feed.metadata.title && feed.metadata.title.toLowerCase().includes(keyword)) ||
        (feed.document && feed.document.toLowerCase().includes(keyword))
      );
    });
  }
  return result;
});

// 计算当前页显示的数据
const displayedFeeds = computed(() => {
  // 无限滚动分页：显示从开始到当前页的所有内容
  const end = currentPage.value * pageSize.value;
  console.log(filteredFeeds.value.slice(0, end));
  return filteredFeeds.value.slice(0, end);
});

// 使用 Intersection Observer 监听滚动到底部
let observer = null;

// 加载更多内容
const loadMore = () => {
  if (!hasMoreItems.value) return;
  
  // 增加页码以显示更多内容
  currentPage.value++;
};

onMounted(() => {
  // 创建 Intersection Observer
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (entry.isIntersecting) {
        loadMore();
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
</script>

<style scoped>
.flat-radio-group .el-radio-button__inner {
  border: none !important;
  background: transparent;
  color: white;
  border-radius: 4px;
  padding: 8px 16px;
  box-shadow: none !important;
}

.flat-radio-group .el-radio-button__inner:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

/* 覆盖 Element UI 默认样式 */
.el-radio-button {
  margin-right: 0 !important;
}

.el-radio-group
  .el-radio-button:not(:first-child):not(:last-child)
  .el-radio-button__inner {
  border: none !important;
}

.el-radio-group .el-radio-button:first-child .el-radio-button__inner {
  border: none !important;
}

.el-radio-group .el-radio-button:last-child .el-radio-button__inner {
  border: none !important;
}
</style>
