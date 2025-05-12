<template>
  <div class="bg-[#409EFF] shadow-sm z-10 p-2 py-6 border-b border-gray-200 w-full">
    <div class="flex w-full max-w-full overflow-hidden">
      <el-button
        class="md:hidden mr-2 border-0 bg-transparent shadow-none flex-shrink-0"
        @click="toggleSidebar"
      >
        <el-icon><Menu /></el-icon>
      </el-button>
      <div class="flex-1 flex justify-center overflow-hidden">
        <div class="flex items-center gap-2 md:gap-4 w-full max-w-md mx-auto">
          <el-select
            v-model="filterType"
            @change="onFilterChange"
            placeholder="筛选条件"
            class="filter-select"
          >
            <el-option label="推荐" value="recommended" />
            <el-option label="全部" value="all" />
            <el-option label="喜欢" value="liked" />
            <el-option label="不喜欢" value="disliked" />
            <el-option label="未标记" value="unmarked" />
          </el-select>
          
          <!-- 订阅源筛选 -->
          <el-select
            v-model="sourceId"
            @change="onSourceChange"
            placeholder="订阅源"
            class="source-select"
          >
            <el-option label="全部源" value="" />
            <el-option 
              v-for="source in props.sources" 
              :key="source._id" 
              :label="source.name" 
              :value="source._id" 
            />
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
            class="date-picker"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits, defineProps, watch, onMounted } from 'vue';
import { Menu } from "@element-plus/icons-vue";
import { server } from '@/server';

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
  },
  initialSourceId: {
    type: String,
    default: ''
  },
  sources: {
    type: Array,
    default: () => []
  },
  isSourcesLoading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['filter-change', 'date-change', 'source-change', 'toggle-sidebar']);

const filterType = ref(props.initialFilterType);
const selectedDate = ref(props.initialSelectedDate === 'all' ? null : props.initialSelectedDate);
const sourceId = ref(props.initialSourceId);

// 监听 initialSelectedDate 变化
watch(() => props.initialSelectedDate, (newValue) => {
  selectedDate.value = newValue === 'all' ? null : newValue;
}, { immediate: true });

// 监听 initialSourceId 变化
watch(() => props.initialSourceId, (newValue) => {
  sourceId.value = newValue;
}, { immediate: true });

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

const onSourceChange = () => {
  emit('source-change', sourceId.value);
};

const toggleSidebar = () => {
  emit('toggle-sidebar');
};
</script>

<style scoped>
/* 菜单按钮样式 */
.md\:hidden.mr-2.border-0 .el-icon {
  color: white;
}

/* 下拉选择框样式 */
.filter-select, .source-select {
  width: 100px;
  min-width: 0;
  flex-shrink: 1;
}

.date-picker {
  width: 130px;
  min-width: 0;
  flex-shrink: 1;
}

@media (min-width: 768px) {
  .filter-select, .source-select {
    width: 120px;
  }
  
  .date-picker {
    width: 160px;
  }
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

/* 防止内容溢出 */
:deep(.el-input__inner) {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 