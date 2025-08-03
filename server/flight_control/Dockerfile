FROM python:3.11-alpine

WORKDIR /app

COPY . /app

# 安装时区数据并配置为上海时区
RUN apk add --no-cache tzdata gcc musl-dev libffi-dev make && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone
    
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
&& pip install -r requirement.txt

EXPOSE 39000

CMD ["python", "main.py"]

