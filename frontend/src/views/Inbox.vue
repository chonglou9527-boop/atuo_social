<template>
  <div>
    <el-page-header content="收件箱" style="margin-bottom: 16px" />
    <el-space>
      <el-select v-model="filter.status" placeholder="状态" clearable style="width: 140px" @change="load">
        <el-option label="新" value="new" />
        <el-option label="已读" value="read" />
        <el-option label="已用" value="used" />
        <el-option label="归档" value="archived" />
      </el-select>
      <el-button @click="load">刷新</el-button>
      <el-button type="primary" @click="runRules">应用规则</el-button>
    </el-space>

    <el-table :data="items" style="margin-top: 16px">
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
      <el-table-column prop="author" label="作者" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="published_at" label="发布时间" width="180" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" type="primary" :loading="rewriting === row.id" @click="rewrite(row)">改写</el-button>
          <el-button size="small" @click="archive(row)">归档</el-button>
          <el-link v-if="row.url" :href="row.url" target="_blank" type="info" style="margin-left: 8px">原文</el-link>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Inbox } from '../api'

const items = ref([])
const filter = reactive({ status: 'new' })
const rewriting = ref(null)

async function load() {
  items.value = await Inbox.listItems({ status: filter.status || undefined, limit: 200 })
}
async function rewrite(row) {
  rewriting.value = row.id
  try {
    const post = await Inbox.rewrite(row.id)
    ElMessage.success(`已生成草稿 #${post.id}`)
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally { rewriting.value = null }
}
async function archive(row) {
  await Inbox.setStatus(row.id, 'archived')
  await load()
}
async function runRules() {
  const r = await Inbox.runRules()
  ElMessage.success(`规则改写完成: ${r.rewritten}`)
  await load()
}
onMounted(load)
</script>
