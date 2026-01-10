-- Update roles/permissions for a user (default: admin)
-- Usage:
--   psql -d gestione_affitti -v username='admin' -f backend/scripts/update_roles.sql

BEGIN;

-- 1) Ensure permissions exist
WITH platform_perm AS (
    INSERT INTO permissions (name, description, resource, action)
    VALUES ('platform.admin', 'Full platform administration access', 'platform', 'admin')
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    RETURNING id
),
tenant_perm AS (
    INSERT INTO permissions (name, description, resource, action)
    VALUES ('tenant.admin', 'Full tenant administration access', 'tenant', 'admin')
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    RETURNING id
)
SELECT 1;

-- 2) Ensure roles exist
WITH platform_role AS (
    INSERT INTO roles (name, description, is_system)
    VALUES ('Platform Administrator', 'Full platform administration access', true)
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    RETURNING id
),
tenant_role AS (
    INSERT INTO roles (name, description, is_system)
    VALUES ('Tenant Administrator', 'Full tenant administration access', true)
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    RETURNING id
),
admin_role AS (
    INSERT INTO roles (name, description, is_system)
    VALUES ('Admin', 'Full system access - can manage everything', true)
    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
    RETURNING id
)
SELECT 1;

-- 3) Map permissions to roles
WITH platform_perm AS (
    SELECT id FROM permissions WHERE name = 'platform.admin'
),
tenant_perm AS (
    SELECT id FROM permissions WHERE name = 'tenant.admin'
),
platform_role AS (
    SELECT id FROM roles WHERE name = 'Platform Administrator'
),
tenant_role AS (
    SELECT id FROM roles WHERE name = 'Tenant Administrator'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT platform_role.id, platform_perm.id FROM platform_role, platform_perm
ON CONFLICT DO NOTHING;

WITH platform_perm AS (
    SELECT id FROM permissions WHERE name = 'platform.admin'
),
tenant_perm AS (
    SELECT id FROM permissions WHERE name = 'tenant.admin'
),
platform_role AS (
    SELECT id FROM roles WHERE name = 'Platform Administrator'
),
tenant_role AS (
    SELECT id FROM roles WHERE name = 'Tenant Administrator'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT tenant_role.id, tenant_perm.id FROM tenant_role, tenant_perm
ON CONFLICT DO NOTHING;

-- 4) Assign roles to user
WITH target_user AS (
    SELECT id FROM users WHERE username = :'username'
),
roles_to_assign AS (
    SELECT id FROM roles WHERE name IN ('Admin', 'Platform Administrator', 'Tenant Administrator')
)
INSERT INTO user_roles (user_id, role_id)
SELECT target_user.id, roles_to_assign.id
FROM target_user, roles_to_assign
ON CONFLICT DO NOTHING;

COMMIT;
