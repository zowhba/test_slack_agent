import os
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# ─────────────────────────────────────────────
# 환경 변수로부터 토큰/시크릿 읽기
# SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET 는 나중에 Slack App 설정에서 복사
# ─────────────────────────────────────────────
slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)


# ─────────────────────────────────────────────
# 1) /deploy 슬래시 커맨드 → 모달 띄우기
# ─────────────────────────────────────────────
@slack_app.command("/deploy")
def open_deploy_modal(ack, body, client, logger):
    ack()  # Slack 에게 "커맨드 잘 받았다" 응답

    trigger_id = body["trigger_id"]
    channel_id = body["channel_id"]  # 나중에 결과 메시지 보낼 채널

    view = {
        "type": "modal",
        "callback_id": "deploy_modal",
        "private_metadata": channel_id,  # 제출 시 다시 돌려받기 위해
        "title": {"type": "plain_text", "text": "Deploy"},
        "submit": {"type": "plain_text", "text": "Submit"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "job_block",
                "label": {"type": "plain_text", "text": "Job"},
                "element": {
                    "type": "static_select",
                    "action_id": "job_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select job",
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "admin"},
                            "value": "admin",
                        },
                        {
                            "text": {"type": "plain_text", "text": "batch"},
                            "value": "batch",
                        },
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "env_block",
                "label": {"type": "plain_text", "text": "Environment"},
                "element": {
                    "type": "static_select",
                    "action_id": "env_select",
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "dev"},
                            "value": "dev",
                        },
                        {
                            "text": {"type": "plain_text", "text": "stg"},
                            "value": "stg",
                        },
                        {
                            "text": {"type": "plain_text", "text": "prod"},
                            "value": "prod",
                        },
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "server_block",
                "label": {"type": "plain_text", "text": "Server"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "server_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 성수 국사1",
                    },
                },
            },
        ],
    }

    client.views_open(trigger_id=trigger_id, view=view)


# ─────────────────────────────────────────────
# 2) 모달 Submit 처리 → 사용자가 입력한 값 그대로 보여주기
# ─────────────────────────────────────────────
@slack_app.view("deploy_modal")
def handle_deploy_submit(ack, body, client, logger):
    # 모달 정상 처리 됐다고 Slack에 응답
    ack()

    user_id = body["user"]["id"]
    channel_id = body["view"]["private_metadata"]

    values = body["view"]["state"]["values"]

    job = values["job_block"]["job_select"]["selected_option"]["value"]
    env = values["env_block"]["env_select"]["selected_option"]["value"]
    server = values["server_block"]["server_input"]["value"]

    text = (
        f"입력받은 값은 아래와 같습니다.\n"
        f"> *Job*: `{job}`\n"
        f"> *Environment*: `{env}`\n"
        f"> *Server*: `{server}`"
    )

    # 테스트용: 사용자가 명령 내렸던 채널에 ephemeral 메시지로 회신
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=text,
    )


# ─────────────────────────────────────────────
# Flask 엔드포인트 하나만 열어두면 됨
# Slash command / Modal submit / 버튼 모두 여기로 옴
# ─────────────────────────────────────────────
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # 로컬에서 3000 포트로 실행 (ngrok 등으로 외부 공개 필요)
    flask_app.run(host="0.0.0.0", port=3000, debug=True)
