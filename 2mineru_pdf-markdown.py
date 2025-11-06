import requests
import time
"""
将PDF文档提交到Mineru API进行处理，并轮询获取处理结果获得最终的结果压缩包。"""
# 提交PDF提取任务
def submit_extraction_task():
    url = 'https://mineru.net/api/v4/extract/task'
    header = {
        'Content-Type':'application/json',
        "Authorization":"Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0MzMwNTk2MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc0ODU4NTg5MCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTg4MTAyNTE1NzUiLCJvcGVuSWQiOm51bGwsInV1aWQiOiI5N2M4MThkNi1mOTAzLTRmNTgtODE5ZC1hMTRmNWEwZWZmMGQiLCJlbWFpbCI6IiIsImV4cCI6MTc0OTc5NTQ5MH0.CgI5Zg66EO6yymO8niBUm5K0oujhzJwrTYM-6e3uvolcgdRWdK6iRxT6pwMqhlkt7vHaTSubMADQCCf6CWV6oQ"
    }
    data = {
        'url': 'https://mineru.oss-cn-shanghai.aliyuncs.com/api-upload/1fe5d23a-9a54-4a94-a77d-fd1e43eafafb/272e7c1c-4257-46fd-9761-ea94dad9c3b3.pdf',
        'is_ocr': True,
        'enable_formula': True,
        'enable_table': True,
        "page_ranges": "5-30",
    }

    try:
        res = requests.post(url, headers=header, json=data)
        res.raise_for_status()  # 检查HTTP错误
        response_data = res.json()
        
        # 检查API返回状态码
        if response_data.get('code') != 0:
            print(f"任务提交失败: {response_data.get('msg')}")
            return None
        
        print(f"任务提交成功! 状态码: {res.status_code}")
        print(f"响应内容: {response_data}")
        return response_data['data']['task_id']  # 返回任务ID
    
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except ValueError as e:
        print(f"JSON解析错误: {e}")
    except KeyError:
        print("响应中未找到task_id字段")
    
    return None

# 轮询任务结果（根据新返回结构修改）
def poll_task_result(task_id):
    if not task_id:
        print("无效的任务ID")
        return
    
    url = f'https://mineru.net/api/v4/extract/task/{task_id}'
    header = {
        'Content-Type': 'application/json',
        "Authorization": "Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0MzMwNTk2MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc0ODU4NTg5MCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTg4MTAyNTE1NzUiLCJvcGVuSWQiOm51bGwsInV1aWQiOiI5N2M4MThkNi1mOTAzLTRmNTgtODE5ZC1hMTRmNWEwZWZmMGQiLCJlbWFpbCI6IiIsImV4cCI6MTc0OTc5NTQ5MH0.CgI5Zg66EO6yymO8niBUm5K0oujhzJwrTYM-6e3uvolcgdRWdK6iRxT6pwMqhlkt7vHaTSubMADQCCf6CWV6oQ"
    }
    
    max_attempts = 30  # 增加最大轮询次数（处理可能需要更长时间）
    wait_seconds = 5    # 增加等待时间
    
    for attempt in range(max_attempts):
        try:
            res = requests.get(url, headers=header)
            res.raise_for_status()
            result = res.json()
            
            # 检查API返回状态码
            code = result.get('code')
            if code != 0:
                print(f"API返回错误: code={code}, msg={result.get('msg')}")
                return
            
            # 获取任务数据
            task_data = result.get('data', {})
            state = task_data.get('state')
            
            # 根据状态处理
            if state == "done":
                print("\n任务处理完成!")
                print(f"状态码: {res.status_code}")
                print(f"任务ID: {task_data.get('task_id')}")
                print(f"数据ID: {task_data.get('data_id')}")
                print(f"结果压缩包URL: {task_data.get('full_zip_url')}")
                return task_data.get('full_zip_url')
            elif state == "failed":
                err_msg = task_data.get('err_msg', '未知错误')
                print(f"\n任务处理失败: {err_msg}")
                return 
            else:
                # 显示进度信息（如果有）
                progress = task_data.get('extract_progress', {})
                if progress:
                    print(f"轮询中... ({attempt+1}/{max_attempts})")
                    print(f"状态: {state.upper()}")
                    print(f"进度: {progress.get('extracted_pages', 0)}/{progress.get('total_pages', 0)}页")
                    print(f"开始时间: {progress.get('start_time', '未知')}")
                else:
                    print(f"轮询中... ({attempt+1}/{max_attempts}), 当前状态: {state.upper()}")
                
        except requests.exceptions.RequestException as e:
            print(f"轮询请求异常: {e}")
        
        # 未完成则等待
        if attempt < max_attempts - 1:
            time.sleep(wait_seconds)
    
    print("\n轮询超时，任务未在预期时间内完成")
import zipfile
import os

def extract_zip(zip_url, extract_to='E:\process\output'):
    """
    下载并解压zip文件到当前目录
    :param zip_url: 压缩包的URL
    :param extract_to: 解压目标路径，默认为当前目录
    """
    try:
        # 下载压缩包
        local_zip = "result.zip"
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        
        with open(local_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 解压文件
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        print(f"压缩包已成功解压到: {os.path.abspath(extract_to)}")
        
        # 删除临时zip文件
        os.remove(local_zip)
        
    except Exception as e:
        print(f"解压过程中出错: {e}")
# 主流程
if __name__ == "__main__":
    # 1. 提交提取任务
    print("提交PDF提取任务...")
    task_id = submit_extraction_task()
    
    # 2. 轮询任务结果
    if task_id:
        print(f"\n开始轮询任务结果, Task ID: {task_id}")
        zip_url=poll_task_result(task_id)
    # 3. 下载并解压结果
    if zip_url:
        extract_zip(zip_url)
        print(f"\n下载并解压结果文件从URL: {zip_url}")