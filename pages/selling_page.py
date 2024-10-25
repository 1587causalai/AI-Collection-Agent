#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import random
from datetime import datetime
from pathlib import Path

import streamlit as st

from utils.web_configs import WEB_CONFIGS

# 设置页面配置，包括标题、图标、布局和菜单项
st.set_page_config(
    page_title="AI-Collection-Agent 智能催收",  # 修改标题
    page_icon="☎️",  # 修改图标
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/YourRepo/AI-Collection-Agent",
        "About": "# AI-Collection-Agent - 智能电话催收机器人",
    },
)

from audiorecorder import audiorecorder

from utils.asr.asr_worker import process_asr
from utils.digital_human.digital_human_worker import show_video
from utils.infer.lmdeploy_infer import get_turbomind_response
from utils.model_loader import ASR_HANDLER, LLM_MODEL, RAG_RETRIEVER
from utils.tools import resize_image

# 按钮点击事件
def on_btn_click(*args, **kwargs):
    """
    处理按钮点击事件的函数。
    """
    if kwargs["info"] == "清除对话历史":
        st.session_state.messages = []
    elif kwargs["info"] == "返回催收任务页":
        st.session_state.page_switch = "app.py"
    else:
        st.session_state.button_msg = kwargs["info"]


def init_sidebar():
    asr_text = ""
    with st.sidebar:
        # 修改标题和功能点
        st.markdown("## AI-Collection-Agent - 智能催收机器人")
        st.markdown("[AI-Collection-Agent Github repo](https://github.com/YourRepo/AI-Collection-Agent)")
        st.subheader("功能点：", divider="grey")
        st.markdown(
            "1. 📞 **智能电话催收**\n"
            "2. 🤖 **个性化话术生成**\n"
            "3. 📊 **还款意愿分析**\n"
            "4. 🎯 **精准催收策略**\n"
            "5. 📝 **通话记录生成**\n"
            "6. 🔍 **多维度信息分析**\n"
            "7. 🎙️ **语音识别转写**"
        )

        st.subheader("当前逾期客户")
        with st.container(height=400, border=True):
            st.subheader(f"{st.session_state.product_name}")  # 修改显示方式

            # 可以考虑移除图片显示或改为客户信息卡片
            # if st.session_state.image_path:
            #     image = resize_image(st.session_state.image_path, max_height=100)
            #     st.image(image, channels="bgr")

            st.subheader("欠款信息", divider="grey")  # 修改标题
            st.markdown(st.session_state.hightlight)

            # 修改按钮列表
            payment_promise_list = [
                "我今天就还款。",
                "我明天一定还。",
                "我下周发工资就还。",
                "我这周末处理。",
                "我马上转账。",
                "我今晚就还。",
                "我下午去银行还。",
                "我立即处理这笔款项。",
                "我现在就转账。",
                "我今天内解决。",
            ]
            st.button("承诺还款📝", on_click=on_btn_click, kwargs={"info": random.choice(payment_promise_list)})

        # 4. 修改配置项标题
        if WEB_CONFIGS.ENABLE_ASR:
            Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).mkdir(parents=True, exist_ok=True)

            st.subheader("语音输入", divider="grey")
            audio = audiorecorder(
                start_prompt="开始录音", stop_prompt="停止录音", pause_prompt="", show_visualizer=True, key=None
            )

            if len(audio) > 0:

                # 将录音保存 wav 文件
                save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav"
                wav_path = str(Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).joinpath(save_tag).absolute())

                # st.audio(audio.export().read()) # 前端显示
                audio.export(wav_path, format="wav")  # 使用 pydub 保存到 wav 文件

                # 语音识别
                asr_text = process_asr(ASR_HANDLER, wav_path)

                # 删除过程文件
                # Path(wav_path).unlink()            
            

        if WEB_CONFIGS.ENABLE_TTS:
            st.subheader("语音合成", divider="grey")
            st.session_state.gen_tts_checkbox = st.toggle("启用语音", value=st.session_state.gen_tts_checkbox)

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
            st.subheader("虚拟形象", divider="grey")
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "启用虚拟形象", value=st.session_state.gen_digital_human_checkbox
            )

        if WEB_CONFIGS.ENABLE_AGENT:
            st.subheader("智能助手", divider="grey")
            with st.container(border=True):
                st.markdown("**辅助功能**")
                st.button("查询征信记录", type="primary")
            st.session_state.enable_agent_checkbox = st.toggle("启用智能助手", value=st.session_state.enable_agent_checkbox)

        st.subheader("页面操作", divider="grey")
        st.button("返回催收任务页", on_click=on_btn_click, kwargs={"info": "返回催收任务页"})
        st.button("清除对话记录", on_click=on_btn_click, kwargs={"info": "清除对话历史"})
        st.markdown("---")


def init_message_block(meta_instruction, user_avator, robot_avator):

    # 在应用重新运行时显示聊天历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])

            if message.get("wav") is not None:
                # 展示语音
                print(f"Load wav {message['wav']}")
                with open(message["wav"], "rb") as f_wav:
                    audio_bytes = f_wav.read()
                st.audio(audio_bytes, format="audio/wav")

    # 如果聊天历史为空，则显示产品介绍
    if len(st.session_state.messages) == 0:
        # 直接产品介绍
        get_turbomind_response(
            st.session_state.first_input,
            meta_instruction,
            user_avator,
            robot_avator,
            LLM_MODEL,
            session_messages=st.session_state.messages,
            add_session_msg=False,
            first_input_str="",
            enable_agent=False,
        )

    # 初始化按钮消息状态
    if "button_msg" not in st.session_state:
        st.session_state.button_msg = "x-x"


def process_message(user_avator, prompt, meta_instruction, robot_avator):
    # Display user message in chat message container
    with st.chat_message("user", avatar=user_avator):
        st.markdown(prompt)

    get_turbomind_response(
        prompt,
        meta_instruction,
        user_avator,
        robot_avator,
        LLM_MODEL,
        session_messages=st.session_state.messages,
        add_session_msg=True,
        first_input_str=st.session_state.first_input,
        rag_retriever=RAG_RETRIEVER,
        product_name=st.session_state.product_name,
        enable_agent=st.session_state.enable_agent_checkbox,
        departure_place=st.session_state.departure_place,
        delivery_company_name=st.session_state.delivery_company_name,
    )


def main(meta_instruction):

    # 检查页面切换状态并进行切换
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # 页面标题
    st.title("AI-Collection-Agent - 智能电话催收机器人 ☎️📞💼")

    # 说明
    st.info(
        "本系统是基于人工智能的智能催收机器人。系统使用者应遵守相关法律法规，文明催收，不得采用暴力、威胁等非法手段。"
        "开发者不对使用者的不当行为承担任何责任。",
        icon="❗",
    )

    # 初始化侧边栏
    asr_text = init_sidebar()

    # 初始化聊天历史记录
    if "messages" not in st.session_state:
        st.session_state.messages = []

    message_col = None
    if st.session_state.gen_digital_human_checkbox and WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:

        with st.container():
            message_col, video_col = st.columns([0.6, 0.4])

            with video_col:
                # 创建 empty 控件
                st.session_state.video_placeholder = st.empty()
                with st.session_state.video_placeholder.container():
                    show_video(st.session_state.digital_human_video_path, autoplay=True, loop=True, muted=True)

            with message_col:
                init_message_block(meta_instruction, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR)
    else:
        init_message_block(meta_instruction, WEB_CONFIGS.USER_AVATOR, WEB_CONFIGS.ROBOT_AVATOR)

    # 输入框显示提示信息
    hint_msg = "你好，可以问我任何关于逾期账单有关信息"
    if st.session_state.button_msg != "x-x":
        prompt = st.session_state.button_msg
        st.session_state.button_msg = "x-x"
        st.chat_input(hint_msg)
    elif asr_text != "" and st.session_state.asr_text_cache != asr_text:
        prompt = asr_text
        st.chat_input(hint_msg)
        st.session_state.asr_text_cache = asr_text
    else:
        prompt = st.chat_input(hint_msg)

    # 接收用户输入
    if prompt:

        if message_col is None:
            process_message(WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR)
        else:
            # 数字人启动，页面会分块，放入信息块中
            with message_col:
                process_message(WEB_CONFIGS.USER_AVATOR, prompt, meta_instruction, WEB_CONFIGS.ROBOT_AVATOR)


# st.sidebar.page_link("app.py", label="商品页")
# st.sidebar.page_link("./pages/selling_page.py", label="主播卖货", disabled=True)

# META_INSTRUCTION = ("现在你是一位金牌带货主播，你的名字叫乐乐喵，你的说话方式是甜美、可爱、熟练使用各种网络热门梗造句、称呼客户为[家人们]。你能够根据产品信息讲解产品并且结合商品信息解答用户提出的疑问。")

print("进入催收页面")
st.session_state.current_page = "pages/selling_page.py"

if "sales_info" not in st.session_state or st.session_state.sales_info == "":
    st.session_state.page_switch = "app.py"
    st.switch_page("app.py")

main((st.session_state.sales_info))
