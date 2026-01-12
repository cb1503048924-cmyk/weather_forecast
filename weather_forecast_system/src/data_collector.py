import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class WeatherDataCollector:
    """从Open-Meteo API采集真实天气数据"""
    
    def __init__(self):
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.location_cache = {}  # 缓存城市坐标
        self.geocoding_cache = {}  # 缓存地理编码结果
        self.baidu_ak = "mY3JUgrCjfYY6NsktCf9HnUlgrR7kqDe"  # 百度地图AK
    
    def get_location(self, city_name):
        """获取城市坐标"""
        city_lower = city_name.lower()
        
        # 首先检查缓存
        if city_lower in self.location_cache:
            return self.location_cache[city_lower]
        
        # 检查地理编码缓存
        if city_lower in self.geocoding_cache:
            return self.geocoding_cache[city_lower]
        
        # 使用百度地图API进行地理编码
        print(f"正在查找 '{city_name}' 的地理位置...")
        
        try:
            # 百度地图地理编码API
            url = "http://api.map.baidu.com/geocoding/v3/"
            params = {
                'address': city_name,
                'output': 'json',
                'ak': self.baidu_ak
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 0 and data.get('result'):
                    result = data['result']
                    location = {
                        'latitude': float(result['location']['lat']),
                        'longitude': float(result['location']['lng'])
                    }
                    # 缓存结果
                    self.location_cache[city_lower] = location
                    self.geocoding_cache[city_lower] = location
                    print(f"成功找到 '{city_name}' 的地理位置: {location['latitude']}, {location['longitude']}")
                    return location
            
            # 如果百度API失败，使用默认坐标（北京）
            print(f"无法找到 '{city_name}' 的地理位置，使用默认坐标（北京）")
            default_location = {
                'latitude': 39.9042,
                'longitude': 116.4074
            }
            self.location_cache[city_lower] = default_location
            return default_location
            
        except Exception as e:
            print(f"地理编码失败: {e}，使用默认坐标（北京）")
            default_location = {
                'latitude': 39.9042,
                'longitude': 116.4074
            }
            self.location_cache[city_lower] = default_location
            return default_location
    
    def reverse_geocoding(self, latitude, longitude):
        """逆地理编码：根据坐标获取地址信息（省份、城市、区县）"""
        print(f"正在对坐标 ({latitude}, {longitude}) 进行逆地理编码...")
        
        try:
            # 百度地图逆地理编码API
            url = "http://api.map.baidu.com/reverse_geocoding/v3/"
            params = {
                'location': f"{latitude},{longitude}",
                'output': 'json',
                'ak': self.baidu_ak,
                'coordtype': 'wgs84'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 0 and data.get('result'):
                    result = data['result']
                    address_component = result.get('addressComponent', {})
                    
                    # 解析省份、城市、区县信息
                    province = address_component.get('province', '')
                    city = address_component.get('city', '')
                    district = address_component.get('district', '')
                    
                    # 如果没有区县，尝试从formatted_address获取
                    formatted_address = result.get('formatted_address', '')
                    if not district and formatted_address:
                        # 尝试从formatted_address中提取区县
                        if '区' in formatted_address:
                            district = formatted_address.split('区')[-1].replace(' ', '')
                        elif '县' in formatted_address:
                            district = formatted_address.split('县')[-1].replace(' ', '')
                    
                    location_info = {
                        'province': province,
                        'city': city,
                        'district': district,
                        'formatted_address': formatted_address
                    }
                    
                    print(f"逆地理编码成功: 省份={province}, 城市={city}, 区县={district}")
                    return location_info
            
            # 如果百度API失败，返回空信息
            print("逆地理编码失败，返回空信息")
            return {
                'province': '',
                'city': '',
                'district': '',
                'formatted_address': ''
            }
            
        except Exception as e:
            print(f"逆地理编码失败: {e}，返回空信息")
            return {
                'province': '',
                'city': '',
                'district': '',
                'formatted_address': ''
            }
    
    def fetch_historical_data(self, city_name, start_date, end_date):
        """
        获取历史天气数据
        
        参数:
            city_name: 城市名称
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
        
        返回:
            DataFrame: 包含历史天气数据
        """
        location = self.get_location(city_name)
        
        params = {
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'start_date': start_date,
            'end_date': end_date,
            'daily': [
                'temperature_2m_mean',
                'temperature_2m_max',
                'temperature_2m_min',
                'relative_humidity_2m_mean',
                'precipitation_sum',
                'precipitation_probability_mean',
                'wind_speed_10m_mean',
                'surface_pressure_mean',
                'weather_code'
            ],
            'timezone': 'Asia/Shanghai'
        }
        
        print(f"正在从Open-Meteo API获取 {city_name} 的历史天气数据...")
        print(f"日期范围: {start_date} 至 {end_date}")
        print(f"坐标: {location['latitude']}, {location['longitude']}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 解析数据
            daily_data = data.get('daily', {})
            
            # 创建DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(daily_data['time']),
                'temperature': daily_data['temperature_2m_mean'],
                'temp_max': daily_data['temperature_2m_max'],
                'temp_min': daily_data['temperature_2m_min'],
                'humidity': daily_data['relative_humidity_2m_mean'],
                'rainfall': daily_data['precipitation_sum'],
                'rain_probability': daily_data['precipitation_probability_mean'],
                'wind_speed': daily_data['wind_speed_10m_mean'],
                'pressure': daily_data['surface_pressure_mean'],
                'weather_code': daily_data['weather_code']
            })
            
            # 添加天气类型
            df['weather_type'] = df['weather_code'].apply(self._weather_code_to_type)
            
            print(f"成功获取 {len(df)} 条历史天气记录")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"获取数据失败: {e}")
            return None
    
    def fetch_forecast_data(self, city_name, days=7):
        """
        获取天气预报数据
        
        参数:
            city_name: 城市名称
            days: 预报天数
        
        返回:
            DataFrame: 包含天气预报数据
        """
        location = self.get_location(city_name)
        
        params = {
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'daily': [
                'temperature_2m_max',
                'temperature_2m_min',
                'relative_humidity_2m_mean',
                'precipitation_sum',
                'precipitation_probability_max',
                'wind_speed_10m_max',
                'surface_pressure_mean',
                'weather_code'
            ],
            'timezone': 'Asia/Shanghai',
            'forecast_days': days
        }
        
        print(f"正在获取 {city_name} 的天气预报数据...")
        
        try:
            response = requests.get(self.forecast_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 解析数据
            daily_data = data.get('daily', {})
            
            # 创建DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(daily_data['time']),
                'temp_max': daily_data['temperature_2m_max'],
                'temp_min': daily_data['temperature_2m_min'],
                'temperature': [(daily_data['temperature_2m_max'][i] + daily_data['temperature_2m_min'][i]) / 2 
                               for i in range(len(daily_data['temperature_2m_max']))],
                'humidity': daily_data['relative_humidity_2m_mean'],
                'rainfall': daily_data['precipitation_sum'],
                'rain_probability': daily_data['precipitation_probability_max'],
                'wind_speed': daily_data['wind_speed_10m_max'],
                'pressure': daily_data['surface_pressure_mean'],
                'weather_code': daily_data['weather_code']
            })
            
            # 添加天气类型
            df['weather_type'] = df['weather_code'].apply(self._weather_code_to_type)
            
            print(f"成功获取 {len(df)} 天天气预报")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"获取预报数据失败: {e}")
            return None
    
    def _weather_code_to_type(self, code):
        """
        将WMO天气代码转换为天气类型
        
        WMO天气代码说明:
        0: 晴
        1, 2, 3: 多云
        45, 48: 雾
        51, 53, 55: 毛毛雨
        56, 57: 冻毛毛雨
        61, 63, 65: 雨
        66, 67: 冻雨
        71, 73, 75: 雪
        77: 雪粒
        80, 81, 82: 阵雨
        85, 86: 阵雪
        95: 雷暴
        96, 99: 雷暴伴冰雹
        """
        if code == 0:
            return 'sunny'
        elif code in [1, 2, 3]:
            return 'cloudy'
        elif code in [45, 48]:
            return 'foggy'
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            return 'rain'
        elif code in [56, 57, 66, 67]:
            return 'freezing_rain'
        elif code in [71, 73, 75, 77, 85, 86]:
            return 'snow'
        elif code in [95, 96, 99]:
            return 'thunderstorm'
        else:
            return 'unknown'
    
    def prepare_training_data(self, city_name, days=365):
        """
        准备训练数据
        
        参数:
            city_name: 城市名称
            days: 获取历史数据的天数
        
        返回:
            DataFrame: 适合训练的天气数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        df = self.fetch_historical_data(city_name, start_date, end_date)
        
        if df is None:
            return None
        
        # 添加日期特征
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['weekday'] = df['date'].dt.weekday  # 0=周一, 6=周日
        df['is_weekend'] = df['weekday'].apply(lambda x: 1 if x in [5, 6] else 0)
        
        # 处理缺失值
        numeric_cols = ['temperature', 'humidity', 'rainfall', 'wind_speed', 'pressure']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean())
        
        return df
    
    def get_city_list(self):
        """获取支持的城市列表"""
        return list(self.location_cache.keys())
    
    def get_cached_cities(self):
        """获取已缓存的城市列表"""
        return list(self.geocoding_cache.keys())

if __name__ == "__main__":
    # 测试数据采集
    collector = WeatherDataCollector()
    
    print("已缓存的城市列表:", collector.get_cached_cities())
    
    # 测试获取任意城市的数据
    test_cities = ['成都', '杭州', '深圳', '武汉', '西安', '青岛']
    
    for city in test_cities:
        print(f"\n{'='*50}")
        print(f"测试城市: {city}")
        print(f"{'='*50}")
        
        df = collector.prepare_training_data(city, days=30)
        
        if df is not None:
            print("\n历史天气数据预览:")
            print(df.head())
            print(f"\n数据形状: {df.shape}")
            print(f"\n天气类型分布:")
            print(df['weather_type'].value_counts())
        else:
            print("获取数据失败")
