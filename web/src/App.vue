<template>
  <div class="app-container">
    <header class="app-header">
      <h1>RSS 阅读器</h1>
    </header>
    <main class="app-main">
      <router-view/>
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #409eff;
  color: white;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-main {
  flex: 1;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #f0f2f5;
  padding: 1rem;
  text-align: center;
  font-size: 0.9rem;
  color: #606266;
}
</style> 