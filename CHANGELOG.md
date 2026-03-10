# CHANGELOG

All notable changes to Operational CPX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- (Nothing yet)

---

## [0.3.0] - 2026-03-10

### Added
- **NATO Documentation**: Created `docs/nato/glossary.md` with NATO terminology, abbreviations, and echelon hierarchy
- **Report Samples**: Created `docs/nato/reports.md` with JSON schemas and samples for SITREP, INTSUM, OPSUM, LOGSITREP, SALUTE
- **i18n Foundation**: Created `frontend/public/locales/ja/translation.json` and `frontend/app/lib/i18n.ts` for UI internationalization
- **MGRS References**: Added grid reference system to all scenario documents
- **ORBAT Tables**: Added Order of Battle sections to all scenarios
- **Arcade 12x8 Notation**: Explicit notation for Arcade mode configuration in all scenarios

### Changed
- **Scenarios**: Updated fulda-lite.md, baltic.md, desert.md with MGRS references and ORBAT tables

---

## [0.2.0] - 2026-03-09

### Added
- **CPX-8: Reproducibility**: RNG seed management, structured logging, AAR enhancement
  - `backend/app/services/rng_service.py`: Seed management per turn
  - `backend/app/services/structured_logging.py`: JSON structured logging
  - `backend/app/services/debriefing.py`: MOP/MOE indicators added
- **CPX-7: Logistics Model**: Class III/V supply, supply routes, resupply cycles
  - `backend/app/services/logistics_service.py`: Supply node/route/convoy management
  - `shared/types/index.ts`: Logistics-related types
- **CPX-6: Multi-role RBAC**: BLUE/RED/WHITE/Observer roles + real-time notifications
  - `backend/app/services/rbac_service.py`: Role-based access control
  - `backend/app/services/notification_service.py`: WebSocket notifications
- **CPX-5: CCIR/PIR/ROE**: Commander's Critical Information Requirements integrated into adjudication
  - CCIR evaluation in `arcade_adjudication.py`
  - Debriefing CCIR summary
- **Report Generator**: Standardized military report formats (SITREP/INTSUM/OPSUM/LOGSITREP/SALUTE)
  - `backend/app/services/report_generator.py`: UnifiedReportGenerator
- **OPORD/FRAGO**: SMESC data model and editor
  - `backend/app/services/opord_service.py`: OPORD CRUD operations
  - Frontend OPORD editor UI
- **MEL/MIL (Inject)**: Injection system with conditions and effects
  - `backend/app/services/inject_system.py`: MEL/MIL management
  - Frontend EXCON panel

### Changed
- **Arcade Adjudication**: Updated to use RNGService, added structured logging

---

## [0.1.0] - 2026-03-08

### Added
- **Arcade Mode**: 12x8 grid condensed gameplay
  - 6 unit types: INFANTRY, ARMOR, ARTILLERY, AIR_DEFENSE, RECON, SUPPORT
  - 6 commands: MOVE, ATTACK, DEFEND, RECON, SUPPLY, STRIKE
  - 2D6 judgment system with difference-based results
  - VP scoring system with victory conditions
  - Event deck (10 cards, 40% draw chance)
  - Enemy AI (basic): adjacent attack > advance > defend
- **Map System**:
  - 50x50 grid for Classic mode
  - 12x8 grid for Arcade mode
  - Terrain types: Plain, Forest, Urban, Mountain, Water
  - Fog of War with observation confidence (confirmed/estimated/unknown)
- **API Endpoints**:
  - `/api/games/*`: Game management
  - `/api/turn/*`: Turn processing
  - `/api/orders/*`: Order management
  - `/api/internal/*`: Internal endpoints (behind flag)
- **Frontend**:
  - Next.js 14 with TypeScript
  - Interactive SVG map with zoom/pan
  - Unit markers with NATO symbols (APP-6)
  - Command panel with batch order support
  - SITREP/OPORD/Reports panels

### Changed
- **Rules**: 2D6 difference system for combat resolution
- **Scenarios**: Added Arcade configurations to all scenarios

---

## [0.0.1] - 2026-03-07

### Added
- Initial project setup
- Basic game engine foundation
- Simple turn-based combat system
- Text map generation

---

## Deprecated
- None

## Removed
- None

## Security
- Internal API endpoints secured behind `ENABLE_INTERNAL_ENDPOINTS` flag (2026-03-09)
- Order API validates unit ownership by side (2026-03-09)

---

## Migration Notes

### Upgrading to 0.3.0
- No breaking changes to API
- New documentation available in `docs/nato/`

### Upgrading to 0.2.0
- Report generator now supports 5 formats
- OPORD/FRAGO are now persistent
- RBAC roles expanded

---

## Related Documents

- [game-rules.md](./docs/game-rules.md)
- [quick-ref.md](./docs/quick-ref.md)
- [architecture.md](./docs/architecture.md)
- [docs/nato/glossary.md](./docs/nato/glossary.md)
- [docs/nato/reports.md](./docs/nato/reports.md)
