import pandas as pd
import numpy as np
from datetime import datetime

class WeatherDataProcessor:
    def __init__(self):
        self.data = None
        self.processed_data = None
    
    def load_data(self, file_path):
        """加载CSV格式的天气数据"""
        try:
            self.data = pd.read_csv(file_path)
            print(f"成功加载数据，共 {len(self.data)} 行")
            return self.data
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None
    
    def preprocess_data(self):
        """数据预处理，包括处理缺失值和特征工程"""
        if self.data is None:
            print("请先加载数据")
            return None
        
        # 创建副本避免修改原始数据
        df = self.data.copy()
        
        # 1. 处理日期列
        df['date'] = pd.to_datetime(df['date'])
        
        # 2. 提取日期特征
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['weekday'] = df['date'].dt.weekday  # 0=周一, 6=周日
        df['is_weekend'] = df['weekday'].apply(lambda x: 1 if x in [5, 6] else 0)
        
        # 3. 处理缺失值
        # 数值型特征使用均值填充
        numeric_cols = ['temperature', 'humidity', 'rainfall', 'wind_speed', 'pressure']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean())
        
        # 4. 处理天气类型（目标变量）
        if 'weather_type' in df.columns:
            # 调试信息：打印原始天气类型
            print(f"原始天气类型的唯一值: {df['weather_type'].unique()}")
            
            # 将天气类型直接使用，不进行映射（因为示例数据中的天气类型已经是英文简写）
            # 对于真实数据，可以使用下面的映射
            # weather_mapping = {
            #     '晴': 'sunny', '晴间多云': 'partly_cloudy', '多云': 'cloudy',
            #     '阴': 'overcast', '小雨': 'rain', '中雨': 'rain', '大雨': 'rain',
            #     '暴雨': 'rain', '雷阵雨': 'thunderstorm', '雪': 'snow'
            # }
            # df['weather_type'] = df['weather_type'].map(weather_mapping).fillna('unknown')
            
            # 直接使用原始天气类型，不进行映射
            df['weather_type'] = df['weather_type'].fillna('unknown')
            
            # 调试信息：打印处理后的天气类型
            print(f"处理后的天气类型的唯一值: {df['weather_type'].unique()}")
        
        # 5. 提取温度特征（最高温、最低温、平均温）
        if 'temp_max' in df.columns and 'temp_min' in df.columns:
            df['temperature'] = (df['temp_max'] + df['temp_min']) / 2
        
        self.processed_data = df
        print("数据预处理完成")
        return df
    
    def save_processed_data(self, file_path):
        """保存处理后的数据"""
        if self.processed_data is not None:
            self.processed_data.to_csv(file_path, index=False)
            print(f"处理后的数据已保存到 {file_path}")
        else:
            print("没有处理后的数据可以保存")
    
    def get_feature_columns(self, target_type='temperature'):
        """获取特征列，根据目标类型返回不同的特征集"""
        if self.processed_data is None:
            print("请先处理数据")
            return None
        
        # 基础特征
        base_features = ['year', 'month', 'day', 'weekday', 'is_weekend']
        
        if target_type == 'temperature':
            # 温度预测特征
            return base_features + ['temperature', 'humidity', 'pressure', 'wind_speed']
        elif target_type == 'weather_type':
            # 天气类型预测特征
            return base_features + ['temperature', 'humidity', 'rainfall', 'wind_speed', 'pressure']
        else:
            return base_features
    
    def split_data(self, target_column, test_size=0.2):
        """划分训练集和测试集"""
        if self.processed_data is None:
            print("请先处理数据")
            return None, None, None, None
        
        # 确保数据按日期排序
        df = self.processed_data.sort_values('date')
        
        # 划分训练集和测试集（时间序列数据不能随机划分）
        split_idx = int(len(df) * (1 - test_size))
        train_data = df.iloc[:split_idx]
        test_data = df.iloc[split_idx:]
        
        # 获取特征和目标
        X_train = train_data[self.get_feature_columns(target_column)]
        y_train = train_data[target_column]
        X_test = test_data[self.get_feature_columns(target_column)]
        y_test = test_data[target_column]
        
        return X_train, y_train, X_test, y_test
