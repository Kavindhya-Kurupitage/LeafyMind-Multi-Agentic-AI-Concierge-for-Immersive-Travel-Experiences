-- Leafy Cave package metadata (for_whom, duration, highlights, customizations)
ALTER TABLE packages
    ADD COLUMN IF NOT EXISTS package_meta JSONB NOT NULL DEFAULT '{}'::jsonb;
