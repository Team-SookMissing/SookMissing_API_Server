import re

# 텍스트에서 url 추출
def extract_urls(text: str):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$\-@\.&+:/?=]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    urls = re.findall(url_pattern, text)
    return list(set(urls))  # 추출된 url들을 리스트 형태로 반환