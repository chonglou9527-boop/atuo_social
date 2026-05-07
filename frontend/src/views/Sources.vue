<template>
  <div>
    <el-page-header content="订阅源" style="margin-bottom: 16px" />
    <el-button type="primary" @click="dlg = true">新增订阅源</el-button>

    <el-table :data="sources" style="margin-top: 16px">
      <el-table-column prop="id" label="#" width="60" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column prop="fetch_interval_min" label="频率(min)" width="120" />
      <el-table-column prop="last_fetched_at" label="上次抓取" width="180" />
      <el-table-column prop="last_error" label="错误" show-overflow-tooltip />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="fetchNow(row)">立即抓取</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="新增订阅源" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" @change="onTypeChange">
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.type === 'rss'" label="RSS URL">
          <el-input v-model="form.config.url" placeholder="https://example.com/feed.xml" />
        </el-form-item>
        <template v-if="form.type === 'twitter_list'">
          <el-form-item label="Bearer Token"><el-input v-model="form.config.bearer_token" type="password" show-password /></el-form-item>
          <el-form-item label="List ID"><el-input v-model="form.config.list_id" /></el-form-item>
        </template>
        <el-form-item label="频率(min)"><el-input-number v-model="form.fetch_interval_min" :min="1" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Inbox } from '../api'

const sources = ref([])
const types = ref([])
const dlg = ref(false)
const form = reactive({ name: '', type: 'rss', config: {}, fetch_interval_min: 30, enabled: true })

function onTypeChange() { form.config = {} }

async function load() {
  sources.value = await Inbox.listSources()
  types.value = (await Inbox.sourceTypes()).types
}
async function submit() {
  await Inbox.createSource(form)
  dlg.value = false
  Object.assign(form, { name: '', type: 'rss', config: {}, fetch_interval_min: 30 })
  await load()
}
async function fetchNow(row) {
  const r = await Inbox.fetchSource(row.id)
  ElMessage.success(`抓取 ${r.fetched}, 新增 ${r.new}`)
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm(`删除订阅源 "${row.name}" ?`)
  await Inbox.deleteSource(row.id)
  await load()
}
onMounted(load)
</script>
