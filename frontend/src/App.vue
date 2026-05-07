<template>
  <el-container style="height: 100vh">
    <el-aside width="200px" class="aside">
      <h2 style="padding: 16px 12px; margin: 0">atuo-social</h2>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/inbox">收件箱</el-menu-item>
        <el-menu-item index="/rules">改写规则</el-menu-item>
        <el-menu-item index="/sources">订阅源</el-menu-item>
        <el-menu-item index="/posts">草稿/发布</el-menu-item>
        <el-menu-item index="/accounts">账号</el-menu-item>
        <el-menu-item index="/ai">AI 设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<style>
.aside { background: #f5f7fa; border-right: 1px solid #e4e7ed; }
</style>
