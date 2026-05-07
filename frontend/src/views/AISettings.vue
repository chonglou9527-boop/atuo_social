<template>
  <div>
    <el-page-header content="AI 设置" style="margin-bottom: 16px" />
    <el-button type="primary" @click="dlg = true">新增配置</el-button>

    <el-table :data="configs" style="margin-top: 16px">
      <el-table-column prop="provider" label="Provider" width="140" />
      <el-table-column prop="model" label="Model" />
      <el-table-column prop="base_url" label="Base URL" show-overflow-tooltip />
      <el-table-column label="启用" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.is_active" type="success">激活</el-tag>
          <el-button v-else size="small" @click="activate(row)">设为激活</el-button>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="新增 LLM 配置" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="Provider">
          <el-select v-model="form.provider">
            <el-option v-for="p in providers" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="Model"><el-input v-model="form.model" placeholder="如 claude-sonnet-4-6 / gpt-4o-mini" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="form.api_key" type="password" show-password /></el-form-item>
        <el-form-item label="Base URL (可选)"><el-input v-model="form.base_url" /></el-form-item>
        <el-form-item label="设为激活"><el-switch v-model="form.is_active" /></el-form-item>
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
import { AI } from '../api'

const configs = ref([])
const providers = ref([])
const dlg = ref(false)
const form = reactive({ provider: '', model: '', api_key: '', base_url: '', is_active: false })

async function load() {
  configs.value = await AI.listConfigs()
  providers.value = (await AI.providers()).providers
}
async function submit() {
  await AI.createConfig(form)
  dlg.value = false
  Object.assign(form, { provider: '', model: '', api_key: '', base_url: '', is_active: false })
  await load()
}
async function activate(row) { await AI.activate(row.id); await load() }
async function remove(row) {
  await ElMessageBox.confirm(`删除配置 #${row.id} ?`)
  await AI.deleteConfig(row.id)
  await load()
}
onMounted(load)
</script>
