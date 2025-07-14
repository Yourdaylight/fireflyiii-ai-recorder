<template>
  <div class="firefly-root">
    <el-row :gutter="20" justify="space-between" align="middle">
      <el-col :xs="24" :sm="16">
        <el-card class="firefly-header" shadow="hover">
          <h1>最近交易记录</h1>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" class="button-col">
        <el-button type="primary" icon="Back" @click="$router.push('/')">返回首页</el-button>
      </el-col>
    </el-row>

    <!-- 最近交易区块 -->
    <el-row :gutter="20" class="firefly-recent-row">
      <el-col :span="24">
        <el-card class="firefly-recent-card">
          <div class="table-container">
            <el-table :data="transactions" stripe border class="firefly-table">
              <el-table-column prop="date" label="日期" width="110" align="center" />
              <el-table-column prop="description" label="描述" min-width="120" align="center" />
              <el-table-column prop="amount" label="金额" width="100" align="center">
                <template #default="scope">
                  <span class="firefly-amount">{{ scope.row && scope.row.amount ? formatAmount(scope.row.amount) : '-' }}</span>
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
                      class="mr-5"
                    >
                      {{ tag }}
                    </el-tag>
                  </template>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" min-width="100" align="center" />
              <el-table-column label="源账户" width="120" align="center">
                <template #default="scope">
                  <el-tag type="danger">{{ getAccountName(scope.row.source_id) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="目的账户" width="120" align="center">
                <template #default="scope">
                  <el-tag type="info">{{ getAccountName(scope.row.destination_id) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElCard, ElTable, ElTableColumn, ElTag, ElRow, ElCol, ElIcon, ElMessage } from 'element-plus'
import api from '@/api'

const transactions = ref([])
const accountMap = ref({})

const loadTransactions = async () => {
  try {
    // 从localStorage获取账户数据
    const accountsData = localStorage.getItem('accounts')
    if (accountsData) {
      const accounts = JSON.parse(accountsData)
      // 转换为ID到账户对象的映射
      accountMap.value = accounts.reduce((map, account) => {
        map[account.id] = account
        return map
      }, {})
    }

    const response = await api.getTransactions()
    transactions.value = Object.values(response).map(trans => ({
      ...trans,
      category: trans.category_name
    }))
  } catch (error) {
    ElMessage.error('加载交易列表失败')
  }
}

const formatAmount = (amountStr) => {
  // 提取数字部分并保留两位小数
  const num = parseFloat(amountStr.replace(/[^\d.-]/g, ''))
  return isNaN(num) ? amountStr : `¥ ${num.toFixed(2)}`
}

const getAccountName = (accountId) => {
  if (!accountId) return '-'
  const account = accountMap.value[accountId]
  return account ? account.name : '-'
}

onMounted(() => {
  loadTransactions()
})
</script>

<style scoped>
.firefly-root {
  width: 100%;
  padding: 24px 16px;
  background: #f8fafc;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .firefly-root {
    padding: 16px 8px;
  }
}
.firefly-header {
  margin-bottom: 24px;
  border-radius: 18px;
  background: linear-gradient(135deg, #e6f0ff 0%, #f7fafc 100%);
  box-shadow: 0 6px 24px -8px rgba(0,0,0,0.08);
  border: none;
  text-align: center;
}
.firefly-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #2563eb;
  margin: 0;
  padding: 22px 0;
  letter-spacing: 1px;
}

.firefly-recent-row { margin-top: 24px; }
.firefly-recent-card {
  border-radius: 14px;
  box-shadow: 0 2px 12px -4px rgba(100, 116, 139, 0.09);
  border: none;
  margin-bottom: 0;
}

.firefly-table :deep(.el-table__header th) {
  background: #f0f9ff;
  color: #2563eb;
  font-weight: 700;
  font-size: 1.05em;
  border-bottom: 2px solid #bae6fd;
}
.firefly-table :deep(.el-table__body tr) {
  transition: background 0.18s;
}
.firefly-table :deep(.el-table__body tr:hover > td) {
  background: #e0f2fe !important;
}
.firefly-tag {
  margin-right: 5px;
  border-radius: 4px;
  font-weight: 500;
  background: #bae6fd;
  color: #0369a1;
}
.firefly-amount {
  color: #ea580c;
  font-weight: bold;
  font-size: 1.08em;
}

.table-container {
  overflow-x: auto;
  width: 100%;
}

@media (max-width: 768px) {
  .button-col {
    text-align: center;
    margin-top: 16px;
  }
}
</style>
