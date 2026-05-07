<template>
  <div>
    <el-page-header content="草稿 / 发布" style="margin-bottom: 16px" />
    <el-button type="primary" @click="newDraft">新建草稿</el-button>

    <div style="display: flex; gap: 16px; margin-top: 16px">
      <el-table :data="posts" style="flex: 1" @row-click="select">
        <el-table-column prop="id" label="#" width="60" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
      </el-table>

      <el-card v-if="current" style="flex: 1.4">
        <el-form :model="current" label-width="80px">
          <el-form-item label="标题"><el-input v-model="current.title" /></el-form-item>
          <el-form-item label="正文">
            <el-input v-model="current.body_md" type="textarea" :rows="10" />
          </el-form-item>
          <el-form-item label="封面 URL"><el-input v-model="current.cover_url" /></el-form-item>
        </el-form>
        <el-button type="primary" @click="save">保存</el-button>
        <el-divider />
        <el-form :model="pubForm" label-width="80px">
          <el-form-item label="账号">
            <el-select v-model="pubForm.account_ids" multiple>
              <el-option v-for="a in accounts" :key="a.id" :label="`${a.platform} / ${a.name}`" :value="a.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="定时">
            <el-date-picker v-model="pubForm.scheduled_at" type="datetime" placeholder="留空=立即发布" />
          </el-form-item>
        </el-form>
        <el-button type="success" @click="publish" :disabled="!pubForm.account_ids.length">发布</el-button>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Posts, Accounts } from '../api'

const posts = ref([])
const accounts = ref([])
const current = ref(null)
const pubForm = reactive({ account_ids: [], scheduled_at: null })

async function load() {
  posts.value = await Posts.list()
  accounts.value = await Accounts.list()
}
async function select(row) { current.value = await Posts.get(row.id) }
async function newDraft() {
  current.value = await Posts.create({ title: '新草稿', body_md: '' })
  await load()
}
async function save() {
  const p = await Posts.update(current.value.id, {
    title: current.value.title, body_md: current.value.body_md, cover_url: current.value.cover_url,
  })
  current.value = p
  ElMessage.success('已保存')
  await load()
}
async function publish() {
  await Posts.publish(current.value.id, {
    account_ids: pubForm.account_ids,
    scheduled_at: pubForm.scheduled_at ? new Date(pubForm.scheduled_at).toISOString() : null,
  })
  ElMessage.success('已提交发布任务')
  await load()
}
onMounted(load)
</script>
