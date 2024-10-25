import cv2
import numpy as np


def resize_image(image_path, max_height=None):
    """
    调整图片大小。
    如果图片路径无效，返回一个默认的空白图片。
    """
    if image_path is None:
        # 创建一个默认的灰色图片
        return np.ones((100, 100, 3), dtype=np.uint8) * 128

    # 读取图片
    image = cv2.imread(image_path)
    
    # 如果图片读取失败，返回默认图片
    if image is None:
        print(f"Warning: Could not load image from {image_path}")
        return np.ones((100, 100, 3), dtype=np.uint8) * 128

    # 如果没有指定最大高度，直接返回原图
    if max_height is None:
        return image

    # 计算调整后的尺寸
    height, width = image.shape[:2]
    ratio = max_height / height
    new_size = (int(width * ratio), max_height)

    # 调整图片大小
    resized_image = cv2.resize(image, new_size)
    return resized_image
