import os
from modelscope import snapshot_download
from modelscope.utils.constant import Invoke, ThirdParty

# 配置下载目录
ASR_MODEL_DIR = "./weights/asr_weights/"
os.makedirs(ASR_MODEL_DIR, exist_ok=True)

# 模型映射
NAME_MAPS_MS = {
    "paraformer-zh": "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "fsmn-vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "ct-punc": "iic/punc_ct-transformer_cn-en-common-vocab471067-large"
}

def test_download_asr_models():
    # 模型下载
    model_path_info = dict()
    
    for model_name in ["paraformer-zh", "fsmn-vad", "ct-punc"]:
        print(f"\n开始下载模型: {model_name}")
        print(f"模型路径: {NAME_MAPS_MS[model_name]}")
        
        try:
            mode_dir = snapshot_download(
                NAME_MAPS_MS[model_name],
                revision="master",
                user_agent={Invoke.KEY: Invoke.PIPELINE, ThirdParty.KEY: "funasr"},
                cache_dir=ASR_MODEL_DIR,
            )
            model_path_info[model_name] = mode_dir
            print(f"下载成功: {mode_dir}")
            
        except Exception as e:
            print(f"下载失败: {str(e)}")
            
    return model_path_info

if __name__ == "__main__":
    print("开始测试ASR模型下载...")
    model_paths = test_download_asr_models()
    print("\n下载结果:")
    for model_name, path in model_paths.items():
        print(f"{model_name}: {path}")