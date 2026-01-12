<script setup>
import { computed } from 'vue'

const props = defineProps({
  forecastData: {
    type: Array,
    default: () => []
  },
  aiPrediction: {
    type: Object,
    default: () => ({ temperature: [], weatherType: [] })
  },
  hasTrainedModel: {
    type: Boolean,
    default: false
  }
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

const getWeekday = (dateStr) => {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleDateString('zh-CN', { weekday: 'long' })
  } catch {
    return ''
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

const getClothingAdvice = (temperature) => {
  if (temperature < 5) {
    return {
      level: '极寒',
      advice: '穿厚羽绒服、毛衣、厚裤子，戴帽子、手套、围巾',
      icon: '🧥'
    }
  } else if (temperature < 12) {
    return {
      level: '寒冷',
      advice: '穿厚外套、毛衣、长裤',
      icon: '🧥'
    }
  } else if (temperature < 18) {
    return {
      level: '凉爽',
      advice: '穿薄外套、长袖衬衫、长裤',
      icon: '👔'
    }
  } else if (temperature < 25) {
    return {
      level: '温和',
      advice: '穿T恤、衬衫、薄长裤或牛仔裤',
      icon: '👕'
    }
  } else if (temperature < 30) {
    return {
      level: '温暖',
      advice: '穿短袖、短裤、裙子等清凉衣物',
      icon: '👕'
    }
  } else {
    return {
      level: '炎热',
      advice: '穿透气轻薄的衣物，注意防晒',
      icon: '🧢'
    }
  }
}

const getTravelAdvice = (weatherType) => {
  if (weatherType === 'rain' || weatherType === 'thunderstorm') {
    return {
      level: '注意',
      advice: '有雨，建议携带雨伞，尽量避免户外活动',
      icon: '🌂'
    }
  } else if (weatherType === 'snow') {
    return {
      level: '注意',
      advice: '有雪，注意防滑，穿保暖衣物',
      icon: '⛸️'
    }
  } else if (weatherType === 'foggy') {
    return {
      level: '谨慎',
      advice: '有雾，能见度低，注意交通安全，谨慎驾驶',
      icon: '🌫️'
    }
  } else if (weatherType === 'sunny' || weatherType === 'partly_cloudy') {
    return {
      level: '适宜',
      advice: '天气较好，适合出行，注意防晒',
      icon: '🚗'
    }
  } else {
    return {
      level: '正常',
      advice: '天气一般，可以正常出行',
      icon: '🚌'
    }
  }
}

const getActivityAdvice = (weatherType, temperature) => {
  if (weatherType === 'rain' || weatherType === 'thunderstorm') {
    return {
      level: '室内',
      advice: ['适合室内活动，如阅读、看电影', '避免外出'],
      icon: '🏠'
    }
  } else if (weatherType === 'snow') {
    return {
      level: '冬季',
      advice: ['适合滑雪、堆雪人等冬季活动', '注意保暖和防滑'],
      icon: '⛷️'
    }
  } else if (weatherType === 'foggy') {
    return {
      level: '谨慎',
      advice: ['能见度低，建议减少户外活动', '如需外出，注意交通安全'],
      icon: '�️'
    }
  } else if (weatherType === 'sunny') {
    if (temperature > 25) {
      return {
        level: '户外',
        advice: ['适合户外运动，但避免正午暴晒', '建议使用防晒霜、戴遮阳帽'],
        icon: '🏃'
      }
    } else {
      return {
        level: '户外',
        advice: ['适合户外运动、野餐、散步', '建议使用防晒霜、戴遮阳帽'],
        icon: '🏃'
      }
    }
  } else {
    return {
      level: '户外',
      advice: ['适合大多数户外活动', '注意适当防晒'],
      icon: '🚴'
    }
  }
}

const getWeatherType = (index) => {
  return props.forecastData[index]?.weatherType || 
         props.forecastData[index]?.weather_type || 
         props.aiPrediction?.weatherType?.[index] || 
         'unknown'
}

const getTemperature = (index) => {
  return props.forecastData[index]?.temperature || 0
}

const dataSource = computed(() => {
  return props.hasTrainedModel ? '真实模型预测' : '模拟数据'
})
</script>

<template>
  <div class="advice-section">
    <div class="section-header">
      <h2>💡 生活建议</h2>
      <p>根据天气预报为您提供个性化的生活建议</p>
    </div>

    <div v-if="forecastData.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>等待预报数据</h3>
      <p>请先在"预报对比"页面获取天气预报数据，然后查看每日生活建议</p>
    </div>

    <div v-else class="advice-list">
      <div class="data-source-indicator">
        <span class="source-label">数据来源：</span>
        <span class="source-value" :class="props.hasTrainedModel ? 'real-data' : 'mock-data'">
          {{ dataSource }}
        </span>
      </div>
      <div v-for="(item, index) in forecastData" :key="index" class="advice-card">
        <div class="card-header">
          <div class="date-info">
            <span class="date">{{ formatDate(item.date) }}</span>
            <span class="weekday">{{ getWeekday(item.date) }}</span>
          </div>
          <div class="weather-info">
            <span class="weather-emoji">{{ getWeatherEmoji(getWeatherType(index)) }}</span>
            <span class="weather-name">{{ getWeatherTypeName(getWeatherType(index)) }}</span>
            <span class="temperature">{{ getTemperature(index).toFixed(1) }}°C</span>
          </div>
        </div>

        <div class="card-content">
          <div class="advice-item clothing">
            <div class="advice-icon">👔</div>
            <div class="advice-details">
              <h4>穿衣建议</h4>
              <p class="advice-text">{{ getClothingAdvice(getTemperature(index)).advice }}</p>
              <span class="advice-level">{{ getClothingAdvice(getTemperature(index)).level }}</span>
            </div>
          </div>

          <div class="advice-item travel">
            <div class="advice-icon">🚗</div>
            <div class="advice-details">
              <h4>出行建议</h4>
              <p class="advice-text">{{ getTravelAdvice(getWeatherType(index)).advice }}</p>
              <span class="advice-level">{{ getTravelAdvice(getWeatherType(index)).level }}</span>
            </div>
          </div>

          <div class="advice-item activity">
            <div class="advice-icon">🏃</div>
            <div class="advice-details">
              <h4>活动建议</h4>
              <ul class="activity-list">
                <li v-for="(advice, i) in getActivityAdvice(getWeatherType(index), getTemperature(index)).advice" :key="i">
                  {{ advice }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.advice-section {
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

.advice-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.advice-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.advice-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.date-info {
  display: flex;
  flex-direction: column;
}

.date {
  font-size: 1.3rem;
  font-weight: bold;
}

.weekday {
  font-size: 0.9rem;
  opacity: 0.9;
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weather-emoji {
  font-size: 2rem;
}

.weather-name {
  font-size: 1.1rem;
  font-weight: 500;
}

.temperature {
  font-size: 1.5rem;
  font-weight: bold;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 5px 15px;
  border-radius: 20px;
}

.card-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.advice-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background-color: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.advice-item.travel {
  border-left-color: #48bb78;
}

.advice-item.activity {
  border-left-color: #ed8936;
}

.advice-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
}

.advice-details {
  flex: 1;
}

.advice-details h4 {
  color: #2d3748;
  margin-bottom: 8px;
  font-size: 1rem;
}

.advice-text {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 8px;
}

.advice-level {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: #e2e8f0;
  color: #4a5568;
}

.activity-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.activity-list li {
  padding: 5px 0;
  color: #4a5568;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.activity-list li::before {
  content: '•';
  color: #667eea;
  font-weight: bold;
}

@media (max-width: 600px) {
  .card-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .weather-info {
    flex-wrap: wrap;
    justify-content: center;
  }
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
