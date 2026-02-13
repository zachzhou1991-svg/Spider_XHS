"""
百度爬虫API使用示例
展示如何在实际应用中集成和使用BaiduSpider
"""

from baidu_spider import BaiduSpider
from loguru import logger
import json
from datetime import datetime


class BaiduSpiderAPI:
    """
    百度爬虫API封装类
    提供更高层的接口供业务逻辑调用
    """
    
    def __init__(self):
        self.spider = BaiduSpider()
    
    def search_and_analyze(
        self,
        query: str,
        count: int = 10,
        include_images: bool = False,
        extract_type: str = "summary",
        save_results: bool = False,
        output_file: str = None
    ) -> dict:
        """
        搜索并分析，返回结构化结果
        
        Args:
            query: 搜索关键词
            count: 爬取网页数
            include_images: 是否爬取图片
            extract_type: 提取类型
            save_results: 是否保存结果到文件
            output_file: 输出文件路径
            
        Returns:
            包含分析结果的字典
        """
        try:
            logger.info(f"开始搜索: {query}")
            
            results = self.spider.search_and_extract(
                query=query,
                count=count,
                include_images=include_images,
                extract_type=extract_type
            )
            
            # 组织返回数据
            response = {
                'success': True,
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }
            
            # 可选保存结果
            if save_results and output_file:
                self._save_results(response, output_file)
            
            return response
            
        except Exception as e:
            logger.error(f"搜索异常: {str(e)}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def search_multiple_queries(
        self,
        queries: list,
        count: int = 5,
        include_images: bool = False
    ) -> dict:
        """
        批量搜索多个查询词
        
        Args:
            queries: 查询词列表
            count: 每个查询的爬取网页数
            include_images: 是否爬取图片
            
        Returns:
            包含所有查询结果的字典
        """
        results = {}
        
        for i, query in enumerate(queries, 1):
            logger.info(f"处理查询 {i}/{len(queries)}: {query}")
            
            result = self.search_and_analyze(
                query=query,
                count=count,
                include_images=include_images,
                extract_type="summary"
            )
            
            results[query] = result
        
        return {
            'total_queries': len(queries),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def extract_keywords_only(
        self,
        query: str,
        count: int = 5
    ) -> dict:
        """
        仅提取关键词（不爬取图片）
        适用于需要快速进行关键词分析的场景
        
        Args:
            query: 搜索关键词
            count: 爬取网页数
            
        Returns:
            提取的关键词结果
        """
        return self.search_and_analyze(
            query=query,
            count=count,
            include_images=False,
            extract_type="keywords"
        )
    
    def extract_summaries_only(
        self,
        query: str,
        count: int = 10
    ) -> dict:
        """
        仅提取摘要信息
        适用于快速了解话题的场景
        
        Args:
            query: 搜索关键词
            count: 爬取网页数
            
        Returns:
            摘要提取结果
        """
        return self.search_and_analyze(
            query=query,
            count=count,
            include_images=False,
            extract_type="summary"
        )
    
    def search_with_media(
        self,
        query: str,
        count: int = 5
    ) -> dict:
        """
        搜索并爬取文字和图片
        适用于需要多媒体内容的场景
        
        Args:
            query: 搜索关键词
            count: 爬取网页数
            
        Returns:
            包含文字和图片的结果
        """
        return self.search_and_analyze(
            query=query,
            count=count,
            include_images=True,
            extract_type="summary"
        )
    
    def _save_results(self, data: dict, filepath: str):
        """保存结果到JSON文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")
    
    def get_urls_only(self, query: str, count: int = 10) -> list:
        """
        仅获取URL列表（不爬取内容）
        适用于需要收集链接的场景
        
        Args:
            query: 搜索关键词
            count: 需要的URL数量
            
        Returns:
            URL列表
        """
        results = self.spider.search(query=query, count=count)
        return [r['link'] for r in results]


# ==================== 使用示例 ====================

def example_1_basic_search():
    """示例1: 基础搜索"""
    print("\n" + "="*80)
    print("示例1: 基础搜索与分析")
    print("="*80)
    
    api = BaiduSpiderAPI()
    result = api.search_and_analyze(
        query="Python数据分析",
        count=3,
        include_images=False,
        extract_type="summary"
    )
    
    if result['success']:
        print(f"查询: {result['query']}")
        print(f"找到: {result['total_results']} 个结果\n")
        
        for r in result['results'][:2]:  # 显示前2个
            print(f"标题: {r['title']}")
            print(f"URL: {r['url']}")
            print(f"摘要: {r['extracted_info'][:100]}...\n")
    else:
        print(f"搜索失败: {result.get('error')}")


def example_2_keyword_extraction():
    """示例2: 关键词提取"""
    print("\n" + "="*80)
    print("示例2: 关键词提取")
    print("="*80)
    
    api = BaiduSpiderAPI()
    result = api.extract_keywords_only(query="人工智能发展", count=3)
    
    if result['success']:
        print(f"查询: {result['query']}")
        print(f"找到: {result['total_results']} 个结果\n")
        
        for r in result['results']:
            print(f"标题: {r['title']}")
            print(f"关键词: {r['extracted_info']}\n")
    else:
        print(f"提取失败: {result.get('error')}")


def example_3_batch_search():
    """示例3: 批量搜索"""
    print("\n" + "="*80)
    print("示例3: 批量搜索多个话题")
    print("="*80)
    
    api = BaiduSpiderAPI()
    queries = [
        "Docker容器化",
        "微服务架构",
        "Kubernetes编排"
    ]
    
    result = api.search_multiple_queries(queries, count=2, include_images=False)
    
    print(f"共查询: {result['total_queries']} 个话题\n")
    
    for query, data in result['results'].items():
        print(f"话题: {query}")
        print(f"结果数: {data['total_results']}")
        print()


def example_4_url_collection():
    """示例4: URL收集"""
    print("\n" + "="*80)
    print("示例4: 收集URL列表")
    print("="*80)
    
    api = BaiduSpiderAPI()
    urls = api.get_urls_only(query="机器学习框架", count=5)
    
    print(f"收集到 {len(urls)} 个URL:\n")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")


def example_5_media_search():
    """示例5: 媒体内容搜索"""
    print("\n" + "="*80)
    print("示例5: 搜索文字和图片")
    print("="*80)
    
    api = BaiduSpiderAPI()
    result = api.search_with_media(query="室内设计", count=2)
    
    if result['success']:
        print(f"查询: {result['query']}")
        print(f"找到: {result['total_results']} 个结果\n")
        
        for r in result['results']:
            print(f"标题: {r['title']}")
            print(f"图片数: {len(r['images'])}")
            if r['images']:
                print(f"图片: {r['images'][0]}")
            print()


def example_6_save_results():
    """示例6: 保存结果到文件"""
    print("\n" + "="*80)
    print("示例6: 保存结果到文件")
    print("="*80)
    
    api = BaiduSpiderAPI()
    result = api.search_and_analyze(
        query="Web开发框架",
        count=3,
        save_results=True,
        output_file="baidu_search_results.json"
    )
    
    if result['success']:
        print(f"已保存 {result['total_results']} 个结果到文件")
    else:
        print(f"保存失败: {result.get('error')}")


# ==================== 实际应用示例 ====================

class NewsCollector:
    """新闻收集器 - 实际应用示例"""
    
    def __init__(self):
        self.api = BaiduSpiderAPI()
    
    def collect_news(self, topics: list, articles_per_topic: int = 5):
        """收集多个话题的新闻"""
        all_news = {}
        
        for topic in topics:
            print(f"\n收集话题: {topic}")
            result = self.api.search_and_analyze(
                query=topic,
                count=articles_per_topic,
                extract_type="summary"
            )
            
            if result['success']:
                all_news[topic] = [
                    {
                        'title': r['title'],
                        'url': r['url'],
                        'summary': r['extracted_info']
                    }
                    for r in result['results']
                ]
        
        return all_news


def example_7_news_collection():
    """示例7: 新闻收集"""
    print("\n" + "="*80)
    print("示例7: 实时新闻收集")
    print("="*80)
    
    collector = NewsCollector()
    topics = ["科技新闻", "股市行情"]
    
    news = collector.collect_news(topics, articles_per_topic=2)
    
    for topic, articles in news.items():
        print(f"\n【{topic}】")
        for article in articles:
            print(f"  - {article['title']}")


if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*15 + "百度爬虫API使用示例 - BaiduSpiderAPI" + " "*27 + "║")
    print("╚" + "="*78 + "╝")
    
    # 运行所有示例
    try:
        example_1_basic_search()
        example_2_keyword_extraction()
        example_3_batch_search()
        example_4_url_collection()
        # example_5_media_search()  # 如果爬虫速度慢可以注释
        # example_6_save_results()  # 如果爬虫速度慢可以注释
        # example_7_news_collection()  # 如果爬虫速度慢可以注释
        
        print("\n" + "="*80)
        print("✓ 所有示例运行完成！")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"示例执行失败: {str(e)}")
        print(f"\n❌ 执行失败: {str(e)}\n")
