-- Migration: add fifa_ranking column to teams table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='teams' AND column_name='fifa_ranking')
    THEN
        ALTER TABLE teams ADD COLUMN fifa_ranking INTEGER;
        RAISE NOTICE 'Added fifa_ranking column to teams';
    END IF;
END$$;
