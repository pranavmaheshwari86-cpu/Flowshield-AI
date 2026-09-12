# alembic-migrations

## Overview

Directory-based community: apps/api/alembic

- **Size**: 4 nodes
- **Cohesion**: 0.0000
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| run_migrations_offline | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 22-32 |
| run_migrations_online | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 34-49 |
| upgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 21-195 |
| downgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 198-221 |

## Execution Flows

No execution flows pass through this community.

## Dependencies

### Outgoing

- `Column` (117 edge(s))
- `String` (53 edge(s))
- `Float` (24 edge(s))
- `DateTime` (16 edge(s))
- `f` (14 edge(s))
- `drop_table` (11 edge(s))
- `create_table` (11 edge(s))
- `PrimaryKeyConstraint` (11 edge(s))
- `drop_index` (10 edge(s))
- `Integer` (10 edge(s))
- `create_index` (10 edge(s))
- `ForeignKeyConstraint` (10 edge(s))
- `JSON` (9 edge(s))
- `Boolean` (5 edge(s))
- `configure` (2 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py` (2 edge(s))
