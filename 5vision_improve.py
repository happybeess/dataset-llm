# -*- coding: utf-8 -*-
import os
import re
from openai import OpenAI
"""处理Markdown文件中的图片，删除与前后文不相关的图片，并将不相关的图片保存到单独文件，便于审查
使用doubao1.5visionpro的API判断图片与前后文的相关性"""
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key="a066f242-8c2f-4585-bd64-4826a6f34684"
)

def get_context_around_image(content, image_position, context_length=500):
    """
    获取图片前后的文本内容作为上下文
    
    参数:
        content (str): 完整的markdown内容
        image_position (tuple): 图片的位置 (start, end)
        context_length (int): 上下文长度
    
    返回:
        tuple: (前文, 后文)
    """
    start, end = image_position
    
    # 获取图片前的文本
    before_start = max(0, start - context_length)
    before_text = content[before_start:start].strip()
    
    # 获取图片后的文本
    after_end = min(len(content), end + context_length)
    after_text = content[end:after_end].strip()
    
    return before_text, after_text

def is_image_relevant(image_url, before_text, after_text):
    """
    使用AI判断图片是否与前后文相关
    
    参数:
        image_url (str): 图片URL
        before_text (str): 图片前的文本
        after_text (str): 图片后的文本
    
    返回:
        bool: 图片是否相关
    """
    try:
        # 构建提示词
        context_text = f"前文：{before_text}\n\n后文：{after_text}"
        prompt = f"""请判断这张图片是否与给定的前后文内容相关。
        
上下文内容：
{context_text}

请仔细观察图片内容，并分析它是否与上下文的主题、概念或内容相关。
如果图片内容与文本内容有明显的关联性（如：插图、示例、说明等），请回答"相关"。
如果图片内容与文本内容没有明显关联或完全无关，请回答"不相关"。

请只回答"相关"或"不相关"，不要添加其他解释。"""
        
        response = client.chat.completions.create(
            model="doubao-1-5-vision-pro-32k-250115",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"AI判断结果: {result} (图片: {image_url[:50]}...)")
        
        # 如果AI明确回答"不相关"，则返回False
        # 如果AI回答"相关"或其他情况，则返回True（保守处理）
        return "不相关" not in result
        
    except Exception as e:
        print(f"判断图片相关性时出错: {e}")
        # 出错时保守处理，保留图片
        return True

def process_markdown_images(input_file, output_file, irrelevant_file):
    """
    处理Markdown文件中的图片，删除与前后文不相关的图片，并将不相关的图片保存到单独文件
    
    参数:
        input_file (str): 输入的Markdown文件路径
        output_file (str): 输出的Markdown文件路径（只包含相关图片）
        irrelevant_file (str): 不相关图片的保存文件路径
    """
    # 读取markdown文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到所有图片链接及其位置
    image_matches = []
    for match in re.finditer(r'!\[.*?\]\((.*?)\)', content):
        full_link = match.group(0)  # 完整的图片链接
        url = match.group(1)        # URL部分
        position = (match.start(), match.end())
        image_matches.append((full_link, url, position))
    
    print(f"找到 {len(image_matches)} 个图片链接")
    
    if not image_matches:
        print("没有找到图片链接，直接复制文件")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return
    
    # 标记需要删除的图片和保存不相关图片的信息
    images_to_remove = []
    irrelevant_images_info = []
    
    for i, (full_link, url, position) in enumerate(image_matches):
        print(f"\n处理第 {i+1}/{len(image_matches)} 张图片: {url[:50]}...")
        
        # 获取图片前后的上下文
        before_text, after_text = get_context_around_image(content, position)
        
        print(f"前文预览: {before_text[-100:] if len(before_text) > 100 else before_text}")
        print(f"后文预览: {after_text[:100] if len(after_text) > 100 else after_text}")
        
        # 判断图片是否相关
        if not is_image_relevant(url, before_text, after_text):
            print(f"########################标记删除############################################: {url}")
            images_to_remove.append((full_link, position))
            # 保存不相关图片的信息
            irrelevant_images_info.append({
                'image': full_link,
                'url': url,
                'before_text': before_text,
                'after_text': after_text,
                'position': position
            })
        else:
            print(f"保留图片: {url}")
    
    # 从后向前删除图片，避免位置偏移
    cleaned_content = content
    images_to_remove.sort(key=lambda x: x[1][0], reverse=True)
    
    for full_link, (start, end) in images_to_remove:
        cleaned_content = cleaned_content[:start] + cleaned_content[end:]
    
    # 写入处理后的文件（只包含相关图片）
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    # 创建不相关图片的文档
    irrelevant_content = "# 不相关图片集合\n\n"
    irrelevant_content += f"本文档包含了从原始文档中识别出的 {len(irrelevant_images_info)} 张与上下文不相关的图片。\n\n"
    irrelevant_content += "---\n\n"
    
    for i, info in enumerate(irrelevant_images_info, 1):
        irrelevant_content += f"## 不相关图片 {i}\n\n"
        irrelevant_content += f"**图片链接：** {info['image']}\n\n"
        irrelevant_content += f"**图片URL：** {info['url']}\n\n"
        irrelevant_content += f"**前文上下文：**\n```\n{info['before_text']}\n```\n\n"
        irrelevant_content += f"**后文上下文：**\n```\n{info['after_text']}\n```\n\n"
        irrelevant_content += "---\n\n"
    
    # 写入不相关图片文档
    with open(irrelevant_file, 'w', encoding='utf-8') as f:
        f.write(irrelevant_content)
    
    print(f"\n处理完成！")
    print(f"原始图片数量: {len(image_matches)}")
    print(f"删除图片数量: {len(images_to_remove)}")
    print(f"保留图片数量: {len(image_matches) - len(images_to_remove)}")
    print(f"相关图片文档保存到: {output_file}")
    print(f"不相关图片文档保存到: {irrelevant_file}")

if __name__ == "__main__":
    input_file = r"E:\process\book\chinese_upgrade_no_duplicates.md"
    output_file = r"E:\process\book\chinese_upgrade_relevant_images.md"
    irrelevant_file = r"E:\process\book\chinese_upgrade_irrelevant_images.md"
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在 {input_file}")
    else:
        process_markdown_images(input_file, output_file, irrelevant_file)