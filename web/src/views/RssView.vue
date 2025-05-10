<template>
  <div class="rss-view">
    <div class="rss-search">
      <el-input 
        v-model="searchQuery" 
        placeholder="搜索RSS内容" 
        class="search-input"
        :prefix-icon="Search"
        clearable
        @keyup.enter="searchRss">
      </el-input>
      <el-button type="primary" @click="searchRss">搜索</el-button>
      <el-button @click="loadAllRss">查看全部</el-button>
    </div>

    <div class="rss-filter">
      <el-radio-group v-model="filterType" @change="applyFilter">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="liked">喜欢</el-radio-button>
        <el-radio-button label="disliked">不喜欢</el-radio-button>
        <el-radio-button label="unmarked">未标记</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="feeds.length === 0" class="empty-state">
      <el-empty description="暂无RSS数据" />
    </div>

    <div v-else class="rss-feed-list">
      <RssItem 
        v-for="feed in displayedFeeds" 
        :key="feed.id" 
        :item="feed" 
      />
    </div>

    <el-pagination
      v-if="feeds.length > pageSize"
      layout="prev, pager, next"
      :total="feeds.length"
      :page-size="pageSize"
      :current-page="currentPage"
      @current-change="handlePageChange"
      class="pagination"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import RssItem from '@/components/RssItem.vue';
import { Search } from '@element-plus/icons-vue';

export default {
  name: 'RssView',
  components: {
    RssItem
  },
  setup() {
    // 数据状态
    const feeds = ref([]);
    const loading = ref(true);
    const searchQuery = ref('');
    const filterType = ref('all');

    // 分页
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 获取所有RSS
    const loadAllRss = async () => {
      try {
        loading.value = true;
        const response = await axios.get('/api/rss/all');
        if (response.data && response.data.ids && response.data.ids[0]) {
          feeds.value = response.data.ids[0].map((id, index) => ({
            id,
            document: response.data.documents[0][index],
            metadata: response.data.metadatas[0][index]
          }));
        } else {
          feeds.value = [];
        }
      } catch (error) {
        console.error('获取RSS数据失败:', error);
        feeds.value = [];
      } finally {
        loading.value = false;
      }
    };

    // 搜索RSS
    const searchRss = async () => {
      if (!searchQuery.value.trim()) {
        loadAllRss();
        return;
      }

      try {
        loading.value = true;
        const response = await axios.post('/api/rss/story', {
          query: searchQuery.value,
          n_results: 30
        });
        
        if (response.data && response.data.ids && response.data.ids[0]) {
          feeds.value = response.data.ids[0].map((id, index) => ({
            id,
            document: response.data.documents[0][index],
            metadata: response.data.metadatas[0][index]
          }));
        } else {
          feeds.value = [];
        }
      } catch (error) {
        console.error('搜索RSS失败:', error);
        feeds.value = [];
      } finally {
        loading.value = false;
      }
    };

    // 过滤RSS
    const applyFilter = () => {
      currentPage.value = 1; // 重置页码
    };

    // 过滤后的RSS数据
    const filteredFeeds = computed(() => {
      if (filterType.value === 'all') {
        return feeds.value;
      }
      
      return feeds.value.filter(feed => {
        const pref = feed.metadata.user_preference;
        
        if (filterType.value === 'liked') {
          return pref && pref.is_liked === true;
        }
        
        if (filterType.value === 'disliked') {
          return pref && pref.is_liked === false;
        }
        
        if (filterType.value === 'unmarked') {
          return !pref;
        }
        
        return true;
      });
    });

    // 当前页显示的RSS数据
    const displayedFeeds = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      return filteredFeeds.value.slice(start, end);
    });

    // 页码变化
    const handlePageChange = (page) => {
      currentPage.value = page;
    };

    onMounted(() => {
      loadAllRss();
    });

    return {
      feeds,
      loading,
      searchQuery,
      filterType,
      currentPage,
      pageSize,
      filteredFeeds,
      displayedFeeds,
      loadAllRss,
      searchRss,
      applyFilter,
      handlePageChange,
      Search
    };
  }
};
</script>

<style scoped>
.rss-view {
  padding: 1rem 0;
}

.rss-search {
  display: flex;
  margin-bottom: 1rem;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
}

.rss-filter {
  margin-bottom: 1.5rem;
}

.loading-state,
.empty-state {
  margin: 2rem 0;
  text-align: center;
}

.pagination {
  margin-top: 1.5rem;
  text-align: center;
}
</style> 