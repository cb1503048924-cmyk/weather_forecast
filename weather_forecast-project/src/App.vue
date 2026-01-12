<script setup>
import { ref, computed } from 'vue'
import DataCollection from './components/DataCollection.vue'
import ModelTraining from './components/ModelTraining.vue'
import ForecastComparison from './components/ForecastComparison.vue'
import Advice from './components/Advice.vue'
import './style.css'

const activeTab = ref('data-collection')
const hasData = ref(false)
const hasTrainedModel = ref(false)
const forecastData = ref([])
const aiPrediction = ref({ temperature: [], weatherType: [] })
const historicalData = ref([])
const weatherDistribution = ref([])
const modelResults = ref(null)

const tabs = [
  { id: 'data-collection', label: '📊 数据采集' },
  { id: 'model-training', label: '🤖 模型训练' },
  { id: 'forecast-comparison', label: '📈 预报对比' },
  { id: 'advice', label: '💡 生活建议' }
]

const handleDataCollected = (params) => {
  hasData.value = true
  historicalData.value = params.historicalData || []
  weatherDistribution.value = params.distribution || []
  console.log('数据采集完成:', params)
}

const handleTrainModel = (params) => {
  modelResults.value = params.modelResults
  hasTrainedModel.value = true
  console.log('模型训练完成:', params)
}

const handleForecastLoaded = (params) => {
  forecastData.value = params.forecastData || []
  aiPrediction.value = params.aiPrediction || { temperature: [], weatherType: [] }
  console.log('预报数据加载完成')
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>🌤️ 智能天气预报与建议系统</h1>
    </header>

    <main class="main-content">
      <nav class="nav-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <div class="tab-content-wrapper">
        <div v-show="activeTab === 'data-collection'">
          <DataCollection
            @data-collected="handleDataCollected"
          />
        </div>

        <div v-show="activeTab === 'model-training'">
          <ModelTraining
            :hasData="hasData"
            :initialHistoricalData="historicalData"
            :initialModelResults="modelResults"
            @train-model="handleTrainModel"
          />
        </div>

        <div v-show="activeTab === 'forecast-comparison'">
          <ForecastComparison
            :hasData="hasData"
            :hasTrainedModel="hasTrainedModel"
            :initialForecastData="forecastData"
            :initialAiPrediction="aiPrediction"
            @forecast-loaded="handleForecastLoaded"
          />
        </div>

        <div v-show="activeTab === 'advice'">
          <Advice
            :forecastData="forecastData"
            :aiPrediction="aiPrediction"
            :hasTrainedModel="hasTrainedModel"
          />
        </div>
      </div>
    </main>

    <footer class="app-footer">
      <p>&copy; 2026 智能天气预报与建议系统</p>
    </footer>
  </div>
</template>

<style>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.nav-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background-color: #f7fafc;
  color: #4a5568;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background-color: #edf2f7;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.tab-content-wrapper {
  min-height: 400px;
}

.app-footer {
  background-color: #2d3748;
  color: white;
  padding: 15px;
  text-align: center;
  margin-top: auto;
}

.app-footer p {
  margin: 0;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.4rem;
  }

  .nav-tabs {
    gap: 5px;
  }

  .tab-btn {
    padding: 10px 15px;
    font-size: 0.9rem;
  }
}
</style>
