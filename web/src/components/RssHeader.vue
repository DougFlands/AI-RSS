<template>
  <div class="bg-[#409EFF] shadow-sm z-10 p-2 py-6 border-b border-gray-200 w-full flex">
    <el-button
      class="md:hidden mr-4 border-0 bg-transparent shadow-none"
      @click="toggleSidebar"
    >
      <el-icon><Menu /></el-icon>
    </el-button>
    <div class="overflow-x-auto pb-1 flex items-center">
      <el-select
        v-model="filterType"
        @change="onFilterChange"
        placeholder="筛选条件"
        class="filter-select"
      >
        <el-option label="全部" value="all" />
        <el-option label="喜欢" value="liked" />
        <el-option label="不喜欢" value="disliked" />
        <el-option label="未标记" value="unmarked" />
      </el-select>
      <!-- 日期选择器 -->
      <el-date-picker
        v-model="selectedDate"
        type="date"
        placeholder="选择日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        :disabled-date="disabledDate"
        @change="onDateChange"
        class="w-full"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits, defineProps } from 'vue';
import { Menu } from "@element-plus/icons-vue";

const props = defineProps({
  availableDates: {
    type: Set,
    required: true
  },
  initialFilterType: {
    type: String,
    default: 'all'
  },
  initialSelectedDate: {
    type: String,
    default: 'all'
  }
});

const emit = defineEmits(['filter-change', 'date-change', 'toggle-sidebar']);

const filterType = ref(props.initialFilterType);
const selectedDate = ref(props.initialSelectedDate);

// 禁用没有数据的日期
const disabledDate = (time) => {
  const dateString = time.toISOString().split("T")[0];
  return !props.availableDates.has(dateString);
};

const onFilterChange = () => {
  emit('filter-change', filterType.value);
};

const onDateChange = (date) => {
  emit('date-change', date || 'all');
};

const toggleSidebar = () => {
  emit('toggle-sidebar');
};
</script>

<style scoped>
/* 菜单按钮样式 */
.md\:hidden.mr-4.border-0 .el-icon {
  color: white;
}

/* 下拉选择框样式 */
.filter-select {
  width: 120px;
}

:deep(.el-select__wrapper), :deep(.el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  color: white;
  border: none;
}

:deep(.el-select__placeholder),
:deep(.el-select__caret),
:deep(.el-input__inner) {
  color: white;
}

:deep(.el-input__prefix), :deep(.el-input__suffix), :deep(.el-range__icon) {
  color: white;
}

:deep(.el-date-editor .el-range-separator) {
  color: white;
}

:deep(.el-date-editor .el-icon) {
  color: white;
}

:deep(.el-date-editor input::placeholder) {
  color: white !important;
}
</style> 