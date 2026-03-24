import shutil
import logging
from pathlib import Path
from uuid import UUID

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from celery.utils.log import get_task_logging
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from src.config.dependencies import PROCESSED_STORAGE_DIR, FAILED_STORAGE_DIR, RAW_STORAGE_DIR
from src.config.settings import get_settings
from src.database.models import DocumentModel
from src.enums import DocumentStatusEnum
from src.exceptions import UnSupportedFormatError

settings = get_settings()

LOADERS = {
    "txt": lambda path: TextLoader(path, encoding="utf-8"),
    "pdf": lambda path: PyPDFLoader(path),
    "md": lambda path: UnstructuredMarkdownLoader(path)
}


async def prepare_document(
        document_id: str,
        file_location: str,
        file_format: str,
        user_id: int,
        db: AsyncSession
) -> None:
    """Service for preparing and sending document data to Qdrant."""
    logging.info(f"Starting to process document {document_id} at {file_location}")

    try:
        loader_factory = LOADERS.get(file_format)

        if loader_factory is None:
            logging.error(f"Document process stopped - unsupported format: {file_format}")
            raise UnSupportedFormatError("File format unsupported!")

        loader = loader_factory(file_location)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True
        )

        chunks = text_splitter.split_documents(documents)
        chunks_count = len(chunks)
        logging.info(f"Document split into {chunks_count} chunks.")

        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["document_id"] = str(document_id)
            chunk.metadata["user_id"] = user_id

        embeddings_model = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings_model,
            url=settings.QDRANT_URL,
            collection_name="knowledge_base",
        )
        logging.info(f"{chunks_count} chunks saved in Qdrant.")

        logging.info("Updating document status to PROCESSED...")
        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == UUID(document_id))
            .values(
                status=DocumentStatusEnum.PROCESSED,
                chunk_count=chunks_count
            )
        )
        await db.execute(stmt)
        await db.commit()

        logging.info(f"Document {document_id} successfully prepared!")

        logging.info("Moving file to processed directory...")

        raw_path = Path(file_location)
        processed_path = PROCESSED_STORAGE_DIR / raw_path.name
        shutil.move(str(raw_path), str(processed_path))

        logging.info(f"File successfully moved to {processed_path}")

    except Exception as e:
        logging.error(f"Error processing document {document_id}: {str(e)}")
        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == UUID(document_id))
            .values(status=DocumentStatusEnum.FAILED)
        )
        await db.execute(stmt)
        await db.commit()

        raw_path = Path(file_location)
        failed_path = FAILED_STORAGE_DIR / raw_path.name
        shutil.move(raw_path, str(failed_path))
        logging.info(f"File successfully moved to {failed_path}")


async def delete_document_embedding(
        file_id: UUID
) -> None:
    """Service for deleting vectors from Qdrant"""
    logging.info(f"Starting to deleting document '{file_id}' vectors from Qdrant")
    try:
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        qdrant_client.delete(
            collection_name="knowledge_base",
            points_selector=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.document_id",
                        match=qdrant_models.MatchValue(value=str(file_id)),
                    )
                ]
            ),
        )
    except Exception as e:
        logging.error(f"Failed to delete vectors from Qdrant for document {file_id}: {e}")


async def delete_document_file(
        file_name: str
) -> None:
    """Service for deleting files."""
    logging.info(f"Starting to deleting document '{file_name}'")
    for directory in [PROCESSED_STORAGE_DIR, RAW_STORAGE_DIR, FAILED_STORAGE_DIR]:
        file_path = directory / file_name
        if file_path.exists():
            file_path.unlink()