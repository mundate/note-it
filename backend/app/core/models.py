"""Shared API model pieces. Feature models (e.g. app/todo/models.py) build on `ApiModel`.

All API models are the source of truth for the frontend's generated TypeScript types.
Model class names become TS type names, so keep them stable. Python attributes are
snake_case; JSON (and therefore TS) is camelCase via the alias generator.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
