<template>
  <div class="h-[calc(100vh-60px)] flex flex-col relative">
    <div class="p-3 border-b flex justify-between items-center">
      <h2 class="text-base font-semibold">订阅源</h2>
      <el-button
        type="primary"
        size="small"
        @click="openAddSourceDialog"
        class="add-button"
        >+</el-button
      >
    </div>

    <div class="flex-grow overflow-y-auto p-3">
      <el-skeleton :rows="3" animated v-if="loading"></el-skeleton>

      <el-empty
        description="没有订阅源，请添加"
        v-else-if="sources.length === 0"
      ></el-empty>

      <div v-else class="source-list">
        <div
          v-for="source in sources"
          :key="source._id"
          class="source-item"
          @click="editSource(source)"
        >
          <span class="source-name" :title="source.url">
            {{ source.name || source.url }}
          </span>
        </div>
      </div>
    </div>

    <!-- 底部刷新按钮 - 放在最底部固定位置 -->
    <div class="mt-auto border-t flex justify-end absolute bottom-0 left-0 right-0">
      <el-button
        type="primary"
        size="small"
        @click="refreshRssData"
        :loading="refreshing"
        :disabled="refreshing"
        class="refresh-button"
      >
        <el-icon class="mr-1" v-if="!refreshing"><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 添加订阅源弹窗 -->
    <el-dialog
      :title="isEditing ? '编辑订阅源' : '添加订阅源'"
      v-model="showAddDialog"
      width="400px"
      center
      :close-on-click-modal="false"
      custom-class="rss-dialog"
    >
      <el-form :model="newSource" label-position="top">
        <el-form-item label="订阅源地址" required>
          <el-input
            v-model="newSource.url"
            placeholder="请输入RSS订阅地址"
            class="custom-input"
          ></el-input>
        </el-form-item>

        <el-form-item label="名称">
          <el-input
            v-model="newSource.name"
            placeholder="订阅源名称（可选）"
            class="custom-input"
          ></el-input>
        </el-form-item>
      </el-form>

      <div v-if="errorMessage" class="mb-4">
        <el-alert :title="errorMessage" type="error" show-icon></el-alert>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeAddSourceDialog" class="cancel-btn">取 消</el-button>
          <el-button
            type="danger"
            v-if="isEditing"
            @click="confirmDeleteSource"
            class="delete-btn"
            >删 除</el-button
          >
          <el-button
            type="primary"
            @click="saveSource"
            :loading="isAdding"
            class="confirm-btn"
            >确 定</el-button
          >
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "@/api";
import { server } from "@/server";
import { ElMessage, ElMessageBox } from "element-plus";
import { Refresh } from "@element-plus/icons-vue";

// 订阅源列表
const sources = ref([]);
const loading = ref(true);

// 添加/编辑订阅源相关状态
const showAddDialog = ref(false);
const newSource = ref({ url: "", name: "" });
const isAdding = ref(false);
const errorMessage = ref("");
const isEditing = ref(false);
const editingSourceId = ref(null);

// 刷新状态
const refreshing = ref(false);

// 使用 vue-query 的 useNewRssQuery
const newRssQuery = server.rss.useNewRssQuery();

// 获取所有订阅源
const fetchSources = async () => {
  try {
    loading.value = true;
    sources.value = await api.rss.getRssSources();
  } catch (error) {
    console.error("Failed to fetch RSS sources:", error);
    ElMessage.error("获取订阅源失败");
  } finally {
    loading.value = false;
  }
};

// 刷新 RSS 数据
const refreshRssData = async () => {
  try {
    refreshing.value = true;

    // 使用 vue-query 的 refetch 方法，它会自动使相关查询失效
    const result = await newRssQuery.refetch();

    if (result.isSuccess) {
      // 刷新成功后重新获取订阅源列表
      await fetchSources();
      ElMessage.success("RSS 数据刷新成功");
    } else {
      throw new Error("刷新 RSS 数据失败");
    }
  } catch (error) {
    console.error("Failed to refresh RSS data:", error);
    ElMessage.error("RSS 数据刷新失败");
  } finally {
    refreshing.value = false;
  }
};

// 打开添加对话框
const openAddSourceDialog = () => {
  isEditing.value = false;
  editingSourceId.value = null;
  showAddDialog.value = true;
  newSource.value = { url: "", name: "" };
  errorMessage.value = "";
};

// 打开编辑对话框
const editSource = (source) => {
  isEditing.value = true;
  editingSourceId.value = source._id;
  newSource.value = {
    url: source.url,
    name: source.name || "",
  };
  showAddDialog.value = true;
  errorMessage.value = "";
};

// 关闭对话框
const closeAddSourceDialog = () => {
  showAddDialog.value = false;
};

// 保存订阅源（添加或更新）
const saveSource = async () => {
  if (!newSource.value.url) {
    errorMessage.value = "请输入订阅源地址";
    return;
  }

  try {
    isAdding.value = true;
    errorMessage.value = "";

    if (isEditing.value) {
      // 更新订阅源
      await api.rss.updateRssSource(editingSourceId.value, newSource.value);
      ElMessage.success("更新订阅源成功");
      location.reload();
    } else {
      // 添加新订阅源
      await api.rss.addRssSource(newSource.value);
      ElMessage.success("添加订阅源成功");
      location.reload();
    }

    await fetchSources();
    closeAddSourceDialog();
  } catch (error) {
    errorMessage.value =
      error.response?.data?.error ||
      (isEditing.value ? "更新订阅源失败" : "添加订阅源失败");
    console.error("Failed to save RSS source:", error);
  } finally {
    isAdding.value = false;
  }
};

// 确认删除操作
const confirmDeleteSource = async () => {
  try {
    await ElMessageBox.confirm("此操作将永久删除该订阅源, 是否继续?", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    deleteSource(editingSourceId.value);
  } catch (error) {
    // 用户取消删除操作，不做任何处理
  }
};

// 删除订阅源
const deleteSource = async (sourceId) => {
  try {
    await api.rss.deleteRssSource(sourceId);
    ElMessage.success("删除成功");
    await fetchSources();
    closeAddSourceDialog();
  } catch (error) {
    console.error("Failed to delete RSS source:", error);
    ElMessage.error("删除订阅源失败");
  }
};

// 初始化
onMounted(() => {
  fetchSources();
});
</script>

<style>
/* Element UI 定制样式 */
.el-card {
  margin-bottom: 10px;
}

.add-button {
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
}

/* 刷新按钮样式 */
.refresh-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
}

/* 订阅源列表样式 */
.source-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background-color: white;
  border-radius: 4px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.source-item:hover {
  background-color: #f5f7fa;
}

.source-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 弹窗样式优化 */
.rss-dialog .el-dialog__header {
  padding: 15px 20px;
  text-align: center;
  font-weight: bold;
  border-bottom: 1px solid #eee;
  margin-right: 0;
}

.rss-dialog .el-dialog__body {
  padding: 20px;
}

.rss-dialog .el-dialog__footer {
  border-top: 1px solid #eee;
  padding: 15px 20px;
}

.dialog-footer {
  display: flex;
  justify-content: center;
}

.cancel-btn {
  margin-right: 15px;
}

.delete-btn {
  margin-right: 15px;
}

.confirm-btn {
  min-width: 80px;
}

.custom-input .el-input__inner {
  border-radius: 4px;
}

.required {
  color: #f56c6c;
  margin-right: 4px;
}

/* 隐藏Element自带的label */
.rss-dialog .el-form-item__label {
  display: none;
}

.el-form-item {
  margin-bottom: 20px;
}
</style>
