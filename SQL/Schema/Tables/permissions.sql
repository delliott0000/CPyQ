CREATE TABLE IF NOT EXISTS permissions (
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    permission_type permission_type NOT NULL,
    permission_scope permission_scope,
    CONSTRAINT type_scope_valid CHECK (
        (permission_type = 'create' AND permission_scope IS NULL)
	    OR
	    (permission_type <> 'create' AND permission_scope IS NOT NULL)
    )
);