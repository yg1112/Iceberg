import numpy as np
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

class PlatformRecommender:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = [
            'mobile_user_ratio', 
            'desktop_usage',
            'tech_complexity',
            'api_dependencies',
            'monetization_score'
        ]
        self.model = DecisionTreeClassifier(
            max_depth=3,
            criterion='gini',
            class_weight='balanced'
        )

    def preprocess_data(self, features):
        """处理跨维度量纲问题"""
        scaled = self.scaler.fit_transform(features)
        return np.nan_to_num(scaled)

    def train_model(self, X, y):
        """训练平台推荐模型"""
        X_processed = self.preprocess_data(X)
        self.model.fit(X_processed, y)
        
        # 可视化决策路径
        plt.figure(figsize=(15,10))
        plot_tree(self.model, 
                 feature_names=self.feature_names,
                 class_names=['Browser Extension','Desktop','Mobile'],
                 filled=True,
                 rounded=True)
        plt.savefig('platform_decision_tree.png')
        plt.close()

    def recommend_platform(self, features):
        """执行平台推荐"""
        REQUIRED_FEATURES = {
            'mobile_user_ratio': (0, 1),
            'desktop_usage': (0, 24),
            'tech_complexity': (1, 5),
            'api_dependencies': (0, 10),
            'monetization_score': (0, 1)
        }

        # 参数验证
        for fname, (min_val, max_val) in REQUIRED_FEATURES.items():
            if not (min_val <= features[fname] <= max_val):
                raise ValueError(f'{fname}参数越界: 应在{min_val}-{max_val}之间')

        # 转换为特征向量
        X = np.array([[features[key] for key in self.feature_names]])
        X_processed = self.preprocess_data(X)
        
        pred = self.model.predict(X_processed)
        proba = self.model.predict_proba(X_processed)
        
        # 生成推荐理由
        node_indicator = self.model.decision_path(X_processed)
        leaf_id = self.model.apply(X_processed)[0]
        
        return {
            'platform': pred[0],
            'confidence': np.max(proba),
            'reasoning': self._get_decision_rules(leaf_id)
        }

    def _get_decision_rules(self, leaf_id):
        """解析决策树路径生成自然语言解释"""
        tree = self.model.tree_
        thresholds = tree.threshold
        features = tree.feature
        
        decision_path = []
        node = leaf_id
        while node != 0:
            parent = np.where(tree.children_left == node)[0]
            if len(parent) == 0:
                parent = np.where(tree.children_right == node)[0][0]
                op = '>'
            else:
                parent = parent[0]
                op = '<='
            
            feat_name = self.feature_names[features[parent]]
            threshold = thresholds[parent]
            decision_path.append(f'{feat_name} {op} {threshold:.2f}')
            node = parent
        
        return ' ∧ '.join(reversed(decision_path))

# 示例用法
if __name__ == '__main__':
    # 训练数据示例
    X_train = np.array([
        [0.8, 4, 3, 2, 0.7],   # Mobile
        [0.2, 8, 2, 1, 0.9],   # Desktop
        [0.5, 6, 4, 3, 0.6]    # Browser
    ])
    y_train = ['Mobile', 'Desktop', 'Browser']
    
    recommender = PlatformRecommender()
    recommender.train_model(X_train, y_train)
    
    # 新案例预测
    test_case = {
        'mobile_user_ratio': 0.65,
        'desktop_usage': 6,
        'tech_complexity': 3,
        'api_dependencies': 2,
        'monetization_score': 0.8
    }
    print(recommender.recommend_platform(test_case))