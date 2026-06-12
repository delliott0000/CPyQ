DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_sort') THEN
        CREATE TYPE task_sort AS ENUM (
        -- Remove the placeholder value when real values are ready to be implemented
        '__placeholder__'
    );
    END IF;
END
$$;