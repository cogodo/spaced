from typing import Dict, Any, List
from datetime import datetime, timezone
from my_agent.utils.state import GraphState
from my_agent.utils.tools import (
    call_ai_with_json_output, call_ai_for_simple_response,
    initialize_session_topics, get_current_topic, get_remaining_topics,
    advance_to_next_topic, build_topic_context, format_topic_conversation_history,
    get_topic_conversation, format_topic_conversation_for_evaluation
)
from my_agent.utils.adaptive_intelligence import (
    analyze_user_response_live,
    calculate_adaptive_difficulty,
    determine_adaptive_conversation_strategy,
    update_live_performance_metrics,
    update_learned_preferences,
    calculate_learning_momentum
)
from my_agent.utils.adaptive_state_integration import (
    auto_save_adaptive_state,
    log_adaptive_decision
)
from my_agent.utils.firebase_service import firebase_service, QuestionBankService
import logging

# Configure logging
logger = logging.getLogger(__name__)


async def ensure_question_bank_exists(user_id: str, topic_id: str, topic_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a question bank exists for the given topic, creating one if necessary.
    
    Args:
        user_id: The user's ID
        topic_id: Unique identifier for the topic
        topic_data: Dictionary containing topic information including 'name' and optional context
        
    Returns:
        Dict with success status and any error information
    """
    try:
        question_service = QuestionBankService()
        
        # Extract topic information
        topic_name = topic_data.get("name", topic_id)
        topic_context = topic_data.get("context", "")
        
        # Use the QuestionBankService to ensure questions exist
        success = await question_service.ensure_topic_has_questions(
            user_id=user_id,
            topic_id=topic_id, 
            topic_name=topic_name,
            topic_context=topic_context
        )
        
        if success:
            logger.info(f"Question bank ensured for topic: {topic_name} (ID: {topic_id})")
            return {"success": True, "message": f"Question bank ready for {topic_name}"}
        else:
            logger.error(f"Failed to ensure question bank for topic: {topic_name}")
            return {"success": False, "error": f"Failed to create question bank for {topic_name}"}
            
    except Exception as e:
        logger.error(f"Error ensuring question bank for topic {topic_id}: {e}")
        return {"success": False, "error": str(e)}

def conversation_node(state: GraphState) -> Dict[str, Any]:
    """
    AI-driven conversation node with explicit topic management
    """
    # Initialize topics if first call
    if state.get("user_input") is None:
        initialize_session_topics(state)
        opening = generate_topic_aware_opening(state)
        state["message_count"] = 1
        return {"next_question": opening}
    
    # Record user's response
    record_user_response(state)
    
    # Get current topic context
    current_topic = get_current_topic(state)
    if not current_topic:
        # No more topics - should end session
        state["session_complete"] = True
        return {"session_complete": True}
    
    topic_source = state.get("topic_sources", {}).get(current_topic, {})
    
    # Let AI drive conversation with topic awareness
    ai_response = get_topic_aware_response(state, current_topic, topic_source)
    
    # Update conversation history
    state["message_count"] = state.get("message_count", 0) + 1
    conversation_history = state.get("conversation_history", [])
    conversation_history.append({
        "role": "assistant",
        "content": ai_response["content"],
        "topic": current_topic,
        "action": ai_response.get("action", "continue"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["conversation_history"] = conversation_history
    
    return {
        "next_question": ai_response["content"],
        "current_topic": current_topic,
        "message_count": state["message_count"],
        "remaining_topics": get_remaining_topics(state),
        "conversation_action": ai_response.get("action", "continue")
    }

def get_topic_aware_response(state: GraphState, current_topic: str, topic_source: Dict) -> Dict:
    """
    Phase 3: Enhanced AI conversation generation with advanced context integration and personalized learning patterns
    """
    topic_context = build_topic_context(current_topic, topic_source)
    topic_history = format_topic_conversation_history(state, current_topic)
    user_input = state.get('user_input', '')
    
    # Phase 3: Advanced context integration
    conversation_context = build_advanced_conversation_context(state, current_topic, user_input)
    learning_personalization = extract_learning_personalization(state)
    cross_topic_insights = analyze_cross_topic_learning_patterns(state, current_topic)
    
    # Enhanced conversation stage with learning pattern awareness
    conversation_stage = get_enhanced_conversation_stage(state, current_topic, learning_personalization)
    
    # Phase 3: Sophisticated conversation prompt with deep personalization
    conversation_prompt = f"""
You are an expert AI learning companion with deep expertise in conversational pedagogy, cognitive science, and personalized learning. You're having a natural, adaptive conversation that feels like ChatGPT but is specifically designed to optimize learning through sophisticated active recall and personalized teaching strategies.

ADVANCED LEARNING CONTEXT:
{conversation_context}

PERSONALIZED LEARNING PROFILE:
{learning_personalization}

CROSS-TOPIC LEARNING INSIGHTS:
{cross_topic_insights}

CONVERSATION STAGE: {conversation_stage}

YOUR ADVANCED PEDAGOGICAL APPROACH:

🧠 ADAPTIVE LEARNING SCIENCE INTEGRATION:
Based on the student's demonstrated learning patterns, adapt your approach:

**If they prefer VERBAL learning**: Use rich explanations, analogies, and narrative examples
**If they prefer VISUAL learning**: Encourage them to describe mental images, diagrams, or visual representations
**If they prefer EXPERIENTIAL learning**: Focus on real-world applications, hands-on scenarios, and practical examples
**If SYSTEMATIC learners**: Provide structured, step-by-step exploration
**If INTUITIVE learners**: Allow for discovery, exploration, and pattern recognition

🎯 SOPHISTICATED ACTIVE RECALL TECHNIQUES:
Dynamically select from advanced techniques based on learning patterns:

1. **Elaborative Recall**: "Can you walk me through how you understand this concept and why it works that way?"
2. **Analogical Thinking**: "What does this remind you of from your own experience?"
3. **Contrastive Analysis**: "How is this different from [related concept they know]?"
4. **Application Transfer**: "If you had to use this in a real situation, how would you approach it?"
5. **Metacognitive Reflection**: "What aspects of this feel clearest to you? What parts are still forming in your mind?"
6. **Causal Reasoning**: "What do you think would happen if we changed [key variable]?"
7. **Synthesis Creation**: "How would you explain this to someone who's never encountered it before?"
8. **Pattern Recognition**: "What patterns do you notice here that connect to what we've discussed before?"

📊 REAL-TIME LEARNING ADAPTATION:
Continuously assess and adapt based on:
- **Confidence signals** in their language
- **Depth of explanations** they provide
- **Connection-making ability** they demonstrate
- **Question quality** they ask
- **Learning velocity** observed in this session
- **Engagement patterns** from previous topics

🎭 NATURAL CONVERSATION PERSONALITY:
Maintain an engaging, curious personality while being pedagogically sophisticated:
- **Genuinely curious**: "I'm really interested in how you're thinking about this..."
- **Encouraging**: "That's exactly the kind of thinking that shows real understanding!"
- **Intellectually humble**: "That's a perspective I hadn't considered..."
- **Adaptively challenging**: Adjust difficulty based on their demonstrated capabilities
- **Contextually aware**: Reference their previous insights and learning patterns

🔄 CROSS-TOPIC INTEGRATION:
Naturally weave in connections to previous learning:
- Reference insights from earlier topics when relevant
- Build on learning patterns that worked well before
- Address areas that needed reinforcement in other topics
- Help them see the bigger picture of their learning journey

ADVANCED CONVERSATION FLOW GUIDELINES:

1. **Listen Actively**: Respond specifically to what they just said, showing you understand their thinking
2. **Adapt Dynamically**: Use their demonstrated learning preferences to guide your approach
3. **Challenge Appropriately**: Based on their confidence and understanding level
4. **Build Progressively**: Each exchange should deepen understanding or reveal new insights
5. **Connect Meaningfully**: Help them see relationships between concepts and their own knowledge
6. **Reflect Learning**: Occasionally highlight their growth and effective learning strategies

TOPIC COMPLETION INTELLIGENCE:
Make sophisticated decisions about topic readiness based on:
- **Conceptual fluency**: Can they explain clearly and accurately?
- **Application confidence**: Do they show ability to use the knowledge?
- **Connection integration**: Can they relate it to other learning?
- **Metacognitive awareness**: Do they understand what they know and don't know?
- **Transfer readiness**: Signs they could apply this in new contexts?

RESPONSE OPTIMIZATION:
Your response should feel like a natural conversation while being pedagogically sophisticated:
- **ONE focused element** per response (question, insight, challenge)
- **Adaptive tone** matching their engagement and confidence level
- **Strategic depth** appropriate for their demonstrated learning stage
- **Natural transitions** that maintain conversation flow
- **Personalized approach** based on their learning profile

RESPONSE FORMAT:
Return JSON with sophisticated analysis:

{{
    "action": "continue" | "topic_complete",
    "content": "Your natural, personalized, pedagogically sophisticated response",
    "reasoning": "Why you chose this approach based on learning patterns and context",
    "learning_technique": "The specific active recall or learning technique being used",
    "personalization_applied": "How you adapted to their learning preferences",
    "difficulty_level": "easy|moderate|challenging",
    "pedagogical_strategy": "The underlying teaching strategy being employed",
    "cross_topic_connection": "Any connections made to previous learning (if applicable)",
    "learning_momentum_assessment": "increasing|steady|needs_support"
}}

CRITICAL SUCCESS FACTORS:
- This should feel like the most engaging, personalized tutor they've ever had
- Every response should be precisely calibrated to optimize their learning
- Use the full power of AI to be more adaptive than any human tutor could be
- Make learning feel effortless and enjoyable while being highly effective
- Be genuinely curious about their thinking and understanding

Remember: You're not just having a conversation - you're orchestrating a sophisticated, personalized learning experience! 🎯
"""

    response = call_ai_with_json_output(conversation_prompt)
    
    # Phase 3: Enhanced response validation and enrichment
    if not response.get("content"):
        response["content"] = generate_fallback_response(state, current_topic, learning_personalization)
    
    # Ensure all Phase 3 fields are present
    response.setdefault("action", "continue")
    response.setdefault("reasoning", "Continuing natural conversation flow")
    response.setdefault("learning_technique", "adaptive_dialogue")
    response.setdefault("personalization_applied", "general_conversational_approach")
    response.setdefault("difficulty_level", "moderate")
    response.setdefault("pedagogical_strategy", "socratic_method")
    response.setdefault("learning_momentum_assessment", "steady")
    
    # Phase 3: Track response analytics
    track_response_analytics(state, current_topic, response, learning_personalization)
        
    return response

def build_advanced_conversation_context(state: GraphState, current_topic: str, user_input: str) -> str:
    """
    Phase 3: Build comprehensive conversation context with cross-topic awareness
    """
    context_parts = []
    
    # Current topic context
    topic_source = state.get("topic_sources", {}).get(current_topic, {})
    context_parts.append(f"CURRENT TOPIC: {current_topic}")
    context_parts.append(f"Topic Source: {build_topic_context(current_topic, topic_source)}")
    
    # Recent conversation for this topic
    topic_history = format_topic_conversation_history(state, current_topic)
    if topic_history and topic_history != "No conversation about this topic yet.":
        context_parts.append(f"\nTOPIC CONVERSATION HISTORY:\n{topic_history}")
    
    # Latest student input
    context_parts.append(f"\nSTUDENT'S LATEST MESSAGE: \"{user_input}\"")
    
    # Session progress context
    completed_topics = state.get("completed_topics", [])
    remaining_topics = get_remaining_topics(state)
    message_count = state.get("message_count", 0)
    
    context_parts.append(f"\nSESSION PROGRESS:")
    context_parts.append(f"- Message count: {message_count}/40")
    context_parts.append(f"- Completed topics: {completed_topics}")
    context_parts.append(f"- Remaining topics: {remaining_topics}")
    
    return "\n".join(context_parts)

def extract_learning_personalization(state: GraphState) -> str:
    """
    Phase 3: Extract personalized learning insights from previous evaluations
    """
    topic_evaluations = state.get("topic_evaluations", {})
    learning_analytics = state.get("learning_analytics", {})
    
    if not topic_evaluations:
        return "LEARNING PROFILE: First topic - no personalization data available yet. Use adaptive exploration to discover learning preferences."
    
    # Extract patterns from previous evaluations
    learning_styles = []
    questioning_preferences = []
    difficulty_preferences = []
    engagement_patterns = []
    
    for topic, evaluation in topic_evaluations.items():
        if "learning_patterns" in evaluation:
            patterns = evaluation["learning_patterns"]
            learning_styles.append(patterns.get("preferred_learning_style", "unknown"))
            questioning_preferences.append(patterns.get("optimal_questioning_style", "unknown"))
            difficulty_preferences.append(patterns.get("cognitive_load_preference", "unknown"))
        
        if "conversation_analysis" in evaluation:
            engagement = evaluation["conversation_analysis"].get("engagement_level", "unknown")
            engagement_patterns.append(engagement)
    
    # Build personalization summary
    personalization_parts = ["PERSONALIZED LEARNING PROFILE:"]
    
    if learning_styles:
        most_common_style = max(set(learning_styles), key=learning_styles.count)
        personalization_parts.append(f"- Preferred Learning Style: {most_common_style}")
    
    if questioning_preferences:
        most_common_questioning = max(set(questioning_preferences), key=questioning_preferences.count)
        personalization_parts.append(f"- Optimal Questioning Style: {most_common_questioning}")
    
    if difficulty_preferences:
        most_common_difficulty = max(set(difficulty_preferences), key=difficulty_preferences.count)
        personalization_parts.append(f"- Cognitive Load Preference: {most_common_difficulty}")
    
    if engagement_patterns:
        recent_engagement = engagement_patterns[-1] if engagement_patterns else "unknown"
        personalization_parts.append(f"- Recent Engagement Level: {recent_engagement}")
    
    # Add learning velocity if available
    if learning_analytics.get("learning_velocity"):
        recent_scores = [item["score"] for item in learning_analytics["learning_velocity"][-3:]]
        if len(recent_scores) > 1:
            trend = "improving" if recent_scores[-1] > recent_scores[0] else "stable" if recent_scores[-1] == recent_scores[0] else "needs_support"
            personalization_parts.append(f"- Learning Trend: {trend}")
    
    return "\n".join(personalization_parts)

def analyze_cross_topic_learning_patterns(state: GraphState, current_topic: str) -> str:
    """
    Phase 3: Analyze learning patterns across topics for context integration
    """
    completed_topics = state.get("completed_topics", [])
    topic_evaluations = state.get("topic_evaluations", {})
    
    if not completed_topics or not topic_evaluations:
        return "CROSS-TOPIC INSIGHTS: No previous topics to analyze patterns from."
    
    insights_parts = ["CROSS-TOPIC LEARNING INSIGHTS:"]
    
    # Performance consistency analysis
    scores = [topic_evaluations[topic].get("understanding_level", 3) for topic in completed_topics if topic in topic_evaluations]
    if scores:
        avg_score = sum(scores) / len(scores)
        consistency = "consistent" if max(scores) - min(scores) <= 1 else "variable"
        insights_parts.append(f"- Performance Pattern: {avg_score:.1f}/5 average, {consistency} across topics")
    
    # Learning style consistency
    learning_styles = []
    strong_areas = []
    growth_areas = []
    
    for topic in completed_topics[-3:]:  # Last 3 topics
        if topic in topic_evaluations:
            eval_data = topic_evaluations[topic]
            
            # Extract learning patterns
            if "learning_patterns" in eval_data:
                style = eval_data["learning_patterns"].get("preferred_learning_style")
                if style:
                    learning_styles.append(style)
            
            # Extract strengths and growth areas
            if "learning_insights" in eval_data:
                insights = eval_data["learning_insights"]
                strengths = insights.get("key_strengths", [])
                growth = insights.get("areas_for_growth", [])
                strong_areas.extend(strengths)
                growth_areas.extend(growth)
    
    # Learning style consistency
    if learning_styles:
        most_consistent_style = max(set(learning_styles), key=learning_styles.count)
        style_consistency = learning_styles.count(most_consistent_style) / len(learning_styles)
        if style_consistency > 0.6:
            insights_parts.append(f"- Consistent Learning Style: {most_consistent_style} ({style_consistency:.0%} of topics)")
    
    # Recurring patterns
    if strong_areas:
        insights_parts.append(f"- Consistent Strengths: {', '.join(strong_areas[:3])}")
    
    if growth_areas:
        insights_parts.append(f"- Areas for Continued Growth: {', '.join(growth_areas[:3])}")
    
    # Topic connections
    insights_parts.append(f"- Ready to connect {current_topic} to: {', '.join(completed_topics[-2:])}")
    
    return "\n".join(insights_parts)

def get_enhanced_conversation_stage(state: GraphState, current_topic: str, learning_personalization: str) -> str:
    """
    Phase 3: Enhanced conversation stage detection with learning pattern awareness
    """
    conversation_history = state.get("conversation_history", [])
    topic_messages = [msg for msg in conversation_history if msg.get("topic") == current_topic]
    message_count = len(topic_messages)
    
    # Base stage detection
    if message_count == 0:
        base_stage = "initial_contact"
    elif message_count <= 2:
        base_stage = "exploration_and_discovery" 
    elif message_count <= 4:
        base_stage = "understanding_development"
    elif message_count <= 6:
        base_stage = "knowledge_integration"
    else:
        base_stage = "mastery_and_application"
    
    # Enhance with learning pattern context
    if "improving" in learning_personalization:
        return f"{base_stage}_with_building_confidence"
    elif "needs_support" in learning_personalization:
        return f"{base_stage}_with_careful_scaffolding"
    elif "advanced" in learning_personalization or "mastery" in learning_personalization:
        return f"{base_stage}_with_advanced_challenge"
    else:
        return base_stage

def generate_fallback_response(state: GraphState, current_topic: str, learning_personalization: str) -> str:
    """
    Phase 3: Generate intelligent fallback response based on learning context
    """
    if "visual" in learning_personalization.lower():
        return f"That's interesting! Can you help me visualize how you're thinking about {current_topic}? What mental picture or diagram comes to mind?"
    elif "experiential" in learning_personalization.lower():
        return f"I'm curious about your hands-on experience with {current_topic}. Can you think of a real-world situation where this would be relevant?"
    elif "verbal" in learning_personalization.lower():
        return f"I'd love to hear more about your understanding of {current_topic}. Can you walk me through your thinking process?"
    else:
        return f"That's a great point about {current_topic}! Tell me more about how you're approaching this concept."

def track_response_analytics(state: GraphState, current_topic: str, response: Dict, learning_personalization: str) -> None:
    """
    Phase 3: Track advanced response analytics for continuous improvement
    """
    if "response_analytics" not in state:
        state["response_analytics"] = []
    
    analytics_entry = {
        "topic": current_topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pedagogical_strategy": response.get("pedagogical_strategy", "unknown"),
        "learning_technique": response.get("learning_technique", "unknown"),
        "difficulty_level": response.get("difficulty_level", "moderate"),
        "personalization_applied": response.get("personalization_applied", "none"),
        "learning_momentum": response.get("learning_momentum_assessment", "steady"),
        "message_count": state.get("message_count", 0)
    }
    
    state["response_analytics"].append(analytics_entry)

def get_conversation_stage(topic_messages: List[Dict], user_input: str) -> str:
    """Determine what stage of the conversation we're in for context"""
    message_count = len(topic_messages)
    
    if message_count == 0:
        return "initial_exploration"
    elif message_count <= 2:
        return "getting_started" 
    elif message_count <= 4:
        return "building_understanding"
    elif message_count <= 6:
        return "deepening_knowledge"
    else:
        return "advanced_discussion"

def generate_topic_aware_opening(state: GraphState) -> str:
    """
    Phase 2: Enhanced opening generation with natural conversation starters
    """
    topics = state.get("topics", [])
    session_type = state.get("session_type", "custom")
    topic_sources = state.get("topic_sources", {})
    
    # Build context about topics and their sources
    topic_contexts = []
    for topic in topics[:3]:  # Show first 3 topics
        source_info = topic_sources.get(topic, {})
        if source_info.get("source") == "firebase":
            days_overdue = source_info.get("days_overdue", 0)
            if days_overdue > 0:
                topic_contexts.append(f"{topic} (due for review, {days_overdue} days)")
            else:
                topic_contexts.append(f"{topic} (scheduled review)")
        else:
            topic_contexts.append(f"{topic} (custom topic)")
    
    system_prompt = """
Generate a warm, natural opening for a learning conversation that feels like chatting with an enthusiastic tutor.

TONE & STYLE:
- Conversational and welcoming (like ChatGPT)
- Enthusiastic about learning together
- Set expectation for natural dialogue, not formal Q&A
- Mention the topics naturally without making it feel like a rigid agenda

OPENING PRINCIPLES:
- Start with friendly greeting
- Show genuine interest in their learning
- Briefly mention what we'll explore together
- Set the tone that this will be a conversation, not a quiz
- End with a natural conversation starter about the first topic

EXAMPLES OF GOOD OPENINGS:
- "Hey there! I'm excited to dive into some interesting topics with you today..."
- "Hi! Ready for a great learning conversation? I'm looking forward to exploring..."
- "Hello! I love having these kinds of discussions. Today we get to talk about..."

Generate ONE natural opening message (2-3 sentences max) that launches into the first topic organically.
Return just the opening text, no JSON or formatting.
"""
    
    user_prompt = f"""
SESSION CONTEXT:
- Topics we'll explore: {topic_contexts}
- Session type: {session_type}
- Total topics: {len(topics)}

Generate the opening message now.
"""
    
    return call_ai_for_simple_response(system_prompt, user_prompt)

def record_user_response(state: GraphState):
    """Record user's response in conversation history"""
    current_topic = get_current_topic(state)
    conversation_history = state.get("conversation_history", [])
    
    conversation_history.append({
        "role": "user", 
        "content": state["user_input"],
        "topic": current_topic,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["conversation_history"] = conversation_history
    
    # Clear user input for next turn
    state["user_input"] = None

def evaluate_topic_node(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3: Pure LLM Evaluation with sophisticated understanding assessment and learning pattern recognition
    """
    current_topic = get_current_topic(state)
    if not current_topic:
        return {"error": "No current topic to evaluate"}
    
    topic_source = state.get("topic_sources", {}).get(current_topic, {})
    
    # Get comprehensive conversation context
    topic_conversation = get_topic_conversation(state, current_topic)
    conversation_analysis = analyze_conversation_quality(topic_conversation)
    
    # Get cross-topic insights for deeper context
    all_conversation_history = state.get("conversation_history", [])
    completed_topics = state.get("completed_topics", [])
    previous_evaluations = state.get("topic_evaluations", {})
    
    # Build comprehensive evaluation context
    evaluation_context = build_comprehensive_evaluation_context(
        current_topic, topic_source, topic_conversation, 
        conversation_analysis, completed_topics, previous_evaluations, all_conversation_history
    )
    
    # Phase 3: Pure LLM evaluation with advanced context awareness
    evaluation_prompt = f"""
You are an expert learning assessment specialist with deep expertise in conversational learning analysis, cognitive science, and personalized education. You're evaluating a student's understanding of a topic through natural dialogue analysis.

COMPREHENSIVE EVALUATION CONTEXT:
{evaluation_context}

ADVANCED ASSESSMENT FRAMEWORK:

🧠 COGNITIVE UNDERSTANDING DIMENSIONS:
1. **Conceptual Mastery**: Can they explain core concepts clearly and accurately?
2. **Procedural Knowledge**: Do they understand how to apply the knowledge?
3. **Conditional Knowledge**: Do they know when and why to use this knowledge?
4. **Metacognitive Awareness**: Do they understand their own understanding?
5. **Transfer Ability**: Can they connect this to other knowledge domains?

📊 CONVERSATIONAL LEARNING INDICATORS:
1. **Explanation Quality**: Clarity, accuracy, and completeness of explanations
2. **Question Handling**: How well they respond to probing questions
3. **Elaboration Depth**: Ability to expand on ideas when prompted
4. **Connection Making**: Links to other concepts or experiences
5. **Confidence Signals**: Language patterns indicating certainty vs uncertainty
6. **Curiosity Indicators**: Questions asked, exploration attempts
7. **Self-Correction**: Recognition and correction of errors or gaps
8. **Application Examples**: Ability to provide relevant, accurate examples

🎯 LEARNING PATTERN ANALYSIS:
- **Learning Style Preferences**: Visual, verbal, experiential patterns observed
- **Cognitive Load Management**: How they handle complex information
- **Engagement Patterns**: What questioning styles elicit best responses
- **Knowledge Construction**: How they build understanding through dialogue
- **Retention Signals**: Indicators of likely long-term retention

🔄 CROSS-TOPIC CONTEXT INTEGRATION:
- **Learning Progression**: How understanding has evolved across topics
- **Consistent Strengths**: Patterns of strong performance areas
- **Recurring Challenges**: Areas that consistently need more support
- **Learning Velocity**: Speed of understanding and adaptation
- **Concept Integration**: Ability to connect current topic to previous learning

EVALUATION METHODOLOGY:
Instead of traditional testing metrics, assess through conversation quality:

📈 UNDERSTANDING LEVELS (Choose the best fit):
- **Mastery (5)**: Demonstrates deep, flexible understanding; explains clearly; makes connections; shows confidence; can teach others
- **Proficient (4)**: Solid understanding with minor gaps; mostly accurate explanations; some connections made
- **Developing (3)**: Basic understanding present; some inaccuracies or incomplete knowledge; shows potential for growth
- **Emerging (2)**: Limited understanding; significant gaps; struggles with explanations but shows some learning
- **Insufficient (1)**: Minimal understanding demonstrated; mostly confused or incorrect; needs fundamental review

🎯 CONTEXTUAL CONSIDERATIONS:
- **Firebase Topics**: Focus on retention quality and recall effectiveness
- **Custom Topics**: Emphasize initial learning and comprehension building
- **Learning History**: Consider performance patterns and growth trends
- **Conversation Quality**: Weight higher-quality dialogue more heavily
- **Individual Learning Style**: Adapt assessment to observed learning preferences

COMPREHENSIVE EVALUATION OUTPUT:
Return a detailed JSON assessment that captures the full learning picture:

{{
    "topic": "{current_topic}",
    "understanding_level": 4,
    "understanding_category": "proficient|developing|emerging|mastery|insufficient",
    "confidence_assessment": {{
        "student_confidence": "high|medium|low",
        "actual_understanding": "high|medium|low", 
        "confidence_accuracy": "overconfident|well_calibrated|underconfident"
    }},
    "cognitive_dimensions": {{
        "conceptual_mastery": "strong|adequate|weak",
        "procedural_knowledge": "strong|adequate|weak",
        "conditional_knowledge": "strong|adequate|weak",
        "metacognitive_awareness": "strong|adequate|weak",
        "transfer_ability": "strong|adequate|weak"
    }},
    "conversation_analysis": {{
        "explanation_quality": "excellent|good|fair|poor",
        "question_handling": "excellent|good|fair|poor",
        "elaboration_depth": "deep|moderate|shallow",
        "connection_making": "extensive|some|minimal",
        "engagement_level": "highly_engaged|engaged|moderately_engaged|disengaged"
    }},
    "learning_patterns": {{
        "preferred_learning_style": "verbal|visual|experiential|mixed",
        "cognitive_load_preference": "high|moderate|low",
        "optimal_questioning_style": "direct|scaffolded|exploratory|socratic",
        "knowledge_construction_pattern": "systematic|intuitive|example_driven|theory_first"
    }},
    "retention_prediction": {{
        "short_term_retention": 0.85,
        "long_term_retention": 0.72,
        "factors_supporting_retention": ["clear_understanding", "personal_examples", "enthusiasm"],
        "factors_hindering_retention": ["complexity", "abstract_concepts"]
    }},
    "learning_insights": {{
        "key_strengths": [
            "Specific strengths observed in this conversation",
            "Learning approaches that worked well"
        ],
        "areas_for_growth": [
            "Specific gaps or areas needing reinforcement",
            "Suggested learning approaches for improvement"
        ],
        "metacognitive_observations": [
            "How well they understand their own learning",
            "Self-awareness of strengths and gaps"
        ]
    }},
    "personalized_recommendations": {{
        "immediate_review_focus": "What to review right after this session",
        "optimal_review_timing": "immediate|1_day|3_days|1_week|2_weeks",
        "recommended_learning_approach": "Specific strategies for future learning",
        "complexity_adjustment": "increase|maintain|decrease",
        "questioning_style_preference": "What works best for this learner"
    }},
    "cross_topic_integration": {{
        "connections_to_previous_topics": ["topic1", "topic2"],
        "learning_velocity_trend": "accelerating|steady|slowing",
        "consistency_with_previous_performance": "consistent|improving|declining",
        "emerging_learning_patterns": "Patterns observed across multiple topics"
    }},
    "session_contribution": {{
        "conversation_quality_rating": "excellent|good|adequate|poor",
        "learning_momentum_impact": "increased|maintained|decreased",
        "engagement_level_change": "increased|stable|decreased",
        "knowledge_construction_effectiveness": "highly_effective|effective|somewhat_effective|ineffective"
    }},
    "summary": "Comprehensive 2-3 sentence summary of understanding and learning patterns",
    "next_session_optimization": "Specific suggestions for optimizing future learning conversations"
}}

CRITICAL INSTRUCTION: This is pure LLM evaluation. Make sophisticated judgments based on conversation quality, learning patterns, and understanding indicators. Be nuanced in your assessment - look for evidence of genuine understanding vs surface-level responses.
"""
    
    evaluation = call_ai_with_json_output(evaluation_prompt)
    
    # Ensure backward compatibility while adding Phase 3 enhancements
    score = evaluation.get("understanding_level", 3)
    evaluation["score"] = score  # Legacy compatibility
    
    # Enhanced evaluation storage with Phase 3 metadata
    evaluation.update({
        "conversation_metadata": conversation_analysis,
        "evaluation_type": "pure_llm_conversational_v3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "3_pure_llm_evaluation",
        "context_depth": "comprehensive_cross_topic_analysis"
    })
    
    # Store comprehensive results
    topic_scores = state.get("topic_scores", {})
    topic_evaluations = state.get("topic_evaluations", {})
    
    topic_scores[current_topic] = score
    topic_evaluations[current_topic] = evaluation
    
    state["topic_scores"] = topic_scores
    state["topic_evaluations"] = topic_evaluations
    
    # Phase 3: Update learning analytics
    update_learning_analytics(state, current_topic, evaluation)
    
    # Move to next topic
    advance_to_next_topic(state)
    
    return {
        "topic_evaluated": current_topic,
        "topic_score": score,
        "topic_evaluation": evaluation,
        "topics_completed": len(state.get("completed_topics", [])),
        "remaining_topics": get_remaining_topics(state),
        "conversation_analysis": conversation_analysis,
        "learning_insights": evaluation.get("learning_insights", {}),
        "personalized_recommendations": evaluation.get("personalized_recommendations", {})
    }

def build_comprehensive_evaluation_context(current_topic: str, topic_source: Dict, 
                                         topic_conversation: List[Dict], conversation_analysis: Dict,
                                         completed_topics: List[str], previous_evaluations: Dict,
                                         all_conversation_history: List[Dict]) -> str:
    """
    Phase 3: Build comprehensive context for sophisticated LLM evaluation
    """
    context_parts = []
    
    # 1. Current Topic Context
    context_parts.append(f"CURRENT TOPIC: {current_topic}")
    context_parts.append(f"Topic Source: {build_topic_context(current_topic, topic_source)}")
    
    # 2. Conversation Quality Analysis
    context_parts.append(f"\nCONVERSATION QUALITY METRICS:")
    context_parts.append(f"- Total exchanges: {conversation_analysis.get('total_exchanges', 0)}")
    context_parts.append(f"- Quality level: {conversation_analysis.get('quality_level', 'unknown')}")
    context_parts.append(f"- Engagement level: {conversation_analysis.get('engagement_level', 'unknown')}")
    context_parts.append(f"- Response depth: {conversation_analysis.get('depth_level', 'unknown')}")
    context_parts.append(f"- Average response length: {conversation_analysis.get('avg_response_length', 0)} chars")
    
    # 3. Full Topic Conversation
    context_parts.append(f"\nCOMPLETE TOPIC CONVERSATION:")
    context_parts.append(format_topic_conversation_for_evaluation(topic_conversation))
    
    # 4. Cross-Topic Learning Context
    if completed_topics and previous_evaluations:
        context_parts.append(f"\nCROSS-TOPIC LEARNING CONTEXT:")
        context_parts.append(f"Previous topics completed: {completed_topics}")
        
        # Include recent performance patterns
        recent_scores = []
        learning_patterns = []
        for topic in completed_topics[-3:]:  # Last 3 topics
            if topic in previous_evaluations:
                eval_data = previous_evaluations[topic]
                recent_scores.append(eval_data.get("score", 0))
                if "learning_patterns" in eval_data:
                    patterns = eval_data["learning_patterns"]
                    learning_patterns.append(f"{topic}: {patterns.get('preferred_learning_style', 'unknown')}")
        
        if recent_scores:
            avg_recent = sum(recent_scores) / len(recent_scores)
            context_parts.append(f"Recent performance trend: {avg_recent:.1f}/5 average")
        
        if learning_patterns:
            context_parts.append(f"Observed learning patterns: {', '.join(learning_patterns)}")
    
    # 5. Session Context
    total_messages = len(all_conversation_history)
    session_engagement = "high" if total_messages > 15 else "medium" if total_messages > 8 else "low"
    context_parts.append(f"\nSESSION CONTEXT:")
    context_parts.append(f"- Total session messages: {total_messages}")
    context_parts.append(f"- Session engagement level: {session_engagement}")
    context_parts.append(f"- Topics completed in session: {len(completed_topics)}")
    
    return "\n".join(context_parts)

def update_learning_analytics(state: Dict, topic: str, evaluation: Dict) -> None:
    """
    Phase 3: Update comprehensive learning analytics with AI insights
    """
    # Initialize learning analytics if not present
    if "learning_analytics" not in state:
        state["learning_analytics"] = {
            "learning_velocity": [],
            "engagement_trends": [],
            "understanding_patterns": {},
            "personalization_insights": {},
            "retention_predictions": {}
        }
    
    analytics = state["learning_analytics"]
    
    # Track learning velocity
    score = evaluation.get("understanding_level", 3)
    analytics["learning_velocity"].append({
        "topic": topic,
        "score": score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Track engagement trends
    engagement = evaluation.get("conversation_analysis", {}).get("engagement_level", "unknown")
    analytics["engagement_trends"].append({
        "topic": topic,
        "engagement": engagement,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Store understanding patterns
    if "learning_patterns" in evaluation:
        analytics["understanding_patterns"][topic] = evaluation["learning_patterns"]
    
    # Store personalization insights
    if "personalized_recommendations" in evaluation:
        analytics["personalization_insights"][topic] = evaluation["personalized_recommendations"]
    
    # Store retention predictions
    if "retention_prediction" in evaluation:
        analytics["retention_predictions"][topic] = evaluation["retention_prediction"]

def analyze_conversation_quality(topic_conversation: List[Dict]) -> Dict[str, str]:
    """
    Phase 2: Analyze the quality of the conversation for evaluation context
    """
    if not topic_conversation:
        return {
            "quality_level": "insufficient",
            "engagement_level": "none",
            "depth_level": "none"
        }
    
    # Count student vs tutor messages
    student_messages = [msg for msg in topic_conversation if msg["role"] == "user"]
    tutor_messages = [msg for msg in topic_conversation if msg["role"] == "assistant"]
    
    # Analyze message lengths and content
    avg_student_length = sum(len(msg["content"]) for msg in student_messages) / len(student_messages) if student_messages else 0
    total_exchanges = len(student_messages)
    
    # Determine quality levels
    if total_exchanges >= 4 and avg_student_length > 100:
        quality_level = "high"
        engagement_level = "high"
        depth_level = "deep"
    elif total_exchanges >= 3 and avg_student_length > 50:
        quality_level = "good"
        engagement_level = "medium"
        depth_level = "moderate"
    elif total_exchanges >= 2:
        quality_level = "basic"
        engagement_level = "medium"
        depth_level = "shallow"
    else:
        quality_level = "minimal"
        engagement_level = "low"
        depth_level = "surface"
    
    return {
        "quality_level": quality_level,
        "engagement_level": engagement_level,
        "depth_level": depth_level,
        "total_exchanges": total_exchanges,
        "avg_response_length": round(avg_student_length)
    }

def complete_session_with_topic_scores(state: GraphState) -> Dict[str, Any]:
    """
    Phase 3: Advanced session completion with sophisticated learning analytics and personalized insights
    """
    topic_scores = state.get("topic_scores", {})
    topic_evaluations = state.get("topic_evaluations", {})
    completed_topics = state.get("completed_topics", [])
    conversation_history = state.get("conversation_history", [])
    learning_analytics = state.get("learning_analytics", {})
    response_analytics = state.get("response_analytics", [])
    
    # Phase 3: Advanced session analysis
    session_analytics = analyze_comprehensive_session_learning(
        conversation_history, completed_topics, topic_evaluations, learning_analytics, response_analytics
    )
    
    # Phase 3: Generate sophisticated session summary with LLM
    session_summary_prompt = f"""
You are an expert learning analytics specialist and educational psychologist. You've just observed a sophisticated AI-driven conversational learning session. Your task is to provide a comprehensive, insightful analysis of the learning experience and outcomes.

COMPREHENSIVE SESSION DATA:
{format_session_analysis_for_llm(session_analytics, topic_scores, topic_evaluations, conversation_history)}

ADVANCED LEARNING ANALYTICS FRAMEWORK:

🧠 LEARNING EFFECTIVENESS ANALYSIS:
Evaluate the session across multiple dimensions:
1. **Knowledge Acquisition**: How effectively were concepts learned?
2. **Retention Indicators**: What suggests strong long-term retention?
3. **Transfer Potential**: Evidence of ability to apply learning in new contexts
4. **Metacognitive Development**: Growth in learning awareness and strategies
5. **Engagement Quality**: Depth and authenticity of learning engagement

📊 PERSONALIZED LEARNING INSIGHTS:
Identify patterns that reveal individual learning characteristics:
1. **Learning Style Preferences**: What approaches worked best?
2. **Cognitive Processing Patterns**: How they construct understanding
3. **Motivation and Interest Drivers**: What energized their learning
4. **Challenge Tolerance**: How they responded to difficulty
5. **Social Learning Preferences**: Response to different interaction styles

🎯 PERFORMANCE QUALITY ASSESSMENT:
Look beyond simple scores to understand learning quality:
1. **Understanding Depth**: Surface vs deep learning indicators
2. **Conceptual Integration**: Ability to connect ideas across topics
3. **Application Readiness**: Signs of practical knowledge transfer
4. **Retention Sustainability**: Factors supporting long-term memory
5. **Learning Acceleration**: Evidence of improving learning efficiency

🔄 CROSS-TOPIC LEARNING PATTERNS:
Analyze learning evolution across the session:
1. **Performance Trajectory**: How understanding developed over time
2. **Learning Velocity Changes**: Acceleration or deceleration patterns
3. **Strategy Adaptation**: How they adjusted approaches across topics
4. **Confidence Evolution**: Changes in self-assurance and certainty
5. **Knowledge Network Building**: Connection-making across domains

COMPREHENSIVE EVALUATION OUTPUT:
Generate a sophisticated assessment that captures the full learning picture:

{{
    "overall_learning_effectiveness": "exceptional|excellent|good|developing|needs_attention",
    "learning_experience_quality": {{
        "engagement_depth": "profound|high|moderate|surface",
        "intellectual_curiosity": "exceptional|strong|moderate|limited",
        "learning_momentum": "accelerating|steady|variable|declining",
        "challenge_response": "thrives|adapts_well|needs_support|struggles"
    }},
    "personalized_learning_profile": {{
        "dominant_learning_style": "verbal|visual|experiential|kinesthetic|mixed",
        "cognitive_processing_preference": "systematic|intuitive|analytical|holistic",
        "optimal_challenge_level": "high|moderate|gentle|scaffolded",
        "preferred_interaction_style": "socratic|collaborative|direct|exploratory",
        "knowledge_construction_pattern": "building_blocks|web_connections|story_narrative|practical_application"
    }},
    "learning_outcomes_analysis": {{
        "knowledge_acquisition_quality": "deep_understanding|solid_grasp|surface_learning|fragmented",
        "retention_probability": {{
            "short_term": 0.95,
            "medium_term": 0.85,
            "long_term": 0.75
        }},
        "transfer_readiness": "high|moderate|developing|limited",
        "metacognitive_growth": "significant|moderate|minimal|none"
    }},
    "session_highlights": [
        "Most significant learning breakthroughs",
        "Moments of exceptional understanding",
        "Examples of effective learning strategies used"
    ],
    "learning_strengths_identified": [
        "Specific cognitive and learning strengths observed",
        "Particularly effective learning approaches",
        "Areas of exceptional performance or insight"
    ],
    "growth_opportunities": [
        "Areas with potential for deeper development",
        "Learning strategies that could be enhanced",
        "Concepts that warrant additional exploration"
    ],
    "pedagogical_insights": {{
        "most_effective_teaching_approaches": [
            "Specific instructional strategies that worked best",
            "Question types that elicited strong responses"
        ],
        "optimal_learning_conditions": "Environmental and contextual factors that enhanced learning",
        "response_to_different_difficulty_levels": "How they handled varying challenge levels"
    }},
    "cross_topic_learning_analysis": {{
        "learning_velocity_trend": "accelerating|steady_improvement|consistent|variable|declining",
        "concept_integration_ability": "excellent|good|developing|limited",
        "knowledge_transfer_evidence": [
            "Examples of connecting concepts across topics",
            "Signs of applying learning in new contexts"
        ],
        "learning_strategy_evolution": "How their approach changed across topics"
    }},
    "personalized_recommendations": {{
        "immediate_follow_up": "Specific actions to reinforce today's learning",
        "optimal_review_schedule": {{
            "next_review": "1_day|3_days|1_week|2_weeks",
            "review_focus": "What to emphasize in next session",
            "review_format": "conversation|practice|application|reflection"
        }},
        "learning_optimization_strategies": [
            "Specific approaches to enhance future learning",
            "Environmental or methodological adjustments"
        ],
        "challenge_level_recommendations": "How to optimize difficulty for continued growth"
    }},
    "future_learning_pathway": {{
        "suggested_next_topics": [
            "Natural progressions from current understanding",
            "Areas that would build on established strengths"
        ],
        "learning_goal_suggestions": "Appropriate learning objectives for continued development",
        "session_format_optimization": "How to structure future learning conversations"
    }},
    "session_quality_metrics": {{
        "conversation_naturalness": "exceptionally_natural|very_natural|natural|somewhat_artificial",
        "ai_tutor_effectiveness": "outstanding|excellent|good|adequate",
        "learning_efficiency": "highly_efficient|efficient|adequate|inefficient",
        "overall_session_satisfaction": "exceptional|high|good|moderate"
    }},
    "learning_analytics_summary": {{
        "total_learning_interactions": {len(conversation_history)},
        "average_topic_performance": 4.2,
        "learning_consistency": "highly_consistent|consistent|variable|inconsistent",
        "engagement_sustainability": "maintained_throughout|mostly_sustained|variable|declined"
    }},
    "comprehensive_summary": "A detailed 3-4 sentence summary that captures the essence of this learner's experience, strengths, learning patterns, and potential",
    "next_session_optimization": "Specific, actionable recommendations for maximizing the effectiveness of future learning conversations based on observed patterns and preferences"
}}

EVALUATION PRINCIPLES:
- Focus on learning quality over simple metrics
- Recognize individual learning differences and strengths
- Provide actionable insights for learning optimization
- Consider the holistic learning experience, not just knowledge acquisition
- Be encouraging while being realistic about areas for growth

Your analysis should feel like it comes from an expert educational psychologist who has deeply understood this learner through careful observation of their conversational learning patterns.
"""
    
    session_summary = call_ai_with_json_output(session_summary_prompt)
    
    # Phase 3: Enhance summary with calculated metrics
    if topic_scores:
        avg_score = sum(topic_scores.values()) / len(topic_scores)
        session_summary["calculated_metrics"] = {
            "average_score": round(avg_score, 1),
            "score_range": f"{min(topic_scores.values())}-{max(topic_scores.values())}",
            "topics_mastered": len([s for s in topic_scores.values() if s >= 4]),
            "topics_need_review": len([s for s in topic_scores.values() if s <= 2])
        }
        
        # Enhanced score distribution
        session_summary["detailed_score_distribution"] = {
            "mastery_level_topics": [topic for topic, score in topic_scores.items() if score >= 5],
            "proficient_topics": [topic for topic, score in topic_scores.items() if score == 4],
            "developing_topics": [topic for topic, score in topic_scores.items() if score == 3],
            "emerging_topics": [topic for topic, score in topic_scores.items() if score == 2],
            "needs_attention_topics": [topic for topic, score in topic_scores.items() if score <= 1]
        }
    
    # Phase 3: Add comprehensive metadata
    session_summary.update({
        "session_analytics": session_analytics,
        "evaluation_approach": "pure_llm_comprehensive_analysis",
        "phase": "3_advanced_learning_analytics",
        "conversation_quality_data": analyze_session_conversation_quality(conversation_history, completed_topics),
        "personalization_effectiveness": calculate_personalization_effectiveness(response_analytics),
        "learning_science_integration": assess_learning_science_effectiveness(topic_evaluations),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    state["session_summary"] = session_summary
    state["session_complete"] = True
    
    return {
        "session_complete": True,
        "topic_scores": topic_scores,
        "topic_evaluations": topic_evaluations,
        "session_summary": session_summary,
        "topics_completed": completed_topics,
        "total_topics": len(state.get("topics", [])),
        "message_count": state.get("message_count", 0),
        "advanced_analytics": session_analytics,
        "learning_insights": session_summary.get("learning_outcomes_analysis", {}),
        "personalized_recommendations": session_summary.get("personalized_recommendations", {})
    }

def analyze_comprehensive_session_learning(conversation_history: List[Dict], completed_topics: List[str], 
                                         topic_evaluations: Dict, learning_analytics: Dict, 
                                         response_analytics: List[Dict]) -> Dict:
    """
    Phase 3: Comprehensive analysis of session learning patterns and effectiveness
    """
    analytics = {
        "conversation_patterns": {},
        "learning_progression": {},
        "engagement_analysis": {},
        "personalization_effectiveness": {},
        "pedagogical_strategy_analysis": {}
    }
    
    # Conversation pattern analysis
    total_exchanges = len([msg for msg in conversation_history if msg["role"] == "user"])
    avg_response_length = 0
    if total_exchanges > 0:
        user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
        avg_response_length = sum(len(msg["content"]) for msg in user_messages) / len(user_messages)
    
    analytics["conversation_patterns"] = {
        "total_exchanges": total_exchanges,
        "average_response_length": round(avg_response_length),
        "conversation_depth": "deep" if avg_response_length > 100 else "moderate" if avg_response_length > 50 else "surface",
        "dialogue_quality": analyze_overall_dialogue_quality(conversation_history)
    }
    
    # Learning progression analysis
    if learning_analytics.get("learning_velocity"):
        velocity_data = learning_analytics["learning_velocity"]
        scores = [item["score"] for item in velocity_data]
        
        analytics["learning_progression"] = {
            "initial_performance": scores[0] if scores else 0,
            "final_performance": scores[-1] if scores else 0,
            "improvement_trajectory": calculate_learning_trajectory(scores),
            "consistency": calculate_performance_consistency(scores),
            "peak_performance": max(scores) if scores else 0
        }
    
    # Engagement analysis
    if learning_analytics.get("engagement_trends"):
        engagement_data = learning_analytics["engagement_trends"]
        analytics["engagement_analysis"] = analyze_engagement_patterns(engagement_data)
    
    # Personalization effectiveness
    if response_analytics:
        analytics["personalization_effectiveness"] = analyze_personalization_effectiveness(response_analytics)
    
    # Pedagogical strategy analysis
    if response_analytics:
        analytics["pedagogical_strategy_analysis"] = analyze_pedagogical_strategies(response_analytics)
    
    return analytics

def format_session_analysis_for_llm(session_analytics: Dict, topic_scores: Dict, 
                                   topic_evaluations: Dict, conversation_history: List[Dict]) -> str:
    """
    Phase 3: Format comprehensive session data for LLM analysis
    """
    formatted_parts = []
    
    # Session overview
    formatted_parts.append("SESSION OVERVIEW:")
    formatted_parts.append(f"- Topics completed: {list(topic_scores.keys())}")
    formatted_parts.append(f"- Scores achieved: {topic_scores}")
    formatted_parts.append(f"- Total conversation exchanges: {len(conversation_history)}")
    
    # Conversation patterns
    if "conversation_patterns" in session_analytics:
        patterns = session_analytics["conversation_patterns"]
        formatted_parts.append(f"\nCONVERSATION PATTERNS:")
        formatted_parts.append(f"- Average response length: {patterns.get('average_response_length', 0)} characters")
        formatted_parts.append(f"- Conversation depth: {patterns.get('conversation_depth', 'unknown')}")
        formatted_parts.append(f"- Dialogue quality: {patterns.get('dialogue_quality', 'unknown')}")
    
    # Learning progression
    if "learning_progression" in session_analytics:
        progression = session_analytics["learning_progression"]
        formatted_parts.append(f"\nLEARNING PROGRESSION:")
        formatted_parts.append(f"- Initial performance: {progression.get('initial_performance', 0)}/5")
        formatted_parts.append(f"- Final performance: {progression.get('final_performance', 0)}/5")
        formatted_parts.append(f"- Learning trajectory: {progression.get('improvement_trajectory', 'unknown')}")
    
    # Key evaluation insights
    if topic_evaluations:
        formatted_parts.append(f"\nKEY EVALUATION INSIGHTS:")
        for topic, evaluation in topic_evaluations.items():
            summary = evaluation.get("summary", "No summary available")
            formatted_parts.append(f"- {topic}: {summary}")
    
    # Recent conversation sample
    recent_conversation = conversation_history[-6:] if conversation_history else []
    if recent_conversation:
        formatted_parts.append(f"\nRECENT CONVERSATION SAMPLE:")
        for msg in recent_conversation:
            role = "Student" if msg["role"] == "user" else "AI Tutor"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            formatted_parts.append(f"{role}: {content}")
    
    return "\n".join(formatted_parts)

def calculate_learning_trajectory(scores: List[int]) -> str:
    """Calculate overall learning trajectory from score progression"""
    if len(scores) < 2:
        return "insufficient_data"
    
    # Calculate trend
    first_half = scores[:len(scores)//2] if len(scores) > 2 else scores[:1]
    second_half = scores[len(scores)//2:] if len(scores) > 2 else scores[1:]
    
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    
    difference = avg_second - avg_first
    
    if difference > 0.5:
        return "strong_improvement"
    elif difference > 0:
        return "moderate_improvement"
    elif abs(difference) <= 0.25:
        return "stable_performance"
    elif difference > -0.5:
        return "slight_decline"
    else:
        return "concerning_decline"

def calculate_performance_consistency(scores: List[int]) -> str:
    """Calculate consistency of performance across topics"""
    if len(scores) < 2:
        return "insufficient_data"
    
    score_range = max(scores) - min(scores)
    
    if score_range <= 1:
        return "highly_consistent"
    elif score_range <= 2:
        return "moderately_consistent"
    elif score_range <= 3:
        return "somewhat_variable"
    else:
        return "highly_variable"

def analyze_overall_dialogue_quality(conversation_history: List[Dict]) -> str:
    """Analyze overall quality of dialogue throughout session"""
    if not conversation_history:
        return "no_conversation"
    
    user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
    if not user_messages:
        return "no_user_input"
    
    # Analyze response quality indicators
    avg_length = sum(len(msg["content"]) for msg in user_messages) / len(user_messages)
    
    # Look for engagement indicators
    engagement_keywords = ["because", "but", "however", "actually", "i think", "what if", "how about"]
    curiosity_keywords = ["why", "how", "what", "where", "when", "can you", "could you"]
    
    total_engagement_signals = 0
    for msg in user_messages:
        content_lower = msg["content"].lower()
        total_engagement_signals += sum(1 for keyword in engagement_keywords + curiosity_keywords if keyword in content_lower)
    
    engagement_density = total_engagement_signals / len(user_messages) if user_messages else 0
    
    # Determine overall quality
    if avg_length > 80 and engagement_density > 1:
        return "exceptional"
    elif avg_length > 60 and engagement_density > 0.5:
        return "high_quality"
    elif avg_length > 40 and engagement_density > 0:
        return "good_quality"
    elif avg_length > 20:
        return "adequate"
    else:
        return "needs_improvement"

def analyze_engagement_patterns(engagement_data: List[Dict]) -> Dict:
    """Analyze engagement patterns throughout the session"""
    if not engagement_data:
        return {"pattern": "no_data", "trend": "unknown"}
    
    engagement_levels = [item.get("engagement", "unknown") for item in engagement_data]
    
    # Map engagement to numeric values for trend analysis
    engagement_values = {
        "highly_engaged": 5,
        "engaged": 4,
        "moderately_engaged": 3,
        "low_engagement": 2,
        "disengaged": 1
    }
    
    numeric_engagement = [engagement_values.get(level, 3) for level in engagement_levels]
    
    if len(numeric_engagement) < 2:
        return {"pattern": "single_point", "trend": "stable"}
    
    # Calculate trend
    first_half_avg = sum(numeric_engagement[:len(numeric_engagement)//2]) / len(numeric_engagement[:len(numeric_engagement)//2])
    second_half_avg = sum(numeric_engagement[len(numeric_engagement)//2:]) / len(numeric_engagement[len(numeric_engagement)//2:])
    
    trend_difference = second_half_avg - first_half_avg
    
    if trend_difference > 0.5:
        trend = "increasing"
    elif trend_difference < -0.5:
        trend = "decreasing"
    else:
        trend = "stable"
    
    overall_avg = sum(numeric_engagement) / len(numeric_engagement)
    
    if overall_avg >= 4:
        pattern = "consistently_high"
    elif overall_avg >= 3:
        pattern = "moderate_to_good"
    else:
        pattern = "needs_attention"
    
    return {"pattern": pattern, "trend": trend, "average_level": overall_avg}

def analyze_personalization_effectiveness(response_analytics: List[Dict]) -> Dict:
    """Analyze how effectively personalization was applied"""
    if not response_analytics:
        return {"effectiveness": "no_data"}
    
    personalization_applications = [item.get("personalization_applied", "none") for item in response_analytics]
    
    # Count different types of personalization
    personalization_counts = {}
    for app in personalization_applications:
        personalization_counts[app] = personalization_counts.get(app, 0) + 1
    
    total_responses = len(response_analytics)
    personalized_responses = total_responses - personalization_counts.get("none", 0) - personalization_counts.get("general_conversational_approach", 0)
    
    personalization_rate = personalized_responses / total_responses if total_responses > 0 else 0
    
    if personalization_rate > 0.7:
        effectiveness = "highly_effective"
    elif personalization_rate > 0.4:
        effectiveness = "moderately_effective"
    elif personalization_rate > 0.1:
        effectiveness = "somewhat_effective"
    else:
        effectiveness = "minimal_personalization"
    
    return {
        "effectiveness": effectiveness,
        "personalization_rate": round(personalization_rate, 2),
        "personalization_types": list(personalization_counts.keys())
    }

def analyze_pedagogical_strategies(response_analytics: List[Dict]) -> Dict:
    """Analyze the variety and effectiveness of pedagogical strategies used"""
    if not response_analytics:
        return {"variety": "no_data"}
    
    strategies = [item.get("pedagogical_strategy", "unknown") for item in response_analytics]
    strategy_counts = {}
    for strategy in strategies:
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    unique_strategies = len(strategy_counts)
    total_responses = len(response_analytics)
    
    variety_score = unique_strategies / min(total_responses, 5)  # Normalize by max expected strategies
    
    if variety_score >= 0.8:
        variety = "highly_varied"
    elif variety_score >= 0.6:
        variety = "good_variety"
    elif variety_score >= 0.4:
        variety = "moderate_variety"
    else:
        variety = "limited_variety"
    
    return {
        "variety": variety,
        "unique_strategies_used": unique_strategies,
        "strategy_distribution": strategy_counts,
        "most_used_strategy": max(strategy_counts.keys(), key=strategy_counts.get) if strategy_counts else "unknown"
    }

def calculate_personalization_effectiveness(response_analytics: List[Dict]) -> float:
    """Calculate overall personalization effectiveness score"""
    if not response_analytics:
        return 0.0
    
    effectiveness_scores = []
    
    for response in response_analytics:
        personalization = response.get("personalization_applied", "none")
        learning_momentum = response.get("learning_momentum", "steady")
        
        # Score based on personalization sophistication
        if personalization in ["advanced_adaptation", "learning_style_optimization"]:
            score = 1.0
        elif personalization in ["moderate_personalization", "preference_based"]:
            score = 0.7
        elif personalization in ["basic_adaptation", "simple_personalization"]:
            score = 0.4
        elif personalization == "general_conversational_approach":
            score = 0.2
        else:
            score = 0.0
        
        # Boost score if learning momentum is positive
        if learning_momentum == "increasing":
            score = min(1.0, score + 0.2)
        elif learning_momentum == "needs_support":
            score = max(0.0, score - 0.1)
        
        effectiveness_scores.append(score)
    
    return sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.0

def assess_learning_science_effectiveness(topic_evaluations: Dict) -> Dict:
    """Assess how effectively learning science principles were applied"""
    if not topic_evaluations:
        return {"effectiveness": "no_data"}
    
    # Analyze retention predictions
    retention_scores = []
    learning_patterns_consistency = []
    
    for evaluation in topic_evaluations.values():
        if "retention_prediction" in evaluation:
            retention = evaluation["retention_prediction"]
            long_term = retention.get("long_term_retention", 0.5)
            retention_scores.append(long_term)
        
        if "learning_patterns" in evaluation:
            # Count how many pattern categories are identified
            patterns = evaluation["learning_patterns"]
            identified_patterns = sum(1 for v in patterns.values() if v and v != "unknown")
            learning_patterns_consistency.append(identified_patterns)
    
    # Calculate effectiveness metrics
    avg_retention = sum(retention_scores) / len(retention_scores) if retention_scores else 0.5
    avg_pattern_identification = sum(learning_patterns_consistency) / len(learning_patterns_consistency) if learning_patterns_consistency else 0
    
    if avg_retention > 0.8 and avg_pattern_identification > 3:
        effectiveness = "highly_effective"
    elif avg_retention > 0.6 and avg_pattern_identification > 2:
        effectiveness = "effective"
    elif avg_retention > 0.4 and avg_pattern_identification > 1:
        effectiveness = "moderately_effective"
    else:
        effectiveness = "needs_improvement"
    
    return {
        "effectiveness": effectiveness,
        "average_retention_prediction": round(avg_retention, 2),
        "learning_pattern_identification": round(avg_pattern_identification, 1),
        "retention_optimization_opportunities": identify_retention_optimization_opportunities(topic_evaluations)
    }

def identify_retention_optimization_opportunities(topic_evaluations: Dict) -> List[str]:
    """Identify opportunities to optimize retention based on evaluation data"""
    opportunities = []
    
    for topic, evaluation in topic_evaluations.items():
        if "retention_prediction" in evaluation:
            retention = evaluation["retention_prediction"]
            hindering_factors = retention.get("factors_hindering_retention", [])
            
            if "complexity" in hindering_factors:
                opportunities.append("Break down complex concepts into smaller chunks")
            if "abstract_concepts" in hindering_factors:
                opportunities.append("Use more concrete examples and analogies")
            if "lack_of_practice" in hindering_factors:
                opportunities.append("Incorporate more application exercises")
            if "insufficient_connections" in hindering_factors:
                opportunities.append("Strengthen connections to prior knowledge")
    
    return list(set(opportunities))  # Remove duplicates

# ===== END OF PHASE 4 NODES =====
