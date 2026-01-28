CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY REFERENCES ids(id),
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    display_name TEXT,
    email TEXT UNIQUE,
    autopilot BOOLEAN NOT NULL DEFAULT FALSE,
    admin BOOLEAN NOT NULL DEFAULT FALSE
);