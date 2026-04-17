import pool from '../db';
import { generateMissionText } from './hermes';

export type MissionAction = 'next_level' | 'retry' | 're_recommend' | 'completed_all';

interface MissionResult {
  action: MissionAction;
  message: string;
  mission_id?: string;
  mission_text?: string;
}

export async function processMissionCompletion(
  missionId: string,
  satisfaction: number,
): Promise<MissionResult> {
  // 미션 조회
  const { rows } = await pool.query(
    `SELECT m.*, s.name AS sport_name
     FROM user_missions m
     LEFT JOIN sports s ON s.id = m.sport_id
     WHERE m.id = $1`,
    [missionId],
  );
  if (!rows.length) throw new Error('Mission not found');
  const mission = rows[0];

  // 완료 처리
  await pool.query(
    `UPDATE user_missions SET completed = true, satisfaction = $1 WHERE id = $2`,
    [satisfaction, missionId],
  );

  if (satisfaction >= 4) {
    const nextLevel = mission.level + 1;
    if (nextLevel > 3) {
      return { action: 'completed_all', message: '모든 레벨 완료! 이제 정식 회원이 되셨네요 🎉' };
    }

    // 다음 레벨 미션 생성
    let missionText: string;
    try {
      missionText = await generateMissionText(mission.sport_name ?? '운동', nextLevel, mission.user_name ?? '');
    } catch {
      const defaults: Record<number, string> = {
        2: `${mission.sport_name} 2~3회 방문하여 기본기를 배워보세요!`,
        3: `${mission.sport_name} 월 정기권을 등록하거나 동호회에 가입해보세요!`,
      };
      missionText = defaults[nextLevel] ?? '다음 미션을 수행해보세요!';
    }

    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 14);

    const { rows: newRows } = await pool.query(
      `INSERT INTO user_missions (user_id, sport_id, mission_text, level, due_date)
       VALUES ($1, $2, $3, $4, $5) RETURNING id`,
      [mission.user_id, mission.sport_id, missionText, nextLevel, dueDate],
    );

    return {
      action: 'next_level',
      message: `레벨 ${nextLevel} 미션이 생성됐어요! 계속 도전해봐요 💪`,
      mission_id: newRows[0].id,
      mission_text: missionText,
    };
  }

  if (satisfaction <= 2) {
    return { action: 're_recommend', message: '다른 종목을 찾아드릴게요!' };
  }

  // satisfaction === 3: retry
  return { action: 'retry', message: '한 번 더 도전해봐요!', mission_id: missionId };
}
