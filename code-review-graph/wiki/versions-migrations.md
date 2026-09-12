# versions-migrations

## Overview

Directory-based community: apps/api/alembic

- **Size**: 6 nodes
- **Cohesion**: 0.0000
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| run_migrations_offline | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 22-32 |
| run_migrations_online | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 34-49 |
| upgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 21-195 |
| downgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 198-221 |
| upgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/c2d4_v2_4_schema_expansion.py | 18-36 |
| downgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/c2d4_v2_4_schema_expansion.py | 39-56 |

## Execution Flows

No execution flows pass through this community.

## Dependencies

### Outgoing

- `Column` (133 edge(s))
- `String` (56 edge(s))
- `Float` (35 edge(s))
- `DateTime` (18 edge(s))
- `drop_column` (16 edge(s))
- `add_column` (16 edge(s))
- `f` (14 edge(s))
- `drop_table` (11 edge(s))
- `create_table` (11 edge(s))
- `PrimaryKeyConstraint` (11 edge(s))
- `drop_index` (10 edge(s))
- `Integer` (10 edge(s))
- `create_index` (10 edge(s))
- `ForeignKeyConstraint` (10 edge(s))
- `JSON` (9 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/c2d4_v2_4_schema_expansion.py` (2 edge(s))
