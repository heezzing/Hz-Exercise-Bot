"""APScheduler 기반 미션 알림 스케줄러.

규칙 (idea.txt):
- 미완료 후 3일 경과 → 동일 레벨 미션 재알림 (1회만)
- 매일 오전 9시 실행
"""

import asyncio
import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, text

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="Asia/Seoul")


async def _check_overdue_missions():
    """3일 이상 미완료 미션을 찾아 재알림 처리."""
    threshold = date.today() - timedelta(days=3)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT
                    um.id::text   AS mission_id,
                    um.user_id::text AS user_id,
                    um.mission_text,
                    um.level,
                    um.due_date,
                    u.name        AS user_name
                FROM user_missions um
                JOIN users u ON um.user_id = u.id
                WHERE um.completed = false
                  AND um.due_date <= :threshold
                  AND um.notified_at IS NULL
                LIMIT 100
            """),
            {"threshold": threshold},
        )
        overdue = result.mappings().all()

        if not overdue:
            logger.info("[Scheduler] 기한 초과 미션 없음")
            return

        for row in overdue:
            # 재알림 기록 (실제 서비스에서는 FCM/이메일 발송)
            logger.info(
                "[알림] %s님의 미션 '%s' (Level %d) 이 %s에 만료됐습니다. 도전해보세요!",
                row["user_name"], row["mission_text"], row["level"], row["due_date"],
            )
            # notified_at 업데이트 → 중복 알림 방지
            await db.execute(
                text("UPDATE user_missions SET notified_at = now() WHERE id = :id::uuid"),
                {"id": row["mission_id"]},
            )

        await db.commit()
        logger.info("[Scheduler] %d건 재알림 처리 완료", len(overdue))


def _run_check():
    asyncio.run(_check_overdue_missions())


def start_scheduler():
    _scheduler.add_job(
        _run_check,
        trigger="cron",
        hour=9,
        minute=0,
        id="mission_reminder",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("[Scheduler] 미션 알림 스케줄러 시작 (매일 09:00 KST)")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] 스케줄러 종료")
