-- LeafyMind initial schema migration (idempotent)
-- Applied by PostgreSQL init scripts and backend init_db() on startup

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Enum types
-- ---------------------------------------------------------------------------
DO $body$ BEGIN
    CREATE TYPE user_role AS ENUM ('guest', 'owner', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE session_status AS ENUM ('active', 'completed', 'abandoned');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE package_tier AS ENUM ('budget', 'mid_range', 'luxury');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE attraction_category AS ENUM (
        'wildlife', 'waterfall', 'temple', 'hiking', 'beach', 'cultural', 'food_experience'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE fitness_level AS ENUM ('low', 'moderate', 'high');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE spice_level AS ENUM ('mild', 'medium', 'hot');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

DO $body$ BEGIN
    CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role NOT NULL DEFAULT 'guest',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ---------------------------------------------------------------------------
-- sessions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    guest_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    conversation_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    status session_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions (session_token);

-- ---------------------------------------------------------------------------
-- packages
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tier package_tier NOT NULL,
    price_per_night_usd DECIMAL(10, 2),
    description TEXT,
    inclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    exclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    travel_styles JSONB NOT NULL DEFAULT '[]'::jsonb,
    group_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    min_nights INT NOT NULL DEFAULT 1,
    max_guests INT NOT NULL DEFAULT 6,
    seasonal_note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- attractions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category attraction_category NOT NULL,
    description TEXT,
    distance_km_from_cabana DECIMAL(8, 2),
    estimated_duration_hours DECIMAL(5, 2),
    entry_fee_usd DECIMAL(10, 2),
    fitness_level_required fitness_level NOT NULL DEFAULT 'low',
    suitable_for JSONB NOT NULL DEFAULT '[]'::jsonb,
    seasonal_availability JSONB NOT NULL DEFAULT '{}'::jsonb,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    tips TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attractions_category ON attractions (category);

-- ---------------------------------------------------------------------------
-- food_items
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description_plain_english TEXT,
    ingredients JSONB NOT NULL DEFAULT '[]'::jsonb,
    spice_level spice_level NOT NULL DEFAULT 'mild',
    dietary_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    allergens JSONB NOT NULL DEFAULT '[]'::jsonb,
    cultural_note TEXT,
    meal_type meal_type NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_food_items_dietary_tags ON food_items USING GIN (dietary_tags);

-- ---------------------------------------------------------------------------
-- feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    package_rating INT CHECK (package_rating >= 1 AND package_rating <= 5),
    food_rating INT CHECK (food_rating >= 1 AND food_rating <= 5),
    itinerary_rating INT CHECK (itinerary_rating >= 1 AND itinerary_rating <= 5),
    ai_helpfulness_rating INT CHECK (ai_helpfulness_rating >= 1 AND ai_helpfulness_rating <= 5),
    free_text_feedback TEXT,
    auto_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    flagged_for_review BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback (session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback (user_id);
