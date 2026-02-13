"""
Selenium无头浏览器爬虫测试脚本
验证新的Selenium实现是否工作正常
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baidu_spider import BaiduSpider
from loguru import logger
import time


def test_selenium_initialization():
    """测试Selenium驱动初始化"""
    print("\n" + "="*80)
    print("测试1: Selenium驱动初始化")
    print("="*80)
    
    try:
        spider = BaiduSpider()
        print("✅ 驱动初始化成功")
        print(f"   浏览器类型: Chrome (无头模式)")
        print(f"   webdriver-manager已集成")
        spider._close_driver()
        return True
    except Exception as e:
        print(f"❌ 驱动初始化失败: {str(e)}")
        return False


def test_baidu_search():
    """测试百度搜索功能"""
    print("\n" + "="*80)
    print("测试2: 百度搜索功能")
    print("="*80)
    
    try:
        spider = BaiduSpider()
        query = "Python"
        print(f"\n搜索关键词: {query}")
        
        results = spider.search(query=query, count=3)
        
        if results:
            print(f"✅ 搜索成功，找到 {len(results)} 个结果:\n")
            for result in results:
                print(f"  【{result['index']}】 {result['title']}")
                print(f"      {result['link']}\n")
            spider._close_driver()
            return True
        else:
            print("❌ 搜索失败，未找到结果")
            spider._close_driver()
            return False
    
    except Exception as e:
        print(f"❌ 搜索异常: {str(e)}")
        return False


def test_page_fetch():
    """测试网页内容爬取"""
    print("\n" + "="*80)
    print("测试3: 网页内容爬取")
    print("="*80)
    
    try:
        spider = BaiduSpider()
        
        # 使用一个简单的URL测试
        url = "https://www.python.org"
        print(f"\n访问网页: {url}")
        
        content = spider.fetch_page_content(url, extract_images=False)
        
        if content['text']:
            text_length = len(content['text'])
            print(f"✅ 网页爬取成功")
            print(f"   文本长度: {text_length} 字符")
            print(f"   文本预览: {content['text'][:100]}...")
            spider._close_driver()
            return True
        else:
            print("❌ 网页爬取失败，无文本内容")
            spider._close_driver()
            return False
    
    except Exception as e:
        print(f"❌ 网页爬取异常: {str(e)}")
        return False


def test_complete_flow():
    """测试完整流程"""
    print("\n" + "="*80)
    print("测试4: 完整流程（搜索 -> 爬取 -> 提取）")
    print("="*80)
    
    try:
        spider = BaiduSpider()
        query = "Selenium网页自动化"
        
        print(f"\n搜索关键词: {query}")
        print("正在执行完整流程...")
        
        results = spider.search_and_extract(
            query=query,
            count=2,  # 仅测试2个结果
            include_images=False,
            extract_type="summary"
        )
        
        if results:
            print(f"\n✅ 完整流程成功，处理 {len(results)} 个网页:\n")
            
            for result in results:
                print(f"【{result['index']}】 {result['title']}")
                print(f"    URL: {result['url']}")
                print(f"    文本长度: {len(result['full_text'])} 字符")
                print(f"    提取信息长度: {len(result['extracted_info'])} 字符")
                print()
            
            spider._close_driver()
            return True
        else:
            print("❌ 完整流程失败")
            spider._close_driver()
            return False
    
    except Exception as e:
        print(f"❌ 完整流程异常: {str(e)}")
        return False


def test_driver_management():
    """测试驱动管理功能"""
    print("\n" + "="*80)
    print("测试5: 驱动管理功能")
    print("="*80)
    
    try:
        spider = BaiduSpider()
        print("✅ 驱动创建成功")
        
        # 测试手动关闭
        spider._close_driver()
        print("✅ 驱动关闭成功")
        
        # 测试重新初始化
        spider._reinit_driver()
        print("✅ 驱动重新初始化成功")
        
        spider._close_driver()
        return True
    
    except Exception as e:
        print(f"❌ 驱动管理异常: {str(e)}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "Selenium无头浏览器爬虫测试套件" + " "*26 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {
        "驱动初始化": test_selenium_initialization(),
        "百度搜索": test_baidu_search(),
        "网页爬取": test_page_fetch(),
        "完整流程": test_complete_flow(),
        "驱动管理": test_driver_management(),
    }
    
    # 打印测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} {status}")
    
    print("-"*80)
    print(f"总计: {passed}/{total} 通过")
    print("="*80 + "\n")
    
    if passed == total:
        print("✅ 所有测试通过！Selenium实现正常工作。\n")
        return True
    else:
        print("❌ 部分测试失败，请检查错误日志。\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
