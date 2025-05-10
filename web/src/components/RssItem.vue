<template>
  <div class="rss-item" :class="{ 'liked': isLiked === true, 'disliked': isLiked === false }">
    <div class="rss-item-header">
      <h3 class="rss-item-title">
        <a :href="item.metadata.link" target="_blank">{{ item.metadata.title }}</a>
      </h3>
      <div class="rss-item-meta">
        <span class="rss-item-source">来源: {{ item.metadata.source }}</span>
        <span class="rss-item-date">{{ formatDate(item.metadata.pub_date) }}</span>
      </div>
    </div>
    <div class="rss-item-content" v-html="formatContent(item.document)"></div>
    <div class="rss-item-actions">
      <el-button 
        type="primary" 
        size="small" 
        :class="{ 'is-active': isLiked === true }"
        @click="toggleLike(true)">
        {{ isLiked === true ? '已喜欢' : '喜欢' }}
      </el-button>
      <el-button 
        type="danger" 
        size="small" 
        :class="{ 'is-active': isLiked === false }"
        @click="showDislikeDialog">
        {{ isLiked === false ? '已不喜欢' : '不喜欢' }}
      </el-button>
    </div>

    <!-- 不喜欢原因对话框 -->
    <el-dialog
      v-model="dislikeDialogVisible"
      title="请说明不喜欢的原因"
      width="30%">
      <el-input
        v-model="dislikeReason"
        type="textarea"
        :rows="4"
        placeholder="请输入不喜欢的原因"
      ></el-input>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dislikeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDislike">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, computed } from 'vue';

export default {
  name: 'RssItem',
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    // 喜好状态
    const isLiked = computed(() => {
      if (props.item.metadata.user_preference) {
        return props.item.metadata.user_preference.is_liked;
      }
      return null;
    });

    // 不喜欢对话框
    const dislikeDialogVisible = ref(false);
    const dislikeReason = ref('');

    // 日期格式化
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN');
    };

    // 内容格式化
    const formatContent = (content) => {
      if (!content) return '';
      // 去除多余换行符，限制内容长度
      return content.replace(/\n{2,}/g, '<br>').substring(0, 300) + '...';
    };

    // 切换喜欢状态
    const toggleLike = async (liked) => {
      try {
        await axios.post('/api/rss/preference', {
          feed_id: props.item.id,
          is_liked: liked
        });
        // 触发刷新
        window.location.reload();
      } catch (error) {
        console.error('保存喜好失败:', error);
      }
    };

    // 显示不喜欢对话框
    const showDislikeDialog = () => {
      dislikeDialogVisible.value = true;
      if (props.item.metadata.user_preference && props.item.metadata.user_preference.reason) {
        dislikeReason.value = props.item.metadata.user_preference.reason;
      } else {
        dislikeReason.value = '';
      }
    };

    // 确认不喜欢
    const confirmDislike = async () => {
      try {
        await axios.post('/api/rss/preference', {
          feed_id: props.item.id,
          is_liked: false,
          reason: dislikeReason.value
        });
        dislikeDialogVisible.value = false;
        // 触发刷新
        window.location.reload();
      } catch (error) {
        console.error('保存不喜欢原因失败:', error);
      }
    };

    return {
      isLiked,
      dislikeDialogVisible,
      dislikeReason,
      formatDate,
      formatContent,
      toggleLike,
      showDislikeDialog,
      confirmDislike
    };
  }
};
</script>

<style scoped>
.rss-item {
  background-color: white;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border-left: 4px solid #e6e6e6;
}

.rss-item.liked {
  border-left-color: #67c23a;
}

.rss-item.disliked {
  border-left-color: #f56c6c;
}

.rss-item-header {
  margin-bottom: 0.5rem;
}

.rss-item-title {
  margin: 0 0 0.5rem 0;
}

.rss-item-title a {
  color: #303133;
  text-decoration: none;
}

.rss-item-title a:hover {
  color: #409eff;
}

.rss-item-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #909399;
}

.rss-item-content {
  margin: 1rem 0;
  color: #606266;
  line-height: 1.5;
}

.rss-item-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.is-active {
  font-weight: bold;
}
</style> 