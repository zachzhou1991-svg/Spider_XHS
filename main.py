import json
import os
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx, save_processed_note_list_to_xlsx
from qwen_utils.qwen import QwenClient
from static.ZHEJIANG_DIVISIONS import ZHEJIANG_DIVISIONS


class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        self.qwen_client = QwenClient("qwen-plus")
        from sql_utils.sql_connector import SqlConnector
        self._sql_conn = SqlConnector()

    def close(self):
        if hasattr(self, '_sql_conn') and self._sql_conn:
            self._sql_conn.close()

    def spider_note(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(note_url, cookies_str, proxies)
            if success:
                note_info = note_info['data']['items'][0]
                note_info['url'] = note_url
                note_info = handle_note_info(note_info)
        except Exception as e:
            success = False
            print(e)
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    def spider_some_note(self, province, city, state, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        for note_info in note_list:
            if save_choice == 'all' or 'media' in save_choice:
                download_note(note_info, base_path['media'], save_choice)
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            # 将note_list先通过qwenApi处理一遍，提取信息
            processed_note_list = []
            from sql_utils.sql_connector import BasketballCourt, CourtUnit
            for note in note_list:
                print("开始使用qwen大模型处理笔记信息...")
                processed_note = self.qwen_client.extract_xhs_info(note)
                print("处理结果为:")
                print(processed_note)
                note_url = note.get('url', '')
                note_type = note.get('note_type', '')
                note_title = note.get('title', '')
                note_desc = note.get('desc', '')
                video_url = note.get('video_url', '')
                image_urls = note.get('image_list', [])
                # 将processed_note转换为json，如果processed_note不是json格式，则跳过
                try:
                    processed_note_json = json.loads(processed_note)
                    if not isinstance(processed_note_json, list):
                        logger.error(f'处理笔记时返回结果不是列表: {processed_note}')
                        continue
                    # 遍历processed_note_json, 跳过success为False的项
                    for item in processed_note_json:
                        if not item.get('success', False):
                            logger.error(f'不能合理提取笔记信息: {processed_note}')
                            continue
                        # 兼容大模型输出格式
                        bc_dict = item.get('basketball_court', {})
                        cu_list = item.get('court_units', [])
                        # 填充省市区等信息
                        bc_dict['province'] = province
                        bc_dict['city'] = city
                        bc_dict['district'] = state
                        # 兼容note原始信息
                        bc_dict['note_url'] = note_url
                        bc_dict['note_type'] = note_type
                        bc_dict['note_title'] = note_title
                        bc_dict['note_desc'] = note_desc
                        bc_dict['video_url'] = video_url
                        bc_dict['image_urls'] = image_urls
                        # 构造BasketballCourt对象
                        court_obj = BasketballCourt(**{k: v for k, v in bc_dict.items() if k in BasketballCourt.__dataclass_fields__})
                        print(court_obj)
                        court_id = self._sql_conn.insert_basketball_court(court_obj)
                        # 插入所有CourtUnit
                        for cu in cu_list:
                            cu['court_id'] = court_id
                            unit_obj = CourtUnit(**{k: v for k, v in cu.items() if k in CourtUnit.__dataclass_fields__})
                            print(unit_obj)
                            self._sql_conn.insert_court_unit(unit_obj)
                        # 也可加入excel导出
                        bc_dict['id'] = court_id
                        processed_note_list.append(bc_dict)
                except json.JSONDecodeError:
                    logger.error(f'处理笔记时发生错误: {processed_note}')
                    continue
                # print(f'处理后的笔记信息: {processed_note_list}')
            # save_processed_note_list_to_xlsx(processed_note_list, file_path)

    def spider_user_all_note(self, user_url: str, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url:
        :param cookies_str:
        :param base_path:
        :return:
        """
        note_list = []
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies)
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = user_url.split('/')[-1].split('?')[0]
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, province, city, state, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        # try:
        success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
        if success:
            notes = list(filter(lambda x: x['model_type'] == "note", notes))
            logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
            for note in notes:
                note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                note_list.append(note_url)
        if save_choice == 'all' or save_choice == 'excel':
            excel_name = query
        self.spider_some_note(province, city, state, note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        # except Exception as e:
        #     success = False
        #     msg = e
        # logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg
    
    def iter_districts_and_counties(self):
        """
        遍历浙江省所有的 区 和 县
        返回结构化数据，包含 省 / 市 / 区县
        """
        return [{
            "full_name": f"杭州市拱墅区",
            "province": "浙江省",
            "city": "杭州市",
            "name": "拱墅区",
            "type": "区"
        }]
        province_name = ZHEJIANG_DIVISIONS["name"]

        for city in ZHEJIANG_DIVISIONS["cities"]:
            city_name = city["name"]

            for d in city["districts"]:
                name = d["name"]

                # 区
                if name.endswith("区"):
                    yield {
                        "full_name": f"{province_name}{city_name}{name}",
                        "province": province_name,
                        "city": city_name,
                        "name": name,
                        "type": "区",
                        "code": d["code"],
                    }

                # 县
                elif name.endswith("县"):
                    yield {
                        "full_name": f"{province_name}{city_name}{name}",
                        "province": province_name,
                        "city": city_name,
                        "name": name,
                        "type": "县",
                        "code": d["code"],
                    }

                # 市属县级市（隐藏地级市）
                elif name.endswith("市"):
                    yield {
                        "full_name": f"{province_name}{name}",
                        "province": province_name,
                        "city": None,          # 显式隐藏
                        "name": name,
                        "type": "市",
                        "code": d["code"],
                    }

def fetch_courts_by_xhs(data_spider, province: str, city: str, state: str, cookies_str: str, base_path: dict, query_num: int = 50):
    """
    通过小红书方式获取免费篮球场信息
    
    :param data_spider: Data_Spider实例
    :param province: 省份
    :param city: 城市
    :param state: 区县
    :param cookies_str: 小红书cookies
    :param base_path: 保存路径
    :param query_num: 搜索数量
    """
    query = f"{province}{city}{state}免费篮球场"
    print(f"[XHS模式] 正在搜索: {query}")
    
    sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    note_type = 2  # 0 不限, 1 视频笔记, 2 普通笔记
    note_time = 0  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    note_range = 0  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo
    
    note_list, success, msg = data_spider.spider_some_search_note(
        province, city, state, query, query_num, cookies_str, base_path, 
        'excel', sort_type_choice, note_type, note_time, note_range, 
        pos_distance, geo=None
    )
    
    print(f"[XHS模式] 搜索完成，成功: {success}, 获取笔记数: {len(note_list)}")
    return note_list, success, msg


def fetch_courts_by_qwen(data_spider, province: str, city: str, state: str, query: str = ""):
    """
    通过Qwen联网搜索方式获取免费篮球场信息
    支持多轮对话，直到Qwen返回"没有了"
    
    使用方式2：逐个处理生成器返回的球场，实时插入数据库
    
    :param data_spider: Data_Spider实例
    :param province: 省份
    :param city: 城市
    :param state: 区县
    :param query: 搜索关键词（可选）
    """
    print(f"[Qwen模式] 正在通过Qwen联网搜索...")
    
    from sql_utils.sql_connector import BasketballCourt, CourtUnit
    
    # 使用生成器逐个处理球场信息
    courts_generator = data_spider.qwen_client.search_and_summarize_courts(
        province=province,
        city=city,
        district=state,
        query=query
    )
    
    total_courts = 0
    total_units = 0
    all_courts_data = []
    
    # 逐个处理生成器返回的球场信息
    for court_data in courts_generator:
        try:
            # 提取篮球场信息
            bc_dict = court_data.get('basketball_court', {})
            cu_list = court_data.get('court_units', [])
            
            # 检查是否成功
            if not court_data.get('success', False):
                print(f"  ⚠️ 跳过失败的球场数据")
                continue
            
            # 填充省市区信息
            bc_dict['province'] = province
            bc_dict['city'] = city
            bc_dict['district'] = state
            
            # 先查询该球场是否已存在
            court_name = bc_dict.get('name', '')
            existing_court = data_spider._sql_conn.get_basketball_court_by_location(
                name=court_name,
                province=province,
                city=city,
                district=state
            )
            
            if existing_court:
                # 球场已存在，跳过插入
                print(f"  ⏭️ 球场已存在: {court_name} (ID: {existing_court.id})，跳过插入")
                court_id = existing_court.id
            else:
                # 球场不存在，执行插入
                # 构造BasketballCourt对象
                court_obj = BasketballCourt(**{k: v for k, v in bc_dict.items() if k in BasketballCourt.__dataclass_fields__})
                
                # 插入篮球场到数据库
                court_id = data_spider._sql_conn.insert_basketball_court(court_obj)
                print(f"  ✅ 已插入球场: {court_obj.name} (ID: {court_id})")
                total_courts += 1
            
            # 插入该球场的所有单元
            for cu in cu_list:
                cu['court_id'] = court_id
                unit_obj = CourtUnit(**{k: v for k, v in cu.items() if k in CourtUnit.__dataclass_fields__})
                data_spider._sql_conn.insert_court_unit(unit_obj)
                total_units += 1
                print(f"    └─ 已插入单元: {unit_obj.unit_name} (court_id: {court_id})")
            
            # 保存原始数据用于Excel导出
            bc_dict['id'] = court_id
            all_courts_data.append(bc_dict)
            
        except Exception as e:
            print(f"  ❌ 处理球场数据失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n[Qwen模式] 搜索和插入完成！")
    print(f"  总计插入球场: {total_courts} 个")
    print(f"  总计插入单元: {total_units} 个")
    
    # 将Qwen搜索结果保存为Excel
    if all_courts_data:
        try:
            import pandas as pd
            excel_path = os.path.join(
                data_spider._sql_conn._db_path if hasattr(data_spider._sql_conn, '_db_path') else './datas/excel_datas/', 
                f'{province}{city}{state}_qwen_courts.xlsx'
            )
            
            df = pd.DataFrame(all_courts_data)
            df.to_excel(excel_path, index=False)
            print(f"  ✅ 结果已保存到Excel: {excel_path}")
        except Exception as e:
            print(f"  ⚠️ Excel保存失败: {e}")
    
    return all_courts_data


if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        apis/xhs_pc_apis.py 为爬虫的api文件，包含小红书的全部数据接口，可以继续封装
        apis/xhs_creator_apis.py 为小红书创作者中心的api文件
        
        使用方式:
        1. XHS模式: python main.py --mode xhs
        2. Qwen模式: python main.py --mode qwen
        默认为XHS模式
    """
    try:
        import sys
        import argparse
        
        # 参数解析
        parser = argparse.ArgumentParser(description='获取免费篮球场信息')
        parser.add_argument('--mode', type=str, default='xhs', choices=['xhs', 'qwen'], 
                          help='获取方式: xhs (小红书) 或 qwen (Qwen联网搜索), 默认为xhs')
        parser.add_argument('--city', type=str, default='杭州市', help='城市名称')
        parser.add_argument('--district', type=str, default='临平区', help='区县名称')
        parser.add_argument('--province', type=str, default='浙江省', help='省份名称')
        parser.add_argument('--count', type=int, default=50, help='XHS模式下的搜索数量')
        
        args = parser.parse_args()
        
        cookies_str, base_path = init()
        data_spider = Data_Spider()  
        
        province = args.province
        city = args.city
        district = args.district
        
        if args.mode == 'xhs':
            # XHS模式
            print(f"\n========== XHS小红书模式 ==========")
            fetch_courts_by_xhs(data_spider, province, city, district, cookies_str, base_path, args.count)
            
        elif args.mode == 'qwen':
            # Qwen模式
            print(f"\n========== Qwen联网搜索模式 ==========")
            fetch_courts_by_qwen(data_spider, province, city, district)
        
        data_spider.close()
        print(f"\n程序执行完成！")
        
    except Exception as e:
        import traceback
        print('主程序发生异常:', e)
        traceback.print_exc()
