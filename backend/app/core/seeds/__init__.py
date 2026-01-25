"""
Core Seeds Module - Platform Domain Data Seeding

This module handles seeding of domain/reference data into the PUBLIC schema.
Domain data is master data managed by platform admin and referenced by all tenants.

Usage:
    from app.core.seeds import seed_all_domain_data
    seed_all_domain_data(db)  # Seeds all domain tables in public schema
"""
from .domain_seeder import seed_all_domain_data, seed_domain_table

__all__ = ["seed_all_domain_data", "seed_domain_table"]
