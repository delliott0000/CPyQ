-- Populate the PostgreSQL database with dummy data.
-- Run this using `psql`.
-- This is a tool to aid in development. Do not run this in production!

-- Define the helper "new_id()" function.

CREATE OR REPLACE FUNCTION new_id() RETURNS INT AS $$

DECLARE
    new_id INT;

BEGIN
    INSERT INTO ids DEFAULT VALUES RETURNING id INTO new_id;
    RETURN new_id;

END;
$$ LANGUAGE plpgsql;

-- Insert the sample data.
-- This will dynamically generate new IDs for insertion, but will fail if any other UNIQUE values are already taken.
-- For example, running the script twice in a row.

DO $$
DECLARE
    company_id INT;
    team_id INT;
    user_id INT;
    quote_id INT;

BEGIN
    company_id := new_id();
    team_id := new_id();
    user_id := new_id();
    quote_id := new_id();

    INSERT INTO companies (
        id,
        name
    ) VALUES (
        company_id,
        'Company'
    );

    INSERT INTO teams (
        id,
        company_id,
        name,
        hierarchy_index
    ) VALUES (
        team_id,
        company_id,
        'Team',
        0
    );

    -- Unencrypted password is "Password".

    INSERT INTO users (
        id,
        username,
        hashed_password,
        display_name,
        email,
        autopilot,
        admin
    ) VALUES (
        user_id,
        'Username',
        '$2b$12$wWwoVXeqNEeF1JzfBBOehecB8EL00Tz4K.sgu0k2p37JQ1K7ygXbm',
        'DisplayName',
        'email@domain.com',
        FALSE,
        FALSE
    );

    INSERT INTO assignments (
        user_id,
        team_id
    ) VALUES (
        user_id,
        team_id
    );

    INSERT INTO permissions (
        team_id,
        permission_type,
        permission_scope
    ) VALUES
        (team_id, 'acquire', 'safe'),
        (team_id, 'preview', 'safe'),
        (team_id, 'view', 'safe');

    INSERT INTO quotes (
        id,
        owner_id
    ) VALUES (
        quote_id,
        user_id
    );

END;
$$ LANGUAGE plpgsql;