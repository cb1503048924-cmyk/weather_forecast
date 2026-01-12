import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class WeatherClassifier:
    def __init__(self):
        self.scaler = StandardScaler()
        self.models = {
            'logistic_regression': LogisticRegression(
                max_iter=5000, 
                solver='lbfgs', 
                random_state=42,
                class_weight='balanced'
            ),
            'decision_tree': DecisionTreeClassifier(
                random_state=42,
                class_weight='balanced',
                min_samples_leaf=2
            )
        }
        self.fitted_models = {}
        self.label_encoder = None
        self.feature_names = None
    
    def train_test_split(self, X, y, test_size=0.2, random_state=42):
        """划分训练集和测试集，当某些类别样本数量不足时移除 stratify 参数"""
        # 检查每个类别的样本数量
        class_counts = y.value_counts()
        min_class_count = class_counts.min()
        
        # 如果最小类别样本数 < 2，不使用 stratify
        use_stratify = min_class_count >= 2
        print(f"类别分布: {class_counts.to_dict()}")
        print(f"最小类别样本数: {min_class_count}, 是否使用分层抽样: {use_stratify}")
        
        # 根据情况决定是否使用 stratify
        if use_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
        return X_train, X_test, y_train, y_test
    
    def encode_labels(self, y):
        """将字符串标签编码为数字"""
        from sklearn.preprocessing import LabelEncoder
        self.label_encoder = LabelEncoder()
        return self.label_encoder.fit_transform(y)
    
    def train(self, X_train, y_train):
        """训练所有分类模型"""
        # 保存特征名称
        self.feature_names = X_train.columns if hasattr(X_train, 'columns') else [f'feature_{i}' for i in range(X_train.shape[1])]
        
        # 调试信息：打印原始标签的唯一值
        print(f"原始标签的唯一值: {y_train.unique()}")
        print(f"原始标签的唯一值数量: {len(y_train.unique())}")
        
        # 编码标签（如果是字符串）
        if isinstance(y_train.iloc[0], str) or isinstance(y_train[0], str):
            y_train_encoded = self.encode_labels(y_train)
        else:
            y_train_encoded = y_train
        
        # 调试信息：打印编码后的标签的唯一值
        print(f"编码后的标签的唯一值: {np.unique(y_train_encoded)}")
        print(f"编码后的标签的唯一值数量: {len(np.unique(y_train_encoded))}")
        
        # 标准化特征数据
        X_train_scaled = self.scaler.fit_transform(X_train)
        print("特征数据已标准化")
        
        # 训练每个模型
        for name, model in self.models.items():
            print(f'正在训练 {name} 模型...')
            # 只有当有至少2个类别时才训练模型
            if len(np.unique(y_train_encoded)) < 2:
                print(f"{name} 模型训练失败：数据中只有一个类别")
                continue
            model.fit(X_train_scaled, y_train_encoded)
            self.fitted_models[name] = model
            print(f'{name} 模型训练完成')
        
        return self.fitted_models
    
    def predict(self, X, model_name='decision_tree'):
        """使用指定模型进行预测"""
        if model_name not in self.fitted_models:
            print(f'请先训练 {model_name} 模型')
            return None
        
        model = self.fitted_models[model_name]
        # 标准化特征数据
        X_scaled = self.scaler.transform(X)
        predictions = model.predict(X_scaled)
        
        # 如果有标签编码器，将数字转回原始标签
        if self.label_encoder is not None:
            predictions = self.label_encoder.inverse_transform(predictions)
        
        return predictions
    
    def evaluate(self, X_test, y_test, model_name='decision_tree'):
        """评估模型性能"""
        if model_name not in self.fitted_models:
            print(f'请先训练 {model_name} 模型')
            return None
        
        # 编码测试标签
        if isinstance(y_test.iloc[0], str) or isinstance(y_test[0], str):
            y_test_encoded = self.label_encoder.transform(y_test)
        else:
            y_test_encoded = y_test
        
        # 标准化测试数据
        X_test_scaled = self.scaler.transform(X_test)
        predictions = self.fitted_models[model_name].predict(X_test_scaled)
        
        # 计算评估指标，添加zero_division参数处理未预测到的类别
        accuracy = accuracy_score(y_test_encoded, predictions)
        
        # 获取实际存在的类别（避免target_names数量不匹配）
        unique_classes = np.unique(np.concatenate([y_test_encoded, predictions]))
        target_names = [self.label_encoder.classes_[i] for i in unique_classes]
        
        report = classification_report(
            y_test_encoded, 
            predictions, 
            target_names=target_names,
            zero_division=0
        )
        cm = confusion_matrix(y_test_encoded, predictions)
        
        print(f'\n{model_name} 模型评估结果:')
        print(f'准确率: {accuracy:.4f}')
        print('分类报告:')
        print(report)
        
        # 绘制混淆矩阵
        self.plot_confusion_matrix(cm, model_name)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'confusion_matrix': cm
        }
    
    def plot_confusion_matrix(self, cm, model_name):
        """绘制混淆矩阵"""
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=self.label_encoder.classes_,
                    yticklabels=self.label_encoder.classes_)
        plt.title(f'{model_name} 混淆矩阵')
        plt.xlabel('预测标签')
        plt.ylabel('真实标签')
        plt.tight_layout()
        plt.savefig(f'D:/Trae/trae_project/weather_forecast/weather_forecast_system/results/{model_name}_confusion_matrix.png')
        plt.close()
        print(f'混淆矩阵已保存到 results/{model_name}_confusion_matrix.png')
    
    def get_feature_importance(self, model_name='decision_tree'):
        """获取特征重要性"""
        if model_name not in self.fitted_models:
            print(f'请先训练 {model_name} 模型')
            return None
        
        model = self.fitted_models[model_name]
        
        if model_name == 'decision_tree':
            importances = model.feature_importances_
        elif model_name == 'logistic_regression':
            importances = np.abs(model.coef_[0])
        else:
            print(f'{model_name} 模型不支持特征重要性分析')
            return None
        
        # 创建特征重要性DataFrame
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        # 绘制特征重要性
        plt.figure(figsize=(12, 6))
        sns.barplot(x='importance', y='feature', data=feature_importance_df)
        plt.title(f'{model_name} 特征重要性')
        plt.tight_layout()
        plt.savefig(f'D:/Trae/trae_project/weather_forecast/weather_forecast_system/results/{model_name}_feature_importance.png')
        plt.close()
        print(f'特征重要性图已保存到 results/{model_name}_feature_importance.png')
        
        return feature_importance_df
    
    def save_model(self, model_name, file_path):
        """保存模型到文件"""
        import joblib
        if model_name in self.fitted_models:
            joblib.dump({
                'model': self.fitted_models[model_name],
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names
            }, file_path)
            print(f'{model_name} 模型已保存到 {file_path}')
        else:
            print(f'请先训练 {model_name} 模型')
    
    def load_model(self, model_name, file_path):
        """从文件加载模型"""
        import joblib
        loaded = joblib.load(file_path)
        self.fitted_models[model_name] = loaded['model']
        self.label_encoder = loaded['label_encoder']
        self.feature_names = loaded['feature_names']
        print(f'{model_name} 模型已从 {file_path} 加载')
