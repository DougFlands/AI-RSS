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
        :initial-source-id="selectedSourceId"
        :sources="sourcesData"
        :is-sources-loading="sourcesQuery.isLoading.value"
        @filter-change="handleFilterChange"
        @date-change="handleDateSelected"
        @source-change="handleSourceChange"
        @toggle-sidebar="toggleSidebar"
      />

      <!-- 使用封装的内容组件 -->
      <RssContent
        ref="rssContent"
        :feeds="displayedFeeds"
        :is-loading="rssQuery.isLoading.value"
        :has-more-items="hasMoreItems"
        @load-more="loadMore"
      />
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
          <div class="flex-1 overflow-hidden">
            <Sidebar />
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

// 使用 TanStack Query 获取日期列表
const datesQuery = server.rss.useRssDatesQuery();

// 获取订阅源列表
const sourcesQuery = server.rss.useRssSourcesQuery();
const sourcesData = computed(() => sourcesQuery.data?.value || []);

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

// 获取最新日期
const latestDate = computed(() => {
  return sortedDates.value.length > 0 ? sortedDates.value[0].date : "all";
});

// 数据状态
const filterType = ref("recommended");
const selectedDate = ref("all"); // 初始化为 all，稍后会更新为最新日期
const keywordFilter = ref("");
const selectedSourceId = ref(""); // 添加源筛选状态

// 使用 Drawer 组件的状态
const drawerVisible = ref(false);

// 分页相关
const currentPage = ref(1);
const pageSize = ref(20); // 每页显示的条目数

// 判断是否还有更多项目可加载
const hasMoreItems = computed(() => {
  return filteredFeeds.value.length > displayedFeeds.value.length;
});

// 切换左侧边栏
const toggleSidebar = () => {
  drawerVisible.value = !drawerVisible.value;
};

// 使用 TanStack Query 获取 RSS 数据
const rssQuery = server.rss.useRssQuery({
  date: selectedDate.value === "all" ? undefined : selectedDate.value,
  preference: filterType.value === "all" ? undefined : filterType.value,
  source_id: selectedSourceId.value || undefined,
});

// 当日期数据加载完成时，设置默认日期为最新日期
watch(
  () => datesQuery.data.value,
  (newData) => {
    if (newData && newData.length > 0 && selectedDate.value === "all") {
      nextTick(() => {
        selectedDate.value = latestDate.value;
      });
    }
  },
  { immediate: true }
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

// 处理源筛选变化
const handleSourceChange = (sourceId) => {
  selectedSourceId.value = sourceId;
  resetPagination();
};

// 重置分页状态
const resetPagination = () => {
  currentPage.value = 1;
  nextTick(() => {
    if (rssContent.value?.scrollContainer) {
      rssContent.value.scrollContainer.scrollTop = 0;
    }
  });
};

// 获取原始 feeds 数据
const feeds = computed(() => {
  if (!rssQuery.data.value || !rssQuery.data.value.ids) {
    return [];
  }

  // 处理多层嵌套的数据结构
  const result = [];
  const responseData = rssQuery.data.value;

  // 检查是否有嵌套数组
  if (responseData.ids && responseData.ids.length > 0) {
    // 遍历所有来源的数据
    for (let sourceIndex = 0; sourceIndex < responseData.ids.length; sourceIndex++) {
      const sourceIds = responseData.ids[sourceIndex];
      const sourceDocuments = responseData.documents
        ? responseData.documents[sourceIndex]
        : [];
      const sourceMetadatas = responseData.metadatas
        ? responseData.metadatas[sourceIndex]
        : [];

      // 遍历当前来源的所有条目
      for (let itemIndex = 0; itemIndex < sourceIds.length; itemIndex++) {
        result.push({
          id: sourceIds[itemIndex],
          document: sourceDocuments ? sourceDocuments[itemIndex] : null,
          metadata: sourceMetadatas ? sourceMetadatas[itemIndex] : {},
        });
      }
    }
  }

  return result;
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

  // 应用源过滤
  if (selectedSourceId.value) {
    const source = sourcesData.value.find(
      (source) => source._id === selectedSourceId.value
    );
    result = result.filter((feed) => {
      const url = feed.metadata.source || "";
      return url === source.url;
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

// 计算当前页显示的数据（前端分页）
const displayedFeeds = computed(() => {
  // 无限滚动分页：显示从开始到当前页的所有内容
  const end = currentPage.value * pageSize.value;
  return filteredFeeds.value.slice(0, end);
});

// 加载更多内容（前端分页）
const loadMore = () => {
  if (!hasMoreItems.value || rssQuery.isLoading.value) return;

  // 增加页码以显示更多内容
  currentPage.value++;
};

// 组件引用
const rssContent = ref(null);

onMounted(() => {
  // 设置初始日期为最新的可用日期
  nextTick(() => {
    if (sortedDates.value.length > 0) {
      selectedDate.value = latestDate.value;
    }
  });
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
