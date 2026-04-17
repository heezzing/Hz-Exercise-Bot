-- ============================================================
-- Supabase SQL Editor에서 순서대로 실행하세요
-- ============================================================

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name            VARCHAR(100) NOT NULL,
  age             INTEGER NOT NULL,
  password_hash   TEXT,
  location_lat    FLOAT,
  location_lng    FLOAT,
  lifestyle_vector JSONB,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 3. Sports
CREATE TABLE IF NOT EXISTS sports (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name           VARCHAR(100) NOT NULL UNIQUE,
  cost_level     INTEGER NOT NULL,
  injury_risk    INTEGER NOT NULL,
  social_level   INTEGER NOT NULL,
  space_required BOOLEAN DEFAULT false,
  indoor         BOOLEAN DEFAULT true,
  tags           TEXT[],
  description    TEXT,
  embedding      vector(384)
);

-- 4. Facilities
CREATE TABLE IF NOT EXISTS facilities (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name             VARCHAR(200) NOT NULL,
  sport_id         UUID REFERENCES sports(id),
  address          TEXT,
  location         GEOMETRY(POINT, 4326),
  cost_per_session FLOAT,
  open_hours       JSONB,
  phone            VARCHAR(50),
  rating           FLOAT
);
CREATE INDEX IF NOT EXISTS idx_facilities_location ON facilities USING GIST(location);

-- 5. User Missions
CREATE TABLE IF NOT EXISTS user_missions (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      UUID REFERENCES users(id) NOT NULL,
  sport_id     UUID REFERENCES sports(id),
  facility_id  UUID REFERENCES facilities(id),
  mission_text TEXT NOT NULL,
  level        INTEGER DEFAULT 1,
  due_date     DATE,
  completed    BOOLEAN DEFAULT false,
  satisfaction INTEGER,
  notified_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- 6. Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id          UUID REFERENCES users(id) NOT NULL,
  sport_ids        UUID[],
  hermes_reasoning TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 7. Seed: Sports (8개 종목)
-- ============================================================
INSERT INTO sports (name, cost_level, injury_risk, social_level, space_required, indoor, tags, description)
VALUES
  ('클라이밍', 3, 2, 2, false, true,  ARRAY['근력','집중력','성취감'],    '실내 암벽 등반. 혼자 집중하면서도 성취감을 느낄 수 있어 스트레스 해소에 탁월.'),
  ('수영',     2, 1, 1, true,  true,  ARRAY['유산소','전신운동','저충격'], '전신 유산소 운동. 관절 부담 없이 꾸준히 할 수 있는 입문자 친화 종목.'),
  ('테니스',   3, 2, 3, true,  false, ARRAY['유산소','반응속도','사교'],   '파트너와 함께 즐기는 라켓 스포츠. 사교성과 경쟁심을 동시에 충족.'),
  ('요가',     2, 1, 2, false, true,  ARRAY['유연성','멘탈','호흡'],       '유연성과 정신 집중을 동시에 키우는 종목. 스트레스 해소에 특히 효과적.'),
  ('러닝',     1, 2, 1, false, false, ARRAY['유산소','자유','멘탈'],       '가장 진입 장벽이 낮은 운동. 장비 없이 언제든 시작 가능.'),
  ('배드민턴', 1, 2, 3, true,  true,  ARRAY['유산소','반응속도','사교'],   '저렴한 비용으로 친구나 동료와 즐길 수 있는 실내 라켓 스포츠.'),
  ('필라테스', 4, 1, 2, false, true,  ARRAY['코어','자세교정','유연성'],   '코어 근력과 자세 교정에 특화된 운동. 재활 목적으로도 많이 활용.'),
  ('자전거',   3, 2, 2, false, false, ARRAY['유산소','자유','야외'],        '도시 이동과 운동을 겸할 수 있는 실용적 종목. 야외 활동을 즐기는 사람에게 적합.')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 8. Seed: Facilities (25개 서울 시설)
-- ============================================================
INSERT INTO facilities (name, sport_id, address, location, cost_per_session, rating, phone)
SELECT f.name, s.id, f.address,
       ST_SetSRID(ST_MakePoint(f.lng, f.lat), 4326),
       f.cost, f.rating, f.phone
FROM (VALUES
  ('더클라이밍 강남점',    '클라이밍', '서울 강남구 테헤란로 427',    127.0633, 37.5087, 18000, 4.7, '02-555-0001'),
  ('클라이밍파크 홍대점',  '클라이밍', '서울 마포구 양화로 160',      126.9239, 37.5567, 15000, 4.5, '02-333-0002'),
  ('살리다클라이밍 신촌',  '클라이밍', '서울 서대문구 신촌로 83',     126.9368, 37.5556, 14000, 4.4, '02-312-0003'),
  ('더클라이밍 합정점',    '클라이밍', '서울 마포구 합정동 372',      126.9148, 37.5500, 16000, 4.6, '02-333-0004'),
  ('클라이밍 성수점',      '클라이밍', '서울 성동구 성수이로 78',     127.0559, 37.5445, 17000, 4.8, '02-444-0005'),
  ('강남구청 수영장',      '수영',     '서울 강남구 삼성로 212',      127.0473, 37.5172,  3000, 4.3, '02-3423-5800'),
  ('잠실실내수영장',       '수영',     '서울 송파구 올림픽로 25',     127.0721, 37.5142,  3500, 4.4, '02-2147-2800'),
  ('마포구민체육센터 수영장','수영',   '서울 마포구 월드컵북로 400',  126.9027, 37.5709,  3000, 4.2, '02-3153-9700'),
  ('서울시민체육관 수영장', '수영',    '서울 강남구 남부순환로 2477', 127.0449, 37.4813,  2500, 4.1, '02-2226-0201'),
  ('코어요가 강남',        '요가',     '서울 강남구 역삼로 160',      127.0368, 37.5004, 20000, 4.8, '02-555-1001'),
  ('하늘요가 홍대',        '요가',     '서울 마포구 어울마당로 65',   126.9246, 37.5570, 18000, 4.6, '02-322-1002'),
  ('요가원 이태원',        '요가',     '서울 용산구 이태원로 177',    126.9940, 37.5344, 22000, 4.7, '02-795-1003'),
  ('선릉요가클럽',         '요가',     '서울 강남구 선릉로 433',      127.0487, 37.5046, 19000, 4.5, '02-566-1004'),
  ('올림픽공원 테니스장',  '테니스',   '서울 송파구 올림픽로 424',    127.1220, 37.5213, 10000, 4.4, '02-2154-8100'),
  ('한강 망원 테니스장',   '테니스',   '서울 마포구 마포나루길 467',  126.8987, 37.5582,  8000, 4.2, '02-3153-0001'),
  ('뚝섬 테니스장',        '테니스',   '서울 광진구 자양로 290',      127.0657, 37.5473,  9000, 4.3, '02-450-1900'),
  ('한강공원 반포 러닝트랙','러닝',    '서울 서초구 신반포로11길 40', 126.9980, 37.5112,     0, 4.9, NULL),
  ('한강공원 여의도 러닝트랙','러닝',  '서울 영등포구 여의동로 330',  126.9336, 37.5283,     0, 4.8, NULL),
  ('올림픽공원 러닝코스',  '러닝',     '서울 송파구 올림픽로 424',    127.1215, 37.5215,     0, 4.7, NULL),
  ('종로체육관 배드민턴',  '배드민턴', '서울 종로구 창경궁로 124',    126.9998, 37.5743,  5000, 4.2, '02-765-3456'),
  ('강서 배드민턴클럽',    '배드민턴', '서울 강서구 공항대로 484',    126.8279, 37.5603,  6000, 4.3, '02-2668-1234'),
  ('바디앤필라테스 강남',  '필라테스', '서울 강남구 도산대로 201',    127.0388, 37.5263, 50000, 4.9, '02-547-2001'),
  ('코어필라테스 마포',    '필라테스', '서울 마포구 백범로 35',       126.9480, 37.5495, 45000, 4.7, '02-712-2002'),
  ('한강 자전거 대여소 뚝섬','자전거', '서울 광진구 자양로 257',      127.0665, 37.5446,  3000, 4.5, '02-3780-0504'),
  ('한강 자전거 대여소 반포','자전거', '서울 서초구 올림픽대로 2085', 126.9985, 37.5121,  3000, 4.4, '02-3780-0521')
) AS f(name, sport_name, address, lng, lat, cost, rating, phone)
JOIN sports s ON s.name = f.sport_name
ON CONFLICT DO NOTHING;
