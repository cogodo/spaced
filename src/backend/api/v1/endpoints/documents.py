from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.models import Document, DocumentListItem, DocumentUploadResponse, SearchResult
from core.monitoring.logger import get_logger
from core.services import DocumentService, DocumentServiceError, SearchService

logger = get_logger("documents_api")
router = APIRouter()


@router.post("/upload", status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: Optional[str] = Query(None, description="Optional topic to link the document to"),
    current_user: dict = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload a document for processing.

    Supports PDF, PPTX, Markdown, TXT, and HTML files.
    Returns immediately with document_id and status="processing".
    """
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    logger.info(
        "Document upload started",
        extra={
            "user_uid": user_uid,
            "filename": file.filename,
            "content_type": file.content_type,
            "topic_id": topic_id,
        },
    )

    try:
        # Read file content
        content = await file.read()

        # Upload and process
        document = await document_service.upload_document(
            user_uid=user_uid,
            filename=file.filename or "unknown",
            content=content,
            content_type=file.content_type or "application/octet-stream",
            topic_id=topic_id,
        )

        return DocumentUploadResponse(
            documentId=document.id,
            status=document.status,
            filename=document.originalFilename,
        )

    except DocumentServiceError as e:
        logger.warning(f"Document upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("/")
async def list_documents(
    topic_id: Optional[str] = Query(None, description="Filter by linked topic"),
    current_user: dict = Depends(get_current_user),
) -> List[DocumentListItem]:
    """
    List all documents for the current user.

    Optionally filter by linked topic.
    """
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    try:
        if topic_id:
            return await document_service.list_topic_documents(user_uid, topic_id)
        return await document_service.list_documents(user_uid)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
) -> Document:
    """Get a specific document by ID"""
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    try:
        document = await document_service.get_document(document_id, user_uid)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete a document and all its files"""
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    try:
        deleted = await document_service.delete_document(document_id, user_uid)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/{document_id}/link/{topic_id}", status_code=200)
async def link_document_to_topic(
    document_id: str,
    topic_id: str,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Link a document to a topic"""
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    try:
        success = await document_service.link_to_topic(document_id, user_uid, topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "linked", "documentId": document_id, "topicId": topic_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to link document: {str(e)}")


@router.delete("/{document_id}/link/{topic_id}", status_code=200)
async def unlink_document_from_topic(
    document_id: str,
    topic_id: str,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Unlink a document from a topic"""
    user_uid = current_user.get("uid")
    document_service = DocumentService()

    try:
        success = await document_service.unlink_from_topic(document_id, user_uid, topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "unlinked", "documentId": document_id, "topicId": topic_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unlink document: {str(e)}")


class SearchRequest(BaseModel):
    query: str
    topic_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    limit: int = 10


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
) -> List[SearchResult]:
    """
    Search through user's documents.

    Uses agentic search (MorphLLM WarpGrep) if configured,
    otherwise falls back to simple keyword search.
    """
    user_uid = current_user.get("uid")
    search_service = SearchService()

    logger.info(
        "Document search",
        extra={
            "user_uid": user_uid,
            "query": request.query[:100],  # Truncate for logging
            "topic_id": request.topic_id,
        },
    )

    try:
        results = await search_service.search_documents(
            query=request.query,
            user_id=user_uid,
            topic_id=request.topic_id,
            document_ids=request.document_ids,
            limit=request.limit,
        )
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
