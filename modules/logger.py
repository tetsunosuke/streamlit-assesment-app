import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Windows環境でのコンソール出力の文字化け/エラー対策
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python 3.7未満など reconfigure がない場合はスキップ（今回は3.12+なので問題なし）
        pass

# ログを保存するディレクトリを作成
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ログファイルのパス
LOG_FILE = os.path.join(LOG_DIR, 'assessment.log')

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """
    指定された名前でロガーをセットアップする関数
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Streamlitの再実行時にハンドラが重複して追加されるのを防ぐため、既存のハンドラをクリアする
    if logger.hasHandlers():
        logger.handlers.clear()

    # ログのフォーマットを定義
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    # ファイルハンドラ: ファイルにログを書き込む
    # 1MBでローテーションし、最大5つのバックアップファイルを保持
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # ストリームハンドラ: コンソールにログを出力する
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # ロガーにハンドラを追加
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler) # コンソールにも出力する場合

    return logger

# アプリケーション全体で利用するロガーインスタンス
logger = setup_logger('assessment_logger', LOG_FILE)
