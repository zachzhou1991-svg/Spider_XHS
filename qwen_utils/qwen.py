import os
from openai import OpenAI

class QwenClient:
    def __init__(self, model):
        self.model = model
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def invoke(self, message):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
            stream=True,
            response_format={"type": "json_object"},
            stream_options={"include_usage": True}
        )
        result = ""
        for chunk in completion:
            if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0 and hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content
        return result
    
    def invoke_with_network_search(self, message):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant with internet access."},
                {"role": "user", "content": message},
            ],
            stream=True,
            response_format={"type": "json_object"},
            stream_options={"include_usage": True},
            extra_body={
                "enable_search": True
            }
        )
        result = ""
        for chunk in completion:
            if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0 and hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content
        return result
    
    # 通过联网搜索获取多条篮球场信息，支持多轮对话，使用yield逐个返回
    def search_and_summarize_courts(self, province: str, city: str, district: str, query: str = ""):
        """
        通过Qwen联网搜索获取免费篮球场信息，支持多轮对话
        直到模型返回"没有了"为止
        
        使用yield逐个返回球场信息，而不是等待全部对话完成
        
        :param province: 省份
        :param city: 城市
        :param district: 区县
        :param query: 搜索关键词（可选，如果为空则使用默认关键词）
        :return: yield 每个球场信息（JSON对象）
        """
        if not query:
            query = f"{province}{city}{district}免费篮球场"
        
        system_message = "你是一个篮球场信息搜索助手。你的任务是通过网络搜索找到指定地区的免费篮球场信息。"
        
        initial_user_message = (
            f"请通过网络搜索找到{province}{city}{district}地区的免费篮球场信息。\n"
            f"搜索关键词：{query}\n"
            f"请每次返回最多5条球场信息。\n\n"
            "# 返回格式（JSON）：\n"
            "# BasketballCourt 字段定义（每个字段后有详细描述）\n"
            "{\n"
            "  name: str, // 场地名称\n"
            "  description: str, // 场地描述\n"
            "  operator: str, // 管理/运营单位（如市政、公园）\n"
            "  is_free: int, // 是否免费开放\n"
            "  access_type: str, // 访问类型，open/gated/appointment/restricted\n"
            "  province: str, // 省份\n"
            "  city: str, // 城市\n"
            "  district: str, // 区/县\n"
            "  address: str, // 地址\n"
            "  place_id: str, // 由第三方提供的场地id\n"
            "  latitude: float, // 纬度（十进制度）\n"
            "  longtitude: float, // 经度（十进制度）\n"
            "  nearest_transit: str, // 公共交通描述\n"
            "  has_parking: int, // 是否可以停车\n"
            "  free_parking: int, // 停车是否免费\n"
            "  parking_type: str, // 停车类型，on_street/lot/garage/none\n"
            "  parking_fee_info: str, // 停车收费说明（文本）\n"
            "  parking_capacity: int, // 预估车位数\n"
            "  has_lights: int, // 是否有夜间照明\n"
            "  light_type: str, // 灯光类型（flood/pole/led/none）\n"
            "  light_hours_desc: str, // 灯光启用时段说明\n"
            "  surface_type: str, // 地面材质\n"
            "  surface_notes: str, // 地面情况备注，如破损、坑洼等\n"
            "  total_units_count: int, // 全场个数（不算单独半场）\n"
            "  half_units_count: int, // 半场个数（不算全场）\n"
            "  week_open_hours: str, // 每周开门时间统计\n"
            "  free_open_hours: str, // 每周免费时间统计\n"
            "  week_appointment_hours: str, // 每周需预约的时间统计\n"
            "  appointment_type_desc: str, // 预约方式描述\n"
            "  amenities_summary: str, // 其他基础设施如WC、洗手池、饮水机等统计\n"
            "  built_time: str, // datetime格式，球场创建时间\n"
            "}\n\n"
            "# CourtUnit 字段定义（每个字段后有详细描述）\n"
            "{\n"
            "  unit_name: str, // 单元名称或编号，如A场\n"
            "  unit_type: str, // 单元类型（full/half/3x3/multi）\n"
            "  length_m: int, // 长度\n"
            "  width_m: int, // 宽度\n"
            "  is_standard: int, // 是否为标准场地\n"
            "  fenced: int, // 是否有围栏\n"
            "  lines_painted: int, // 球线是否清晰可见\n"
            "  surface_condition_score: int, // 场地综合评分，100分满分\n"
            "  hoop_brand: str, // 篮筐/篮板品牌（文本）\n"
            "  hoop_material: str, // 篮板材质\n"
            "  rim_type: str, // 篮筐类型（breakaway/fixed/none）\n"
            "  rim_height_cm: int, // 篮筐高度，厘米制\n"
            "  is_standard_rim: int, // 是否为标准篮筐\n"
            "  unit_status: str, // 单元状态（损坏、临时封闭等）\n"
            "  surface_type: str, // 场地地面材质\n"
            "  surface_status: str // 场地地面状态，破损、坑洼等等\n"
            "}\n\n"
            "# 输出格式\n"
            "[\n"
            "  {\n"
            "    'success': 该场地的提取是否成功，true/false,\n"
            "    'basketball_court': {BasketballCourt字段...},\n"
            "    'court_units': [ {CourtUnit字段...}, ... ]\n"
            "  }, ...\n"
            "]\n\n"
            "# 要求\n"
            "1. 只输出上述json格式，不要输出多余内容。\n"
            "2. 字段名、类型、结构必须与定义完全一致。\n"
            "3. 一个输入可能包含多个球场，每个球场下可有多个单元。如果无法从描述中区分出球场有几块场地，默认按照一个全场来算。\n"
            "4. 未获取到的字段请置为空字符串。\n"
            "5. 不要自行编造信息。\n"
            "如果没有更多信息，请回复：没有了"
        )
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": initial_user_message}
        ]
        
        total_count = 0
        round_num = 1
        
        while True:
            # 进行API调用
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                response_format={"type": "json_object"},
                stream_options={"include_usage": True},
                extra_body={
                    "enable_search": True
                }
            )
            
            result = ""
            for chunk in completion:
                if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0 and hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    result += chunk.choices[0].delta.content
            
            # 检查是否返回"没有了"
            if "没有了" in result:
                print(f"\n✅ 搜索完成！Qwen回复：没有了")
                print(f"总计获取 {total_count} 条球场信息\n")
                break
            
            # 尝试解析JSON结果
            courts = []
            try:
                import json
                # 尝试提取JSON部分
                json_start = result.find('[')
                json_end = result.rfind(']') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = result[json_start:json_end]
                    courts = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果解析失败，跳过此轮
                pass
            
            print(f"\n📍 第 {round_num} 轮搜索结果:")
            print(f"✅ 本轮获取到 {len(courts)} 条球场信息")
            
            # 逐个yield返回球场信息
            for court in courts:
                total_count += 1
                print(f"  [{total_count}] 返回球场: {court.get('basketball_court', {}).get('name', 'N/A')}")
                yield court
            
            print(f"累计已返回 {total_count} 条球场信息")
            print("正在准备下一轮搜索...\n")
            
            # 只将球场名称加入消息历史，避免上下文过长导致幻觉
            courts_names = [court.get('basketball_court', {}).get('name', 'N/A') for court in courts]
            assistant_summary = f"本轮搜索到以下{len(courts)}个球场：{', '.join(courts_names)}"
            messages.append({"role": "assistant", "content": assistant_summary})
            
            # 构造下一轮的用户消息
            next_user_message = f"请继续搜索更多{province}{city}{district}地区的免费篮球场信息。如果没有更多信息，请回复：没有了"
            messages.append({"role": "user", "content": next_user_message})
            
            round_num += 1

    # 提取小红书文本中的篮球场及单元信息，字段严格对应BasketballCourt和CourtUnit
    def extract_xhs_info(self, text):
        prompt = (
            "# 职责\n"
            "你是一个数据信息提取员，你的职责是从输入的内容中提取、整理出与篮球场地相关的所有结构化信息。\n"
            "请根据下方的字段定义，提取出每个球场（BasketballCourt）及其包含的所有单元（CourtUnit）的信息。\n"
            "输出内容必须严格按照给定的json格式，字段名和类型必须与定义完全一致，未获取到的字段请置为null或空字符串。\n\n"
            "# BasketballCourt 字段定义（每个字段后有详细描述）\n"
            "{\n"
            "  id: int, // 主键，自增\n"
            "  name: str, // 场地名称\n"
            "  description: str, // 场地描述\n"
            "  operator: str, // 管理/运营单位（如市政、公园）\n"
            "  is_free: int, // 是否免费开放\n"
            "  access_type: str, // 访问类型，open/gated/appointment/restricted\n"
            "  province: str, // 省份\n"
            "  city: str, // 城市\n"
            "  district: str, // 区/县\n"
            "  address: str, // 地址\n"
            "  place_id: str, // 由第三方提供的场地id\n"
            "  latitude: float, // 纬度（十进制度）\n"
            "  longtitude: float, // 经度（十进制度）\n"
            "  nearest_transit: str, // 公共交通描述\n"
            "  has_parking: int, // 是否可以停车\n"
            "  free_parking: int, // 停车是否免费\n"
            "  parking_type: str, // 停车类型，on_street/lot/garage/none\n"
            "  parking_fee_info: str, // 停车收费说明（文本）\n"
            "  parking_capacity: int, // 预估车位数\n"
            "  has_lights: int, // 是否有夜间照明\n"
            "  light_type: str, // 灯光类型（flood/pole/led/none）\n"
            "  light_hours_desc: str, // 灯光启用时段说明\n"
            "  surface_type: str, // 地面材质\n"
            "  surface_notes: str, // 地面情况备注，如破损、坑洼等\n"
            "  total_units_count: int, // 全场个数（不算单独半场）\n"
            "  half_units_count: int, // 半场个数（不算全场）\n"
            "  week_open_hours: str, // 每周开门时间统计\n"
            "  free_open_hours: str, // 每周免费时间统计\n"
            "  week_appointment_hours: str, // 每周需预约的时间统计\n"
            "  appointment_type_desc: str, // 预约方式描述\n"
            "  amenities_summary: str, // 其他基础设施如WC、洗手池、饮水机等统计\n"
            "  gmt_create: str, // 创建时间\n"
            "  creator: str, // 创建人\n"
            "  creator_id: str, // 创建人id\n"
            "  gmt_modified: str, // 修改时间\n"
            "  modifier_id: str, // 修改人id\n"
            "  modifier: str // 修改人\n"
            "}\n\n"
            "# CourtUnit 字段定义（每个字段后有详细描述）\n"
            "{\n"
            "  id: int, // 主键，自增\n"
            "  court_id: int, // 外键，篮球场id\n"
            "  unit_name: str, // 单元名称或编号，如A场\n"
            "  unit_type: str, // 单元类型（full/half/3x3/multi）\n"
            "  length_m: int, // 长度\n"
            "  width_m: int, // 宽度\n"
            "  is_standard: int, // 是否为标准场地\n"
            "  fenced: int, // 是否有围栏\n"
            "  lines_painted: int, // 球线是否清晰可见\n"
            "  surface_condition_score: int, // 场地综合评分，100分满分\n"
            "  hoop_brand: str, // 篮筐/篮板品牌（文本）\n"
            "  hoop_material: str, // 篮板材质\n"
            "  rim_type: str, // 篮筐类型（breakaway/fixed/none）\n"
            "  rim_height_cm: int, // 篮筐高度，厘米制\n"
            "  is_standard_rim: int, // 是否为标准篮筐\n"
            "  unit_status: str, // 单元状态（损坏、临时封闭等）\n"
            "  gmt_create: str, // 创建时间\n"
            "  gmt_modified: str, // 修改时间\n"
            "  modifier_id: str, // 修改人id\n"
            "  modifier: str, // 修改人\n"
            "  creator_id: str, // 创建人id\n"
            "  creator: str, // 创建人\n"
            "  surface_type: str, // 场地地面材质\n"
            "  surface_status: str // 场地地面状态，破损、坑洼等等\n"
            "}\n\n"
            "# 输出格式\n"
            "[\n"
            "  {\n"
            "    'success': 该场地的提取是否成功，true/false,\n"
            "    'basketball_court': {BasketballCourt字段...},\n"
            "    'court_units': [ {CourtUnit字段...}, ... ]\n"
            "  }, ...\n"
            "]\n\n"
            "# 要求\n"
            "1. 只输出上述json格式，不要输出多余内容。\n"
            "2. 字段名、类型、结构必须与定义完全一致。\n"
            "3. 一个输入可能包含多个球场，每个球场下可有多个单元。如果无法从描述中区分出球场有几块场地，默认按照一个全场来算。\n"
            "4. 未获取到的字段请置为空字符串。\n"
            "5. 不要自行编造信息。\n"
            "# 输入内容\n"
            f"{text}\n"
        )
        response = self.invoke(prompt)
        return response