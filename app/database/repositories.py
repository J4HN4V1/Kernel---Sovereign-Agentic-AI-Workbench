from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    CapabilityExecutionModel,
    DocumentModel,
    PaymentModel,
    TaskModel,
)


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        task_id: str,
        user_id: str,
        prompt: str,
        status: str = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> TaskModel:
        task = TaskModel(
            id=task_id,
            user_id=user_id,
            prompt=prompt,
            status=status,
            metadata_json=metadata,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def get(
        self,
        task_id: str,
    ) -> TaskModel | None:
        return self.db.get(
            TaskModel,
            task_id,
        )

    def update(
        self,
        task_id: str,
        **fields: Any,
    ) -> TaskModel | None:
        task = self.get(task_id)

        if task is None:
            return None

        allowed = {
            "status",
            "result",
            "error",
            "workflow",
            "metadata_json",
        }

        for key, value in fields.items():
            if key in allowed:
                setattr(task, key, value)

        self.db.commit()
        self.db.refresh(task)

        return task

    def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[TaskModel]:
        statement = (
            select(TaskModel)
            .where(TaskModel.user_id == user_id)
            .order_by(TaskModel.created_at.desc())
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: str,
        user_id: str,
        filename: str,
        content_type: str | None = None,
        file_path: str | None = None,
        size_bytes: int = 0,
        checksum: str | None = None,
        sensitivity: str = "internal",
        metadata: dict[str, Any] | None = None,
    ) -> DocumentModel:
        document = DocumentModel(
            id=document_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            size_bytes=size_bytes,
            checksum=checksum,
            sensitivity=sensitivity,
            metadata_json=metadata,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get(
        self,
        document_id: str,
    ) -> DocumentModel | None:
        return self.db.get(
            DocumentModel,
            document_id,
        )

    def list_by_user(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[DocumentModel]:
        statement = (
            select(DocumentModel)
            .where(DocumentModel.user_id == user_id)
            .order_by(DocumentModel.created_at.desc())
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )


class CapabilityExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        execution_id: str,
        task_id: str,
        capability_id: str,
        success: bool,
        execution_time_ms: float = 0.0,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        payment_id: str | None = None,
        transaction_id: str | None = None,
    ) -> CapabilityExecutionModel:
        execution = CapabilityExecutionModel(
            id=execution_id,
            task_id=task_id,
            capability_id=capability_id,
            success=success,
            execution_time_ms=execution_time_ms,
            result=result,
            error=error,
            payment_id=payment_id,
            transaction_id=transaction_id,
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return execution

    def list_by_task(
        self,
        task_id: str,
    ) -> list[CapabilityExecutionModel]:
        statement = (
            select(CapabilityExecutionModel)
            .where(
                CapabilityExecutionModel.task_id == task_id
            )
            .order_by(
                CapabilityExecutionModel.created_at.asc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        payment_id: str,
        capability_id: str,
        amount: float,
        currency: str = "ALGO",
        network: str = "algorand-testnet",
        task_id: str | None = None,
        status: str = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> PaymentModel:
        payment = PaymentModel(
            id=payment_id,
            task_id=task_id,
            capability_id=capability_id,
            amount=amount,
            currency=currency,
            network=network,
            status=status,
            metadata_json=metadata,
        )

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        return payment

    def get(
        self,
        payment_id: str,
    ) -> PaymentModel | None:
        return self.db.get(
            PaymentModel,
            payment_id,
        )

    def update(
        self,
        payment_id: str,
        **fields: Any,
    ) -> PaymentModel | None:
        payment = self.get(payment_id)

        if payment is None:
            return None

        allowed = {
            "status",
            "transaction_id",
            "payment_proof",
            "metadata_json",
        }

        for key, value in fields.items():
            if key in allowed:
                setattr(payment, key, value)

        self.db.commit()
        self.db.refresh(payment)

        return payment


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        event_id: str,
        event_type: str,
        user_id: str | None = None,
        task_id: str | None = None,
        severity: str = "info",
        details: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            id=event_id,
            event_type=event_type,
            user_id=user_id,
            task_id=task_id,
            severity=severity,
            details=details,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event


class RepositoryFactory:
    """
    Provides all database repositories from one SQLAlchemy session.
    """

    def __init__(self, db: Session):
        self.tasks = TaskRepository(db)
        self.documents = DocumentRepository(db)
        self.executions = CapabilityExecutionRepository(db)
        self.payments = PaymentRepository(db)
        self.audit = AuditRepository(db)