CREATE INDEX IF NOT EXISTS idx_permissions_team_id
ON permissions(team_id);

CREATE UNIQUE INDEX IF NOT EXISTS unique_idx_scope_null
ON permissions (team_id, type)
WHERE type = 'create' AND scope IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS unique_idx_scope_not_null
ON permissions (team_id, type, scope)
WHERE type <> 'create' AND scope IS NOT NULL;