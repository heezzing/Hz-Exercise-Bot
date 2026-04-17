import db from '../db';
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
  const result = await db.execute({
    sql: `SELECT m.*, s.name AS sport_name
          FROM user_missions m
          LEFT JOIN sports s ON s.id = m.sport_id
          WHERE m.id = ?`,
    args: [missionId],
  });
  if (!result.rows.length) throw new Error('Mission not found');
  const mission = result.rows[0];

  await db.execute({
    sql: `UPDATE user_missions SET completed = 1, satisfaction = ? WHERE id = ?`,
    args: [satisfaction, missionId],
  });

  if (satisfaction >= 4) {
    const nextLevel = (mission.level as number) + 1;
    if (nextLevel > 3) {
      return { action: 'completed_all', message: '모든 레벨 완료! 이제 정식 회원이 되셨네요 🎉' };
    }

    let missionText: string;
    try {
      missionText = await generateMissionText(
        (mission.sport_name as string) ?? '운동',
        nextLevel,
        '',
      );
    } catch {
      const defaults: Record<number, string> = {
        2: `${mission.sport_name} 2~3회 방문하여 기본기를 배워보세요!`,
        3: `${mission.sport_name} 월 정기권을 등록하거나 동호회에 가입해보세요!`,
      };
      missionText = defaults[nextLevel] ?? '다음 미션을 수행해보세요!';
    }

    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 14);
    const newMissionId = crypto.randomUUID();

    await db.execute({
      sql: `INSERT INTO user_missions (id, user_id, sport_id, mission_text, level, due_date)
            VALUES (?, ?, ?, ?, ?, ?)`,
      args: [
        newMissionId,
        mission.user_id as string,
        mission.sport_id as string,
        missionText,
        nextLevel,
        dueDate.toISOString().split('T')[0],
      ],
    });

    return {
      action: 'next_level',
      message: `레벨 ${nextLevel} 미션이 생성됐어요! 계속 도전해봐요 💪`,
      mission_id: newMissionId,
      mission_text: missionText,
    };
  }

  if (satisfaction <= 2) {
    return { action: 're_recommend', message: '다른 종목을 찾아드릴게요!' };
  }

  return { action: 'retry', message: '한 번 더 도전해봐요!', mission_id: missionId };
}
