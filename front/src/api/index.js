import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 100000
})

export default {
  parseTransactions(text) {
    return api.post('/parse', text, {
      headers: {
        'Content-Type': 'text/plain'
      }
    }).then(res => res.data)
  },
  
  recordTransactions(transactions) {
    return api.post('/record', transactions)
  },
  
  getTransactions() {
    return api.get('/transactions').then(res => res.data)
  },
  
  getAccounts() {
    return api.get('/accounts').then(res => res.data)
  },
  
  getDefaultAccount() {
    return api.get('/default_account').then(res => res.data)
  },
  
  updateDefaultAccount(data) {
    return api.post('/default', data)
  }
}
