# Development Guides & How-To Documentation

This directory contains practical guides for developing features, implementing modules, and testing the Gestione Affitti platform.

## Quick Start by Role

### Backend Developer
1. Start: `docs/architecture/BACKEND_DOMAIN_REFACTORING_COMPLETED.md`
2. Then: `MODULE_DEVELOPMENT_GUIDE.md` - How to create modules
3. Test: `TESTING.md` - Testing strategies
4. Reference: `IMPORT_WIZARD_IMPLEMENTATION.md` for real-world example

### Frontend Developer
1. Start: `IMPORT_WIZARD_IMPLEMENTATION.md` - Implementation details
2. Quick ref: `IMPORT_WIZARD_FRONTEND_QUICKSTART.md` - Quick start
3. Components: `IMPORT_WIZARD_FRONTEND_README.md` - Component reference
4. Changes: `CHANGELOG_IMPORT_WIZARD.md` - What's changed
5. Test: `TESTING.md` - Testing strategies

### Full Stack Developer
Follow both backend and frontend paths above.

## Files in This Directory

### MODULE_DEVELOPMENT_GUIDE.md
Comprehensive guide for developing new modules in the Gestione Affitti platform.

**Contents:**
- Module system overview
- Creating module structure and layout
- Defining SQLAlchemy models
- Creating Pydantic schemas
- Implementing FastAPI routes
- Module manifest and metadata
- Testing modules
- Module publishing and discovery
- Real-world examples

**Key Sections:**
- Step-by-step module creation
- Common patterns and best practices
- Handling cross-module dependencies
- Database migrations
- API conventions

**For:** Backend developers creating new modules

### TESTING.md
Complete testing guide for the Gestione Affitti platform.

**Contents:**
- Testing strategy
- Unit testing approaches
- Integration testing
- Frontend component testing
- End-to-end testing
- Test organization
- Running test suites
- Test coverage targets
- Continuous integration

**For:** QA engineers, developers writing tests

### IMPORT_WIZARD_IMPLEMENTATION.md
Real-world implementation guide for the import wizard feature (frontend + backend).

**Contents:**
- Import wizard architecture
- Component structure and hierarchy
- State management
- API integration
- User flows and interactions
- Error handling and validation
- File handling and uploads
- Progress tracking
- Completion and confirmation
- Implementation decisions and trade-offs

**For:** Frontend developers, full-stack developers

### IMPORT_WIZARD_FRONTEND_README.md
Frontend component reference for the import wizard.

**Contents:**
- Component structure
- Props and configuration
- Event handlers
- Component hierarchy
- Styling and layout
- Accessibility features
- Browser compatibility

**For:** React developers working with import wizard

### IMPORT_WIZARD_FRONTEND_QUICKSTART.md
Quick reference for getting the import wizard up and running.

**Contents:**
- Installation steps
- Basic configuration
- Common use cases
- API endpoints needed
- Testing the implementation
- Troubleshooting

**For:** Developers integrating import wizard

### CHANGELOG_IMPORT_WIZARD.md
Version history and changes to the import wizard component.

**Contents:**
- Version history
- New features by version
- Bug fixes
- Breaking changes
- Migration guides
- Known issues
- Deprecated features

**For:** Developers maintaining or upgrading the import wizard

## Development Workflows

### Creating a New Module

1. Read `MODULE_DEVELOPMENT_GUIDE.md` (full guide)
2. Follow step-by-step creation process
3. Create `__manifest__.py` for module metadata
4. Define models in `models/` directory
5. Create schemas in `schemas/` directory
6. Implement routes in `routes/` directory
7. Test using guidelines in `TESTING.md`
8. Module auto-discovers at startup

### Adding Features to Import Wizard

1. Review `IMPORT_WIZARD_IMPLEMENTATION.md` for architecture
2. Understand component structure from `IMPORT_WIZARD_FRONTEND_README.md`
3. Make changes to relevant components
4. Test using procedures in `TESTING.md`
5. Update `CHANGELOG_IMPORT_WIZARD.md`

### Writing Tests

1. Understand testing philosophy in `TESTING.md`
2. Choose appropriate test type (unit/integration/e2e)
3. Follow test organization recommendations
4. Set up test data and fixtures
5. Run test suite and verify coverage

## Common Development Tasks

### Task: Create a New Entity Management Module

**Steps:**
1. Design your entities (what data will you manage?)
2. Follow `MODULE_DEVELOPMENT_GUIDE.md` structure
3. Create models and database tables
4. Implement CRUD routes
5. Create frontend components (if needed)
6. Write tests
7. Document in CHANGELOG

**Time Estimate:** 2-4 hours for simple module

### Task: Add a New Feature to Existing Module

**Steps:**
1. Identify the module you're modifying
2. Add model fields if needed
3. Create new routes or modify existing ones
4. Update frontend components
5. Write tests for new behavior
6. Update documentation

**Time Estimate:** 1-2 hours depending on complexity

### Task: Fix a Bug

**Steps:**
1. Write a test that reproduces the bug
2. Verify test fails
3. Fix the bug in code
4. Verify test passes
5. Run full test suite
6. Update relevant documentation if needed

**Time Estimate:** 30 minutes to 2 hours

## Best Practices

### Code Organization
- Keep related functionality in the same module
- Use meaningful names for functions and variables
- Follow naming conventions from `docs/architecture/`

### Testing
- Write tests as you write code
- Aim for 80%+ code coverage
- Include both happy path and error cases
- Use fixtures for test data

### Documentation
- Update docstrings as you code
- Add comments for complex logic
- Update CHANGELOG when adding features
- Keep README files current

### Database Changes
- Create migrations for schema changes
- Test migrations work forward and backward
- Document schema changes in code comments

## References

- `docs/architecture/` - System design and module structure
- `docs/api/` - API design and conventions
- `docs/features/` - Feature documentation
- Root `CLAUDE.md` - Coding patterns and conventions
- `docs/setup/DEPLOYMENT_GUIDE.md` - Deployment information

## Support & Questions

- Check CLAUDE.md for development patterns
- Review existing module examples
- Look at similar features for patterns
- Ask in team communication channels

---

**Last Updated:** 2025-12-04
**Status:** Production Ready
**Covers:** All modules and features
