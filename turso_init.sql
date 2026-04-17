-- ============================================================
-- Turso Shell 또는 turso db shell <db-name> 에서 실행
-- ============================================================

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  age           INTEGER NOT NULL,
  password_hash TEXT,
  location_lat  REAL,
  location_lng  REAL,
  lifestyle_vector TEXT,  -- JSON string
  created_at    TEXT DEFAULT (datetime('now')),
  updated_at    TEXT DEFAULT (datetime('now'))
);

-- 2. Sports (Turso 네이티브 벡터 타입)
CREATE TABLE IF NOT EXISTS sports (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE,
  cost_level     INTEGER NOT NULL,
  injury_risk    INTEGER NOT NULL,
  social_level   INTEGER NOT NULL,
  space_required INTEGER DEFAULT 0,
  indoor         INTEGER DEFAULT 1,
  tags           TEXT,  -- JSON array string
  description    TEXT,
  embedding      F32_BLOB(384)  -- Turso 벡터 타입
);

CREATE INDEX IF NOT EXISTS sports_embedding_idx ON sports (libsql_vector_idx(embedding));

-- 3. Facilities (lat/lng 컬럼으로 Haversine 거리 계산)
CREATE TABLE IF NOT EXISTS facilities (
  id               TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  sport_id         TEXT REFERENCES sports(id),
  address          TEXT,
  lat              REAL,
  lng              REAL,
  cost_per_session REAL,
  phone            TEXT,
  rating           REAL
);

-- 4. User Missions
CREATE TABLE IF NOT EXISTS user_missions (
  id           TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users(id),
  sport_id     TEXT REFERENCES sports(id),
  facility_id  TEXT REFERENCES facilities(id),
  mission_text TEXT NOT NULL,
  level        INTEGER DEFAULT 1,
  due_date     TEXT,
  completed    INTEGER DEFAULT 0,
  satisfaction INTEGER,
  notified_at  TEXT,
  created_at   TEXT DEFAULT (datetime('now'))
);

-- 5. Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
  id               TEXT PRIMARY KEY,
  user_id          TEXT NOT NULL REFERENCES users(id),
  sport_ids        TEXT,  -- JSON array string
  hermes_reasoning TEXT,
  created_at       TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 6. Seed: Sports (8개 종목)
-- ============================================================
INSERT OR IGNORE INTO sports (id, name, cost_level, injury_risk, social_level, space_required, indoor, tags, description)
VALUES
  (lower(hex(randomblob(16))), '클라이밍', 3, 2, 2, 0, 1, '["근력","집중력","성취감"]',    '실내 암벽 등반. 혼자 집중하면서도 성취감을 느낄 수 있어 스트레스 해소에 탁월.'),
  (lower(hex(randomblob(16))), '수영',     2, 1, 1, 1, 1, '["유산소","전신운동","저충격"]', '전신 유산소 운동. 관절 부담 없이 꾸준히 할 수 있는 입문자 친화 종목.'),
  (lower(hex(randomblob(16))), '테니스',   3, 2, 3, 1, 0, '["유산소","반응속도","사교"]',   '파트너와 함께 즐기는 라켓 스포츠. 사교성과 경쟁심을 동시에 충족.'),
  (lower(hex(randomblob(16))), '요가',     2, 1, 2, 0, 1, '["유연성","멘탈","호흡"]',       '유연성과 정신 집중을 동시에 키우는 종목. 스트레스 해소에 특히 효과적.'),
  (lower(hex(randomblob(16))), '러닝',     1, 2, 1, 0, 0, '["유산소","자유","멘탈"]',       '가장 진입 장벽이 낮은 운동. 장비 없이 언제든 시작 가능.'),
  (lower(hex(randomblob(16))), '배드민턴', 1, 2, 3, 1, 1, '["유산소","반응속도","사교"]',   '저렴한 비용으로 친구나 동료와 즐길 수 있는 실내 라켓 스포츠.'),
  (lower(hex(randomblob(16))), '필라테스', 4, 1, 2, 0, 1, '["코어","자세교정","유연성"]',   '코어 근력과 자세 교정에 특화된 운동. 재활 목적으로도 많이 활용.'),
  (lower(hex(randomblob(16))), '자전거',   3, 2, 2, 0, 0, '["유산소","자유","야외"]',        '도시 이동과 운동을 겸할 수 있는 실용적 종목. 야외 활동을 즐기는 사람에게 적합.');

-- ============================================================
-- 7. Seed: Facilities (25개 서울 시설)
-- ============================================================
INSERT OR IGNORE INTO facilities (id, name, sport_id, address, lat, lng, cost_per_session, rating, phone)
SELECT lower(hex(randomblob(16))), f.name, s.id, f.address, f.lat, f.lng, f.cost, f.rating, f.phone
FROM (SELECT '더클라이밍 강남점'     AS name, '클라이밍' AS sport, '서울 강남구 테헤란로 427'    AS address, 37.5087 AS lat, 127.0633 AS lng, 18000 AS cost, 4.7 AS rating, '02-555-0001' AS phone UNION ALL
      SELECT '클라이밍파크 홍대점',  '클라이밍', '서울 마포구 양화로 160',      37.5567, 126.9239, 15000, 4.5, '02-333-0002' UNION ALL
      SELECT '살리다클라이밍 신촌',  '클라이밍', '서울 서대문구 신촌로 83',     37.5556, 126.9368, 14000, 4.4, '02-312-0003' UNION ALL
      SELECT '더클라이밍 합정점',    '클라이밍', '서울 마포구 합정동 372',      37.5500, 126.9148, 16000, 4.6, '02-333-0004' UNION ALL
      SELECT '클라이밍 성수점',      '클라이밍', '서울 성동구 성수이로 78',     37.5445, 127.0559, 17000, 4.8, '02-444-0005' UNION ALL
      SELECT '강남구청 수영장',      '수영',     '서울 강남구 삼성로 212',      37.5172, 127.0473,  3000, 4.3, '02-3423-5800' UNION ALL
      SELECT '잠실실내수영장',       '수영',     '서울 송파구 올림픽로 25',     37.5142, 127.0721,  3500, 4.4, '02-2147-2800' UNION ALL
      SELECT '마포구민체육센터 수영장','수영',   '서울 마포구 월드컵북로 400',  37.5709, 126.9027,  3000, 4.2, '02-3153-9700' UNION ALL
      SELECT '서울시민체육관 수영장', '수영',    '서울 강남구 남부순환로 2477', 37.4813, 127.0449,  2500, 4.1, '02-2226-0201' UNION ALL
      SELECT '코어요가 강남',        '요가',     '서울 강남구 역삼로 160',      37.5004, 127.0368, 20000, 4.8, '02-555-1001' UNION ALL
      SELECT '하늘요가 홍대',        '요가',     '서울 마포구 어울마당로 65',   37.5570, 126.9246, 18000, 4.6, '02-322-1002' UNION ALL
      SELECT '요가원 이태원',        '요가',     '서울 용산구 이태원로 177',    37.5344, 126.9940, 22000, 4.7, '02-795-1003' UNION ALL
      SELECT '선릉요가클럽',         '요가',     '서울 강남구 선릉로 433',      37.5046, 127.0487, 19000, 4.5, '02-566-1004' UNION ALL
      SELECT '올림픽공원 테니스장',  '테니스',   '서울 송파구 올림픽로 424',    37.5213, 127.1220, 10000, 4.4, '02-2154-8100' UNION ALL
      SELECT '한강 망원 테니스장',   '테니스',   '서울 마포구 마포나루길 467',  37.5582, 126.8987,  8000, 4.2, '02-3153-0001' UNION ALL
      SELECT '뚝섬 테니스장',        '테니스',   '서울 광진구 자양로 290',      37.5473, 127.0657,  9000, 4.3, '02-450-1900' UNION ALL
      SELECT '한강공원 반포 러닝트랙','러닝',    '서울 서초구 신반포로11길 40', 37.5112, 126.9980,     0, 4.9, NULL UNION ALL
      SELECT '한강공원 여의도 러닝트랙','러닝',  '서울 영등포구 여의동로 330',  37.5283, 126.9336,     0, 4.8, NULL UNION ALL
      SELECT '올림픽공원 러닝코스',  '러닝',     '서울 송파구 올림픽로 424',    37.5215, 127.1215,     0, 4.7, NULL UNION ALL
      SELECT '종로체육관 배드민턴',  '배드민턴', '서울 종로구 창경궁로 124',    37.5743, 126.9998,  5000, 4.2, '02-765-3456' UNION ALL
      SELECT '강서 배드민턴클럽',    '배드민턴', '서울 강서구 공항대로 484',    37.5603, 126.8279,  6000, 4.3, '02-2668-1234' UNION ALL
      SELECT '바디앤필라테스 강남',  '필라테스', '서울 강남구 도산대로 201',    37.5263, 127.0388, 50000, 4.9, '02-547-2001' UNION ALL
      SELECT '코어필라테스 마포',    '필라테스', '서울 마포구 백범로 35',       37.5495, 126.9480, 45000, 4.7, '02-712-2002' UNION ALL
      SELECT '한강 자전거 대여소 뚝섬','자전거', '서울 광진구 자양로 257',      37.5446, 127.0665,  3000, 4.5, '02-3780-0504' UNION ALL
      SELECT '한강 자전거 대여소 반포','자전거', '서울 서초구 올림픽대로 2085', 37.5121, 126.9985,  3000, 4.4, '02-3780-0521') AS f
JOIN sports s ON s.name = f.sport;
