class WeatherAdviceEngine:
    def __init__(self):
        # 穿衣建议规则
        self.clothing_rules = {
            'temperature': {
                'very_cold': {'range': (-float('inf'), 5), 'advice': '穿厚羽绒服、毛衣、厚裤子，戴帽子、手套、围巾'},
                'cold': {'range': (5, 12), 'advice': '穿厚外套、毛衣、长裤'},
                'cool': {'range': (12, 18), 'advice': '穿薄外套、长袖衬衫、长裤'},
                'mild': {'range': (18, 25), 'advice': '穿T恤、衬衫、薄长裤或牛仔裤'},
                'warm': {'range': (25, 30), 'advice': '穿短袖、短裤、裙子等清凉衣物'},
                'hot': {'range': (30, float('inf')), 'advice': '穿透气轻薄的衣物，注意防晒'}
            }
        }
        
        # 出行建议规则
        self.travel_rules = {
            'weather_type': {
                'sunny': '天气晴朗，适合户外活动，注意防晒',
                'partly_cloudy': '天气较好，适合出行',
                'cloudy': '天气一般，可以正常出行',
                'overcast': '天气阴沉，建议携带雨具',
                'rain': '有雨，建议携带雨伞，尽量避免户外活动',
                'thunderstorm': '有雷雨，不建议外出，注意安全',
                'snow': '有雪，注意防滑，穿保暖衣物'
            }
        }
        
        # 活动建议规则
        self.activity_rules = {
            'weather_type': {
                'sunny': ['适合户外运动、野餐、散步', '建议使用防晒霜、戴遮阳帽'],
                'partly_cloudy': ['适合大多数户外活动', '注意适当防晒'],
                'cloudy': ['适合户外活动，但可能有变化'],
                'overcast': ['适合室内活动或短途出行'],
                'rain': ['适合室内活动，如阅读、看电影', '避免外出'],
                'thunderstorm': ['建议待在室内，远离窗户和电器'],
                'snow': ['适合滑雪、堆雪人等冬季活动', '注意保暖和防滑']
            }
        }
    
    def get_clothing_advice(self, temperature):
        """根据温度获取穿衣建议"""
        for temp_range, rule in self.clothing_rules['temperature'].items():
            if rule['range'][0] < temperature <= rule['range'][1]:
                return rule['advice']
        return '请根据实际情况穿着'
    
    def get_travel_advice(self, weather_type):
        """根据天气类型获取出行建议"""
        return self.travel_rules['weather_type'].get(weather_type, '请根据实际天气情况调整出行计划')
    
    def get_activity_advice(self, weather_type):
        """根据天气类型获取活动建议"""
        return self.activity_rules['weather_type'].get(weather_type, ['建议根据实际天气情况安排活动'])
    
    def generate_advice(self, forecast_data):
        """生成综合建议"""
        advice = []
        
        for date, data in forecast_data.items():
            temp = data['temperature']
            weather = data['weather_type']
            
            # 生成穿衣建议
            clothing_advice = self.get_clothing_advice(temp)
            
            # 生成出行建议
            travel_advice = self.get_travel_advice(weather)
            
            # 生成活动建议
            activity_advice = self.get_activity_advice(weather)
            
            # 格式化建议
            date_advice = {
                'date': date,
                'weather_summary': f"{date} 的天气预报：{weather}，温度 {temp:.1f}°C",
                'clothing_advice': clothing_advice,
                'travel_advice': travel_advice,
                'activity_advice': activity_advice
            }
            
            advice.append(date_advice)
        
        return advice
    
    def print_advice(self, advice):
        """打印建议"""
        for day_advice in advice:
            print(f"\n{'='*50}")
            print(day_advice['weather_summary'])
            print(f"{'='*50}")
            print(f"👔 穿衣建议：{day_advice['clothing_advice']}")
            print(f"🚗 出行建议：{day_advice['travel_advice']}")
            print(f"🏃 活动建议：")
            for act_advice in day_advice['activity_advice']:
                print(f"   - {act_advice}")
        print(f"\n{'='*50}")
    
    def get_weekend_advice(self, weather_type, temperature):
        """获取周末特别建议"""
        weekend_base = "今天是周末，"
        
        if weather_type in ['sunny', 'partly_cloudy']:
            return weekend_base + f"天气很好，适合外出游玩。{self.get_clothing_advice(temperature)}"
        elif weather_type == 'rain':
            return weekend_base + "有雨，建议安排室内活动，如看电影、购物等。"
        elif weather_type == 'snow':
            return weekend_base + "有雪，适合进行冬季运动，如滑雪、堆雪人，但要注意保暖和安全。"
        else:
            return weekend_base + f"可以根据个人喜好安排活动。{self.get_clothing_advice(temperature)}"
