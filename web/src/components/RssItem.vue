<template>
  <a
    :href="item.metadata.link"
    target="_blank"
    class="no-underline bg-white block rounded-lg shadow-sm p-3 hover:shadow-md transition-shadow"
  >
    <div class="flex flex-col space-y-1.5">
      <!-- 标题和链接 -->
      <div class="flex items-start justify-between">
        <h3 class="text-base font-medium text-gray-800 hover:text-blue-600 line-clamp-2">
          {{ item.metadata.title }}
        </h3>
        <div class="flex items-center space-x-1 ml-2">
          <!-- 喜欢按钮 -->
          <button
            v-if="isLiked === null"
            @click="toggleLike(true)"
            class="p-1 text-gray-400 hover:text-green-500 transition-colors border-0 bg-transparent outline-none focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
              ></path>
            </svg>
          </button>
          <button
            v-else-if="isLiked"
            @click="toggleLike(false)"
            class="p-1 text-green-500 hover:text-gray-400 transition-colors border-0 bg-transparent outline-none focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="currentColor"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
              ></path>
            </svg>
          </button>
          <!-- 不喜欢按钮 -->
          <button
            v-if="isLiked === false"
            @click="cancelDislikeDirectly"
            class="p-1 text-red-500 hover:text-gray-400 transition-colors border-0 bg-transparent outline-none focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"
              ></path>
            </svg>
          </button>
          <button
            v-else
            @click="showDislikeDialog"
            class="p-1 text-gray-400 hover:text-red-500 transition-colors border-0 bg-transparent outline-none focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"
              ></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 日期 -->
      <div class="flex items-center text-xs text-gray-500 space-x-3">
        <span>{{ formatDate(item.metadata.published) }}</span>
      </div>

      <!-- 内容 -->
      <p class="text-gray-600 text-xs line-clamp-2 leading-snug mt-1">
        {{ item.metadata.summary }}
      </p>
    </div>

    <!-- 不喜欢原因对话框 -->
    <el-dialog
      v-model="dislikeDialogVisible"
      title="不喜欢的原因"
      width="90%"
      :fullscreen="false"
      class="dislike-dialog"
    >
      <div class="py-3">
        <el-input
          v-model="dislikeReason"
          type="textarea"
          :rows="3"
          placeholder="请输入不喜欢的原因"
          class="mb-3 rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>
      <div class="border-t border-gray-200 pt-3 flex justify-end space-x-2">
        <el-button
          @click="dislikeDialogVisible = false"
          class="rounded-md bg-white text-gray-700 hover:bg-gray-50 text-sm"
        >
          取消
        </el-button>
        <el-button
          v-if="isLiked === false"
          @click="cancelDislike"
          class="rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 text-sm"
        >
          取消不喜欢
        </el-button>
        <el-button
          type="primary"
          @click="confirmDislike"
          class="rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm"
        >
          确认
        </el-button>
      </div>
    </el-dialog>
  </a>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { server } from "@/server";

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
});

// 检测移动设备
const isMobile = ref(false);

onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
});

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768;
};

// 喜好状态
const isLiked = computed(() => {
  if (props.item.metadata.user_preference) {
    return props.item.metadata.user_preference.is_liked;
  }
  return null;
});

// 使用 TanStack Query 更新偏好设置
const updatePreferenceMutation = server.rss.useUpdateRssPreferenceMutation();

// 不喜欢对话框
const dislikeDialogVisible = ref(false);
const dislikeReason = ref("");

// 日期格式化
const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleString("zh-CN");
};

// 来源格式化
const formatSource = (source) => {
  if (!source) return "";
  // 移除 http:// 或 https:// 前缀，并只显示域名部分
  return source.replace(/^(https?:\/\/)?(www\.)?/i, "").split("/")[0];
};

// 内容格式化
const formatContent = (content) => {
  if (!content) return "";
  return content.replace(/\n{2,}/g, "<br>").substring(0, 200) + "...";
};

// 切换喜欢状态
const toggleLike = async (liked) => {
  await updatePreferenceMutation.mutateAsync({
    feed_id: props.item.id,
    is_liked: liked,
  });
};

// 显示不喜欢对话框
const showDislikeDialog = () => {
  dislikeDialogVisible.value = true;
  if (props.item.metadata.user_preference && props.item.metadata.user_preference.reason) {
    dislikeReason.value = props.item.metadata.user_preference.reason;
  } else {
    dislikeReason.value = "";
  }
};

// 确认不喜欢
const confirmDislike = async () => {
  await updatePreferenceMutation.mutateAsync({
    feed_id: props.item.id,
    is_liked: false,
    reason: dislikeReason.value,
  });
  dislikeDialogVisible.value = false;
};

// 取消不喜欢
const cancelDislike = async () => {
  await updatePreferenceMutation.mutateAsync({
    feed_id: props.item.id,
    is_liked: null, // 设置为 null 表示取消喜好状态
  });
  dislikeDialogVisible.value = false;
};

// 取消不喜欢直接
const cancelDislikeDirectly = async () => {
  await updatePreferenceMutation.mutateAsync({
    feed_id: props.item.id,
    is_liked: null, // 设置为 null 表示取消喜好状态
  });
  dislikeDialogVisible.value = false;
};
</script>

<style>
/* 移除所有 :deep 样式，使用 Tailwind 类名替代 */
.el-dialog {
  @apply rounded-lg;
}

.el-dialog__header {
  @apply border-b border-gray-200 pb-3;
}

.el-dialog__title {
  @apply text-base font-medium text-gray-800;
}

.el-dialog__body {
  @apply py-3;
}

.el-dialog__footer {
  @apply border-t border-gray-200 pt-3;
}

.el-button {
  @apply rounded-md text-sm;
}

.el-button--primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white;
}

.el-textarea__inner {
  @apply rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500;
}

/* 移除默认 hover 下划线 */
a.no-underline:hover {
  text-decoration: none !important;
}

/* 自定义对话框样式 */
.dislike-dialog {
  @apply rounded-lg border border-gray-200;
}

.dislike-dialog :deep(.el-dialog) {
  @apply max-w-md mx-auto my-0 rounded-lg;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 移动端适配样式 */
@media (max-width: 768px) {
  .el-dialog {
    @apply w-full max-w-full;
  }

  .dislike-dialog :deep(.el-dialog) {
    @apply w-11/12 max-w-sm;
  }

  .el-dialog__body {
    @apply px-3;
  }
}
</style>
