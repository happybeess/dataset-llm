import re
import os
"""
清理Markdown文件中的拼音和图片链接(保留图片链接)，
1. 删除模糊的图片
3. 删除拼音标注
4. 精确替换拼音，但保留空格和格式
5. 删除特殊符号 $0$ 和类似的无法识别的正则表达式符号
6. 删除所有 $\textcircled{...}$ 格式的符号，支持多层嵌套花括号
7. 保护Markdown图片链接，避免被清理
"""
def clean_markdown(input_file, output_file):
    # 读取markdown文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 0. 识别并保护所有Markdown图片链接
    # 使用正则表达式匹配Markdown图片链接格式 ![alt text](image_url)
    image_links = []
    image_positions = []
    
    # 找到所有图片链接及其位置
    for match in re.finditer(r'!\[.*?\]\(.*?\)', content):
        image_links.append(match.group(0))
        image_positions.append((match.start(), match.end()))
    
    # 创建一个不包含图片链接的内容副本
    content_without_images = content
    # 从后向前替换，这样不会影响前面的位置
    for i in range(len(image_links) - 1, -1, -1):
        start, end = image_positions[i]
        content_without_images = content_without_images[:start] + f"IMAGE_PLACEHOLDER_{i}_PROTECTED" + content_without_images[end:]
    
    # 创建一个新的内容副本，我们将在这个副本上进行所有的清理操作
    cleaned_content = content_without_images
    
    # 1. 删除模糊的图片和重复的图片
    # 删除图片标记
    cleaned_content = re.sub(r'\(图\)[^\n]*', '', cleaned_content)
    
    # 2. 删除HTML表格形式的拼音列表
    cleaned_content = re.sub(r'<html><body><table>.*?</table></body></html>', '', cleaned_content, flags=re.DOTALL)
    
    # 3. 删除拼音标注 - 使用通用正则表达式匹配所有拼音
    # 拼音由小写字母a-z组成，长度通常为1-6个字符
    
    # 4. 精确替换拼音，但保留空格和格式
    # 处理空格分隔的拼音 - 使用空格替换，保留原有格式
    cleaned_content = re.sub(r'(?<=\s)[a-z]{1,6}(?=\s)', lambda m: ' ' * len(m.group(0)), cleaned_content)
    
    # 处理行尾的拼音 - 使用空格替换，保留原有格式
    cleaned_content = re.sub(r'(?<=\S)\s+[a-z]{1,6}\s*$', lambda m: ' ' * len(m.group(0)), cleaned_content, flags=re.MULTILINE)
    
    # 处理行中的拼音 - 保留一个空格，确保格式不变
    cleaned_content = re.sub(r'(?<=\S)\s+[a-z]{1,6}\s+(?=\S)', ' ', cleaned_content)
    
    # 处理紧跟在汉字后的拼音（无空格）- 直接删除，不影响格式
    cleaned_content = re.sub(r'(?<=[\u4e00-\u9fa5])[a-z]{1,6}', '', cleaned_content)
    
    # 处理汉字中间的拼音 - 保留原有结构
    cleaned_content = re.sub(r'([\u4e00-\u9fa5])([a-z]{1,6})([\u4e00-\u9fa5])', r'\1\3', cleaned_content)
    
    # 处理单独存在的拼音（包括行首的拼音）- 保留原有空格结构
    cleaned_content = re.sub(r'\b[a-z]{1,6}\b', lambda m: ' ' * len(m.group(0)), cleaned_content)
    
    # 处理行首的拼音（特殊情况，如"hao在..."）- 保留原有结构
    cleaned_content = re.sub(r'^[a-z]{1,6}(?=[\u4e00-\u9fa5])', '', cleaned_content, flags=re.MULTILINE)
    cleaned_content = re.sub(r'(?<=\s)[a-z]{1,6}(?=[\u4e00-\u9fa5])', '', cleaned_content)
    
    # 处理特殊情况："hao在..."这样的拼音 - 保留原有结构
    cleaned_content = re.sub(r'\b[a-z]{1,6}\b(?=[\u4e00-\u9fa5])', '', cleaned_content)
    
    # 最后一次全面扫描所有可能的拼音 - 保留原有结构
    cleaned_content = re.sub(r'[a-z]{1,6}(?=[\u4e00-\u9fa5])', '', cleaned_content)
    cleaned_content = re.sub(r'(?<=[\u4e00-\u9fa5])[a-z]{1,6}', '', cleaned_content)
    cleaned_content = re.sub(r'\b[a-z]{1,6}\b', lambda m: ' ' * len(m.group(0)), cleaned_content)
    
    # 处理单个大写字母或字母组合（如Z、SU、U、XT、D、CT、ICT等）- 保留原有结构
    cleaned_content = re.sub(r'(?<=[\u4e00-\u9fa5])[A-Z]{1,3}(?=[\u4e00-\u9fa5])', '', cleaned_content)  # 汉字中间的大写字母
    cleaned_content = re.sub(r'(?<=[\u4e00-\u9fa5])[A-Z]{1,3}\b', '', cleaned_content)  # 汉字后的大写字母
    cleaned_content = re.sub(r'\b[A-Z]{1,3}(?=[\u4e00-\u9fa5])', '', cleaned_content)  # 汉字前的大写字母
    cleaned_content = re.sub(r'^[A-Z]{1,3}$', lambda m: ' ' * len(m.group(0)), cleaned_content, flags=re.MULTILINE)  # 单独一行的大写字母
    
    # 处理单独一行的大写字母（更严格的匹配）- 保留原有结构和空格
    cleaned_content = re.sub(r'^\s*[A-Z]{1,3}\s*$', lambda m: ' ' * len(m.group(0)), cleaned_content, flags=re.MULTILINE)  # 单独一行的大写字母（包括空格）
    
    # 删除特殊符号 $0$ 和类似的无法识别的正则表达式符号
    cleaned_content = re.sub(r'\$0\$', '', cleaned_content)  # 删除 $0$ 符号
    
    # 删除所有 $任何内容$ 格式的内容
    cleaned_content = re.sub(r'\$[^$]*\$', '', cleaned_content)  # 删除所有 $...$ 格式的内容
    
    # 删除所有 $\textcircled{...}$ 格式的符号，支持多层嵌套花括号
    # 使用更强大的递归方式处理多层嵌套的花括号结构
    def remove_textcircled(text):
        # 处理完整的 $\textcircled{...}$ 格式
        complete_pattern = r'\$\\textcircled\{[^{}]*\}\$'
        text = re.sub(complete_pattern, '', text)
        
        # 处理不完整的格式，只要包含 $\textcircled{ 就删除到对应的 }
        # 使用更宽松的匹配，处理各种可能的格式
        incomplete_pattern = r'\$\\textcircled\s*\{[^{}]*\}'
        text = re.sub(incomplete_pattern, '', text)
        
        # 处理带有嵌套内容的格式
        nested_pattern = r'\$\\textcircled\s*\{(?:[^{}]*|\{[^{}]*\})*\}'
        prev_text = ""
        while prev_text != text:
            prev_text = text
            text = re.sub(nested_pattern, '', text)
        
        # 处理任何剩余的 $\textcircled 开头的模式，直到找到匹配的花括号
        # 这个模式会匹配 $\textcircled{ 开头，然后匹配到对应的 }
        general_pattern = r'\$\\textcircled\s*\{[^}]*\}'
        text = re.sub(general_pattern, '', text)
        
        # 最后清理任何剩余的单独的 $\textcircled 标记
        leftover_pattern = r'\$\\textcircled[^\$]*'
        text = re.sub(leftover_pattern, '', text)
        
        return text
    
    cleaned_content = remove_textcircled(cleaned_content)
    
    # 恢复图片链接占位符
    for i, link in enumerate(image_links):
        cleaned_content = cleaned_content.replace(f"IMAGE_PLACEHOLDER_{i}_PROTECTED", link)
    
    # 5. 直接写入最终文件，确保编码正确
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"已清理完成，结果保存到 {output_file}")

if __name__ == "__main__":
    # 确保使用正确的路径
    input_file = r"E:\process\book\chinese_upgrade.md"
    output_file = r"E:\process\book\chinese_upgrade_cleaned.md"
    clean_markdown(input_file, output_file)