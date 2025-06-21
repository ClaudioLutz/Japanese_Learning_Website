# Deprecated Files

This directory contains files that are no longer actively used in the Japanese Learning Website project but are preserved for reference and backup purposes.

## Files Moved to Deprecated (June 21, 2025)

### Legacy Application Files
- **app_old_backup.py** - Backup of old application structure before unified authentication
- **redirect_old_admin.py** - Legacy admin redirect script (no longer needed)

### Legacy Database Files
- **japanese_learning.db** - Original SQLite database before unified system
- **site.db** - Old database file (main database now in `instance/site.db`)

### Legacy Templates
- **legacy_templates/** - Original template directory structure
  - Contains old admin templates before migration to `app/templates/admin/`
  - Preserved for reference in case of rollback needs

### Development Files
- **brainstorming.md** - Initial project planning and brainstorming notes
- **AGENTS.md** - Development agent configuration and notes

## Current Active Structure

The main project now uses:
- **Database**: `instance/site.db` (unified authentication system)
- **Templates**: `app/templates/` (proper Flask structure)
- **Admin Panel**: Integrated with main authentication system

## Why These Files Were Deprecated

1. **Unified Authentication**: The project migrated from separate admin/user systems to a unified authentication system
2. **Template Structure**: Templates moved to proper Flask application structure (`app/templates/`)
3. **Database Consolidation**: Multiple database files consolidated into single unified database
4. **Code Organization**: Improved project structure and removed redundant files

## Recovery Instructions

If you need to restore any of these files:

1. **Legacy Templates**: Copy from `deprecated/legacy_templates/` back to root as `templates/`
2. **Legacy Database**: Copy `deprecated/japanese_learning.db` back to root
3. **Old Application**: Use `deprecated/app_old_backup.py` as reference for old structure

## Safe to Delete

These files can be safely deleted if you're confident the new unified system is working correctly:
- All files in this directory are backups/legacy versions
- The current system in the main project directory is fully functional
- No active code references these deprecated files

---

*Cleanup performed: June 21, 2025*
*Unified authentication system fully implemented and tested*
