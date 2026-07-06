-- ai-copy-validator DB 스키마 초안 (PostgreSQL 기준)
-- 지금까지 코드에 하드코딩되어 있던 PERSONAS / AD_COPIES / 평가결과 구조를
-- 그대로 테이블화한 버전입니다. 2주차 FastAPI 파이프라인에서 바로 쓸 수 있도록 설계.

-- ─────────────────────────────────────────────
-- 1. personas : 지금 코드의 PERSONAS 리스트
-- ─────────────────────────────────────────────
CREATE TABLE personas (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,          -- 예: "가성비 대학생"
    demographic     VARCHAR(100) NOT NULL,          -- 예: "20대 초반, 여"
    spending_type   VARCHAR(50) NOT NULL,           -- 예: "가성비형", "프리미엄형", "트렌드추종형"
    ad_literacy     VARCHAR(200) NOT NULL,          -- 예: "냉소적 (광고를 잘 신뢰하지 않음)"
    channel         VARCHAR(100) NOT NULL,          -- 예: "인스타 릴스"
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,  -- 페르소나 추가/폐기 관리용
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 2. campaigns : 카피들을 묶는 상위 단위 (지금은 코드에 없지만
--    "어떤 제품/캠페인에 대한 카피 비교인지"를 남기려면 필요)
-- ─────────────────────────────────────────────
CREATE TABLE campaigns (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,          -- 예: "스킨케어 첫구매 프로모션"
    product_desc    TEXT,                            -- /generate-variants 입력으로 쓰일 제품 설명
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 3. copy_variants : 지금 코드의 AD_COPIES 딕셔너리
--    (사람이 직접 넣은 카피든, /generate-variants가 생성한 카피든 여기 저장)
-- ─────────────────────────────────────────────
CREATE TABLE copy_variants (
    id              SERIAL PRIMARY KEY,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    label           VARCHAR(50) NOT NULL,            -- 예: "A_감성어필", "B_근거중심"
    content         TEXT NOT NULL,                    -- 실제 카피 문구
    angle           VARCHAR(50),                      -- 예: "감성어필", "근거중심", "긴급성" (생성 시 태깅)
    source          VARCHAR(20) NOT NULL DEFAULT 'manual',  -- 'manual' | 'ai_generated'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────
-- 4. evaluations : 지금 코드가 eval_results_*.json에 저장하던 결과
-- ─────────────────────────────────────────────
CREATE TABLE evaluations (
    id              SERIAL PRIMARY KEY,
    variant_id      INTEGER NOT NULL REFERENCES copy_variants(id) ON DELETE CASCADE,
    persona_id      INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    run_number      INTEGER NOT NULL DEFAULT 1,       -- 같은 조합 반복 실행 시 구분 (N=3 반복 검증 대비)
    click_intent    SMALLINT,                          -- 1~5, NULL 허용 (API_ERROR/PARSE_ERROR 대비)
    trust           SMALLINT,
    brand_fit       SMALLINT,
    reasoning       TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'ok', -- 'ok' | 'api_error' | 'parse_error'
    model_name      VARCHAR(50) NOT NULL,              -- 예: "gemini-2.5-flash"
    temperature     NUMERIC(3,2) NOT NULL,             -- 예: 1.10
    latency_ms      INTEGER,                           -- 호출 소요시간 (지금은 미기록, 2주차부터 수집 권장)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_scores CHECK (
        (click_intent IS NULL OR click_intent BETWEEN 1 AND 5) AND
        (trust IS NULL OR trust BETWEEN 1 AND 5) AND
        (brand_fit IS NULL OR brand_fit BETWEEN 1 AND 5)
    )
);

-- 자주 쓰일 조회 패턴에 맞춘 인덱스
CREATE INDEX idx_evaluations_variant ON evaluations(variant_id);
CREATE INDEX idx_evaluations_persona ON evaluations(persona_id);
CREATE INDEX idx_copy_variants_campaign ON copy_variants(campaign_id);

-- ─────────────────────────────────────────────
-- 참고: A vs B 승자 집계는 뷰로 미리 만들어두면
--       /evaluate 응답이나 대시보드에서 바로 재사용 가능
-- ─────────────────────────────────────────────
CREATE VIEW v_variant_persona_avg AS
SELECT
    variant_id,
    persona_id,
    ROUND(AVG(click_intent), 2) AS avg_click_intent,
    ROUND(AVG(trust), 2)        AS avg_trust,
    ROUND(AVG(brand_fit), 2)    AS avg_brand_fit,
    COUNT(*) FILTER (WHERE status = 'ok') AS ok_count,
    COUNT(*) FILTER (WHERE status != 'ok') AS error_count
FROM evaluations
GROUP BY variant_id, persona_id;
