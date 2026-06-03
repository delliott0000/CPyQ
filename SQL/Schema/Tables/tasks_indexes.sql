CREATE INDEX IF NOT EXISTS idx_tasks_incomplete
ON tasks(created_at)
WHERE completed_at IS NULL;