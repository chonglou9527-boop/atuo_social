<template>
  <div>
    <el-page-header content="改写规则" style="margin-bottom: 16px" />
    <el-button type="primary" @click="dlg = true">新增规则</el-button>
    <el-button @click="run">立即应用规则</el-button>

    <el-table :data="rules" style="margin-top: 16px">
      <el-table-column prop="id" label="#" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column label="关键词">
        <template #default="{ row }">{{ row.keywords_json.join(', ') }}</template>
      </el-table-column>
      <el-table-column label="标签">
        <template #default="{ row }">{{ row.tags_json.join(', ') }}</template>
      </el-table-column>
      <el-table-column prop="enabled" label="启用" width="80" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="新增规则" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="关键词(逗号分隔)"><el-input v-model="kwInput" /></el-form-item>
        <el-form-item label="标签(逗号分隔)"><el-input v-model="tagInput" /></el-form-item>
        <el-form-item label="目标平台">
          <el-checkbox-group v-model="form.target_platforms">
            <el-checkbox label="twitter" />
            <el-checkbox label="weibo" />
            <el-checkbox label="xiaohongshu" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="风格 Prompt">
          <el-input v-model="form.style_prompt" type="textarea" :rows="3" placeholder="例：小红书风、口语化、emoji 适量" />
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
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

const rules = ref([])
const dlg = ref(false)
const kwInput = ref('')
const tagInput = ref('')
const form = reactive({
  name: '', enabled: true, source_ids: [], keywords: [], tags: [],
  style_prompt: '', target_platforms: [], llm_config_id: null, auto_publish: false,
})

async function load() { rules.value = await Inbox.listRules() }
async function submit() {
  form.keywords = kwInput.value.split(',').map(s => s.trim()).filter(Boolean)
  form.tags = tagInput.value.split(',').map(s => s.trim()).filter(Boolean)
  await Inbox.createRule(form)
  dlg.value = false
  kwInput.value = ''; tagInput.value = ''
  Object.assign(form, { name: '', enabled: true, source_ids: [], keywords: [], tags: [], style_prompt: '', target_platforms: [], llm_config_id: null, auto_publish: false })
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm(`删除规则 "${row.name}" ?`)
  await Inbox.deleteRule(row.id)
  await load()
}
async function run() {
  const r = await Inbox.runRules()
  ElMessage.success(`改写 ${r.rewritten} 条`)
}
onMounted(load)
</script>
