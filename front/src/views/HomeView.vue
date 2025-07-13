<template>
  <el-row justify="center" style="min-height:100vh;background:linear-gradient(135deg,#f5f8ff 0%,#e8edf7 100%);padding:32px 0;">
    <el-col :xs="24" :sm="20" :md="16" :lg="14" :xl="12">
      <!-- Header -->
      <el-card class="firefly-header" shadow="always">
        <h1>Firefly AI 记账系统</h1>
      </el-card>

      <!-- 账户卡片 -->
      <el-row :gutter="20" style="margin-bottom:24px;">
        <el-col :span="12">
          <el-card shadow="hover" class="firefly-account-card">
        <template #header>
          <el-icon><Wallet /></el-icon>
          <span> 支出来源账户 </span>
        </template>
            <el-form label-position="top">
              <el-form-item>
                <el-skeleton :rows="3" animated v-if="accounts.length === 0" />
                <el-radio-group v-model="defaultExpense" v-else>
                  <el-radio
                    v-for="account in expenseAccounts"
                    :key="account.id"
                    :value="account.id"
                    border
                    class="firefly-account-radio"
                  >
                    <span>{{ account.name }}</span>
                    <el-tag :type="account.current_balance >= 0 ? 'success' : 'danger'" size="small">
                      {{ account.current_balance }}
                    </el-tag>
                  </el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" class="firefly-account-card">
        <template #header>
          <el-icon><CreditCard /></el-icon>
          <span> 支出目的账户</span>
        </template>
            <el-form label-position="top">
              <el-form-item>
                <el-skeleton :rows="3" animated v-if="accounts.length === 0" />
                <el-radio-group v-model="defaultRevenue" v-else>
                  <el-radio
                    v-for="account in revenueAccounts"
                    :key="account.id"
                    :value="account.id"
                    border
                    class="firefly-account-radio"
                  >
                    <span>{{ account.name }}</span>
                    <el-tag :type="account.current_balance >= 0 ? 'success' : 'danger'" size="small">
                      {{ account.current_balance }}
                    </el-tag>
                  </el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <!-- 输入交易卡片 -->
      <el-card class="firefly-input-card" shadow="hover" style="margin-bottom:28px;">
        <template #header>
          <el-icon><Edit /></el-icon>
          <span> 输入交易记录</span>
          <el-tooltip effect="light" placement="top">
            <template #content>
              <div style="max-width: 300px; line-height: 1.6;">
                输入格式示例：<br>
                日期（如：07.06）<br>
                每行一条交易，以“-”开头，后跟金额,标题(备注信息)和花费时间（如果没写ai会随机生成时间），例如：<br>
                7.6<br>
                - 66 午餐 12:00 <br>
                - 900 物业费(最近一季度) 16:00<br>
                7.7<br>
                - 10.30 购物 150<br>
              </div>
            </template>
            <el-icon style="margin-left: 8px; cursor: pointer;"><QuestionFilled /></el-icon>
          </el-tooltip>

        </template>
        <el-input
          type="textarea"
          v-model="rawInput"
          :rows="7"
          placeholder="输入交易记录，格式如：&#10;07.06&#10;- 12.00 午餐 66&#10;- 16.00 物业费 900"
          resize="none"
          class="firefly-transaction-input"
        ></el-input>
        <div style="display:flex;justify-content:flex-end;gap:16px;margin-top:18px;">
          <el-link type="info">Version: {{ version }}</el-link>
          <el-button 
              v-if="fireflyUrl" 
              type="info" 
              icon="Link" 
              @click="openFirefly"
            >
              前往Firefly III
            </el-button>
          <el-button
            type="success"
            @click="$router.push('/recent-transactions')"
            icon="Document"
          >查看最近交易</el-button>
          <el-button
            :loading="isParsing"
            type="primary"
            @click="handleParse"
            :disabled="isParsing"
            icon="Edit"
          >AI 解析交易记录</el-button>

        </div>

      </el-card>

      <!-- 解析结果区 -->
      <transition name="el-fade-in-linear">
        <el-card v-if="showResult" class="firefly-result-card" shadow="hover" style="margin-bottom:26px;">
        <template #header>
          <el-icon><Document /></el-icon>
          <span>AI 解析结果</span>
        </template>
        
        <!-- AI思考结果 -->
        <el-alert
          v-if="thinkResult"
          :title="thinkResult"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom:20px;"
        />
        
        <el-table :data="parsedTransactions" stripe border show-overflow-tooltip style="margin-bottom:18px;">
          <el-table-column prop="date" label="日期" width="110" align="center" />
          <el-table-column prop="description" label="描述" min-width="120" align="center" />
          <el-table-column prop="amount" label="金额" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.amount >= 0 ? 'success' : 'danger'">
                {{ scope.row && scope.row.amount ? `${scope.row.amount}元` : '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="100" align="center" />
          <el-table-column prop="tags" label="标签" width="160" align="center">
            <template #default="scope">
              <template v-if="scope.row && scope.row.tags?.length">
                <el-tag
                  v-for="tag in scope.row.tags"
                  :key="tag"
                  size="small"
                  class="mr-5 firefly-tag"
                >{{ tag }}</el-tag>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="100" align="center" />
        </el-table>
        <div style="text-align:right;">
          <el-button
            :loading="loading"
            type="success"
            @click="submitForm"
            size="large"
            icon="Check"
          >确认记录</el-button>
          <el-button
            @click="resetForm"
            size="large"
            icon="Close"
          >取消</el-button>
        </div>
      </el-card>
    </transition>

      <!-- 确认对话框 -->
      <el-dialog
        v-model="showForm"
        title="确认提交"
        width="380px"
        :show-close="true"
        :close-on-click-modal="false"
        v-loading="isSubmitting"
        element-loading-text="提交中..."
        element-loading-background="rgba(0, 0, 0, 0.7)"
      >
        <el-alert
          title="确定要提交这些交易记录吗？"
          type="warning"
          show-icon
          effect="plain"
          :closable="false"
          style="margin-bottom:20px;"
        />
        <template #footer>
          <el-button @click="showForm = false">取消</el-button>
          <el-button type="primary" @click="confirmSubmit">确认</el-button>
        </template>
      </el-dialog>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  ElRow,
  ElCol,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElButton,
  ElButtonGroup,
  ElRadio,
  ElRadioGroup,
  ElSkeleton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElDialog,
  ElIcon,
  ElAlert,
  ElMessage,
  ElPopover
} from 'element-plus'
import { Wallet, CreditCard, Edit, Document, Check, Close } from '@element-plus/icons-vue'
import api from '@/api'

const rawInput = ref('')
const accounts = ref([])
const defaultExpense = ref('')
const defaultRevenue = ref('')
const version = ref('') // 存储版本号
const fireflyUrl = ref('') // Firefly III URL
const isSubmitting = ref(false)
const loading = ref(false)

watch(defaultExpense, (newVal) => {
  if (newVal) saveDefaultAccount('expense', newVal)
})

watch(defaultRevenue, (newVal) => {
  if (newVal) saveDefaultAccount('revenue', newVal)
})

watch(rawInput, async (newVal) => {
  if (newVal.trim()) {
    try {
      await api.updateDefaultAccount({
        last_transaction_text: newVal,
        last_edit: new Date().toISOString()
      })
    } catch (error) {
      console.error('保存交易记录失败:', error)
    }
  }
}, { deep: true })

const expenseAccounts = computed(() =>
  accounts.value.filter(a => a.type === 'revenue' || a.type === 'asset' || a.type === 'cash')
)

const revenueAccounts = computed(() =>
  accounts.value.filter(a => a.type === 'expense' || a.type === 'asset' || a.type === 'cash')
)

const loadAccounts = async () => {
  try {
    const [accountsData, defaultAccounts] = await Promise.all([
      api.getAccounts(),
      api.getDefaultAccount()
    ])
    const accountsArray = Object.entries(accountsData)
      .map(([id, account]) => ({
        id,
        ...account
      }))
      .sort((a, b) => a.name.localeCompare(b.name))
    
    accounts.value = accountsArray
    // 将账户数据存储到localStorage
    localStorage.setItem('accounts', JSON.stringify(accountsArray))
    
    defaultExpense.value = defaultAccounts.default_expense || ''
    defaultRevenue.value = defaultAccounts.default_revenue || ''
    if (defaultAccounts.last_transaction_text) {
      rawInput.value = defaultAccounts.last_transaction_text
    }
    version.value = defaultAccounts.version || '' // 设置版本号
    fireflyUrl.value = defaultAccounts.firefly_iii_url || '' // 设置Firefly III URL
  } catch (error) {
    ElMessage.error('加载账户失败')
    console.error(error)
  }
}

const openFirefly = () => {
  if (fireflyUrl.value) {
    window.open(fireflyUrl.value, '_blank')
  }
}

const saveDefaultAccount = async (type, accountId) => {
  try {
    await api.updateDefaultAccount({
      [`default_${type}`]: accountId,
      last_edit: new Date().toISOString()
    })
  } catch (error) {
    ElMessage.error('保存默认账户失败')
  }
}

onMounted(() => {
  loadAccounts()
})

const isParsing = ref(false)
const showResult = ref(false)
const showForm = ref(false)
const parsedTransactions = ref([])
const thinkResult = ref('')

const handleParse = async () => {
  if (!rawInput.value.trim()) {
    ElMessage.warning('请输入交易记录内容')
    return
  }
  try {
    isParsing.value = true
    const data = await api.parseTransactions(rawInput.value)
    parsedTransactions.value = data.transactions || []
    thinkResult.value = data.think_result || 'AI未返回思考结果'
    showResult.value = true
  } catch (error) {
    ElMessage.error(`解析交易记录时出错: ${error.message}`)
  } finally {
    isParsing.value = false
  }
}

const submitForm = () => {
  if (parsedTransactions.value.length === 0) {
    ElMessage.warning('没有交易记录可提交')
    return
  }
  showForm.value = true
}

const confirmSubmit = async () => {
  if (isSubmitting.value) return
  try {
    isSubmitting.value = true
    await api.recordTransactions(parsedTransactions.value)
    ElMessage.success('交易记录成功')
    resetForm()
    showForm.value = false
  } catch (error) {
    ElMessage.error(`记录交易时出错: ${error.message}`)
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  rawInput.value = ''
  showResult.value = false
  parsedTransactions.value = []
  thinkResult.value = ''
}
</script>

<style scoped>
.firefly-header {
  margin-bottom: 32px;
  border-radius: 20px;
  background: linear-gradient(135deg, #e6f0ff 0%, #f7fafc 100%);
  box-shadow: 0 6px 24px -8px rgba(0,0,0,0.11);
  border: none;
  text-align: center;
  position: relative;
}
.firefly-header h1 {
  font-size: 2.2rem;
  font-weight: 800;
  color: #296fff;
  margin: 0;
  padding: 26px 0 16px 0;
  letter-spacing: 1.5px;
}

.firefly-account-card {
  border-radius: 16px;
  transition: box-shadow 0.22s;
  min-height: 224px;
  border: none;
}
.firefly-account-radio {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  border-radius: 9px;
  margin-bottom: 10px;
  padding: 7px 14px;
  font-size: 1.07em;
}
.firefly-account-radio:hover {
  background: #f3f6fb;
}

.firefly-input-card {
  border-radius: 14px;
  background: #fff;
}
.firefly-transaction-input :deep(.el-textarea__inner) {
  min-height: 112px;
  padding: 18px;
  border-radius: 10px;
  font-size: 1.07rem;
  line-height: 1.7;
  border: 1.5px solid #dbeafe;
  background: #f9fbff;
  transition: border 0.2s, box-shadow 0.2s;
}
.firefly-transaction-input :deep(.el-textarea__inner):focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.10);
}

.firefly-tag {
  margin-right: 6px;
  border-radius: 4px;
  font-weight: 500;
  background: #bae6fd;
  color: #0369a1;
}
</style>
