-- Run this once on existing database

-- 1. Make telegram_id nullable (experts may not have Telegram)
ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;

-- 2. Add expert credentials columns
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS expert_username VARCHAR(64) UNIQUE,
  ADD COLUMN IF NOT EXISTS expert_password_hash VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_users_expert_username ON users (expert_username);
