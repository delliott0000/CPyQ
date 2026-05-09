CREATE TABLE IF NOT EXISTS permissions (
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    type permission_type NOT NULL,
    scope permission_scope,
    CONSTRAINT type_scope_valid CHECK (
        (type = 'create' AND scope IS NULL)
	    OR
	    (type <> 'create' AND scope IS NOT NULL)
    )
);