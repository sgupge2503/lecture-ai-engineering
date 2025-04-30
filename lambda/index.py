# lambda/index.py

import json
import os
import urllib.request
import urllib.error

def lambda_handler(event, context):
    """Lambda ハンドラ: FastAPI サーバーに HTTP POST して推論結果を返す"""
    # ① 環境変数から API URL を取得
    INFERENCE_API_URL = os.environ.get("INFERENCE_API_URL")
    if not INFERENCE_API_URL:
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "error": "INFERENCE_API_URL not set"})
        }

    try:
        # ② リクエストイベントからメッセージを取得
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        conversation_history = body.get("conversationHistory", [])

        # シンプル実装: 受け取った message だけ送る
        payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        data = json.dumps(payload).encode("utf-8")

        # ③ FastAPI の /generate エンドポイントに HTTP POST
        req = urllib.request.Request(
            INFERENCE_API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")

        api_res = json.loads(resp_body)
        assistant_response = api_res.get("generated_text", "")

        # 会話履歴に追加
        conversation_history.append({"role": "user",      "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # ④ 成功レスポンスを返す
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except urllib.error.HTTPError as he:
        # HTTP ステータスエラー
        err = he.read().decode()
        return {
            "statusCode": he.code,
            "body": json.dumps({"success": False, "error": err})
        }
    except Exception as e:
        # その他例外
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "error": str(e)})
        }
