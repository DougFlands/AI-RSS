<template>
  <div class="flex justify-center mt-2 mb-2">
    <div class="loading-dots-small">
      <span></span>
      <span></span>
      <span></span>
    </div>
  </div>
</template>

<style scoped>
/* 小型加载动画样式 */
.loading-dots-small {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 10px;
}

.loading-dots-small span {
  width: 5px;
  height: 5px;
  background-color: #c0c4cc;
  border-radius: 50%;
  margin: 0 3px;
  animation: fadeInOut 1.2s infinite both;
}

.loading-dots-small span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots-small span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes fadeInOut {
  0% {
    opacity: 0.2;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0.2;
    transform: scale(0.8);
  }
}
</style> 