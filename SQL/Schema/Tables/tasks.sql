CREATE TABLE IF NOT EXISTS tasks (
    id INT PRIMARY KEY REFERENCES ids(id),
    sort task_sort NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);