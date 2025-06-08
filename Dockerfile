# ベースイメージとしてPythonを使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    git cmake swig && \
    apt-get clean

# OR-Toolsをインストール
RUN pip install ortools

# アプリケーションコードをコンテナにコピー
COPY . /app

# スクリプトを実行するコマンドを指定
CMD ["python", "or-tools.py"]