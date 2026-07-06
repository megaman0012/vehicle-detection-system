-- Initial database setup for Vehicle Detection System
-- This script runs on first container startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables if they don't exist (this is a supplement to Alembic migrations)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    role VARCHAR DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cameras table
CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    rtsp_url VARCHAR NOT NULL,
    username VARCHAR,
    password VARCHAR,
    location VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    fps INTEGER DEFAULT 30,
    width INTEGER DEFAULT 1920,
    height INTEGER DEFAULT 1080,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Parking zones table
CREATE TABLE IF NOT EXISTS parking_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    coordinates JSONB NOT NULL,  -- Stores polygon coordinates as JSON array
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Detected vehicles table
CREATE TABLE IF NOT EXISTS detected_vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id VARCHAR UNIQUE NOT NULL,  -- Tracking ID from ByteTrack
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    zone_id UUID REFERENCES parking_zones(id) ON DELETE SET NULL,
    license_plate VARCHAR,
    vehicle_type VARCHAR,
    confidence FLOAT,
    bbox JSONB,  -- Bounding box coordinates
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_parked BOOLEAN DEFAULT FALSE,
    park_start_time TIMESTAMP WITH TIME ZONE,
    total_park_time INTERVAL DEFAULT '0 seconds',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    zone_id UUID REFERENCES parking_zones(id) ON DELETE SET NULL,
    vehicle_id UUID REFERENCES detected_vehicles(id) ON DELETE SET NULL,
    event_type VARCHAR NOT NULL,
    description TEXT,
    license_plate VARCHAR,
    metadata JSONB,  -- Flexible field for additional data
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);
CREATE INDEX IF NOT EXISTS idx_detected_vehicles_vehicle_id ON detected_vehicles(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_detected_vehicles_camera ON detected_vehicles(camera_id);
CREATE INDEX IF NOT EXISTS idx_detected_vehicles_parked ON detected_vehicles(is_parked);
CREATE INDEX IF NOT EXISTS idx_parking_zones_camera ON parking_zones(camera_id);

-- Insert default system configuration
INSERT INTO system_config (key, value, description) VALUES
('parking_time_threshold', '{"minutes": 30}', 'Time threshold in minutes to consider a vehicle as parked'),
('motion_threshold', '{"pixels": 50}', 'Minimum pixel movement to consider vehicle as moving'),
('plate_confidence_threshold', '{"value": 0.6}', 'Minimum confidence for license plate recognition'),
('max_vehicles_per_zone', '{"count": 50}', 'Maximum number of vehicles to track per zone'),
('notification_cooldown', '{"minutes": 5}', 'Minimum time between notifications for same event')
ON CONFLICT (key) DO NOTHING;

-- Create a default admin user (password: admin123)
-- In production, this should be changed immediately
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@vehicle-detection.com') THEN
        INSERT INTO users (email, username, hashed_password, full_name, role, is_superuser)
        VALUES (
            'admin@vehicle-detection.com',
            'admin',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- hash of 'admin123'
            'Administrador del Sistema',
            'admin',
            TRUE
        );
    END IF;
END $$;