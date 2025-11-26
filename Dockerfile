FROM python:3.10-slim

# PYTHONDONTWRITEBYTECODE=1: .pyc(컴파일된 파일) 생성을 막아 이미지 용량 아낌
# PYTHONUNBUFFERED=1: 로그가 버퍼링 없이 즉시 출력되게 하여, 컨테이너 로그 확인 시 지연 방지
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /API-Server

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]