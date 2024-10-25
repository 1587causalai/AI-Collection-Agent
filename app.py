#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import copy
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from utils.web_configs import WEB_CONFIGS #

# 初始化 Streamlit 页面配置
st.set_page_config(
    page_title="AI-Collection-Agent - 智能电话催收机器人",
    page_icon="☎️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/PeterH0323/AI-Collection-Agent/tree/main",
        "Report a bug": "https://github.com/PeterH0323/AI-Collection-Agent/issues",
        "About": "# AI-Collection-Agent - 智能电话催收机器人",
    },
)
from utils.rag.rag_worker import gen_rag_db # RAG 相关配置
from utils.tools import resize_image

from utils.model_loader import RAG_RETRIEVER  # 读入相关模型


# 这段代码定义了一个 Streamlit 对话框函数，用于显示产品说明书
@st.experimental_dialog("说明书", width="large")
def instruction_dialog(instruction_path):
    """
    显示产品说明书的popup窗口。

    通过给定的说明书路径，将文件内容以markdown格式在Streamlit应用中显示出来，并提供一个“确定”按钮供用户确认阅读。

    Args:
        instruction_path (str): 说明书的文件路径，该文件应为文本文件，并使用utf-8编码。
    """
    print(f"Show instruction : {instruction_path}")
    with open(instruction_path, "r", encoding="utf-8") as f:
        instruct_lines = "".join(f.readlines())

    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    st.markdown(instruct_lines)
    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    if st.button("确定"):
        st.rerun()

# 按钮点击事件的回调函数
def on_btton_click(*args, **kwargs):
    """
    按钮点击事件的回调函数。
    """

    # 根据按钮类型执行相应操作
    if kwargs["type"] == "check_instruction":
        # 显示说明书
        st.session_state.show_instruction_path = kwargs["instruction_path"]

    elif kwargs["type"] == "process_sales":
        # 切换到主播卖货页面
        st.session_state.page_switch = "pages/selling_page.py"

        # 更新会话状态中的产品信息
        st.session_state.hightlight = kwargs["heighlights"]
        product_info_struct = copy.deepcopy(st.session_state.product_info_struct_template)
        product_info_str = product_info_struct[0].replace("{name}", kwargs["product_name"])
        product_info_str += product_info_struct[1].replace("{highlights}", st.session_state.hightlight)

        # 生成商品文案 prompt
        st.session_state.first_input = copy.deepcopy(st.session_state.first_input_template).replace(
            "{product_info}", product_info_str
        )

        # 更新图片路径和产品名称
        st.session_state.image_path = kwargs["image_path"]
        st.session_state.product_name = kwargs["product_name"]

        # 更新发货地、快递公司名称
        st.session_state.departure_place = kwargs["departure_place"]
        st.session_state.delivery_company_name = kwargs["delivery_company_name"]

        # 设置为默认数字人视频路径
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH

        # # 清空语音
        # if ENABLE_TTS:
        #     for message in st.session_state.messages:
        #         if "wav" not in message:
        #             continue
        #         Path(message["wav"]).unlink()

        # 清空历史对话
        st.session_state.messages = []

# 创建催收任务卡片
def make_client_container(client_id, client_info, image_height, each_card_offset):
    """
    创建催收任务卡片
    """
    # 创建带边框的客户信息容器，设置高度
    with st.container(border=True, height=image_height + each_card_offset):

        # 页面标题使用客户ID
        st.header(client_id)

        # 划分左右两列，左侧为图片，右侧为客户信息
        image_col, info_col = st.columns([0.1, 0.9])

        # 图片展示区域
        with image_col:
            # print(f"Loading {client_info['images']} ...")
            image = resize_image(None, max_height=image_height)
            st.image(image, channels="bgr")
            pass

        # 客户信息展示区域
        with info_col:
            # 亮点展示
            st.subheader("关键信息", divider="grey")
            highlights_str = "、".join(client_info["highlights"])
            st.text(highlights_str)

            # 客户详细信息按钮
            st.subheader("详细信息", divider="grey")
            st.button(
                "查看",
                key=f"check_instruction_{client_id}",
                on_click=on_btton_click,
                kwargs={
                    "type": "check_instruction",
                    "product_name": client_id,  # 这里仍使用原有的参数名，但传入client_id
                    "instruction_path": client_info["instruction"],
                },
            )

            # 开始催收按钮
            st.subheader("个性化催收", divider="grey")
            st.button(
                "开始催收",  # 修改按钮文字
                key=f"process_sales_{client_id}",
                on_click=on_btton_click,
                kwargs={
                    "type": "process_sales",
                    "product_name": client_id,  # 这里仍使用原有的参数名，但传入client_id
                    "heighlights": highlights_str,
                    "image_path": client_info["images"],
                    "departure_place": client_info["departure_place"],
                    "delivery_company_name": client_info["delivery_company_name"],
                },
            )

# 删除指定目录下超过一定时间的文件
def delete_old_files(directory, limit_time_s=60 * 60 * 5):
    """
    删除指定目录下超过一定时间的文件。

    :param directory: 要检查和删除文件的目录路径
    """
    # 获取当前时间戳
    current_time = time.time()

    # 遍历目录下的所有文件和子目录
    for file_path in Path(directory).iterdir():

        # 获取文件的修改时间戳
        file_mtime = os.path.getmtime(file_path)

        # 计算文件的年龄（以秒为单位）
        file_age_seconds = current_time - file_mtime

        # 检查文件是否超过 n 秒
        if file_age_seconds > limit_time_s:
            try:

                if file_path.is_dir():
                    shutil.rmtree(file_path)
                    continue

                # 删除文件
                file_path.unlink()
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

# 从配置文件中加载销售相关信息，并存储到session状态中
def get_sales_info():
    """
    从配置文件中加载销售相关信息，并存储到session状态中。

    该函数不接受参数，也不直接返回任何值，但会更新全局的session状态，包括：
    - sales_info: 系统问候语，针对销售角色定制
    - first_input_template: 对话开始时的第一个输入模板
    - product_info_struct_template: 产品信息结构模板

    """

    # 加载对话配置文件
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 从配置中提取角色信息
    sales_info = dataset_yaml["role_type"][WEB_CONFIGS.SALES_NAME]

    # 从配置中提取对话设置相关的信息
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", WEB_CONFIGS.SALES_NAME).replace("{character}", "、".join(sales_info))

    # 更新session状态，存储销售相关信息
    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct

# 初始化客户信息列表
def init_product_info():
    """
    初始化客户信息列表
    """
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        client_info_dict = yaml.safe_load(f)

    # 根据 ID 排序，避免乱序
    client_info_dict = dict(sorted(client_info_dict.items(), key=lambda item: item[1]["id"]))

    client_list = list(client_info_dict.keys())[:2]

    # 生成客户信息卡片
    for row_id in range(0, len(client_list), WEB_CONFIGS.EACH_ROW_COL):
        for col_id, col_handler in enumerate(st.columns(WEB_CONFIGS.EACH_ROW_COL)):
            with col_handler:
                if row_id + col_id >= len(client_list):
                    continue

                client_name = client_list[row_id + col_id]
                client_info = client_info_dict[client_name]
                
                # 使用客户ID作为标题
                client_id = f"客户ID: {client_info['id']}"
                
                make_client_container(
                    client_id, 
                    client_info, 
                    WEB_CONFIGS.PRODUCT_IMAGE_HEIGHT, 
                    WEB_CONFIGS.EACH_CARD_OFFSET
                )

    return len(client_list)

# TTS 初始化
def init_tts():
    # TTS 初始化
    if "gen_tts_checkbox" not in st.session_state:
        st.session_state.gen_tts_checkbox = WEB_CONFIGS.ENABLE_TTS
    if WEB_CONFIGS.ENABLE_TTS:
        # 清除 1 小时之前的所有语音
        Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).mkdir(parents=True, exist_ok=True)
        delete_old_files(WEB_CONFIGS.TTS_WAV_GEN_PATH)

# 数字人 初始化
def init_digital_human():
    # 数字人 初始化
    if "digital_human_video_path" not in st.session_state:
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH
    if "gen_digital_human_checkbox" not in st.session_state:
        st.session_state.gen_digital_human_checkbox = WEB_CONFIGS.ENABLE_DIGITAL_HUMAN

    if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
        # 清除 1 小时之前的所有视频
        Path(WEB_CONFIGS.DIGITAL_HUMAN_GEN_PATH).mkdir(parents=True, exist_ok=True)
        # delete_old_files(st.session_state.digital_human_root)

# ASR 初始化
def init_asr():
    # 清理 ASR 旧文件
    if WEB_CONFIGS.ENABLE_ASR and Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).exists():
        delete_old_files(WEB_CONFIGS.ASR_WAV_SAVE_PATH)

    st.session_state.asr_text_cache = ""


def main():
    """
    初始化页面配置，加载模型，处理页面跳转，并展示商品信息。
    """
    print("Starting...")

    # 初始化页面跳转
    if "page_switch" not in st.session_state:
        st.session_state.page_switch = "app.py"
    st.session_state.current_page = "app.py"

    # 显示商品说明书
    if "show_instruction_path" not in st.session_state:
        st.session_state.show_instruction_path = "X-X"
    if st.session_state.show_instruction_path != "X-X":
        instruction_dialog(st.session_state.show_instruction_path)
        st.session_state.show_instruction_path = "X-X"

    # 判断是否需要跳转页面
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # TTS 初始化
    init_tts()

    # 数字人 初始化
    init_digital_human()

    # ASR 初始化
    init_asr()

    if "enable_agent_checkbox" not in st.session_state:
        st.session_state.enable_agent_checkbox = WEB_CONFIGS.ENABLE_AGENT

        if WEB_CONFIGS.AGENT_DELIVERY_TIME_API_KEY is None or WEB_CONFIGS.AGENT_WEATHER_API_KEY is None:
            WEB_CONFIGS.ENABLE_AGENT = False
            st.session_state.enable_agent_checkbox = False

    # 获取销售信息
    if "sales_info" not in st.session_state:
        get_sales_info()

    # 添加页面导航页
    st.sidebar.page_link("app.py", label="催收任务", disabled=True)
    st.sidebar.page_link("./pages/selling_page.py", label="智能催收")

    # 主页标题: 
    st.title("AI-Collection-Agent - 智能电话催收机器人") 
    st.header("催收机器人后台", divider="grey")

    # 说明
    st.info(
        "这里需要展示催收机器人后台，包括催收任务列表、催收记录、催收成功率等指标。",
        icon="ℹ️",
    )

    # 初始化客户列表
    client_num = init_product_info()

    # 侧边栏显示客户数量，入驻品牌方
    with st.sidebar:
        # 标题
        st.header("AI-Collection-Agent - 智能电话催收机器人", divider="grey")
        st.subheader("功能点：", divider="grey")
        st.markdown(
            "1. 📜 **个性化催收话术生成**\n"
            "2. 📚 **RAG 检索增强生成**\n"
            "3. 🎙️ **ASR 语音识别**\n"
            "4. 🔊 **TTS 文字转语音输出**\n"
            "5. 🌐 **Agent 查询欠款信息**"
        )

        st.subheader(f"催收后台信息", divider="grey")
        st.markdown(f"电话催收：{client_num} 人次")

        # TODO 单品成交量
        # st.markdown(f"共有品牌方：{len(client_name_list)} 个")

        if WEB_CONFIGS.ENABLE_TTS:
            # 是否生成 TTS
            st.subheader(f"TTS 配置", divider="grey")
            st.session_state.gen_tts_checkbox = st.toggle("生成语音", value=st.session_state.gen_tts_checkbox)

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
            # 是否生成 数字人
            st.subheader(f"数字人 配置", divider="grey")
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "生成数字人视频", value=st.session_state.gen_digital_human_checkbox
            )

        if WEB_CONFIGS.ENABLE_AGENT:
            # 是否使用 agent
            st.subheader(f"Agent 配置", divider="grey")
            with st.container(border=True):
                st.markdown("**插件列表**")
                st.button("结合天气查询到货时间", type="primary")
            st.session_state.enable_agent_checkbox = st.toggle("使用 Agent 能力", value=st.session_state.enable_agent_checkbox)

    # 添加催收任务
    with st.form(key="add_collection_task_form"):
        debtor_id = st.text_input(label="欠款人ID")
        debtor_name = st.text_input(label="欠款人姓名")
        debt_amount = st.number_input(label="欠款金额", min_value=0.0, step=100.0)
        due_date = st.date_input(label="到期日期")
        contact_number = st.text_input(label="联系电话")
        address = st.text_area(label="地址")
        notes = st.text_area(label="备注信息")
        
        submit_button = st.form_submit_button(label="提交", disabled=WEB_CONFIGS.DISABLE_UPLOAD)

        if WEB_CONFIGS.DISABLE_UPLOAD:
            st.info(
                "Github 上面的代码已支持添加新催收任务的逻辑。\n但因开放性的 Web APP 没有新增任务审核机制，暂不在此开放添加功能。\n您可以 clone 本项目到您的机器启动即可使能上传按钮",
                icon="ℹ️",
            )

        if submit_button:
            add_collection_task(
                debtor_id,
                debtor_name,
                debt_amount,
                due_date,
                contact_number,
                address,
                notes
            )


def add_collection_task(
    debtor_id, debtor_name, debt_amount, due_date, contact_number, address, notes
):
    """
    添加催收任务的函数。

    参数:
    - debtor_id: 欠款人ID。
    - debtor_name: 欠款人姓名。
    - debt_amount: 欠款金额。
    - due_date: 到期日期。
    - contact_number: 联系电话。
    - address: 地址。
    - notes: 备注信息。

    返回值:
    无。该函数直接操作UI状态，不返回任何值。
    """

    # 检查入参
    if debtor_id == "" or debtor_name == "":
        st.error("欠款人ID和姓名不能为空")
        return

    if debt_amount == 0 or due_date is None or contact_number == "":
        st.error("欠款金额、到期日期和联系电话不能为空")
        return

    # 显示上传状态，并执行上传操作
    with st.status("正在添加催收任务...", expanded=True) as status:

        # 更新催收任务列表
        if "collection_tasks" not in st.session_state:
            st.session_state.collection_tasks = []

        new_task = {
            "debtor_id": debtor_id,
            "debtor_name": debtor_name,
            "debt_amount": debt_amount,
            "due_date": due_date,
            "contact_number": contact_number,
            "address": address,
            "notes": notes
        }

        st.session_state.collection_tasks.append(new_task)

        # 更新状态
        status.update(label="添加催收任务成功!", state="complete", expanded=False)

        st.toast("添加催收任务成功!", icon="🎉")

        with st.spinner("准备刷新页面..."):
            time.sleep(3)

        # 刷新页面
        st.rerun()


if __name__ == "__main__":
    # streamlit run app.py --server.address=0.0.0.0 --server.port 7860

    # print("Starting...")
    main()



