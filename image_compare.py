import requests
from PIL import Image
import imagehash
from io import BytesIO

def are_images_consistent(image_urls):
    """
    处理插图以及角标等*************************
    通过URL列表检查多张图片是否一致（视觉内容相同）
    
    参数:
        image_urls (list): 图片URL的列表
        
    返回:
        bool: 所有图片一致返回True，否则返回False
        str: 错误消息（如果出错），否则为None
    """
    if not image_urls:
        return True, "是空的URL列表（无图片需要比较）"
    
    try:
        # 下载第一张图片作为基准
        first_image = download_image(image_urls[0])
        if first_image is None:
            return False, f"无法下载基准图片: {image_urls[0]}"
            
        ref_hash = calculate_image_hash(first_image)
        
        # 比较后续图片
        for url in image_urls[1:]:
            img = download_image(url)
            if img is None:
                return False, f"图片下载失败: {url}"
                
            current_hash = calculate_image_hash(img)
            if current_hash != ref_hash:
                return False, f"图片不一致: {url}"
        
        return True, "所有图片一致"
    
    except Exception as e:
        return False, f"处理过程中发生错误: {str(e)}"

def download_image(url):
    """下载图片并返回PIL Image对象"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception:
        return None

def calculate_image_hash(image):
    """计算图片的感知哈希（pHash）"""
    return imagehash.phash(image)


if __name__ == "__main__":
    # 示例URL列表
    image_urls = [
        "https://cdn-mineru.openxlab.org.cn/extract/00758bcf-2350-40d9-b883-c99fa469c94a/9bf4e9121f96a725f7dda5bdf96bd4aab72f2569c56de3f8e1f5ca95e7cf6e23.jpg",
        "https://cdn-mineru.openxlab.org.cn/extract/00758bcf-2350-40d9-b883-c99fa469c94a/9bf4e9121f96a725f7dda5bdf96bd4aab72f2569c56de3f8e1f5ca95e7cf6e23.jpg"
    ]
    
    consistent, message = are_images_consistent(image_urls)
    print(f"一致: {consistent}, 消息: {message}")
