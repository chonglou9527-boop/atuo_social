<template>
  <div>
    <el-page-header content="账号" style="margin-bottom: 16px" />
    <el-button type="primary" @click="dlg = true">新增账号</el-button>

    <el-table :data="accounts" style="margin-top: 16px">
      <el-table-column prop="id" label="#" width="60" />
      <el-table-column prop="platform" label="平台" width="120" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="auth_type" label="认证方式" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="新增账号" width="500px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="平台">
          <el-select v-model="form.platform">
            <el-option v-for="p in platforms" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <template v-if="form.platform === 'twitter'">
          <el-form-item label="consumer_key"><el-input v-model="form.credentials.consumer_key" /></el-form-item>
          <el-form-item label="consumer_secret"><el-input v-model="form.credentials.consumer_secret" type="password" show-password /></el-form-item>
          <el-form-item label="access_token"><el-input v-model="form.credentials.access_token" /></el-form-item>
          <el-form-item label="access_token_secret"><el-input v-model="form.credentials.access_token_secret" type="password" show-password /></el-form-item>
          <el-form-item label="bearer_token (可选)"><el-input v-model="form.credentials.bearer_token" /></el-form-item>
        </template>
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
import { ElMessageBox } from 'element-plus'
import { Accounts } from '../api'

const accounts = ref([])
const platforms = ref([])
const dlg = ref(false)
const form = reactive({ platform: '', name: '', auth_type: 'api', credentials: {} })

async function load() {
  accounts.value = await Accounts.list()
  platforms.value = (await Accounts.platforms()).platforms
}
async function submit() {
  await Accounts.create(form)
  dlg.value = false
  Object.assign(form, { platform: '', name: '', auth_type: 'api', credentials: {} })
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm(`删除账号 "${row.name}" ?`)
  await Accounts.remove(row.id)
  await load()
}
onMounted(load)
</script>
