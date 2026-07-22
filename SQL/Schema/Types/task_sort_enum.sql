DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_sort') THEN
        CREATE TYPE task_sort AS ENUM (
        'export_quote'
    );
    END IF;
END
$$;