from lmdeploy import pipeline, GenerationConfig, TurbomindEngineConfig

import streamlit as st
import torch
from modelscope import snapshot_download


def prepare_generation_config():

    gen_config = GenerationConfig(
        top_p=0.8,
        top_k=40,
        temperature=0.7,
        # max_new_tokens=4096
    )
    return gen_config


@st.cache_resource
def load_turbomind_model(model_dir, model_format="hf"):  # hf awq

    # model_dir = snapshot_download(model_dir, revision="master")
    backend_config = TurbomindEngineConfig(model_format=model_format, session_len=32768)
    pipe = pipeline(model_dir, backend_config=backend_config, log_level="INFO")

    return pipe, None


def combine_history(prompt, meta_instruction, history_msg=None):
    total_prompt = [
        [
            {
                "role": "system",
                "content": meta_instruction,
            },
        ],
    ]
    if history_msg is not None:
        for message in history_msg:
            total_prompt[0].append(
                {
                    "role": message["role"],
                    "content": message["content"],
                }
            )

    total_prompt[0].append(
        {
            "role": "user",
            "content": prompt,
        }
    )
    return total_prompt


def get_turbomind_response(
    prompt,
    meta_instruction,
    user_avator,
    robot_avator,
    model_pipe,
    tokenizer,
    session_messages,
    first_input=False,
):
    real_prompt = combine_history(prompt, meta_instruction, history_msg=session_messages)  # 是否加上历史对话记录
    print(real_prompt)

    # Add user message to chat history
    if not first_input:
        session_messages.append({"role": "user", "content": prompt, "avatar": user_avator})

    with st.chat_message("assistant", avatar=robot_avator):
        message_placeholder = st.empty()
        cur_response = ""
        for item in model_pipe.stream_infer(real_prompt, gen_config=prepare_generation_config()):
            cur_response += item.text
            # if cur_response == "~":
            # continue
            message_placeholder.markdown(cur_response + "▌")
        message_placeholder.markdown(cur_response)

    # Add robot response to chat history
    session_messages.append(
        {
            "role": "assistant",
            "content": cur_response,  # pylint: disable=undefined-loop-variable
            "avatar": robot_avator,
        }
    )
    torch.cuda.empty_cache()