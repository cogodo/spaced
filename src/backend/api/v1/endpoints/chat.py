from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.v1.dependencies import get_current_user
from core.monitoring.logger import get_logger
from core.services.conversation_service import ConversationService
from core.services.question_service import QuestionGenerationError, QuestionService
from core.services.session_service import SessionService, SessionServiceError
from core.services.topic_service import TopicService, TopicServiceError

logger = get_logger("chat_api")
router = APIRouter()


class StartChatRequest(BaseModel):
    topics: List[str]
    chat_id: Optional[str] = None  # Allow frontend to specify chat ID


class StartChatResponse(BaseModel):
    chat_id: str
    message: str
    next_question: str
    topics: List[str]
    topic_id: str


# Keep the old endpoint for backward compatibility
class TurnRequest(BaseModel):
    user_input: str


class TurnResponse(BaseModel):
    bot_response: str


@router.post("/chat/start", response_model=StartChatResponse)
async def start_chat(request: StartChatRequest, current_user: dict = Depends(get_current_user)) -> StartChatResponse:
    """Start a chat-based learning session."""
    user_uid = current_user["uid"]
    logger.info(f"Starting chat for user {user_uid} with topics: {request.topics}")

    try:
        topic_service = TopicService()
        session_service = SessionService()
        question_service = QuestionService()

        # 1. Find or create topics
        topics = await topic_service.find_or_create_topics(request.topics, user_uid)
        if not topics:
            raise HTTPException(400, "No valid topics provided")
        primary_topic = topics[0]

        # 2. Ensure topic has questions, generating them if necessary
        questions = await question_service.get_topic_questions(primary_topic.id, user_uid)
        if not questions:
            logger.info(f"Generating initial questions for topic {primary_topic.name}...")
            questions = await question_service.generate_initial_questions(primary_topic, user_uid)
            if not questions:
                raise HTTPException(500, f"Question generation returned no questions for topic: {primary_topic.name}")

            logger.info(f"Updating question bank for topic {primary_topic.id} with {len(questions)} questions.")
            await topic_service.update_question_bank(primary_topic.id, user_uid, [q.id for q in questions])
            logger.info(f"Successfully updated question bank for topic {primary_topic.id}.")

        # 3. Start the session (unified learning session)
        logger.info(f"Starting session for user {user_uid} and topic {primary_topic.id}.")
        session = await session_service.start_session(
            user_uid=user_uid,
            topic_id=primary_topic.id,
            session_id=request.chat_id,
            topics=[t.name for t in topics],
            name=f"Session - {topics[0] if topics else 'Learning'}",
        )
        logger.info(f"Successfully started session {session.id}.")

        # 4. Get the first question
        logger.info(f"Getting current question for session {session.id}.")
        _, question = await session_service.get_current_question(session.id, user_uid)
        if not question:
            raise HTTPException(500, "Failed to get first question for the session")
        logger.info(f"Successfully retrieved first question {question.id} for session {session.id}.")

        # 5. Return the successful response
        response = StartChatResponse(
            chat_id=session.id,
            message=f"Let's learn about {primary_topic.name}!\n\n**Question 1:**\n{question.text}",
            next_question=question.text,
            topics=[t.name for t in topics],
            topic_id=primary_topic.id,
        )

        logger.info(f"Successfully started chat {session.id} for user {user_uid}")
        return response

    except (QuestionGenerationError, TopicServiceError, SessionServiceError) as e:
        # Log the service-specific error. The exc_info argument is removed to prevent the KeyError.
        # FastAPI's default error handling will still capture and log the full traceback.
        logger.error(f"A specific service error occurred during chat start for user {user_uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        # Re-raise HTTPException directly to avoid being caught by the generic Exception
        raise
    except Exception:
        # Catch any other unexpected errors and log them.
        logger.error(f"An unexpected error occurred during chat start for user {user_uid}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")


# Keep backward compatibility with old endpoint
@router.post("/chat/{chat_id}/messages", response_model=TurnResponse)
async def handle_turn(
    chat_id: str, request: TurnRequest, current_user: dict = Depends(get_current_user)
) -> TurnResponse:
    """Handles a single turn in the conversation."""
    try:
        conversation_service = ConversationService()
        user_uid = current_user["uid"]
        bot_response = await conversation_service.process_turn(chat_id, user_uid, request.user_input)
        return TurnResponse(bot_response=bot_response)
    except Exception as e:
        logger.error(f"Unexpected error handling turn for chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred while handling turn.")


@router.post("/chat/completions")
async def openai_compatible_chat_completions(request: Request, current_user: dict = Depends(get_current_user)):
    """
    OpenAI-compatible endpoint for LiveKit voice agent integration.
    Supports both streaming and non-streaming responses.
    Extracts chat_id from system message and routes to our backend chat API.
    Uses existing chat session context from Firebase.
    """
    logger.info("Starting OpenAI-compatible chat completions request")

    try:
        # Parse OpenAI-style request
        logger.info("Parsing request body...")
        body = await request.json()
        messages = body.get("messages", [])
        stream = body.get("stream", False)
        stream_options = body.get("stream_options", {})

        logger.info(f"Parsed request: messages={len(messages)}, stream={stream}")

        if not messages:
            logger.error("No messages provided in request")
            raise HTTPException(status_code=400, detail="No messages provided")

        # Extract the user's message (last message should be from user)
        user_message = messages[-1].get("content", "")
        logger.info(f"User message: '{user_message[:100]}...'")

        # Extract chat_id from the system message
        chat_id = None
        for msg in messages:
            if msg.get("role") == "system" and "chat_id:" in msg.get("content", ""):
                # Extract chat_id from system message like "chat_id:abc123"
                content = msg.get("content", "")
                for line in content.split("\n"):
                    if line.startswith("chat_id:"):
                        chat_id = line.split(":", 1)[1].strip()
                        break

        logger.info(f"Extracted chat_id: {chat_id}")

        if not chat_id:
            logger.warning("No chat_id found in voice request system message")
            raise HTTPException(status_code=400, detail="No chat_id provided in system message")

        logger.info(f"Voice LLM request: chat={chat_id}, message='{user_message[:100]}...', stream={stream}")

        # Initialize services
        logger.info("Initializing services...")
        try:
            conversation_service = ConversationService()
            session_service = SessionService()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Service initialization error: {str(e)}")

        # Get existing session from Firebase
        logger.info(f"Fetching session for chat_id={chat_id}")
        user_uid = current_user.get("uid", "anonymous")

        session = await session_service.get_session(chat_id, user_uid)

        if not session:
            logger.error(f"Session {chat_id} not found for user {user_uid}")
            # Let's check what sessions do exist for this user
            try:
                all_sessions = await session_service.repository.list_by_user(user_uid)
                session_ids = [s.id for s in all_sessions]
                logger.error(f"Available sessions for user {user_uid}: {session_ids}")
            except Exception as e:
                logger.error(f"Error listing sessions for user {user_uid}: {e}")

            raise HTTPException(
                status_code=404,
                detail=f"Chat session {chat_id} not found. Please start a chat session first before using voice.",
            )

        logger.info(f"Found session: {chat_id}, topic={session.topicId}, state={session.state}")

        # Process the conversation turn
        logger.info(f"Calling process_turn with chat_id={chat_id}, user_uid={user_uid}")
        try:
            response = await conversation_service.process_turn(
                chat_id=chat_id, user_uid=user_uid, user_input=user_message
            )
            logger.info(f"Got response from conversation service: '{response[:100]}...'")
        except Exception as e:
            logger.error(f"Failed to process conversation turn: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Conversation processing error: {str(e)}")

        # Calculate token usage (rough estimation)
        prompt_tokens = len(user_message.split())
        completion_tokens = len(response.split())
        total_tokens = prompt_tokens + completion_tokens

        logger.info(f"Token usage: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")

        if stream:
            logger.info("Generating streaming response...")
            # Return streaming response (Server-Sent Events format)
            import json

            from fastapi.responses import StreamingResponse

            async def generate_stream():
                logger.info("Starting stream generation...")
                try:
                    # First chunk with content
                    chunk = {
                        "id": f"voice-{chat_id}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": "backend-voice",
                        "choices": [
                            {"index": 0, "delta": {"role": "assistant", "content": response}, "finish_reason": None}
                        ],
                    }
                    logger.info("Yielding first chunk...")
                    yield f"data: {json.dumps(chunk)}\n\n"

                    # Final chunk with finish_reason
                    final_chunk = {
                        "id": f"voice-{chat_id}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": "backend-voice",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }

                    # Include usage if requested
                    if stream_options.get("include_usage"):
                        final_chunk["usage"] = {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                        }

                    logger.info("Yielding final chunk...")
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    logger.info("Stream generation completed")
                except Exception as e:
                    logger.error(f"Error in stream generation: {e}", exc_info=True)
                    raise

            return StreamingResponse(generate_stream(), media_type="text/plain", headers={"Cache-Control": "no-cache"})
        else:
            logger.info("Generating non-streaming response...")
            # Return non-streaming response
            return {
                "id": f"voice-{chat_id}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": "backend-voice",
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": response}, "finish_reason": "stop"}
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI-compatible chat completions endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
