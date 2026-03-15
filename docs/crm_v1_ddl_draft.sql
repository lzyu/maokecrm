-- 猫课 CRM V1 DDL 草案
-- PostgreSQL 14+
-- 生成日期: 2026-03-15

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- updated_at 自动更新时间
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------- 基础字典 ----------

CREATE TABLE IF NOT EXISTS roles (
  id            BIGSERIAL PRIMARY KEY,
  role_name     VARCHAR(32) NOT NULL UNIQUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO roles (role_name)
VALUES ('sales'), ('consultant'), ('admin'), ('super_admin')
ON CONFLICT (role_name) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
  id              BIGSERIAL PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  role_id         BIGINT NOT NULL REFERENCES roles(id),
  phone           VARCHAR(32),
  email           VARCHAR(255),
  password_hash   VARCHAR(255),
  status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
  last_login_at   TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at      TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_phone_active
  ON users(phone)
  WHERE deleted_at IS NULL AND phone IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_active
  ON users(email)
  WHERE deleted_at IS NULL AND email IS NOT NULL;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 客户域 ----------

CREATE TABLE IF NOT EXISTS customers (
  id                BIGSERIAL PRIMARY KEY,
  name              VARCHAR(100) NOT NULL,
  phone             VARCHAR(32),
  wechat            VARCHAR(64),
  company_name      VARCHAR(255),
  industry          VARCHAR(100),
  source_channel    VARCHAR(100),
  owner_user_id     BIGINT NOT NULL REFERENCES users(id),
  customer_status   VARCHAR(20) NOT NULL DEFAULT 'potential'
                    CHECK (customer_status IN ('potential', 'interested', 'converted', 'lost')),
  last_followup_at  TIMESTAMPTZ,
  next_followup_at  TIMESTAMPTZ,
  created_by        BIGINT REFERENCES users(id),
  updated_by        BIGINT REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_customers_owner_status_updated
  ON customers(owner_user_id, customer_status, updated_at DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_customers_phone
  ON customers(phone)
  WHERE deleted_at IS NULL AND phone IS NOT NULL;

CREATE TRIGGER trg_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS tags (
  id            BIGSERIAL PRIMARY KEY,
  tag_name      VARCHAR(100) NOT NULL,
  tag_type      VARCHAR(20) NOT NULL CHECK (tag_type IN ('sales', 'consultant')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(tag_name, tag_type)
);

CREATE TABLE IF NOT EXISTS customer_tags (
  id            BIGSERIAL PRIMARY KEY,
  customer_id   BIGINT NOT NULL REFERENCES customers(id),
  tag_id        BIGINT NOT NULL REFERENCES tags(id),
  created_by    BIGINT REFERENCES users(id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(customer_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_customer_tags_customer_id ON customer_tags(customer_id);

-- ---------- 销售与服务流水 ----------

CREATE TABLE IF NOT EXISTS sales_followups (
  id                BIGSERIAL PRIMARY KEY,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  sales_id          BIGINT NOT NULL REFERENCES users(id),
  followup_time     TIMESTAMPTZ NOT NULL,
  contact_method    VARCHAR(30) NOT NULL,
  content           TEXT NOT NULL,
  result            VARCHAR(30) CHECK (result IN ('no_answer', 'contacted', 'interested', 'rejected', 'pending')),
  next_action_time  TIMESTAMPTZ,
  created_by        BIGINT REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_followups_customer_time
  ON sales_followups(customer_id, followup_time DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_followups_sales_time
  ON sales_followups(sales_id, followup_time DESC)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_sales_followups_updated_at
BEFORE UPDATE ON sales_followups
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS sales_opportunities (
  id                   BIGSERIAL PRIMARY KEY,
  customer_id          BIGINT NOT NULL REFERENCES customers(id),
  owner_user_id        BIGINT NOT NULL REFERENCES users(id),
  stage                VARCHAR(30) NOT NULL CHECK (stage IN ('new', 'qualified', 'proposal', 'negotiation', 'won', 'lost')),
  probability          NUMERIC(5,2) CHECK (probability >= 0 AND probability <= 100),
  expected_close_date  DATE,
  expected_amount      NUMERIC(14,2) DEFAULT 0,
  currency             VARCHAR(10) NOT NULL DEFAULT 'CNY',
  closed_at            TIMESTAMPTZ,
  created_by           BIGINT REFERENCES users(id),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_opportunities_customer_stage
  ON sales_opportunities(customer_id, stage)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_sales_opportunities_updated_at
BEFORE UPDATE ON sales_opportunities
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS service_records (
  id                   BIGSERIAL PRIMARY KEY,
  customer_id          BIGINT NOT NULL REFERENCES customers(id),
  consultant_id        BIGINT NOT NULL REFERENCES users(id),
  service_time         TIMESTAMPTZ NOT NULL,
  service_content      TEXT NOT NULL,
  customer_feedback    TEXT,
  satisfaction_score   SMALLINT CHECK (satisfaction_score BETWEEN 1 AND 5),
  created_by           BIGINT REFERENCES users(id),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_service_records_customer_time
  ON service_records(customer_id, service_time DESC)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_service_records_updated_at
BEFORE UPDATE ON service_records
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS consultation_analysis (
  id                  BIGSERIAL PRIMARY KEY,
  customer_id         BIGINT NOT NULL REFERENCES customers(id),
  consultant_id       BIGINT NOT NULL REFERENCES users(id),
  analysis_summary    TEXT,
  customer_problem    TEXT,
  consultation_result TEXT,
  uploaded_file_url   TEXT,
  created_by          BIGINT REFERENCES users(id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_consultation_analysis_customer_time
  ON consultation_analysis(customer_id, created_at DESC)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_consultation_analysis_updated_at
BEFORE UPDATE ON consultation_analysis
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS service_reminders (
  id                BIGSERIAL PRIMARY KEY,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  created_by        BIGINT NOT NULL REFERENCES users(id),
  assignee_user_id  BIGINT NOT NULL REFERENCES users(id),
  reminder_type     VARCHAR(30) NOT NULL CHECK (reminder_type IN ('followup', 'renewal', 'progress_check', 'other')),
  reminder_time     TIMESTAMPTZ NOT NULL,
  priority          VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  status            VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'canceled')),
  content           TEXT,
  done_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_service_reminders_assignee_status_time
  ON service_reminders(assignee_user_id, status, reminder_time)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_service_reminders_updated_at
BEFORE UPDATE ON service_reminders
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 导入域 ----------

CREATE TABLE IF NOT EXISTS import_batches (
  id                BIGSERIAL PRIMARY KEY,
  batch_no          VARCHAR(64) NOT NULL UNIQUE,
  import_type       VARCHAR(30) NOT NULL CHECK (import_type IN ('course_purchase', 'course_attendance')),
  file_name         VARCHAR(255) NOT NULL,
  file_url          TEXT,
  status            VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'partial_success')),
  total_rows        INTEGER NOT NULL DEFAULT 0,
  success_rows      INTEGER NOT NULL DEFAULT 0,
  failed_rows       INTEGER NOT NULL DEFAULT 0,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at       TIMESTAMPTZ,
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_import_batches_updated_at
BEFORE UPDATE ON import_batches
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS import_errors (
  id                BIGSERIAL PRIMARY KEY,
  batch_id          BIGINT NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
  row_no            INTEGER NOT NULL,
  error_code        VARCHAR(50) NOT NULL,
  error_message     TEXT NOT NULL,
  row_data          JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_errors_batch_row
  ON import_errors(batch_id, row_no);

CREATE TABLE IF NOT EXISTS course_purchase_records (
  id                BIGSERIAL PRIMARY KEY,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  course_name       VARCHAR(255) NOT NULL,
  purchase_date     DATE NOT NULL,
  amount            NUMERIC(14,2) NOT NULL DEFAULT 0,
  currency          VARCHAR(10) NOT NULL DEFAULT 'CNY',
  import_batch_id   BIGINT REFERENCES import_batches(id),
  import_source     VARCHAR(30) NOT NULL DEFAULT 'manual' CHECK (import_source IN ('manual', 'excel', 'csv', 'sync')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_purchase_customer_date
  ON course_purchase_records(customer_id, purchase_date DESC)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_course_purchase_records_updated_at
BEFORE UPDATE ON course_purchase_records
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS course_attendance_records (
  id                BIGSERIAL PRIMARY KEY,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  course_name       VARCHAR(255) NOT NULL,
  class_date        DATE NOT NULL,
  status            VARCHAR(20) NOT NULL CHECK (status IN ('attended', 'absent', 'leave')),
  import_batch_id   BIGINT REFERENCES import_batches(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_attendance_customer_date
  ON course_attendance_records(customer_id, class_date DESC)
  WHERE deleted_at IS NULL;

CREATE TRIGGER trg_course_attendance_records_updated_at
BEFORE UPDATE ON course_attendance_records
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- 时间线与审计 ----------

CREATE TABLE IF NOT EXISTS pipeline_events (
  id                BIGSERIAL PRIMARY KEY,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  event_type        VARCHAR(30) NOT NULL CHECK (event_type IN ('followup', 'service_record', 'consultation', 'purchase', 'attendance', 'reminder')),
  reference_id      BIGINT NOT NULL,
  event_time        TIMESTAMPTZ NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_customer_time
  ON pipeline_events(customer_id, event_time DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
  id                BIGSERIAL PRIMARY KEY,
  actor_user_id     BIGINT REFERENCES users(id),
  action            VARCHAR(64) NOT NULL,
  resource_type     VARCHAR(64) NOT NULL,
  resource_id       BIGINT,
  before_data       JSONB,
  after_data        JSONB,
  ip_address        INET,
  user_agent        TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_time
  ON audit_logs(actor_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
  ON audit_logs(resource_type, resource_id, created_at DESC);

COMMIT;
