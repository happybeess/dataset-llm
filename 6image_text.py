# -*- coding: utf-8 -*-
import os
import re
from openai import OpenAI
"""将Markdown文件中的图片替换为结合上下文的具体描述
使用doubao1.5visionpro的API分析图片内容并生成描述"""

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

def generate_image_description(image_url, before_text, after_text):
    """
    使用AI生成图片的具体描述，结合上下文
    
    参数:
        image_url (str): 图片URL
        before_text (str): 图片前的文本
        after_text (str): 图片后的文本
    
    返回:
        str: 图片的描述文本
    """
    try:
        # 构建提示词
        context_text = f"前文：{before_text}\n\n后文：{after_text}"
        prompt = f"""请仔细观察这张图片，并结合给定的上下文内容，生成一个准确、详细、具体的图片描述。

上下文内容：
{context_text}

要求：
1. 描述要非常详细具体，包含图片中的所有重要元素和细节
2. 如果是人物，描述其外貌、动作、表情、服装等
3. 如果是场景，描述环境、物品、颜色、布局等
4. 如果包含文字，完整准确地识别并包含所有文字内容
5. 如果是图表、示意图，详细说明类型、数据、标签、趋势等
6. 如果是教学内容，详细描述知识点、步骤、公式等
7. 结合上下文主题，突出图片与文本的关联性
8. 描述要生动具体，让读者能够清晰想象图片内容
9. 用中文回答，不要包含"这张图片显示"等开头语
10. 描述长度要充分，不要过于简短

请直接给出详细的图片描述："""
        
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
            max_tokens=500,
            temperature=0.3
        )
        
        description = response.choices[0].message.content.strip()
        print(f"生成描述: {description[:50]}... (图片: {image_url[:50]}...)")
        
        return description
        
    except Exception as e:
        print(f"生成图片描述时出错: {e}")
        # 出错时返回默认描述
        return "[图片内容]"  # 简单的占位符

def replace_images_with_descriptions(input_file, output_file):
    """
    将Markdown文件中的图片替换为具体描述
    
    参数:
        input_file (str): 输入的Markdown文件路径
        output_file (str): 输出的Markdown文件路径
    """
    # 读取markdown文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到所有图片链接及其位置
    image_matches = []
    for match in re.finditer(r'!\[.*?\]\((.*?)\)', content):
        full_link = match.group(0)  # 完整的图片链接
        alt_text = re.search(r'!\[(.*?)\]', match.group(0))
        alt_text = alt_text.group(1) if alt_text else ""
        url = match.group(1)        # URL部分
        position = (match.start(), match.end())
        image_matches.append((full_link, alt_text, url, position))
    
    print(f"找到 {len(image_matches)} 个图片链接")
    
    if not image_matches:
        print("没有找到图片链接，直接复制文件")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return
    
    # 从后向前替换图片，避免位置偏移
    processed_content = content
    image_matches.sort(key=lambda x: x[3][0], reverse=True)
    
    for i, (full_link, alt_text, url, position) in enumerate(image_matches):
        print(f"\n处理第 {len(image_matches)-i}/{len(image_matches)} 张图片: {url[:50]}...")
        
        # 获取图片前后的上下文
        before_text, after_text = get_context_around_image(processed_content, position)
        
        print(f"前文预览: {before_text[-100:] if len(before_text) > 100 else before_text}")
        print(f"后文预览: {after_text[:100] if len(after_text) > 100 else after_text}")
        
        # 生成图片描述
        description = generate_image_description(url, before_text, after_text)
        
        # 替换图片链接为描述文本
        start, end = position
        # 保持一定的格式，用方括号包围描述，前面加上提示文字
        replacement_text = f"接下来是一张图片：[图片描述：{description}]"
        processed_content = processed_content[:start] + replacement_text + processed_content[end:]
        
        print(f"替换完成: {replacement_text[:50]}...")
    
    # 写入处理后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    
    print(f"\n处理完成！")
    print(f"原始图片数量: {len(image_matches)}")
    print(f"已替换为描述文本")
    print(f"结果保存到: {output_file}")

if __name__ == "__main__":
    input_file = r"E:\process\book\chinese_upgrade_relevant_images.md"
    output_file = r"E:\process\book\chinese_upgrade_text_only.md"
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在 {input_file}")
    else:
        replace_images_with_descriptions(input_file, output_file)