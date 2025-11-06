import re
import os
import sys
import re
from image_compare import are_images_consistent
"""图片处理，删除重复图片如图标等"""
def remove_duplicate_images(input_file, output_file):
    """
    删除Markdown文件中的重复图片（按章节分组检测）
    
    参数:
        input_file (str): 输入的Markdown文件路径
        output_file (str): 输出的Markdown文件路径
    """
    # 读取markdown文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 识别所有Markdown图片链接
    image_links = []
    image_positions = []
    image_urls = []
    
    # 找到所有图片链接及其位置
    for match in re.finditer(r'!\[.*?\]\((.*?)\)', content):
        full_link = match.group(0)  # 完整的图片链接 ![alt text](url)
        url = match.group(1)        # 只有URL部分
        image_links.append(full_link)
        image_positions.append((match.start(), match.end()))
        image_urls.append(url)
    
    print(f"找到 {len(image_links)} 个图片链接")
    
    if not image_links:
        print("没有找到图片链接，直接复制文件")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return
    
    # 按章节分组图片
    chapters = get_chapter_groups(content, image_positions)
    print(f"识别到 {len(chapters)} 个章节")
    
    # 创建一个不包含图片链接的内容副本
    content_without_images = content
    # 从后向前替换，这样不会影响前面的位置
    for i in range(len(image_links) - 1, -1, -1):
        start, end = image_positions[i]
        content_without_images = content_without_images[:start] + f"IMAGE_PLACEHOLDER_{i}_PROTECTED" + content_without_images[end:]
    
    # 检测重复图片并标记需要删除的图片（按章节分组）
    print("按章节检测重复图片...")
    
    # 标记需要保留的图片
    keep_image = [True] * len(image_links)
    removed_count = 0
    
    # 对每个章节内部检测重复图片
    for chapter_name, chapter_indices in chapters.items():
        if len(chapter_indices) <= 1:
            continue
            
        print(f"检测章节 '{chapter_name}' 中的重复图片（共{len(chapter_indices)}张图片）")
        
        # 第一步：基于URL检测完全相同的图片
        chapter_url_indices = {}
        for idx in chapter_indices:
            url = image_urls[idx]
            if url in chapter_url_indices:
                chapter_url_indices[url].append(idx)
            else:
                chapter_url_indices[url] = [idx]
        
        # 标记重复URL的图片（每个URL只保留第一次出现）
        for url, indices in chapter_url_indices.items():
            if len(indices) > 1:
                print(f"  发现重复图片URL: {url}，在章节内出现{len(indices)}次")
                # 将除第一次出现外的所有实例标记为删除
                for i in indices[1:]:
                    keep_image[i] = False
                    removed_count += 1
        
        # 第二步：使用image_compare检测视觉上相似的图片（不同URL但内容相同）
        unique_urls = list(chapter_url_indices.keys())
        
        if len(unique_urls) > 1:
            print(f"  检测章节 '{chapter_name}' 中视觉上相似的图片...")
            # 对每个唯一URL的第一个实例进行比较
            for i in range(len(unique_urls)):
                # 如果当前URL的图片已被标记为删除，则跳过
                first_idx_i = chapter_url_indices[unique_urls[i]][0]
                if not keep_image[first_idx_i]:
                    continue
                    
                for j in range(i+1, len(unique_urls)):
                    first_idx_j = chapter_url_indices[unique_urls[j]][0]
                    # 如果第二个URL的图片已被标记为删除，则跳过
                    if not keep_image[first_idx_j]:
                        continue
                        
                    # 比较两个URL的图片是否视觉上相同
                    try:
                        consistent, message = are_images_consistent([unique_urls[i], unique_urls[j]])
                        if consistent:
                            print(f"    发现视觉上相同的图片: {unique_urls[i]} 和 {unique_urls[j]}")
                            # 标记第二个URL的所有实例为删除
                            for idx in chapter_url_indices[unique_urls[j]]:
                                if keep_image[idx]:
                                    keep_image[idx] = False
                                    removed_count += 1
                    except Exception as e:
                        print(f"    比较图片时出错: {e}")
                        continue
    
    # 恢复图片链接占位符，但跳过标记为删除的图片
    cleaned_content = content_without_images
    for i, link in enumerate(image_links):
        if keep_image[i]:
            cleaned_content = cleaned_content.replace(f"IMAGE_PLACEHOLDER_{i}_PROTECTED", link)
        else:
            # 删除重复图片（用空字符串替换占位符）
            cleaned_content = cleaned_content.replace(f"IMAGE_PLACEHOLDER_{i}_PROTECTED", "")
    
    # 写入最终文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"处理完成！")
    print(f"原始图片数量: {len(image_links)}")
    print(f"删除重复图片数量: {removed_count}")
    print(f"保留图片数量: {len(image_links) - removed_count}")
    print(f"结果保存到: {output_file}")

def get_chapter_groups(content, image_positions):
    """
    根据章节标题对图片进行分组
    
    参数:
        content (str): Markdown文件内容
        image_positions (list): 图片位置列表
    
    返回:
        dict: 章节名称到图片索引列表的映射
    """
    # 查找所有章节标题（# 开头的行）
    chapter_pattern = r'^(#{1,6})\s+(.+)$'
    chapters = {}
    chapter_positions = []
    
    # 找到所有章节标题及其位置
    for match in re.finditer(chapter_pattern, content, re.MULTILINE):
        level = len(match.group(1))  # 标题级别
        title = match.group(2).strip()  # 标题文本
        position = match.start()
        chapter_positions.append((position, title, level))
    
    # 如果没有找到章节，将所有图片归为一个默认章节
    if not chapter_positions:
        chapters["默认章节"] = list(range(len(image_positions)))
        return chapters
    
    # 为每张图片分配到对应的章节
    current_chapter = "开头部分"
    chapters[current_chapter] = []
    
    chapter_idx = 0
    for img_idx, (img_start, img_end) in enumerate(image_positions):
        # 检查是否需要切换到下一个章节
        while (chapter_idx < len(chapter_positions) and 
               img_start >= chapter_positions[chapter_idx][0]):
            # 切换到新章节
            current_chapter = chapter_positions[chapter_idx][1]
            if current_chapter not in chapters:
                chapters[current_chapter] = []
            chapter_idx += 1
        
        # 将图片分配到当前章节
        if current_chapter not in chapters:
            chapters[current_chapter] = []
        chapters[current_chapter].append(img_idx)
    
    return chapters

if __name__ == "__main__":
    # 确保使用正确的路径
    input_file = r"E:\process\book\chinese_upgrade_cleaned.md"
    output_file = r"E:\process\book\chinese_upgrade_no_duplicates.md"
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在 {input_file}")
        sys.exit(1)
    
    remove_duplicate_images(input_file, output_file)