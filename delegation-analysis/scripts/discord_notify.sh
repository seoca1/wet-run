#!/bin/bash
# discord_notify.sh - Discord 웹훅으로 진행상황 전송

source ~/.config/opencode/secrets/discord.env 2>/dev/null || { echo "Webhook URL not set"; exit 1; }

send_discord() {
    local title="$1"
    local description="$2"
    local color="${3:-3447003}"  # 기본 파란색

    local payload=$(cat <<PAYLOAD
{
  "embeds": [{
    "title": "$title",
    "description": "$description",
    "color": $color,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "footer": { "text": "wet-run delegation" }
  }]
}
PAYLOAD
)

    curl -s -H "Content-Type: application/json" -d "$payload" "$DISCORD_WEBHOOK_URL" >/dev/null
}

case "${1:-}" in
    start)
        send_discord "🚀 작업 시작" "$2" 3066993
        ;;
    progress)
        send_discord "📋 진행 중" "$2" 15844367
        ;;
    success)
        send_discord "✅ 완료" "$2" 3447003
        ;;
    fail)
        send_discord "❌ 실패" "$2" 15158332
        ;;
    test)
        send_discord "🧪 테스트" "Discord 웹훅 연결 확인" 10181046
        ;;
    *)
        echo "Usage: $0 {start|progress|success|fail|test} \"메시지\""
        exit 1
        ;;
esac