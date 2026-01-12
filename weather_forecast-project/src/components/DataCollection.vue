<script setup>
import { ref, reactive, computed, onMounted, watch ,nextTick} from 'vue'

const props = defineProps({
  initialData: {
    type: Array,
    default: () => []
  },
  initialDistribution: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['data-collected'])

/* ===== 状态 ===== */
const isLoading = ref(false)
const error = ref('')
const isLocating = ref(false)
const currentLocation = ref('')

const selectedProvince = ref('')
const selectedCity = ref('')
const selectedDistrict = ref('')

const provinces = ref([])
const cities = ref([])
const districts = ref([])

/* ===== 初始化 ===== */
onMounted(loadProvinces)

/* ===== 加载省市区 ===== */
async function loadProvinces() {
  const res = await fetch('http://localhost:5000/api/region/provinces')
  provinces.value = await res.json()
}

watch(selectedProvince, async (adcode) => {
  selectedCity.value = ''
  selectedDistrict.value = ''
  cities.value = []
  districts.value = []

  if (!adcode) return

  const res = await fetch(
    `http://localhost:5000/api/region/cities?adcode=${adcode}`
  )
  cities.value = await res.json()
})

watch(selectedCity, async (adcode) => {
  selectedDistrict.value = ''
  districts.value = []

  if (!adcode) return

  const res = await fetch(
    `http://localhost:5000/api/region/districts?adcode=${adcode}`
  )
  districts.value = await res.json()
})

const getProvinceName = () => {
  return provinces.value.find(p => p.adcode === selectedProvince.value)?.name || ''
}

const getCityName = () => {
  return cities.value.find(c => c.adcode === selectedCity.value)?.name || ''
}

const getDistrictName = () => {
  return districts.value.find(d => d.adcode === selectedDistrict.value)?.name || ''
}

/* ===== 工具：通过 name 找 adcode ===== */
const findByName = (list, name) => {
  return list.find(item => item.name === name)
}

/* ===== 重庆显示名 ===== */
const displayCityName = (city) => {
  if (city.adcode === '500100') return '重庆市（市辖区）'
  if (city.adcode === '500200') return '重庆市（县域）'
  return city.name
}

/* ===== 表单 ===== */
const collectionForm = reactive({
  city: '',
  days: 30
})

const historicalData = ref([])
const weatherTypeDistribution = ref([])

const hasData = computed(() => historicalData.value.length > 0)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return dateStr
    const year = date.getFullYear()
    const month = String(date.getMonth() +1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch {
    return dateStr
  }
}

const getWeatherTypeName = (type) => {
  const mapping = {
    sunny: '晴天',
    cloudy: '多云',
    rain: '雨天',
    snow: '雪天',
    foggy: '雾天',
    thunderstorm: '雷暴',
    freezing_rain: '冻雨',
    unknown: '未知'
  }
  return mapping[type] || type || '-'
}

const getWeatherEmoji = (type) => {
  const mapping = {
    sunny: '☀️',
    cloudy: '☁️',
    rain: '🌧️',
    snow: '❄️',
    foggy: '🌫️',
    thunderstorm: '⛈️',
    freezing_rain: '🧊',
    unknown: '❓'
  }
  return mapping[type] || '❓'
}

const collectData = async () => {
  if (!selectedProvince.value || !selectedCity.value) {
    error.value = '请选择省份和城市'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  const provinceName = getProvinceName()
  const cityName = getCityName()
  const districtName = getDistrictName()

  let locationName = ''

  if (districtName) {
    locationName = `${provinceName}${cityName}${districtName}`
  } else if (cityName) {
    locationName = `${provinceName}${cityName}`
  } else if (provinceName) {
    locationName = provinceName
  }
  
  if (!locationName) {
    error.value = '请选择省份、城市或区县'
    isLoading.value = false
    return
  }
  
  collectionForm.city = locationName
  
  console.log('开始采集数据:', { 
    location: locationName, 
    days: collectionForm.days, 
    selectedProvince: selectedProvince.value, 
    selectedCity: selectedCity.value, 
    selectedDistrict: selectedDistrict.value
  })
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
      error.value = '数据采集超时，请检查网络连接或重试'
    }, 30000)
    
    const response = await fetch('http://localhost:5000/api/collect-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        city: locationName,
        days: collectionForm.days
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    console.log('响应状态:', response.status, response.statusText)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('错误响应:', errorData)
      throw new Error(errorData.error || `数据采集失败 (${response.status})`)
    }
    
    const data = await response.json()
    console.log('响应数据:', data)
    
    if (data.historical_data && data.weather_distribution) {
      historicalData.value = data.historical_data
      weatherTypeDistribution.value = data.weather_distribution
      
      emit('data-collected', {
        city: locationName,
        days: collectionForm.days,
        historicalData: historicalData.value,
        distribution: weatherTypeDistribution.value
      })
    } else {
      throw new Error('无效的数据采集结果')
    }
  } catch (err) {
    console.error('数据采集失败:', err)
    if (err.name === 'AbortError') {
      error.value = '数据采集超时，请检查网络连接或重试'
    } else {
      error.value = '数据采集失败：' + err.message
    }
  } finally {
    isLoading.value = false
  }
}

/* ===== 定位功能（⭐重点修改） ===== */
const locateCurrentPosition = async () => {
  if (!navigator.geolocation) {
    error.value = '您的浏览器不支持地理定位功能'
    return
  }

  isLocating.value = true
  error.value = ''

  try {
    // 1️⃣ 获取 GPS
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        resolve,
        reject,
        { timeout: 10000, enableHighAccuracy: true }
      )
    })
    const { latitude, longitude } = position.coords

    // 2️⃣ 调用后端逆地理编码
    const response = await fetch('http://localhost:5000/api/reverse-geocoding', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude })
    })
    const data = await response.json()

    const provinceName = data.province || data.location_info?.province
    const cityName = data.city || data.location_info?.city
    const districtName = data.district || data.location_info?.district

    currentLocation.value = `${provinceName}${cityName}${districtName || ''}`

    // 3️⃣ 设置省份
    const provinceItem = findByName(provinces.value, provinceName)
    if (!provinceItem) {
      error.value = `定位成功，但未匹配省份：${provinceName}`
      return
    }
    selectedProvince.value = provinceItem.adcode

    // 4️⃣ 等待城市列表加载完成
    await waitUntil(() => cities.value.length > 0)

    let cityItem = null
    if (provinceName === cityName && provinceName === '重庆市') {
      // 重庆市特殊处理：市辖区 / 县域
      cityItem = cities.value[0] || null
    } else {
      cityItem = findByName(cities.value, cityName)
    }

    if (!cityItem) {
      error.value = `定位成功，但未匹配城市：${cityName}`
      return
    }
    selectedCity.value = cityItem.adcode

    // 5️⃣ 等待区县列表加载完成
    await waitUntil(() => districts.value.length > 0 || !districtName)

    if (districtName) {
      const districtItem = findByName(districts.value, districtName)
      if (districtItem) selectedDistrict.value = districtItem.adcode
    }

  } catch (err) {
    console.error(err)
    error.value = '定位失败，请手动选择城市'
  } finally {
    isLocating.value = false
  }
}

/* ===== 工具函数：等待条件成立 ===== */
function waitUntil(conditionFn, interval = 100, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const timer = setInterval(() => {
      if (conditionFn()) {
        clearInterval(timer)
        resolve()
      } else if (Date.now() - start > timeout) {
        clearInterval(timer)
        resolve() // 超时也 resolve，避免卡住
      }
    }, interval)
  })
}

</script>

<template>
  <div class="data-collection">
    <div class="section-header">
      <h2>📊 数据采集</h2>
      <p>从Open-Meteo API获取真实天气数据</p>
    </div>

    <div class="form-section">
      <form class="collection-form" @submit.prevent="collectData">
        <div class="location-section">
          <button type="button" class="btn btn-location" @click="locateCurrentPosition" :disabled="isLocating">
            {{ isLocating ? '定位中...' : '📍 我的位置' }}
          </button>
          <span v-if="currentLocation" class="current-location">
            当前位置：{{ currentLocation }}
          </span>
        </div>
        
        <div class="area-selector">
          <select v-model="selectedProvince" class="area-select">
            <option value="">请选择省份</option>
            <option v-for="p in provinces" :key="p.adcode" :value="p.adcode">
              {{ p.name }}
            </option>
          </select>

          <select v-model="selectedCity" :disabled="!selectedProvince" class="area-select">
            <option value="">请选择城市</option>
            <option v-for="c in cities" :key="c.adcode" :value="c.adcode">
              {{displayCityName(c)}}
            </option>
          </select>

          <select v-model="selectedDistrict" :disabled="!selectedCity" class="area-select">
            <option value="">请选择区县</option>
            <option v-for="d in districts" :key="d.adcode" :value="d.adcode">
              {{ d.name }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="days">历史数据天数</label>
          <input
            type="number"
            id="days"
            v-model.number="collectionForm.days"
            min="8"
            max="365"
          >
        </div>
        <button type="submit" class="btn btn-primary" :disabled="isLoading">
          {{ isLoading ? '采集中...' : '开始采集数据' }}
        </button>
      </form>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="!hasData" class="empty-state">
      <div class="empty-icon">📡</div>
      <h3>等待数据采集</h3>
      <p>请选择省份、城市和区县，或使用定位功能获取当前位置，然后点击"开始采集数据"按钮</p>
      <ul class="feature-list">
        <li>支持全国省市区三级联动选择</li>
        <li>支持地理定位，自动获取所在城市</li>
        <li>数据来源于Open-Meteo免费天气API</li>
        <li>可获取最多365天的历史天气数据</li>
      </ul>
    </div>

    <div v-else class="results-section">
      <div class="data-summary">
        <div class="summary-card">
          <span class="summary-value">{{ historicalData.length }}</span>
          <span class="summary-label">数据记录</span>
        </div>
        <div class="summary-card">
          <span class="summary-value">{{ weatherTypeDistribution.length }}</span>
          <span class="summary-label">天气类型</span>
        </div>
      </div>
      <div class="data-preview">
        <h3>历史数据预览</h3>
        <div class="data-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>天气类型</th>
                <th>平均温度 (°C)</th>
                <th>最高温度 (°C)</th>
                <th>最低温度 (°C)</th>
                <th>湿度 (%)</th>
                <th>降雨量 (mm)</th>
                <th>风速 (m/s)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in historicalData.slice(0, 10)" :key="index">
                <td>{{ formatDate(item.date) }}</td>
                <td>
                  <span class="weather-type-cell">
                    <span class="weather-emoji">{{ getWeatherEmoji(item.weather_type) }}</span>
                    <span>{{ getWeatherTypeName(item.weather_type) }}</span>
                  </span>
                </td>
                <td>{{ item.temperature?.toFixed(1) || '-' }}</td>
                <td>{{ item.temp_max?.toFixed(1) || '-' }}</td>
                <td>{{ item.temp_min?.toFixed(1) || '-' }}</td>
                <td>{{ item.humidity?.toFixed(1) || '-' }}</td>
                <td>{{ item.rainfall?.toFixed(1) || '-' }}</td>
                <td>{{ item.wind_speed?.toFixed(1) || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="historicalData.length > 10" class="more-data-hint">
            还有 {{ historicalData.length - 10 }} 条数据...
          </p>
        </div>
      </div>

      <div class="chart-section">
        <h3>天气类型分布</h3>
        <div class="chart-container">
          <div v-if="weatherTypeDistribution.length > 0" class="distribution-grid">
            <div
              v-for="(item, index) in weatherTypeDistribution"
              :key="index"
              class="distribution-item"
            >
              <span class="type-name">{{ item.name }}</span>
              <div class="type-bar-container">
                <div
                  class="type-bar"
                  :style="{ width: (item.value / Math.max(...weatherTypeDistribution.map(d => d.value)) * 100) + '%' }"
                ></div>
              </div>
              <span class="type-count">{{ item.value }}天</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-collection {
  padding: 20px;
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

.section-header h2 {
  color: #2d3748;
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.section-header p {
  color: #718096;
}

.form-section {
  background-color: #f7fafc;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.collection-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.location-section {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 8px;
}

.btn-location {
  flex: 1;
  background: linear-gradient(135deg, #48bb78 0%, #37b6d6 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-location:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(72, 187, 120, 0.2);
}

.btn-location:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.current-location {
  flex: 1;
  color: #22543d;
  font-weight: 500;
  font-size: 0.9rem;
  padding: 12px 20px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid #48bb78;
}

.area-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.area-select {
  flex: 1;
  padding: 10px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.area-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 500;
  color: #4a5568;
}

.form-group input {
  padding: 10px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background-color: #f7fafc;
  border-radius: 8px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #2d3748;
  margin-bottom: 10px;
}

.empty-state p {
  color: #718096;
  margin-bottom: 20px;
}

.feature-list {
  list-style: none;
  text-align: left;
  max-width: 400px;
  margin: 0 auto;
}

.feature-list li {
  padding: 8px 0;
  color: #4a5568;
  display: flex;
  align-items: center;
  gap: 10px;
}

.feature-list li::before {
  content: '✓';
  color: #48bb78;
  font-weight: bold;
}

.error-message {
  background-color: #fed7d7;
  color: #c53030;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.data-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.summary-value {
  display: block;
  font-size: 2rem;
  font-weight: bold;
}

.summary-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.results-section h3 {
  color: #2d3748;
  margin: 20px 0 15px;
  font-size: 1.25rem;
}

.data-table-container {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.data-table th,
.data-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.data-table th {
  background-color: #f7fafc;
  font-weight: 600;
  color: #4a5568;
}

.data-table tr:hover {
  background-color: #f7fafc;
}

.more-data-hint {
  text-align: center;
  color: #718096;
  padding: 10px;
  font-style: italic;
}

.chart-section {
  margin-top: 30px;
}

.chart-section h3 {
  color: #2d3748;
  margin-bottom: 15px;
}

.chart-container {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.distribution-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-item {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: 10px;
}

.type-name {
  font-weight: 500;
  color: #4a5568;
}

.type-bar-container {
  background-color: #e2e8f0;
  border-radius: 4px;
  height: 20px;
  overflow: hidden;
}

.type-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.type-count {
  color: #718096;
  font-size: 0.9rem;
}

.weather-type-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.weather-emoji {
  font-size: 1.2em;
}
</style>