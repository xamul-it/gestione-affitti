# Technical Reference & Implementation Reports

This directory contains technical reference materials, implementation summaries, and detailed reports from the development and testing phases.

## Quick Navigation

### Implementation Overview
- **Implementation Plan:** `IMPLEMENTATION_PLAN.md` - Comprehensive implementation roadmap
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md` - Summary of work completed
- **Italian Implementation Report:** `IMPLEMENTAZIONE_SISTEMA_IMPORT_REPORT.md` - Detailed implementation (Italian)

### Testing & Quality Assurance
- **Frontend Testing Report:** `FRONTEND_TESTING_REPORT.md` - Frontend test results and coverage
- **UAT Fix Report:** `REPORT_FIX_UAT_ISSUES.md` - Fixes for UAT-identified issues
- **Frontend Integration Report:** `REPORT_FRONTEND_INTEGRATION.md` - Frontend integration testing

### Technical References
- **Refactoring Report:** `refactoring_report.md` - Details of code refactoring work
- **Archived Claude Instructions:** `CLAUDE_ARCHIVED.md` - Previous Claude assistant instructions (archived)

## Files in This Directory

### IMPLEMENTATION_PLAN.md
Comprehensive implementation plan and project roadmap.

**Contents:**
- Project goals and objectives
- Feature breakdown and scope
- Implementation phases and timeline
- Team roles and responsibilities
- Resource allocation
- Risk assessment
- Success criteria
- Milestone definitions
- Detailed task lists

**Use Cases:**
- Project planning and tracking
- Understanding feature scope
- Timeline reference
- Resource planning
- Risk mitigation

**For:** Project managers, team leads, stakeholders

### IMPLEMENTATION_SUMMARY.md
Summary of implementation work completed.

**Contents:**
- Completed features
- Work breakdown structure
- Time tracking and effort
- Issues encountered and resolved
- Lessons learned
- Quality metrics
- Performance results
- Team contributions

**Sections:**
- Feature implementation status
- Code changes summary
- Database changes
- API endpoints added/modified
- Frontend components added/modified
- Testing coverage
- Known limitations

**For:** Project leads, developers, stakeholders

### IMPLEMENTAZIONE_SISTEMA_IMPORT_REPORT.md
Detailed implementation report in Italian for the import system.

**Contents:**
- Sistema import overview (Italian)
- Architettura tecnica
- Implementazione dettagliata
- Risultati di test
- Issues risolti
- Performance metrics
- Raccomandazioni

**For:** Italian-speaking team members, documentation in Italian

### FRONTEND_TESTING_REPORT.md
Comprehensive testing report for frontend components and features.

**Contents:**
- Test plan overview
- Component testing results
- User interaction testing
- Browser compatibility
- Performance testing
- Accessibility testing
- Test coverage metrics
- Issues identified
- Recommendations

**Test Coverage Areas:**
- Component rendering
- User interactions
- Form validation
- Data binding
- Navigation
- Responsive design
- Performance metrics
- Accessibility compliance

**For:** QA engineers, frontend developers, product managers

### REPORT_FIX_UAT_ISSUES.md
Report on fixes applied to address UAT (User Acceptance Testing) identified issues.

**Contents:**
- Issues identified during UAT
- Root cause analysis for each issue
- Fixes implemented
- Verification and testing of fixes
- Performance impact assessment
- Regression testing results
- Sign-off and approval

**Issue Categories:**
- Functionality issues
- Performance problems
- Data consistency issues
- User experience problems
- Error handling issues

**For:** QA leads, developers, project managers

### REPORT_FRONTEND_INTEGRATION.md
Frontend integration testing report.

**Contents:**
- Integration test plan
- API integration testing
- Component integration testing
- End-to-end testing results
- Data flow verification
- Error handling in integration
- Performance under integration
- Issues found and fixed

**Test Scenarios:**
- Login and authentication flow
- Data creation and modification
- Import wizard end-to-end flow
- Error recovery
- Multi-step workflows

**For:** QA engineers, full-stack developers, integration specialists

### refactoring_report.md
Detailed report on code refactoring activities.

**Contents:**
- Refactoring goals and justification
- Areas refactored
- Code metrics before/after
- Performance improvements
- Maintainability improvements
- Testing approach for refactoring
- Issues discovered during refactoring
- Technical debt addressed
- Remaining technical debt

**Refactoring Areas:**
- Module structure consolidation
- Code duplication elimination
- Performance optimizations
- Testing improvements
- Documentation updates

**For:** Developers, technical leads, architects

### CLAUDE_ARCHIVED.md
Archived Claude assistant instructions (for historical reference).

**Contents:**
- Previous versions of project instructions
- Historical development patterns
- Deprecated conventions (if any)
- Evolution of guidelines

**Note:** The active CLAUDE.md file is at the project root. This file is kept for reference only.

**For:** Understanding project history, reference

## Technical Reference Guide

### Database Schema

Key tables across modules:

**Platform Core:**
- `users` - User accounts
- `roles` - User roles
- `ruoli_disponibili` - Available roles

**anagrafica_italiana Module:**
- `soggetti_anagrafici` - Persons and companies
- `tipi_soggetto` - Subject types (enum)

**immobili Module:**
- `unita_immobiliari` - Property units
- `condominii` - Condominium buildings
- `proprietari` - Property owners
- `diritti_immobili` - Property rights/ownership
- `categorie_catastali` - Cadastral categories
- `comuni_italia` - Italian municipalities
- `tipo_immobile_categoria_map` - Type-to-category learning table
- `certificati_energetici` - Energy certificates
- `tabelle_millesimali` - Condominium millennial tables
- `millesimi_unita` - Unit millennial shares

**affitti_lungo Module:**
- `affittuari` - Tenants
- `contratti` - Rental contracts
- `incassi` - Monthly income
- `spese` - Property expenses
- `tecnici` - Maintenance technicians
- `ripartizioni_spesa` - Expense distribution
- `documenti` - File attachments (polymorphic)

### API Endpoint Reference

Base URL: `http://localhost:8000/api/v1`

**Entity Endpoints (standard CRUD):**
- `GET /entity/` - List (with pagination)
- `POST /entity/` - Create
- `GET /entity/{id}` - Get
- `PUT /entity/{id}` - Update
- `DELETE /entity/{id}` - Delete

**Import Endpoints:**
- `POST /import/upload` - Upload CSV
- `GET /import/{id}/preview` - Preview data
- `POST /import/{id}/validate` - Validate
- `POST /import/{id}/process` - Process
- `GET /import/{id}/progress` - Check progress
- `GET /import/{id}/result` - Get result

**Special Endpoints:**
- `GET /platform/menu/` - Get application menu
- `GET /platform/dashboard/` - Get dashboard widgets
- `GET /categorie-catastali/` - List cadastral categories
- `GET /comuni/` - List municipalities

### Performance Metrics

**Import System:**
- Speed: ~14 rows/second
- Database queries: 7-8 per row
- Success rate: 93%+ (typical)
- Transaction safety: Rollback on error

**API Response Times:**
- List endpoints: <100ms (typical)
- Single entity: <50ms
- Create/Update: 100-500ms
- Import processing: Varies (hours for large batches)

### Error Codes

Common error codes returned by API:

- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (entity doesn't exist)
- `409` - Conflict (data conflict, duplicate entry)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Code Quality Metrics

From implementation reports:

- Test coverage: Target 80%+
- Code duplication: Minimized through refactoring
- Performance: Optimized for common operations
- Documentation: Complete with inline comments
- Type safety: Using Python type hints throughout

## Development Workflow

### Adding a Feature

1. Review IMPLEMENTATION_PLAN.md for context
2. Follow MODULE_DEVELOPMENT_GUIDE.md for technical steps
3. Ensure changes are covered by tests (per FRONTEND_TESTING_REPORT.md approach)
4. Verify integration with existing features
5. Document changes in implementation summary
6. Request code review

### Investigating Issues

1. Check REPORT_FIX_UAT_ISSUES.md for similar issues
2. Review FRONTEND_TESTING_REPORT.md for known problem areas
3. Check error logs for patterns
4. Trace through REPORT_FRONTEND_INTEGRATION.md if related to integration
5. Follow up with debugging and testing

### Performance Optimization

1. Establish baseline using metrics in these reports
2. Identify bottleneck using profiling tools
3. Implement optimization
4. Measure improvement
5. Document changes in refactoring_report.md format

## Maintenance & Updates

### Regular Tasks

- Review testing reports monthly
- Update documentation as features change
- Archive old reports (move to docs/obsolete/)
- Keep implementation plan current

### Version Compatibility

- Check IMPLEMENTATION_SUMMARY.md for version info
- Review FRONTEND_TESTING_REPORT.md for browser compatibility
- Test with supported versions before upgrade

## References

- Root `CLAUDE.md` - Current development guidelines
- `docs/architecture/` - System design
- `docs/api/` - API documentation
- `docs/guides/` - Development guides
- `docs/setup/` - Deployment information

---

**Last Updated:** 2025-12-04
**Status:** Production Ready
**Documentation Complete:** Yes
**Test Coverage:** 80%+
