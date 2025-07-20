import datetime
import enum
import uuid
import typing as t

from pydantic import BaseModel


class ModelDumpMixin(BaseModel):
    def model_dump_serialized(
        self,
        *,
        mode: t.Literal["json", "python"] | str = "python",
        include: t.Any = None,  # IncEx = None,
        exclude: t.Any = None,  # IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, t.Any]:
        dump_obj = super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )
        for key, value in dump_obj.items():
            dump_obj[key] = self._serialize_item(value)
        return dump_obj

    def _serialize_item(self, item: t.Any) -> t.Any:
        if isinstance(item, datetime.datetime | datetime.date | datetime.time):
            return item.isoformat()
        elif isinstance(item, uuid.UUID):  # noqa: RET505
            return str(item)
        elif isinstance(item, enum.Enum):
            return item.value
        elif isinstance(item, list | tuple):
            return [self._serialize_item(sub_item) for sub_item in item]
        elif isinstance(item, dict):
            return {k: self._serialize_item(v) for k, v in item.items()}
        return item
