import os
from datetime import datetime
import requests
import matplotlib.pyplot as plt

SIMILARWEB_API_KEY = os.getenv('SIMILARWEB_API_KEY')

class CompetitorAnalyzer:
    def __init__(self, domain):
        self.domain = domain
        self.base_url = 'https://api.similarweb.com/v1/website'

    def get_traffic_stats(self):
        endpoint = f'{self.base_url}/{self.domain}/total-traffic-and-engagement/visits'
        params = {
            'api_key': SIMILARWEB_API_KEY,
            'start_date': (datetime.now().replace(day=1)).strftime('%Y-%m'),
            'end_date': datetime.now().strftime('%Y-%m'),
            'granularity': 'monthly',
            'main_domain_only': 'false'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            data = response.json()
            return {
                'global_rank': data.get('global_rank', 'N/A'),
                'category_rank': data.get('category_rank', 'N/A'),
                'avg_visit_duration': data.get('visit_duration', 0),
                'pages_per_visit': data.get('pages_per_visit', 0),
                'bounce_rate': data.get('bounce_rate', 0)
            }
        except Exception as e:
            print(f'竞品分析失败: {str(e)}')
            return None

    def plot_traffic_trend(self, metrics):
        plt.figure(figsize=(10, 6))
        for metric, values in metrics.items():
            plt.plot(values, label=metric)
        plt.title(f'{self.domain} Traffic Trend')
        plt.legend()
        plt.savefig(f'{self.domain}_traffic_trend.png')
        plt.close()

    def generate_swot(self, our_metrics, competitor_metrics):
        swot_analysis = {
            'strengths': [
                'Lower bounce rate compared to competitors',
                'Higher user engagement metrics'
            ],
            'weaknesses': [
                'Smaller market share in target category',
                'Less brand recognition'
            ],
            'opportunities': [
                'Untapped regional markets',
                'Feature gaps in competitor products'
            ],
            'threats': [
                'Established competitor ecosystems',
                'Rapid feature development by competitors'
            ]
        }
        return swot_analysis