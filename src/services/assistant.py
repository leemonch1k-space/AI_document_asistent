from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate

from src.config.settings import get_settings
from src.schemas import AskResponseSchema, SourceSchema

settings = get_settings()


async def generate_answer(
        question: str,
        valid_document_ids: list[str],
        user_id: int,
        is_admin: bool
) -> AskResponseSchema:
    """Service to search documents and generate AI answer using Mistral API."""

    embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name="knowledge_base",
        embedding=embeddings_model,
    )

    must_conditions = []

    if not is_admin:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="metadata.user_id",
                match=qdrant_models.MatchValue(value=user_id),
            )
        )

    if valid_document_ids:
        must_conditions.append(
            qdrant_models.FieldCondition(
                key="metadata.document_id",
                match=qdrant_models.MatchAny(any=valid_document_ids),
            )
        )

    filter_query = qdrant_models.Filter(must=must_conditions) if must_conditions else None

    found_docs = vector_store.similarity_search(
        query=question,
        k=4,
        filter=filter_query
    )

    if not found_docs:
        return AskResponseSchema(
            answer="Selected documents do not contain the requested information.",
            sources=[]
        )

    context_text = "\n\n---\n\n".join([doc.page_content for doc in found_docs])
    unique_sources = {doc.metadata.get("document_id", "Unknown") for doc in found_docs}
    sources = [SourceSchema(document=doc_id) for doc_id in unique_sources]

    prompt_template = PromptTemplate.from_template(
        "You are a helpful AI assistant. Answer the question using ONLY the provided context.\n"
        "If the answer is not in the context, say so; do not make anything up.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
    )

    prompt = prompt_template.format(context=context_text, question=question)

    llm = ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=settings.MISTRAL_API_KEY,
        temperature=0
    )

    ai_msg = llm.invoke(prompt)

    return AskResponseSchema(answer=ai_msg.content, sources=sources)