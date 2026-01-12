import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class TemperatureARIMA:
    def __init__(self):
        self.model = None
        self.fitted_model = None
        self.train_data = None
        self.test_data = None
    
    def train_test_split(self, data, test_size=0.2):
        """划分训练集和测试集（时间序列）"""
        split_idx = int(len(data) * (1 - test_size))
        self.train_data = data[:split_idx]
        self.test_data = data[split_idx:]
        return self.train_data, self.test_data
    
    def check_stationarity(self, time_series):
        """检查时间序列的平稳性"""
        result = adfuller(time_series)
        print('ADF Statistic:', result[0])
        print('p-value:', result[1])
        print('Critical Values:')
        for key, value in result[4].items():
            print(f'\t{key}: {value}')
        return result[1] <= 0.05
    
    def difference_series(self, time_series, lag=1):
        """对时间序列进行差分"""
        return time_series.diff(lag).dropna()
    
    def find_optimal_order(self, time_series, max_p=5, max_d=2, max_q=5):
        """寻找ARIMA模型的最优阶数"""
        import warnings
        warnings.filterwarnings('ignore')
        
        best_aic = float('inf')
        best_order = (0, 0, 0)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(time_series, order=(p, d, q))
                        fitted = model.fit()
                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_order = (p, d, q)
                    except:
                        continue
        
        print(f'最优ARIMA阶数: {best_order}, AIC: {best_aic:.2f}')
        return best_order
    
    def train(self, time_series, order=(1, 1, 1)):
        """训练ARIMA模型"""
        try:
            self.model = ARIMA(time_series, order=order)
            self.fitted_model = self.model.fit()
            print('模型训练完成')
            return self.fitted_model
        except Exception as e:
            print(f'ARIMA模型训练失败: {e}')
            return None
    
    def forecast(self, steps=7):
        """预测未来steps步的温度"""
        if self.fitted_model is None:
            print('请先训练模型')
            return None
        
        forecast_result = self.fitted_model.forecast(steps=steps)
        return forecast_result
    
    def evaluate_model(self, actual, predicted):
        """评估模型性能"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)
        
        print(f'MAE: {mae:.2f}')
        print(f'MSE: {mse:.2f}')
        print(f'RMSE: {rmse:.2f}')
        
        return {'mae': mae, 'mse': mse, 'rmse': rmse}
    
    def plot_forecast(self, time_series, forecast_result, title='Temperature Forecast'):
        """绘制预测结果"""
        plt.figure(figsize=(12, 6))
        plt.plot(time_series, label='Historical Temperature')
        plt.plot(pd.date_range(start=time_series.index[-1] + pd.Timedelta(days=1), periods=len(forecast_result), freq='D'),
                 forecast_result, label='Forecasted Temperature', color='red')
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Temperature (°C)')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('D:/Trae/trae_project/weather_forecast/weather_forecast_system/results/temperature_forecast.png')
        plt.close()
        print('预测图已保存到 results/temperature_forecast.png')
