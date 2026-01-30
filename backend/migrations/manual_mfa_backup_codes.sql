-- Manual SQL migration for adding mfa_backup_codes to auth.users table
-- This can be used as an alternative to Alembic migration

-- Add mfa_backup_codes column
ALTER TABLE auth.users
ADD COLUMN IF NOT EXISTS mfa_backup_codes JSONB;

-- Add comment for documentation
COMMENT ON COLUMN auth.users.mfa_backup_codes IS 'Hashed backup codes for MFA recovery (JSONB array of {code_hash, used, used_at})';

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'auth'
  AND table_name = 'users'
  AND column_name = 'mfa_backup_codes';
