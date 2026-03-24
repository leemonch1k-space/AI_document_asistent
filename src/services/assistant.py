from uuid import UUID

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import get_settings
from src.exceptions import DocumentNotFoundError
from src.schemas import AskResponseSchema, SourceSchema, AskSummaryResponseSchema

settings = get_settings()


async def generate_answer(
        question: str,
        valid_document_ids: list[str],
        user_id: int,
        is_admin: bool
) -> AskResponseSchema:
    """Service to search documents and generate AI answer."""
    embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)

    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name="knowledge_base",
        embedding=embeddings_model,
    )

    must_conditions = []

    if valid_document_ids:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="metadata.document_id",
                match=qdrant_models.MatchAny(any=valid_document_ids),
            )
        )

    if not is_admin:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="metadata.user_id",
                match=qdrant_models.MatchValue(value=user_id),
            )
        )

    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": qdrant_models.Filter(must=must_conditions) if must_conditions else None
        }
    )

    llm = ChatMistralAI(api_key=settings.MISTRAL_API_KEY)


    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.\n"
            "If the answer is not in the context, say 'I don't know based on the provided documents'.\n\n"
            "Context:\n{context}"
        )),
        ("human", "{input}")
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = await rag_chain.ainvoke({"input": question})
    source_documents = response.get("context", [])
    sources = []

    for doc in source_documents:
        sources.append(
            SourceSchema(
                document=doc.metadata.get("document_id", "Unknown Document"),
                chunk_id=str(doc.metadata.get("chunk_id", ""))
            )
        )

    return AskResponseSchema(
        answer=response["answer"],
        sources=sources
    )


async def generate_summary(
        document_id: UUID,
        user_id: int,
        is_admin: bool
) -> AskSummaryResponseSchema:
    """Service to search documents and generate AI summary."""
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)

    must_conditions = [
        qdrant_models.FieldCondition(
            key="metadata.document_id",
            match=qdrant_models.MatchValue(value=str(document_id)),
        )
    ]

    if not is_admin:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="metadata.user_id",
                match=qdrant_models.MatchValue(value=user_id),
            )
        )

    all_chunks = []
    offset = None

    while True:
        records, offset = qdrant_client.scroll(
            collection_name="knowledge_base",
            scroll_filter=qdrant_models.Filter(must=must_conditions),
            with_payload=True,
            with_vectors=False,
            limit=100,
            offset=offset
        )

        for record in records:
            content = record.payload.get("page_content", "")
            all_chunks.append(Document(page_content=content))

        if offset is None:
            break

    if not all_chunks:
        raise DocumentNotFoundError("Document not found or access denied")

    llm = ChatMistralAI(api_key=settings.MISTRAL_API_KEY)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert AI summarizer. Your task is to provide a comprehensive summary of the provided document. Use ONLY the provided context."),
        ("human", "Document context:\n\n{context}\n\nWrite a detailed summary:")
    ])

    summary_chain = create_stuff_documents_chain(llm, prompt)
    summary_text = await summary_chain.ainvoke({"context": all_chunks})

    return AskSummaryResponseSchema(
        document_id=document_id,
        summary=summary_text
    )