import requests
"""将本地的PDF文档上传到Mineru API，并获取处理结果的URL"""
url='https://mineru.net/api/v4/file-urls/batch'
header = {
    'Content-Type':'application/json',
    "Authorization":"Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0MzMwNTk2MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc0ODU4NTg5MCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTg4MTAyNTE1NzUiLCJvcGVuSWQiOm51bGwsInV1aWQiOiI5N2M4MThkNi1mOTAzLTRmNTgtODE5ZC1hMTRmNWEwZWZmMGQiLCJlbWFpbCI6IiIsImV4cCI6MTc0OTc5NTQ5MH0.CgI5Zg66EO6yymO8niBUm5K0oujhzJwrTYM-6e3uvolcgdRWdK6iRxT6pwMqhlkt7vHaTSubMADQCCf6CWV6oQ"
}
data = {
    "enable_formula": True,
    "language": "en",
    "enable_table": True,
    "files": [
        {"name":"六年级下册.pdf", "is_ocr": True}
    ]
}
file_path = ["E://process//book//六年级下册.pdf"]
try:
    response = requests.post(url,headers=header,json=data)
    if response.status_code == 200:
        result = response.json()
        print('response success. result:{}'.format(result))
        if result["code"] == 0:
            batch_id = result["data"]["batch_id"]
            urls = result["data"]["file_urls"]
            print('batch_id:{},urls:{}'.format(batch_id, urls))
            for i in range(0, len(urls)):
                with open(file_path[i], 'rb') as f:
                    res_upload = requests.put(urls[i], data=f)
                    if res_upload.status_code == 200:
                        print(f"{urls[i]} upload success")
                    else:
                        print(f"{urls[i]} upload failed")
        else:
            print('apply upload url failed,reason:{}'.format(result.msg))
    else:
        print('response not success. status:{} ,result:{}'.format(response.status_code, response))
except Exception as err:
    print(err)