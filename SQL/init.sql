-- Initialise the PostgreSQL database.
-- Run this using `psql` from the project root.

\set PATH 'SQL/Schema'

-- Types

\i :PATH/Types/permission_scope_enum.sql
\i :PATH/Types/permission_type_enum.sql

-- Tables, Constraints & Indexes

\i :PATH/Tables/ids.sql

\i :PATH/Tables/companies.sql
\i :PATH/Tables/teams.sql
\i :PATH/Tables/users.sql

\i :PATH/Tables/assignments.sql
\i :PATH/Tables/assignments_indexes.sql

\i :PATH/Tables/permissions.sql
\i :PATH/Tables/permissions_indexes.sql

\i :PATH/Tables/tasks.sql
\i :PATH/Tables/tasks_indexes.sql

\i :PATH/Tables/quotes.sql