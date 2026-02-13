"""
百度爬虫工具测试脚本
演示如何使用BaiduSpider的各种功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baidu_spider import BaiduSpider
from loguru import logger
import json


def test_basic_search():
    """测试基础搜索功能"""
    print("\n" + "="*80)
    print("测试1: 基础搜索功能")
    print("="*80)
    
    spider = BaiduSpider()
    results = spider.search(query="Python爬虫", count=5)
    
    print(f"\n搜索关键词: Python爬虫")
    print(f"返回结果数: {len(results)}\n")
    
    for result in results:
        print(f"[{result['index']}] {result['title']}")
        print(f"    URL: {result['link']}\n")


def test_fetch_content():
    """测试网页内容提取"""
    print("\n" + "="*80)
    print("测试2: 网页内容提取")
    print("="*80)
    
    spider = BaiduSpider()
    
    # 获取一个测试URL
    search_results = spider.search(query="Python教程", count=1)
    if not search_results:
        print("搜索失败，跳过此测试")
        return
    
    url = search_results[0]['link']
    print(f"\n访问URL: {url}")
    
    # 仅提取文本
    content = spider.fetch_page_content(url, extract_images=False)
    
    print(f"\n成功提取内容:")
    print(f"文本长度: {len(content['text'])} 字符")
    print(f"文本预览:\n{content['text'][:300]}...\n")


def test_extract_info():
    """测试大模型信息提取"""
    print("\n" + "="*80)
    print("测试3: 大模型信息提取")
    print("="*80)
    
    spider = BaiduSpider()
    
    test_text = """
    Python是一门高级编程语言，具有简洁、易学的特点。
    它广泛应用于数据科学、人工智能、网络爬虫、自动化等领域。
    Python的特点包括：
    1. 语法简单易学，适合初学者
    2. 拥有丰富的第三方库
    3. 跨平台支持
    4. 提供了强大的数据处理能力
    Python的发展历程已经超过30年，目前已成为全球最受欢迎的编程语言之一。
    """
    
    print(f"\n输入文本:\n{test_text}\n")
    
    # 测试摘要提取
    print("=" * 40)
    print("提取摘要:")
    print("=" * 40)
    summary = spider.extract_info(test_text, extract_type="summary")
    print(f"\n{summary}\n")
    
    # 测试关键词提取
    print("=" * 40)
    print("提取关键词:")
    print("=" * 40)
    keywords = spider.extract_info(test_text, extract_type="keywords")
    print(f"\n{keywords}\n")


def test_complete_flow():
    """测试完整流程：搜索 -> 爬取 -> 提取"""
    print("\n" + "="*80)
    print("测试4: 完整流程（搜索->爬取->提取）")
    print("="*80)
    
    spider = BaiduSpider()
    
    query = "机器学习基础"
    print(f"\n搜索关键词: {query}")
    print(f"爬取网页数: 3")
    print(f"爬取图片: 否")
    print(f"提取类型: 摘要")
    print("\n正在处理...")
    
    results = spider.search_and_extract(
        query=query,
        count=3,
        include_images=False,
        extract_type="summary"
    )
    
    print(f"\n完成! 获取 {len(results)} 个结果\n")
    
    for result in results:
        print("="*80)
        print(f"【结果 {result['index']}】")
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\n文本预览 ({len(result['full_text'])} 字符):")
        print(f"{result['text_preview']}")
        print(f"\n大模型提取的信息:")
        print(f"{result['extracted_info']}")
        print("\n")


def test_with_images():
    """测试包含图片的爬取"""
    print("\n" + "="*80)
    print("测试5: 爬取文字和图片")
    print("="*80)
    
    spider = BaiduSpider()
    
    query = "风景摄影"
    print(f"\n搜索关键词: {query}")
    print(f"爬取网页数: 2")
    print(f"爬取图片: 是")
    print("\n正在处理...")
    
    results = spider.search_and_extract(
        query=query,
        count=2,
        include_images=True,
        extract_type="summary"
    )
    
    print(f"\n完成! 获取 {len(results)} 个结果\n")
    
    for result in results:
        print("="*80)
        print(f"【结果 {result['index']}】")
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"找到图片数: {len(result['images'])}")
        
        if result['images']:
            print(f"\n图片URLs (显示前5个):")
            for i, img_url in enumerate(result['images'][:5], 1):
                print(f"  {i}. {img_url}")
        
        print("\n")


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "百度爬虫工具 (BaiduSpider) 测试套件" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        # 测试1: 基础搜索
        test_basic_search()
        
        # 测试2: 网页内容提取
        test_fetch_content()
        
        # 测试3: 大模型信息提取
        test_extract_info()
        
        # 测试4: 完整流程
        test_complete_flow()
        
        # 测试5: 包含图片的爬取
        test_with_images()
        
        print("\n" + "="*80)
        print("✓ 所有测试完成！")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        print(f"\n❌ 测试失败: {str(e)}\n")


if __name__ == "__main__":
    # 如果提供了参数，运行特定测试
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "1":
            test_basic_search()
        elif test_name == "2":
            test_fetch_content()
        elif test_name == "3":
            test_extract_info()
        elif test_name == "4":
            test_complete_flow()
        elif test_name == "5":
            test_with_images()
        else:
            print("用法: python test_baidu_spider.py [1-5]")
            print("  1: 基础搜索功能")
            print("  2: 网页内容提取")
            print("  3: 大模型信息提取")
            print("  4: 完整流程")
            print("  5: 图片爬取")
    else:
        # 运行所有测试
        run_all_tests()
