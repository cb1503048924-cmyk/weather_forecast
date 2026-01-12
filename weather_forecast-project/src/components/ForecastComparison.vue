<script setup>
import { ref, computed, watch } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const props = defineProps({
  hasData: {
    type: Boolean,
    default: false
  },
  hasTrainedModel: {
    type: Boolean,
    default: false
  },
  initialForecastData: {
    type: Array,
    default: () => []
  },
  initialAiPrediction: {
    type: Object,
    default: () => ({ temperature: [], weatherType: [] })
  }
})

const emit = defineEmits(['forecast-loaded'])

const isLoading = ref(false)
const error = ref('')
const forecastData = ref([])
const aiPrediction = ref({
  temperature: [],
  weatherType: []
})

watch(() => props.initialForecastData, (newData) => {
  if (newData && newData.length > 0) {
    forecastData.value = newData
    console.log('forecastData updated:', forecastData.value)
    console.log('forecastData length:', forecastData.value.length)
  }
}, { immediate: true })

watch(() => props.initialAiPrediction, (newData) => {
  if (newData && newData.temperature) {
    aiPrediction.value = newData
  }
}, { immediate: true })

const hasResults = computed(() => forecastData.value.length > 0)

const dataSource = computed(() => {
  return props.hasTrainedModel ? '真实模型预测' : '模拟数据'
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return dateStr
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch {
    return dateStr
  }
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    }
  },
  scales: {
    y: {
      beginAtZero: false,
      title: {
        display: true,
        text: '温度 (°C)'
      }
    },
    x: {
      title: {
        display: true,
        text: '日期'
      }
    }
  }
}

const compareForecast = async () => {
  if (!props.hasData) {
    error.value = '请先采集数据后再获取预报'
    return
  }
  
  isLoading.value = true
  error.value = ''
  try {
    // 设置请求超时
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch('http://localhost:5000/api/forecast', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `获取预报失败 (${response.status})`)
    }
    
    const data = await response.json()
    
    // 检查返回数据结构
    if (data.official_forecast) {
      forecastData.value = data.official_forecast
      aiPrediction.value = {
        temperature: data.ai_temperature_forecast || [],
        weatherType: data.ai_weather_forecast || []
      }
      
      emit('forecast-loaded', { forecastData: forecastData.value, aiPrediction: aiPrediction.value })
    } else {
      throw new Error('无效的预报数据')
    }
  } catch (err) {
    console.error('预报获取失败:', err)
    if (err.name === 'AbortError') {
      error.value = '获取预报超时，请重试'
    } else {
      error.value = '预报获取失败：' + err.message
    }
    // 保持模拟数据作为后备
    forecastData.value = [
      { date: '2026-01-06', temperature: 2.2, weatherType: 'cloudy', rainProbability: 10 },
      { date: '2026-01-07', temperature: 3.0, weatherType: 'sunny', rainProbability: 5 },
      { date: '2026-01-08', temperature: 1.5, weatherType: 'rain', rainProbability: 70 },
      { date: '2026-01-09', temperature: 0.8, weatherType: 'rain', rainProbability: 85 },
      { date: '2026-01-10', temperature: 2.0, weatherType: 'cloudy', rainProbability: 20 },
      { date: '2026-01-11', temperature: 3.5, weatherType: 'sunny', rainProbability: 0 },
      { date: '2026-01-12', temperature: 4.2, weatherType: 'sunny', rainProbability: 0 }
    ]
    aiPrediction.value = {
      temperature: [2.1, 2.9, 1.7, 1.0, 2.2, 3.3, 4.0],
      weatherType: ['cloudy', 'sunny', 'rain', 'rain', 'cloudy', 'sunny', 'sunny']
    }
  } finally {
    isLoading.value = false
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

const getAiTemperature = (index) => {
  const temp = aiPrediction.value.temperature?.[index]
  return temp !== undefined && temp !== null ? temp.toFixed(1) : '-'
}

const getAiWeatherType = (index) => {
  return aiPrediction.value.weatherType?.[index] || 'unknown'
}

const getRainProbability = (item) => {
  return item.rainProbability ?? item.precipitation_probability_max ?? 0
}

const chartData = computed(() => {
  if (!hasResults.value) {
    return { labels: [], datasets: [] }
  }
  
  const dates = forecastData.value.map(item => formatDate(item.date))
  const officialTemp = forecastData.value.map(item => item.temperature)
  const aiTemp = forecastData.value.map((_, index) => getAiTemperature(index))
  
  return {
    labels: dates,
    datasets: [
      {
        label: '官方预报',
        data: officialTemp,
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        tension: 0.3,
        pointRadius: 6,
        pointHoverRadius: 8
      },
      {
        label: 'AI预测',
        data: aiTemp,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        tension: 0.3,
        pointRadius: 6,
        pointHoverRadius: 8
      }
    ]
  }
})

const avgTemperature = computed(() => {
  if (forecastData.value.length === 0) return '0.0'
  const sum = forecastData.value.reduce((acc, item) => acc + (item.temperature || 0), 0)
  return (sum / forecastData.value.length).toFixed(1)
})

const rainDays = computed(() => {
  return forecastData.value.filter(item => {
    const type = item.weatherType || item.weather_type
    return type === 'rain'
  }).length
})

const sunnyDays = computed(() => {
  return forecastData.value.filter(item => {
    const type = item.weatherType || item.weather_type
    return type === 'sunny'
  }).length
})
</script>

<template>
  <div class="forecast-comparison">
    <div class="section-header">
      <h2>📈 预报对比</h2>
      <p>对比官方天气预报与AI模型预测结果</p>
    </div>

    <div class="action-section">
      <button class="btn btn-primary" @click="compareForecast" :disabled="isLoading || !hasData">
        {{ isLoading ? '获取中...' : '获取预报数据' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="!hasData && !hasResults" class="empty-state">
      <div class="empty-icon">📡</div>
      <h3>等待数据获取</h3>
      <p>请先在"数据采集"页面获取历史天气数据，然后点击"获取预报数据"按钮</p>
    </div>

    <div v-else-if="!hasResults" class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>预报未获取</h3>
      <p>点击"获取预报数据"按钮，获取官方天气预报和AI预测结果</p>
    </div>

    <div v-else class="results-section">
      <div class="data-source-indicator">
        <span class="source-label">数据来源：</span>
        <span class="source-value" :class="props.hasTrainedModel ? 'real-data' : 'mock-data'">
          {{ dataSource }}
        </span>
      </div>
      <div class="chart-section">
        <h3>温度预报对比</h3>
        <div class="chart-container">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>

      <div class="comparison-table">
        <h3>详细预报对比</h3>
        <div class="table-container">
          <table class="forecast-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>官方预报</th>
                <th>AI预测</th>
                <th>降水概率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in forecastData" :key="index">
                <td class="date-cell">{{ formatDate(item.date) }}</td>
                <td class="weather-cell">
                  {{ getWeatherEmoji(item.weatherType || item.weather_type) }}
                  {{ getWeatherTypeName(item.weatherType || item.weather_type) }}
                  | {{ item.temperature?.toFixed(1) || '-' }}°C
                </td>
                <td class="weather-cell">
                  {{ getWeatherEmoji(getAiWeatherType(index)) }}
                  {{ getWeatherTypeName(getAiWeatherType(index)) }}
                  | {{ getAiTemperature(index) }}°C
                </td>
                <td class="rain-cell">
                  {{ getRainProbability(item) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="comparison-summary">
        <h3>预测分析</h3>
        <div class="summary-cards">
          <div class="summary-card">
            <div class="summary-icon">🌡️</div>
            <div class="summary-content">
              <span class="summary-title">平均温度</span>
              <span class="summary-value">{{ avgTemperature }}°C</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">🌧️</div>
            <div class="summary-content">
              <span class="summary-title">降雨天数</span>
              <span class="summary-value">{{ rainDays }}天</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">☀️</div>
            <div class="summary-content">
              <span class="summary-title">晴天数</span>
              <span class="summary-value">{{ sunnyDays }}天</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forecast-comparison {
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

.action-section {
  text-align: center;
  margin-bottom: 30px;
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
}

.error-message {
  background-color: #fed7d7;
  color: #c53030;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.results-section {
  margin-top: 20px;
}

.chart-section {
  margin-bottom: 30px;
}

.chart-section h3 {
  color: #2d3748;
  margin-bottom: 15px;
}

.chart-container {
  height: 350px;
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.comparison-table h3,
.comparison-summary h3 {
  color: #2d3748;
  margin: 20px 0 15px;
}

.table-container {
  overflow-x: auto;
}

.forecast-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  table-layout: fixed;
}

.forecast-table th,
.forecast-table td {
  padding: 12px 15px;
  text-align: center;
  vertical-align: middle;
}

.forecast-table th:nth-child(1),
.forecast-table td:nth-child(1) {
  width: 15%;
  min-width: 100px;
}

.forecast-table th:nth-child(2),
.forecast-table td:nth-child(2) {
  width: 30%;
  min-width: 200px;
}

.forecast-table th:nth-child(3),
.forecast-table td:nth-child(3) {
  width: 30%;
  min-width: 200px;
}

.forecast-table th:nth-child(4),
.forecast-table td:nth-child(4) {
  width: 25%;
  min-width: 100px;
}

.forecast-table th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 2px solid #e2e8f0;
}

.forecast-table tbody tr {
  border-bottom: 1px solid #e2e8f0;
}

.forecast-table tbody tr:last-child {
  border-bottom: none;
}

.forecast-table tr:hover {
  background-color: #f9fafb;
}

.date-cell {
  font-weight: 500;
  color: #2d3748;
  text-align: left;
  border-right: 1px solid #e2e8f0;
  white-space: nowrap;
}

.weather-cell {
  padding: 15px 20px;
  border-right: 1px solid #e2e8f0;
  text-align: center;
  white-space: nowrap;
}

.weather-info {
  display: inline-block;
  margin-right: 10px;
}

.weather-emoji {
  font-size: 1.2rem;
  margin-right: 5px;
}

.weather-name {
  color: #4a5568;
  font-weight: 500;
}

.vertical-line {
  color: #cbd5e1;
  font-weight: 300;
  margin: 0 10px;
}

.temperature {
  font-weight: 600;
  color: #667eea;
}

.rain-cell {
  text-align: center;
  padding: 15px 20px;
  border-right: none;
  white-space: nowrap;
}

.rain-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #e2e8f0;
  color: #4a5568;
  font-weight: 600;
  font-size: 0.9rem;
  border: 2px solid #cbd5e1;
}

.rain-indicator.high-rain {
  background-color: #fed7d7;
  color: #c53030;
  border-color: #feb2b2;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
}

.summary-icon {
  font-size: 2rem;
}

.summary-content {
  display: flex;
  flex-direction: column;
}

.summary-title {
  font-size: 0.9rem;
  opacity: 0.9;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: bold;
}

/* 数据来源指示器样式 */
.data-source-indicator {
  background-color: #f7fafc;
  padding: 10px 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
}

.source-label {
  color: #718096;
  font-weight: 500;
}

.source-value {
  padding: 3px 12px;
  border-radius: 20px;
  font-weight: bold;
}

.source-value.real-data {
  background-color: #c6f6d5;
  color: #22543d;
}

.source-value.mock-data {
  background-color: #e6fffa;
  color: #2c7a7b;
}
</style>
