import re
import time
import os
from typing import List, Dict, Optional
from urllib.parse import quote, unquote, urljoin
from loguru import logger
from bs4 import BeautifulSoup
from qwen_utils.qwen import QwenClient
from xhs_utils.data_util import norm_text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class BaiduSpider:
    """百度爬虫工具，用于搜索百度并提取网页内容（使用Selenium无头浏览器）"""
    
    def __init__(self, model: str = "qwen-plus", headless: bool = True):
        """
        初始化百度爬虫
        
        Args:
            model: 使用的大模型，默认为qwen-plus
            headless: 是否使用无头浏览器，默认True（推荐）
        """
        self.base_url = "https://www.baidu.com/s"
        self.qwen_client = QwenClient(model)
        self.headless = headless
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化Chrome驱动（无头浏览器）"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")  # 无头模式
            
            # 常用的反爬虫绕过选项
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("")
            
            # 设置User-Agent
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # 禁用图片加载以加快速度
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 使用webdriver-manager自动下载和管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            logger.info("Chrome驱动初始化成功")
        
        except Exception as e:
            logger.error(f"Chrome驱动初始化失败: {str(e)}")
            raise
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器驱动已关闭")
            except Exception as e:
                logger.error(f"关闭驱动异常: {str(e)}")
    
    def _close_driver(self):
        """手动关闭驱动"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("浏览器驱动已关闭")
            except Exception as e:
                logger.error(f"关闭驱动异常: {str(e)}")
    
    def _reinit_driver(self):
        """重新初始化驱动"""
        self._close_driver()
        time.sleep(1)
        self._init_driver()
    
    def search(self, query: str, count: int = 10) -> List[Dict]:
        """
        使用Selenium无头浏览器搜索百度并获取查询结果
        
        Args:
            query: 搜索关键词
            count: 需要的结果数量，默认10个
            
        Returns:
            包含搜索结果的列表，每个结果包含title、link等信息
        """
        try:
            results = []
            page_num = 0
            
            while len(results) < count:
                # 构建搜索URL
                url = f"{self.base_url}?wd={quote(query)}&pn={page_num * 10}"
                
                logger.info(f"搜索百度: query={query}, page={page_num}, url={url}")
                
                try:
                    # 使用Selenium访问页面
                    self.driver.get(url)
                    
                    # 等待搜索结果加载
                    time.sleep(3)  # 等待JavaScript渲染
                    
                    # 获取页面源代码
                    page_source = self.driver.page_source
                    print(page_source)
                    
                    # 使用BeautifulSoup解析HTML
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # 查找搜索结果项
                    search_items = soup.find_all('div', class_='result')
                    
                    if not search_items:
                        logger.warning(f"第{page_num}页未找到搜索结果")
                        break
                    
                    for item in search_items:
                        if len(results) >= count:
                            break
                        
                        # 提取标题和链接
                        title_elem = item.find('a', class_='t')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        # 处理百度重定向链接
                        if link.startswith('/link?'):
                            # 从重定向链接中提取真实URL
                            url_match = re.search(r'url=([^&]+)', link)
                            if url_match:
                                from urllib.parse import unquote
                                link = unquote(url_match.group(1))
                        
                        if link and title and link.startswith('http'):
                            results.append({
                                'title': norm_text(title),
                                'link': link,
                                'index': len(results) + 1
                            })
                            logger.info(f"找到结果 {len(results)}: {title[:50]}...")
                    
                    page_num += 1
                    time.sleep(2)  # 避免频繁请求
                    
                except Exception as page_error:
                    logger.error(f"爬取第{page_num}页失败: {str(page_error)}")
                    break
            
            logger.info(f"共获取 {len(results)} 个搜索结果")
            return results[:count]
            
        except Exception as e:
            logger.error(f"搜索百度异常: {str(e)}")
            return []
    
    def fetch_page_content(self, url: str, extract_images: bool = False) -> Dict:
        """
        使用Selenium无头浏览器访问网页并提取内容
        
        Args:
            url: 网页URL
            extract_images: 是否同时提取图片URL
            
        Returns:
            包含文本内容和可选图片的字典
        """
        try:
            logger.info(f"访问网页: {url}")
            
            # 使用Selenium访问页面
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(2)
            
            # 获取页面源代码
            page_source = self.driver.page_source
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 移除不需要的标签
            for script in soup(['script', 'style', 'noscript', 'iframe']):
                script.decompose()
            
            # 提取文本内容
            text_content = soup.get_text(separator='\n', strip=True)
            text_content = norm_text(text_content)
            
            # 删除过多的空行
            text_content = '\n'.join([line.strip() for line in text_content.split('\n') if line.strip()])
            
            result = {
                'text': text_content,
                'images': []
            }
            
            # 提取图片URLs
            if extract_images:
                img_tags = soup.find_all('img')
                image_urls = []
                for img in img_tags:
                    img_url = img.get('src', '') or img.get('data-src', '')
                    if img_url:
                        # 处理相对URL
                        if img_url.startswith('/'):
                            img_url = urljoin(url, img_url)
                        if img_url.startswith('http'):
                            image_urls.append(img_url)
                result['images'] = image_urls
            
            logger.info(f"成功获取网页内容，文本长度: {len(text_content)}")
            return result
            
        except Exception as e:
            logger.error(f"访问网页异常: {str(e)}")
            return {'text': '', 'images': []}
    
    
    def extract_info(self, text: str, extract_type: str = "summary") -> str:
        """
        使用大模型从文本中提取相关信息
        
        Args:
            text: 输入文本
            extract_type: 提取类型，支持 'summary'(摘要)、'keywords'(关键词)、'custom'(自定义)
            
        Returns:
            提取结果
        """
        if not text or len(text.strip()) == 0:
            logger.warning("输入文本为空")
            return ""
        
        # 限制文本长度以避免超过模型限制
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length]
        
        try:
            if extract_type == "summary":
                prompt = (
                    "请对下面的文本内容进行总结，提炼出核心信息和关键要点。\n\n"
                    f"文本内容:\n{text}\n\n"
                    "请提供一个结构化的总结，包括：\n"
                    "1. 主题\n"
                    "2. 核心内容\n"
                    "3. 关键信息点\n"
                    "4. 相关结论"
                )
            elif extract_type == "keywords":
                prompt = (
                    "请从下面的文本中提取关键词和重要概念，并按重要性排序。\n\n"
                    f"文本内容:\n{text}\n\n"
                    "请返回JSON格式的结果：{\"keywords\": [...]}"
                )
            else:  # custom
                prompt = (
                    "请对下面的文本进行分析并提取重要信息。\n\n"
                    f"文本内容:\n{text}"
                )
            
            response = self.qwen_client.invoke(prompt)
            logger.info(f"大模型提取完成，结果长度: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"大模型提取异常: {str(e)}")
            return ""
    
    def search_and_extract(
        self,
        query: str,
        count: int = 10,
        include_images: bool = False,
        extract_type: str = "summary"
    ) -> List[Dict]:
        """
        完整流程：搜索百度 -> 访问网页 -> 提取内容 -> 使用大模型提取信息
        
        Args:
            query: 搜索关键词
            count: 要爬取的网页个数，默认10
            include_images: 是否同时爬取图片，默认False
            extract_type: 大模型提取类型，支持 'summary'、'keywords'、'custom'，默认'summary'
            
        Returns:
            包含搜索结果、网页内容和提取信息的列表
        """
        logger.info(f"开始百度爬取流程: query={query}, count={count}, include_images={include_images}")
        
        # 第一步：搜索百度
        search_results = self.search(query, count)
        if not search_results:
            logger.error("搜索结果为空")
            return []
        
        # 第二步：访问并提取每个网页的内容
        final_results = []
        for idx, result in enumerate(search_results, 1):
            logger.info(f"处理第 {idx}/{len(search_results)} 个结果")
            
            # 访问网页
            content = self.fetch_page_content(result['link'], extract_images=include_images)
            
            # 使用大模型提取信息
            extracted_info = ""
            if content['text']:
                extracted_info = self.extract_info(content['text'], extract_type=extract_type)
            
            # 组合结果
            final_result = {
                'index': result['index'],
                'title': result['title'],
                'url': result['link'],
                'text_preview': content['text'][:500] if content['text'] else "",  # 文本预览
                'full_text': content['text'],
                'images': content['images'] if include_images else [],
                'extracted_info': extracted_info
            }
            
            final_results.append(final_result)
            time.sleep(1)  # 避免频繁请求
        
        logger.info(f"爬取完成，共处理 {len(final_results)} 个网页")
        return final_results


def main():
    """测试函数"""
    # 初始化爬虫
    spider = BaiduSpider()
    
    # 搜索示例
    query = "杭州市免费篮球场"
    print(f"\n开始搜索: {query}")
    print("=" * 80)
    
    results = spider.search_and_extract(
        query=query,
        count=3,  # 只爬取前3个
        include_images=False,  # 不爬取图片
        extract_type="summary"  # 提取摘要
    )
    
    # 输出结果
    for result in results:
        print(f"\n【第 {result['index']} 个结果】")
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\n文本预览:\n{result['text_preview']}\n")
        print(f"\n大模型提取的信息:\n{result['extracted_info']}\n")
        print("-" * 80)


if __name__ == "__main__":
    main()
