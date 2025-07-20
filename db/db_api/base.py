import copy
import typing as t

from asyncpg import exceptions as ae
from sqlalchemy import (
    Column,
    column as sa_column,
    delete,
    desc,
    exc as sa_exc,
    exists,
    func,
    future,
    literal,
    text,
    union,
    update,
)
from sqlalchemy import orm as so
from sqlalchemy.dialects import postgresql as pg_dialect
from sqlalchemy.ext import asyncio as sa_asyncio
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql import Subquery
from sqlalchemy.sql.elements import Case
from sqlalchemy.sql.expression import BinaryExpression

from logger import logger
from utils import exceptions as custom_exc


Base = so.declarative_base()


class BaseDbApiHandler:
    @classmethod
    async def handle_exception(cls, exc):
        exc_name = "Unhandled Exception"
        raised_error = custom_exc.SomethingWentWrongException
        if isinstance(exc, sa_exc.IntegrityError):
            exc_name = "IntegrityError"
            raised_error = custom_exc.ObjectAlreadyExistsException
        if isinstance(exc, sa_exc.DBAPIError):  # noqa: SIM102
            if hasattr(exc, "orig") and hasattr(exc.orig, "sqlstate"):
                if exc.orig.sqlstate == ae.CharacterNotInRepertoireError.sqlstate:
                    exc_name = "CharacterNotInRepertoireError"
                else:
                    exc_name = exc.orig.args[0]
        logger.error(f"{exc_name}: {repr(exc)}")
        raise raised_error()

    @classmethod
    async def _execute(cls, session: sa_asyncio.AsyncSession, stmt, kwargs=None):
        kwargs = kwargs if kwargs else {}
        try:
            res = await session.execute(stmt, kwargs)
        except Exception as exc:
            await session.rollback()
            await cls.handle_exception(exc)
        else:
            return res

    @classmethod
    async def execute(cls, session: sa_asyncio.AsyncSession, stmt, kwargs=None):
        return await cls._execute(session, stmt, kwargs)

    @classmethod
    async def session_cls_execute(cls, session_cls: sa_asyncio.AsyncSession, stmt, kwargs: dict | None = None):
        async with session_cls() as session:
            return await cls._execute(session, stmt, kwargs)

    @classmethod
    async def _commit(cls, session: sa_asyncio.AsyncSession):
        try:
            await session.commit()
        except Exception as exc:
            await session.rollback()
            await cls.handle_exception(exc)

    @classmethod
    async def commit(cls, session: sa_asyncio.AsyncSession):
        await cls._commit(session)

    @classmethod
    async def ping(cls, session_cls: sa_asyncio.AsyncSession):
        async with session_cls() as session:
            await cls._execute(session, text("SELECT 1"))

    @classmethod
    async def _retrieve_session(
        cls,
        session: sa_asyncio.AsyncSession,
        model: DeclarativeMeta | None = None,
        condition: tuple[BinaryExpression | bool, ...] = (),
        joins: tuple[dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...] | None = None,
        subquery_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        joined_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        selectin_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        many: bool = False,
        order_fields: tuple[Column | str | Case, ...] | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        page: int | None = None,
        distinct: tuple[Column | str | Case, ...] | bool | None = None,
        group_by: tuple[Column | str | Case] | None = None,
    ) -> DeclarativeMeta | list[DeclarativeMeta]:
        """
        This is an asynchronous class method that is used to retrieve objects from the database using SQLAlchemy ORM.

        Parameters:

            :param session: Assync database session.
            :param model: SQLAlchemy DeclarativeMeta model class that represents the table in the database to query from.
                If not provided, the method will use the model associated with the class (`cls.model`).
            :param condition: A tuple of SQLAlchemy BinaryExpression conditions for the SQL WHERE clause.
            :param joins: ...
            :param subquery_load: A tuple of SQLAlchemy ORM paths to be loaded using subquery eager loading.
                The paths can be specified as column objects or column names as strings.
            :param joined_load: ...
            :param selectin_load: ...
            :param many: Boolean flag that, if True, indicates that all records that match the conditions should be returned.
                If False, only the first matching record will be returned. Default is False.
            :param order_fields: SQLAlchemy Column object that represents the column to order the results by.
            :param order_desc: Boolean flag that, if True, indicates that the results should be ordered in descending order.
                If False, the results will be ordered in ascending order. Default is False.
            :param limit: The maximum number of results to return. If not provided, all matching results will be returned.
            :param page: The number of the page of results to return, based on the limit. If not provided, the first page of results will be returned.
                If `page` is provided and `limit` is not set, 10 will be used as a default limit.
            :param distinct: ...

        Returns:

            If `many` is True or `limit` is set, a list of SQLAlchemy ORM objects that represent the records that match the conditions is returned.
            If `many` is False and `limit` is not set, a single SQLAlchemy ORM object that represents the first record that matches the conditions is returned.

        Raises:

            Various SQLAlchemy exceptions can be raised depending on the validity of the parameters and the state of the database.

        Usage:

            result = await MyClass._retrieve(session_cls=MyAsyncSession, model=MyModel, condition=(MyModel.id == 1,), many=True)
        """
        stmt = future.select(model or cls.model)
        if distinct:
            stmt = stmt.distinct(*distinct) if isinstance(distinct, tuple) else stmt.distinct()
        if joins:
            for join in joins:
                stmt = stmt.join(**join)
        options = []

        if subquery_load:
            options += [so.subqueryload(el) for el in subquery_load]
        if joined_load:
            options += [so.joinedload(el) for el in joined_load]
        if selectin_load:
            options += [so.selectinload(el) for el in selectin_load]
        if options:
            stmt = stmt.options(*options)
        stmt = stmt.filter(*condition)
        if order_fields is not None:
            if order_desc:
                stmt.order_by(*((desc(order_fields[0]),) + order_fields[1:]))
            else:
                stmt = stmt.order_by(*order_fields)
        if group_by:
            stmt = stmt.group_by(*group_by)
        if limit:
            stmt = stmt.limit(limit)
        if page:
            stmt = stmt.offset((page - 1) * (limit or 10))
        res = await cls._execute(session, stmt)
        return res.scalars().all() if many or limit else res.scalar()

    # fmt: off
    @classmethod
    async def _retrieve_union_session(
        cls,
        session: sa_asyncio.AsyncSession,
        models: tuple[DeclarativeMeta, ...],
        columns: tuple[str, ...],
        conditions: tuple[tuple[BinaryExpression | bool | None, ...], ...],
        joins: tuple[tuple[
            dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...], ...] | None = None,
        subquery_load: tuple[Column | str, ...] | None = None,
        order_field: str | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        page: int | None = None,
        literal_replacement: dict[str, str] | None = None,
    ) -> list[dict, ...]:
        """
        Asynchronous method to retrieve a UNION of query results from different models. The method allows sorting, limiting and paginating the results.

        Parameters:

            :param session: Async database session.
            :param models: Tuple of SQLAlchemy models which define the tables for the UNION query.
            :param columns: Tuple of string representing column names that should be included in the result set.
            :param conditions: Tuple of conditions (BinaryExpressions) to filter the data for each model.
            :param subquery_load: Optional Tuple of columns or strings for eager loading of relationships.
            :param order_field: Optional string that defines the column by which the result set should be ordered.
            :param order_desc: Optional boolean that determines if the order should be descending (default is ascending).
            :param limit: Optional integer that limits the number of results returned.
            :param page: Optional integer for pagination. Specifies the page number when the result set is divided into 'limit' number of rows.
            :param literal_replacement: Optional dictionary of replacements for literals in the query.

        Returns:

            :return: A list of dictionaries where each dictionary represents a row in the result set.
                Each dictionary contains the column names as keys and the corresponding data as values.
        """
        union_statements = [
            future.select(
                *(getattr(model, column) for column in columns),
                literal(
                    model.__name__ if not literal_replacement else literal_replacement.get(
                        model.__name__, model.__name__
                    )
                ).label('type')
            ).where(*condition) for model, condition in zip(models, conditions, strict=True)
        ]
        if joins:
            for stmt, for_model_joins in zip(union_statements, joins, strict=True):
                if for_model_joins:
                    for join in for_model_joins:
                        stmt = stmt.join(*join)
        union_statement = union(*union_statements)
        stmt = future.select(
            *(sa_column(column) for column in columns), sa_column("type")
        ).select_from(union_statement.alias())
        # fmt: on
        if subquery_load:
            stmt = stmt.options(*[so.subqueryload(el) for el in subquery_load])
        if order_field:
            stmt = (
                stmt.order_by(text(f"{order_field}"))
                if not order_desc
                else stmt.order_by(desc(text(f"{order_field}")))
            )
        if limit:
            stmt = stmt.limit(limit)
        if page:
            stmt = stmt.offset((page - 1) * (limit or 10))
        res = await cls._execute(session, stmt)
        results = res.fetchall()
        return [dict(zip(list(columns) + ["type"], row, strict=True)) for row in results]

    @classmethod
    async def _retrieve_count(
        cls,
        session_cls: sa_asyncio.AsyncSession,
        model: DeclarativeMeta | None = None,
        field: Column | None = None,
        condition: tuple[BinaryExpression | bool, ...] = (),
        joins: tuple[dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...] | None = None,
        subquery_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        distinct: bool | None = None,
    ):
        async with session_cls() as session:
            if field:
                stmt = future.select(func.count(field).label("count"))
            else:
                stmt = future.select(func.count(model.id if model else cls.model.id).label("count"))
            if distinct:
                stmt = stmt.distinct()
            if joins:
                for join in joins:
                    stmt = stmt.join(**join)
            if subquery_load:
                stmt = stmt.options(*[so.subqueryload(el) for el in subquery_load])
            stmt = stmt.filter(*condition)
            res = await cls._execute(session, stmt)
            return int(res.fetchone()[0])

    @classmethod
    async def _retrieve_union_count(  # TODO: needs testing
        cls,
        session_cls: sa_asyncio.AsyncSession,
        models: tuple[DeclarativeMeta, ...],
        conditions: tuple[tuple[BinaryExpression | bool | None, ...], ...],
        literal_replacement: dict[str, str] | None = None,
    ):
        async with session_cls() as session:
            # fmt: off
            union_statement = union(
                *(
                    future.select(
                        func.count(model.id).filter(*condition).label("count"),
                        literal(
                            model.__name__ if not literal_replacement else literal_replacement.get(
                                model.__name__, model.__name__
                            )
                        ).label('type')
                    ).where(*condition) for model, condition in zip(models, conditions, strict=True)
                )
            )
            stmt = future.select(sa_column("count"), sa_column("type")).select_from(union_statement.alias())
            # fmt: on
            res = await cls._execute(session, stmt)
            results = res.fetchall()
            return [dict(zip(["count", "type"], [int(row[0]), row[1]], strict=True)) for row in results]


class DBApiBase(BaseDbApiHandler):
    model: Base = None
    pk_filed = ""

    @classmethod
    async def retrieve_session(
        cls,
        session: sa_asyncio.AsyncSession,
        model: DeclarativeMeta | None = None,
        condition: tuple[BinaryExpression | bool, ...] = (),
        joins: tuple[dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...] | None = None,
        subquery_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        joined_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        selectin_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        many: bool = False,
        order_fields: tuple[Column | str | Case, ...] | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        page: int | None = None,
        distinct: tuple[Column | str | Case, ...] | bool | None = None,
    ) -> DeclarativeMeta | list[DeclarativeMeta]:
        return await cls._retrieve_session(
            session=session,
            model=model,
            condition=condition,
            joins=joins,
            subquery_load=subquery_load,
            joined_load=joined_load,
            selectin_load=selectin_load,
            many=many,
            order_fields=order_fields,
            order_desc=order_desc,
            limit=limit,
            page=page,
            distinct=distinct,
        )

    @classmethod
    async def retrieve(
        cls,
        session_cls: sa_asyncio.AsyncSession,
        model: DeclarativeMeta | None = None,
        condition: tuple[BinaryExpression | bool, ...] = (),
        joins: tuple[dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...] | None = None,
        subquery_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        joined_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        selectin_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        many: bool = False,
        order_fields: tuple[Column | str | Case, ...] | None = None,
        order_desc: bool = False,
        limit: int | None = None,
        page: int | None = None,
        distinct: tuple[Column | str | Case, ...] | bool | None = None,
        group_by: tuple[Column | str | Case] | None = None,
    ) -> model | DeclarativeMeta | list[DeclarativeMeta]:
        async with session_cls() as session:
            return await cls._retrieve_session(
                session=session,
                model=model,
                condition=condition,
                joins=joins,
                subquery_load=subquery_load,
                joined_load=joined_load,
                selectin_load=selectin_load,
                many=many,
                order_fields=order_fields,
                order_desc=order_desc,
                limit=limit,
                page=page,
                distinct=distinct,
                group_by=group_by,
            )

    @classmethod
    async def exists(cls, session_cls: sa_asyncio.AsyncSession, condition: list, many: bool = False) -> list[bool] | bool:
        async with session_cls() as session:
            return await cls.exists_session(session=session, condition=condition, many=many)

    @classmethod
    async def exists_session(cls, session, condition: list, many: bool = False) -> list[bool] | bool:
        stmt = future.select(exists(cls.model.id)).where(*condition)
        res = await cls._execute(session, stmt)
        return res.scalars().all() if many else res.scalar()

    @classmethod
    async def create(
        cls,
        session_cls: sa_asyncio.AsyncSession,
        data: dict,
        return_: bool = False,
    ) -> model | DeclarativeMeta | None:
        async with session_cls() as session:
            obj = await cls.create_session(session, data, return_)
            await cls._commit(session)
            return obj

    @classmethod
    async def create_session(
        cls,
        session,
        data: dict,
        return_: bool = False,
    ) -> model | DeclarativeMeta | None:
        res = None
        obj = cls.model(**data)
        session.add(obj)
        if return_:
            try:
                await session.flush()
            except Exception as exc:
                await cls.handle_exception(exc)
            res = copy.deepcopy(obj)
        return res

    @classmethod
    async def insert_on_conflict_update_session(
        cls,
        session,
        data: dict,
        on_conflict_update_data: dict,
        constraint: str | None = None,
    ):
        if not constraint:
            constraint = f"{cls.model.__tablename__}_pkey"
        stmt = pg_dialect.insert(cls.model).values(**data)
        do_update_stmt = stmt.on_conflict_do_update(constraint=constraint, set_=on_conflict_update_data)
        await cls.execute(session, do_update_stmt)

    @classmethod
    async def add_session(
        cls,
        session,
        data: dict,
        return_: bool = False,
    ) -> model | DeclarativeMeta | None:
        res = None
        obj = cls.model(**data)
        session.add(obj)
        if return_:
            try:
                await session.flush()
            except Exception as exc:
                await cls.handle_exception(exc)
            res = copy.deepcopy(obj)
        return res

    @classmethod
    async def bulk_create_session(cls, session, data: t.Iterable | t.Generator, return_: bool = False):
        res = None
        objects = [cls.model(**el) for el in data]
        session.add_all(objects)
        if return_:
            try:
                await session.flush()
            except Exception as exc:
                await cls.handle_exception(exc)
            res = copy.deepcopy(objects)
        return res

    @classmethod
    async def bulk_create(
        cls,
        session_cls: sa_asyncio.AsyncSession,
        data: t.Iterable | t.Generator,
        return_: bool = False,
    ):
        res = None
        async with session_cls() as session:
            objects = [cls.model(**el) for el in data]
            session.add_all(objects)
            if return_:
                try:
                    await session.flush()
                except Exception as exc:
                    await cls.handle_exception(exc)
                res = objects
            await cls._commit(session)
            return res

    @classmethod
    async def update_session(cls, session: t.ClassVar[sa_asyncio.AsyncSession], data: dict, condition: list):
        stmt = update(cls.model).where(*condition).values(data)
        await cls._execute(session, stmt)

    @classmethod
    async def update(cls, session_cls: sa_asyncio.AsyncSession, data: dict, condition: tuple):
        async with session_cls() as session:
            await cls.update_session(session, data, condition)
            await cls._commit(session)

    @classmethod
    async def delete_session(
        cls, session: sa_asyncio.AsyncSession, condition: tuple[BinaryExpression | bool, ...], return_: bool = False
    ) -> list[dict] | None:
        stmt = delete(cls.model).where(*condition)
        if return_:
            stmt = stmt.returning(cls.model)
        res = await cls._execute(session, stmt)
        return [dict(el) for el in list(res.mappings())] if return_ else None

    @classmethod
    async def delete(
        cls, session_cls: sa_asyncio.AsyncSession, condition: tuple[BinaryExpression | bool, ...], return_: bool = False
    ) -> list[dict] | None:
        async with session_cls() as session:
            result = await cls.delete_session(session, condition, return_)
            await session.commit()
            return result

    @classmethod
    async def retrieve_count(
        cls,
        session_cls: sa_asyncio.AsyncSession,
        model: DeclarativeMeta | None = None,
        field: Column | None = None,
        condition: tuple[BinaryExpression | bool, ...] = (),
        joins: tuple[dict[DeclarativeMeta | Subquery, BinaryExpression | bool, bool, bool], ...] | None = None,
        subquery_load: tuple[DeclarativeMeta | list[DeclarativeMeta] | str, ...] | None = None,
        distinct: bool | None = None,
    ):
        return await cls._retrieve_count(session_cls, model, field, condition, joins, subquery_load, distinct)

    @classmethod
    async def retrieve_union_count(  # TODO: needs testing
        cls,
        session_cls: sa_asyncio.AsyncSession,
        models: tuple[DeclarativeMeta, ...],
        conditions: tuple[tuple[BinaryExpression | bool | None, ...], ...],
        literal_replacement: dict[str, str] | None = None,
    ):
        return await cls._retrieve_union_count(session_cls, models, conditions, literal_replacement)
