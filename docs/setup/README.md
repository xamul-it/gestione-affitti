# Setup & Deployment Documentation

This directory contains all documentation related to installation, configuration, migration, and deployment of the Gestione Affitti platform.

## Quick Start

For first-time setup, follow these steps:

1. **Installation & Environment Setup:** `DEPLOYMENT_GUIDE.md`
2. **Database Migration:** `MIGRATION.md`
3. **Quick Start for Import System:** `IMPORT_AUTOMATISMI_QUICK_START.md`
4. **Data Migration (if needed):** `MIGRAZIONE_SOGGETTI_ANAGRAFICI.md`

## Files in This Directory

### DEPLOYMENT_GUIDE.md
Complete guide for deploying the Gestione Affitti platform to production or development environments.

**Contents:**
- Environment setup and prerequisites
- Backend installation and configuration
- Frontend setup and build process
- PostgreSQL database setup
- Running with production servers (Gunicorn)
- Docker configuration (if applicable)
- Common deployment issues and troubleshooting

**For:** DevOps engineers, backend developers, deployment specialists

### MIGRATION.md
Database migration guide for updating existing installations.

**Contents:**
- Migration procedures
- Schema updates
- Data consistency checks
- Rollback procedures
- Testing migrations

**For:** Database administrators, DevOps engineers

### MIGRAZIONE_SOGGETTI_ANAGRAFICI.md
Italian language guide for migrating Subject/Anagrafico data between systems.

**Contents:**
- Data migration procedures for anagrafica_italiana module
- Subject (Soggetto) data handling
- Validation procedures
- Common issues and solutions

**For:** System administrators, data migration specialists

### IMPORT_AUTOMATISMI_QUICK_START.md
Quick reference guide for setting up and using the import automatisms (automated systems).

**Contents:**
- Quick setup for import features
- Enabling automatisms
- Configuration options
- Testing the import system
- Troubleshooting import issues

**For:** Backend developers, QA engineers, system administrators

## Setup Workflows by Role

### Backend Developer
1. Read DEPLOYMENT_GUIDE.md (Development section)
2. Follow the setup instructions
3. Review MIGRATION.md if updating an existing installation

### DevOps/System Administrator
1. DEPLOYMENT_GUIDE.md (Production section)
2. MIGRATION.md for existing systems
3. IMPORT_AUTOMATISMI_QUICK_START.md for feature setup

### Data Migration Specialist
1. MIGRATION.md
2. MIGRAZIONE_SOGGETTI_ANAGRAFICI.md
3. Verify data consistency after migration

## Common Setup Tasks

### Initial Installation
1. Clone the repository
2. Follow DEPLOYMENT_GUIDE.md
3. Set up `.env` file with database credentials
4. Run database migrations
5. Start backend and frontend servers

### Adding Import Features
1. Review IMPORT_AUTOMATISMI_QUICK_START.md
2. Enable automatisms in configuration
3. Test with sample data
4. Monitor for issues

### Migrating to New Environment
1. Backup current database
2. Follow DEPLOYMENT_GUIDE.md in new environment
3. Use MIGRATION.md procedures for database transfer
4. Verify all functionality works

## Environment Variables

Key environment variables needed for setup:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key
- `BACKEND_CORS_ORIGINS` - CORS allowed origins
- `VITE_API_BASE_URL` - Frontend API endpoint

See DEPLOYMENT_GUIDE.md for complete list.

## Troubleshooting

- **Database connection issues:** Check DEPLOYMENT_GUIDE.md troubleshooting section
- **Migration problems:** Refer to MIGRATION.md rollback procedures
- **Import feature issues:** See IMPORT_AUTOMATISMI_QUICK_START.md troubleshooting

## References

- Root-level `README.md` - Project overview
- Root-level `CLAUDE.md` - Architecture and development patterns
- `docs/architecture/` - System design documentation
- `docs/guides/MODULE_DEVELOPMENT_GUIDE.md` - For adding new modules

---

**Last Updated:** 2025-12-04
**Status:** Production Ready
