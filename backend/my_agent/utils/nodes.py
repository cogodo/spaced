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
    
    opening_prompt = f"""
Generate a warm, natural opening for a learning conversation that feels like chatting with an enthusiastic tutor.

SESSION CONTEXT:
- Topics we'll explore: {topic_contexts}
- Session type: {session_type}
- Total topics: {len(topics)}

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
    
    return call_ai_for_simple_response(opening_prompt)

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

# ===== LEGACY NODES - DEPRECATED =====
# Keep for backward compatibility during transition

def respond_node(state: GraphState) -> Dict[str, Any]:
    """
    DEPRECATED: Legacy respond node - redirects to new conversation_node
    """
    print("WARNING: Using deprecated respond_node, redirecting to conversation_node")
    return conversation_node(state)

def evaluate_node(state: GraphState) -> Dict[str, Any]:
    """
    DEPRECATED: Legacy evaluate node - redirects to topic evaluation
    """
    print("WARNING: Using deprecated evaluate_node, completing session")
    return complete_session_with_topic_scores(state)

# ================================================================================================
# PHASE 2: NEW NODE ARCHITECTURE - Question → Conversation → Scoring
# ================================================================================================

async def question_maker_node(state: GraphState) -> Dict[str, Any]:
    """
    Phase 4: Intelligent adaptive question selection with real-time personalization
    
    Flow:
    1. Ensure question bank exists for current topic
    2. Analyze user's live performance metrics and learned preferences
    3. Calculate adaptive difficulty level for optimal challenge
    4. Select next question using intelligent adaptation algorithms
    5. Initialize question conversation with personalization context
    """
    
    try:
        current_topic = get_current_topic(state)
        if not current_topic:
            logger.warning("No current topic in question_maker_node")
            return {"action": "error", "message": "No current topic available"}
        
        topic_data = current_topic["topic_data"]
        topic_id = current_topic["topic_id"]
        user_id = state.get("user_id")
        
        if not user_id:
            logger.warning("No user_id in question_maker_node")
            return {"action": "error", "message": "User ID required"}
        
        # Ensure question bank exists
        question_bank_result = await ensure_question_bank_exists(user_id, topic_id, topic_data)
        if not question_bank_result["success"]:
            return {
                "action": "error", 
                "message": f"Failed to create question bank: {question_bank_result.get('error', 'Unknown error')}"
            }
        
        # Get session settings for question management
        session_settings = state.get("session_settings", {})
        max_questions_per_topic = session_settings.get("max_questions_per_topic", 7)
        
        # Check if we've completed enough questions for this topic
        topic_question_summaries = state.get("topic_question_summaries", [])
        completed_questions = len(topic_question_summaries)
        
        # PHASE 4: Analyze performance and preferences for adaptive selection
        live_performance = state.get("live_performance_metrics", {})
        learned_preferences = state.get("learned_user_preferences", {})
        adaptive_difficulty = state.get("adaptive_difficulty_level", 0.5)
        learning_momentum = state.get("learning_momentum_score", 0.5)
        
        # PHASE 4: Enhanced topic completion logic with adaptive factors
        should_complete_topic = await evaluate_adaptive_topic_completion(
            state, completed_questions, max_questions_per_topic, live_performance, learning_momentum
        )
        
        if should_complete_topic["should_complete"]:
            logger.info(f"Topic completion triggered: {should_complete_topic['reason']}")
            return {
                "action": "topic_complete",
                "completion_reason": should_complete_topic["reason"],
                "questions_completed": completed_questions,
                "adaptive_factors": should_complete_topic.get("adaptive_factors", []),
                "performance_summary": live_performance
            }
        
        # PHASE 4: Select next question with adaptive intelligence
        next_question_result = await select_adaptive_next_question(
            user_id, topic_id, topic_question_summaries, adaptive_difficulty, 
            learned_preferences, live_performance
        )
        
        if not next_question_result["success"]:
            if next_question_result.get("reason") == "no_more_questions":
                # Natural completion - no more questions available
                return {
                    "action": "topic_complete",
                    "completion_reason": "All available questions completed",
                    "questions_completed": completed_questions,
                    "adaptive_factors": ["question_exhaustion"]
                }
            else:
                return {
                    "action": "error", 
                    "message": f"Failed to select question: {next_question_result.get('error', 'Unknown error')}"
                }
        
        next_question = next_question_result["question"]
        
        # PHASE 4: Initialize question with adaptive context
        current_question = {
            "id": next_question["id"],
            "text": next_question["text"],
            "type": next_question.get("type", "conceptual"),
            "difficulty": next_question.get("difficulty", "medium"),
            "adaptive_difficulty": adaptive_difficulty,  # Phase 4: Track adapted difficulty
            "learning_objectives": next_question.get("learning_objectives", []),
            "conversation_history": [],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "personalization_context": {  # Phase 4: Personalization tracking
                "detected_learning_style": state.get("detected_learning_style", "mixed"),
                "cognitive_load_level": state.get("cognitive_load_level", "moderate"),
                "engagement_trend": state.get("engagement_trend", "stable"),
                "learning_momentum": learning_momentum,
                "adaptation_factors": next_question_result.get("adaptation_factors", [])
            }
        }
        
        state["current_question"] = current_question
        state["current_topic_id"] = topic_id
        
        # PHASE 4: Log adaptive question selection for analytics
        log_adaptive_question_selection(state, current_question, next_question_result)
        
        # Format question presentation with adaptive context
        question_presentation = format_adaptive_question_presentation(current_question, state)
        
        logger.info(f"Adaptive question selected: Q{completed_questions + 1}/{max_questions_per_topic}, "
                   f"difficulty={adaptive_difficulty:.2f}, style={state.get('detected_learning_style', 'mixed')}")
        
        return {
            "action": "present_question",
            "message": question_presentation["content"],
            "question_context": {
                "question_number": completed_questions + 1,
                "total_planned": max_questions_per_topic,
                "topic": topic_data.get("name", "Current Topic"),
                "difficulty_level": adaptive_difficulty,
                "personalization_applied": question_presentation.get("personalization_applied", []),
                "adaptation_reasoning": next_question_result.get("adaptation_reasoning", "Adaptive selection")
            }
        }
        
    except Exception as e:
        logger.error(f"Error in adaptive question_maker_node: {e}")
        return {
            "action": "error",
            "message": "Error selecting next question. Please try again.",
            "error": str(e)
        }


async def evaluate_adaptive_topic_completion(state: GraphState, completed_questions: int, 
                                           max_questions: int, live_performance: Dict, 
                                           learning_momentum: float) -> Dict[str, Any]:
    """Phase 4: Evaluate topic completion with adaptive intelligence"""
    
    # Basic completion check
    if completed_questions >= max_questions:
        return {
            "should_complete": True,
            "reason": f"Reached maximum questions ({max_questions})",
            "adaptive_factors": ["question_limit_reached"]
        }
    
    # No questions completed yet
    if completed_questions == 0:
        return {
            "should_complete": False,
            "reason": "Just starting topic",
            "adaptive_factors": ["initial_question_needed"]
        }
    
    # PHASE 4: Adaptive completion logic based on performance
    session_settings = state.get("session_settings", {})
    performance_threshold = session_settings.get("performance_threshold", 0.85)
    struggle_threshold = session_settings.get("struggle_threshold", 0.3)
    
    # Get performance metrics
    current_understanding = live_performance.get("current_understanding", 0.5)
    performance_trend = live_performance.get("performance_trend", "stable")
    session_average = live_performance.get("session_average", 0.5)
    
    # Early completion for high performers (adaptive)
    if (completed_questions >= 3 and 
        current_understanding >= performance_threshold and 
        session_average >= performance_threshold and
        performance_trend in ["stable", "improving"] and
        learning_momentum > 0.7):
        
        return {
            "should_complete": True,
            "reason": "Strong performance indicates mastery achieved",
            "adaptive_factors": ["high_performance_completion", "strong_momentum"]
        }
    
    # Extended learning for struggling learners (adaptive)
    if (completed_questions >= max_questions * 0.8 and
        current_understanding < struggle_threshold and
        performance_trend == "declining"):
        
        return {
            "should_complete": False,
            "reason": "Extended practice needed for struggling learner",
            "adaptive_factors": ["struggle_detection", "extended_practice"]
        }
    
    # Continue with normal flow
    return {
        "should_complete": False,
        "reason": "Continue with planned question sequence",
        "adaptive_factors": ["normal_progression"]
    }


async def select_adaptive_next_question(user_id: str, topic_id: str, 
                                      completed_questions: List[Dict], 
                                      adaptive_difficulty: float,
                                      learned_preferences: Dict[str, Any],
                                      live_performance: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 4: Select next question using adaptive intelligence"""
    
    try:
        # Get all available questions for topic
        questions_result = await firebase_service.get_topic_questions(user_id, topic_id)
        if not questions_result["success"]:
            return {"success": False, "error": "Failed to retrieve questions"}
        
        available_questions = questions_result["questions"]
        if not available_questions:
            return {"success": False, "reason": "no_more_questions"}
        
        # Filter out already used questions
        used_question_ids = {q.get("question_id") for q in completed_questions}
        unused_questions = [q for q in available_questions if q["id"] not in used_question_ids]
        
        if not unused_questions:
            return {"success": False, "reason": "no_more_questions"}
        
        # PHASE 4: Apply adaptive intelligence to question selection
        optimal_question = await apply_adaptive_question_selection(
            unused_questions, adaptive_difficulty, learned_preferences, 
            live_performance, completed_questions
        )
        
        return {
            "success": True,
            "question": optimal_question["question"],
            "adaptation_reasoning": optimal_question["reasoning"],
            "adaptation_factors": optimal_question["factors"],
            "selection_confidence": optimal_question["confidence"]
        }
        
    except Exception as e:
        logger.error(f"Error in adaptive question selection: {e}")
        return {"success": False, "error": str(e)}


async def apply_adaptive_question_selection(questions: List[Dict], adaptive_difficulty: float,
                                          learned_preferences: Dict[str, Any], 
                                          live_performance: Dict[str, Any],
                                          completed_questions: List[Dict]) -> Dict[str, Any]:
    """Phase 4: Apply AI-powered adaptive question selection algorithms"""
    
    # Analyze question characteristics for matching
    question_analysis = []
    for question in questions:
        difficulty_score = map_difficulty_to_score(question.get("difficulty", "medium"))
        question_type = question.get("type", "conceptual")
        
        # Calculate compatibility with learned preferences
        learning_style = learned_preferences.get("detected_learning_style", "mixed")
        style_compatibility = calculate_style_compatibility(question, learning_style)
        
        # Calculate optimal difficulty match
        difficulty_match = 1.0 - abs(difficulty_score - adaptive_difficulty)
        
        # Calculate question type appropriateness
        type_appropriateness = calculate_type_appropriateness(
            question_type, live_performance, completed_questions
        )
        
        question_analysis.append({
            "question": question,
            "difficulty_match": difficulty_match,
            "style_compatibility": style_compatibility,
            "type_appropriateness": type_appropriateness,
            "overall_score": (difficulty_match * 0.4 + 
                            style_compatibility * 0.3 + 
                            type_appropriateness * 0.3)
        })
    
    # Sort by overall adaptive fitness score
    question_analysis.sort(key=lambda x: x["overall_score"], reverse=True)
    
    # Select best match
    best_match = question_analysis[0]
    
    # Generate adaptation reasoning
    reasoning = f"Selected based on adaptive difficulty match ({best_match['difficulty_match']:.2f}), "
    reasoning += f"learning style compatibility ({best_match['style_compatibility']:.2f}), "
    reasoning += f"and question type appropriateness ({best_match['type_appropriateness']:.2f})"
    
    return {
        "question": best_match["question"],
        "reasoning": reasoning,
        "factors": ["adaptive_difficulty", "learning_style", "question_type"],
        "confidence": best_match["overall_score"]
    }


def map_difficulty_to_score(difficulty: str) -> float:
    """Map difficulty string to numerical score"""
    mapping = {
        "easy": 0.2,
        "medium": 0.5,
        "hard": 0.8,
        "very_hard": 1.0
    }
    return mapping.get(difficulty.lower(), 0.5)


def calculate_style_compatibility(question: Dict, learning_style: str) -> float:
    """Calculate how well question matches user's learning style"""
    if learning_style == "mixed":
        return 0.7  # Good compatibility for mixed style
    
    question_text = question.get("text", "").lower()
    question_type = question.get("type", "").lower()
    
    # Visual learner compatibility
    if learning_style == "visual":
        visual_indicators = ["diagram", "chart", "visualize", "draw", "picture", "graph"]
        if any(indicator in question_text for indicator in visual_indicators):
            return 0.9
        elif question_type in ["visual", "diagram"]:
            return 0.8
        else:
            return 0.5
    
    # Experiential learner compatibility
    elif learning_style == "experiential":
        experiential_indicators = ["example", "real-world", "practice", "scenario", "case"]
        if any(indicator in question_text for indicator in experiential_indicators):
            return 0.9
        elif question_type in ["application", "scenario"]:
            return 0.8
        else:
            return 0.5
    
    # Verbal learner compatibility
    elif learning_style == "verbal":
        verbal_indicators = ["explain", "describe", "discuss", "define"]
        if any(indicator in question_text for indicator in verbal_indicators):
            return 0.9
        elif question_type in ["conceptual", "explanation"]:
            return 0.8
        else:
            return 0.5
    
    return 0.6  # Default compatibility


def calculate_type_appropriateness(question_type: str, live_performance: Dict, 
                                 completed_questions: List[Dict]) -> float:
    """Calculate appropriateness of question type based on performance"""
    
    understanding = live_performance.get("current_understanding", 0.5)
    confidence = live_performance.get("current_confidence", 0.5)
    
    # Count question types completed so far
    completed_types = [q.get("question_type", "conceptual") for q in completed_questions]
    type_counts = {t: completed_types.count(t) for t in set(completed_types)}
    
    # Encourage variety
    variety_bonus = 0.2 if question_type not in completed_types else 0.0
    
    # Type appropriateness based on performance
    if understanding < 0.4:  # Struggling - need conceptual support
        if question_type in ["conceptual", "definition"]:
            return 0.8 + variety_bonus
        else:
            return 0.3 + variety_bonus
    
    elif understanding > 0.8:  # Strong - ready for application
        if question_type in ["application", "analysis", "synthesis"]:
            return 0.9 + variety_bonus
        else:
            return 0.4 + variety_bonus
    
    else:  # Moderate - balanced approach
        return 0.7 + variety_bonus


def format_adaptive_question_presentation(current_question: Dict, state: GraphState) -> Dict[str, Any]:
    """Phase 4: Format question presentation with adaptive personalization"""
    
    question_text = current_question["text"]
    detected_style = state.get("detected_learning_style", "mixed")
    adaptive_difficulty = current_question.get("adaptive_difficulty", 0.5)
    
    # Base presentation
    presentation = f"Here's your next question:\n\n{question_text}"
    
    personalization_applied = []
    
    # Add style-specific enhancements
    if detected_style == "visual":
        presentation += "\n\n💡 *Feel free to describe any diagrams or visualizations that might help with your answer.*"
        personalization_applied.append("visual_enhancement")
    
    elif detected_style == "experiential":
        presentation += "\n\n🌍 *Think about real-world examples or practical applications as you answer.*"
        personalization_applied.append("experiential_enhancement")
    
    elif detected_style == "verbal":
        presentation += "\n\n💬 *Take your time to explain your thinking step by step.*"
        personalization_applied.append("verbal_enhancement")
    
    # Add difficulty context if needed
    if adaptive_difficulty < 0.3:
        presentation += "\n\n🎯 *This question is adapted to provide extra support for your learning.*"
        personalization_applied.append("difficulty_support")
    elif adaptive_difficulty > 0.8:
        presentation += "\n\n🚀 *This question is designed to challenge you based on your strong performance!*"
        personalization_applied.append("difficulty_challenge")
    
    return {
        "content": presentation,
        "personalization_applied": personalization_applied
    }


def log_adaptive_question_selection(state: GraphState, current_question: Dict, 
                                  selection_result: Dict[str, Any]) -> None:
    """Phase 4: Log adaptive question selection for analytics"""
    
    try:
        if "question_adaptation_history" not in state:
            state["question_adaptation_history"] = []
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question_id": current_question["id"],
            "adaptive_difficulty": current_question.get("adaptive_difficulty", 0.5),
            "detected_learning_style": state.get("detected_learning_style", "mixed"),
            "adaptation_reasoning": selection_result.get("adaptation_reasoning", ""),
            "adaptation_factors": selection_result.get("adaptation_factors", []),
            "selection_confidence": selection_result.get("selection_confidence", 0.7),
            "performance_context": state.get("live_performance_metrics", {}).get("current_understanding", 0.5)
        }
        
        state["question_adaptation_history"].append(log_entry)
        
        # Keep history manageable
        if len(state["question_adaptation_history"]) > 20:
            state["question_adaptation_history"] = state["question_adaptation_history"][-20:]
            
    except Exception as e:
        logger.error(f"Error logging adaptive question selection: {e}")


async def enhanced_conversation_node(state: GraphState) -> Dict[str, Any]:
    """
    Phase 4: Real-time adaptive conversation with intelligent personalization
    
    Flow:
    1. Analyze user's response in real-time for adaptation signals
    2. Update live performance metrics and learned preferences  
    3. Determine optimal conversation strategy based on live analysis
    4. Generate adaptive response with personalized teaching approach
    5. Handle user skip/next requests with context awareness
    """
    
    try:
        user_input = state.get("user_input", "")
        current_question = state.get("current_question", {})
        
        if not current_question:
            logger.warning("No current question in enhanced_conversation_node")
            return {"action": "error", "message": "No active question found"}
        
        # Check for user skip signals
        skip_signals = ["skip", "next", "next question", "move on", "skip this"]
        if any(signal in user_input.lower() for signal in skip_signals):
            return handle_skip_request(state)
        
        # Add user response to conversation history
        record_user_response_to_question(state, user_input)
        
        # PHASE 4: Real-time analysis of user response
        live_analysis = await analyze_user_response_live(user_input, state)
        
        # PHASE 4: Update live performance metrics
        update_live_performance_metrics(state, live_analysis)
        
        # PHASE 4: Update learned user preferences
        update_learned_preferences(state, live_analysis)
        
        # PHASE 4: Determine adaptive conversation strategy
        conversation_strategy = await determine_adaptive_conversation_strategy(
            understanding_level=live_analysis["understanding"],
            engagement_level=live_analysis["engagement"],
            confusion_signals=live_analysis.get("confusion_indicators", []),
            user_preferences=state.get("learned_user_preferences", {}),
            conversation_history=current_question.get("conversation_history", [])
        )
        
        # Store conversation intelligence for tracking
        state["conversation_intelligence"] = conversation_strategy
        
        # Calculate adaptive difficulty for potential next question
        adaptive_difficulty = calculate_adaptive_difficulty(
            current_performance=live_analysis,
            historical_data=state.get("question_adaptation_history", []),
            user_profile=state.get("learned_user_preferences", {})
        )
        state["adaptive_difficulty_level"] = adaptive_difficulty
        
        # Determine conversation action using enhanced context
        conversation_decision = await determine_conversation_action_adaptive(
            state, current_question, user_input, live_analysis, conversation_strategy
        )
        
        if conversation_decision["action"] == "continue_conversation":
            # Generate adaptive follow-up response
            follow_up = await generate_adaptive_follow_up(
                state, current_question, user_input, conversation_strategy, live_analysis
            )
            
            # Add AI response to conversation history
            record_ai_response_to_question(state, follow_up["content"])
            
            # Calculate learning momentum
            learning_momentum = calculate_learning_momentum(state)
            state["learning_momentum_score"] = learning_momentum
            
            return {
                "action": "continue_conversation",
                "message": follow_up["content"],
                "reasoning": follow_up.get("reasoning", "Adaptive conversation continuation"),
                "live_analysis": live_analysis,
                "conversation_strategy": conversation_strategy,
                "adaptive_difficulty": adaptive_difficulty,
                "learning_momentum": learning_momentum,
                "conversation_turns": len(current_question.get("conversation_history", []))
            }
            
        elif conversation_decision["action"] == "question_complete":
            # Question conversation is naturally complete
            return {
                "action": "question_complete",
                "completion_reason": conversation_decision.get("reason", "Natural conversation endpoint"),
                "live_analysis": live_analysis,
                "final_understanding": live_analysis["understanding"],
                "conversation_strategy": conversation_strategy,
                "conversation_turns": len(current_question.get("conversation_history", [])),
                "understanding_evidence": conversation_decision.get("completion_evidence", "Sufficient understanding demonstrated")
            }
        
        else:
            # Fallback to continue
            return {
                "action": "continue_conversation",
                "message": "Can you tell me more about that?",
                "reasoning": "Fallback response for unclear conversation state",
                "live_analysis": live_analysis
            }
            
    except Exception as e:
        logger.error(f"Error in enhanced_conversation_node: {e}")
        return {
            "action": "error",
            "message": "Error processing conversation. Please try again.",
            "error": str(e)
        }


async def determine_conversation_action_adaptive(state: GraphState, current_question: Dict, 
                                               user_input: str, live_analysis: Dict[str, Any],
                                               conversation_strategy: Dict[str, Any]) -> Dict:
    """Phase 4: Enhanced conversation action determination with adaptive context"""
    
    conversation_history = current_question.get("conversation_history", [])
    question_text = current_question.get("text", "")
    understanding = live_analysis.get("understanding", 0.5)
    confidence = live_analysis.get("confidence", 0.5)
    
    # Format conversation for LLM analysis
    formatted_history = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""
You are analyzing a conversation between an AI tutor and student about a specific question with advanced adaptive intelligence.

QUESTION: {question_text}
CONVERSATION HISTORY:
{formatted_history}

LATEST USER RESPONSE: {user_input}

LIVE ANALYSIS INSIGHTS:
- Understanding Level: {understanding:.2f}/1.0
- Confidence Level: {confidence:.2f}/1.0  
- Response Quality: {live_analysis.get('response_quality_score', 0.5):.2f}/1.0
- Cognitive Load: {live_analysis.get('cognitive_load', 'moderate')}
- Key Insights: {live_analysis.get('key_insights', [])}

ADAPTIVE STRATEGY CONTEXT:
- Teaching Strategy: {conversation_strategy.get('teaching_strategy', 'unknown')}
- Difficulty Adjustment: {conversation_strategy.get('difficulty_adjustment', 'unknown')}
- Engagement Tactics: {conversation_strategy.get('engagement_tactics', [])}

Determine if this conversation about this specific question should:
1. CONTINUE - More discussion needed (unclear answer, opportunity for deeper exploration, natural flow suggests more)
2. COMPLETE - Natural endpoint reached (solid understanding demonstrated, user signals readiness, sufficient exploration)

Consider the adaptive context:
- Real-time understanding and confidence levels
- Quality and completeness of user's demonstrated knowledge
- Natural conversation flow and momentum 
- User signals about readiness to continue
- Teaching opportunities for deeper learning
- Length of conversation (avoid dragging unnecessarily)
- Adaptive strategy effectiveness

Return JSON:
{{
    "action": "continue_conversation|question_complete",
    "reasoning": "Why this decision was made based on adaptive analysis",
    "follow_up_focus": "What to explore next (if continuing)",
    "completion_evidence": "What shows understanding is sufficient (if complete)",
    "confidence_score": 0.85,
    "adaptive_factors": ["factor1", "factor2"]
}}
"""

    try:
        response = call_ai_with_json_output(prompt)
        
        # Validate response
        if not response.get("action") or response["action"] not in ["continue_conversation", "question_complete"]:
            response["action"] = "continue_conversation"  # Default to continue
        
        response.setdefault("reasoning", "Continuing adaptive conversation flow")
        response.setdefault("follow_up_focus", "understanding")
        response.setdefault("completion_evidence", "")
        response.setdefault("confidence_score", 0.7)
        response.setdefault("adaptive_factors", ["live_analysis_integration"])
        
        return response
        
    except Exception as e:
        logger.error(f"Error determining adaptive conversation action: {e}")
        return {
            "action": "continue_conversation",
            "reasoning": "Fallback due to adaptive analysis error",
            "follow_up_focus": "clarification",
            "adaptive_factors": ["fallback_heuristic"]
        }


async def generate_adaptive_follow_up(state: GraphState, current_question: Dict, user_input: str, 
                                    conversation_strategy: Dict[str, Any], live_analysis: Dict[str, Any]) -> Dict:
    """Phase 4: Generate adaptive follow-up response with personalized teaching approach"""
    
    conversation_history = current_question.get("conversation_history", [])
    question_text = current_question.get("text", "")
    
    # Format conversation for context
    formatted_history = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history[-6:]  # Last 6 messages for context
    ])
    
    # Get learned user preferences for personalization
    learned_preferences = state.get("learned_user_preferences", {})
    detected_learning_style = state.get("detected_learning_style", "mixed")
    
    prompt = f"""
You are an expert AI tutor with advanced adaptive intelligence, generating a personalized follow-up response based on real-time learning analysis.

ORIGINAL QUESTION: {question_text}
RECENT CONVERSATION:
{formatted_history}

LATEST USER RESPONSE: {user_input}

LIVE ANALYSIS:
- Understanding: {live_analysis.get('understanding', 0.5):.2f}/1.0
- Confidence: {live_analysis.get('confidence', 0.5):.2f}/1.0  
- Engagement: {live_analysis.get('engagement', 0.5):.2f}/1.0
- Cognitive Load: {live_analysis.get('cognitive_load', 'moderate')}
- Confusion Indicators: {live_analysis.get('confusion_indicators', [])}

ADAPTIVE STRATEGY:
- Teaching Strategy: {conversation_strategy.get('teaching_strategy', 'socratic_questioning')}
- Difficulty Adjustment: {conversation_strategy.get('difficulty_adjustment', 'maintain_current')}
- Conversation Style: {conversation_strategy.get('conversation_style', {})}
- Engagement Tactics: {conversation_strategy.get('engagement_tactics', [])}

PERSONALIZATION CONTEXT:
- Detected Learning Style: {detected_learning_style}
- Learned Preferences: {json.dumps(learned_preferences, indent=2) if learned_preferences else 'None yet'}
- Current Understanding Velocity: {state.get('understanding_velocity', 'unknown')}

Generate an adaptive, personalized follow-up response that:

1. Responds specifically to what the student just said with adaptive intelligence
2. Applies the recommended teaching strategy: {conversation_strategy.get('teaching_strategy', 'socratic_questioning')}
3. Adjusts difficulty as recommended: {conversation_strategy.get('difficulty_adjustment', 'maintain_current')}
4. Uses personalized conversation style based on their learning preferences
5. Maintains natural conversation flow while optimizing for learning
6. Addresses any confusion indicators: {live_analysis.get('confusion_indicators', [])}

Adaptive Response Guidelines:
- If understanding is LOW (<0.4): Provide more scaffolding and support
- If understanding is HIGH (>0.8): Increase challenge and depth
- If engagement is LOW (<0.4): Use curiosity and relevance tactics
- If engagement is HIGH (>0.8): Maintain momentum with challenging questions
- Adapt to their detected learning style: {detected_learning_style}

Your response should feel like a brilliant, adaptive tutor who understands this specific learner perfectly.

Return JSON:
{{
    "content": "Your adaptive, personalized follow-up response",
    "reasoning": "Why you chose this specific approach based on live analysis",
    "teaching_technique": "The pedagogical approach being used",
    "personalization_applied": ["specific adaptations made"],
    "adaptive_factors": ["factors from live analysis that influenced response"]
}}
"""

    try:
        response = call_ai_with_json_output(prompt)
        
        if not response.get("content"):
            response["content"] = "That's interesting! Can you tell me more about that?"
        
        response.setdefault("reasoning", "Adaptive response based on live analysis")
        response.setdefault("teaching_technique", "adaptive_questioning")
        response.setdefault("personalization_applied", ["learning_style_adaptation"])
        response.setdefault("adaptive_factors", ["understanding_level", "engagement_level"])
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating adaptive follow-up: {e}")
        return {
            "content": "Can you elaborate on that a bit more?",
            "reasoning": "Fallback response due to generation error",
            "teaching_technique": "clarification_request",
            "personalization_applied": [],
            "adaptive_factors": ["fallback_heuristic"]
        }


async def question_summary_node(state: GraphState) -> Dict[str, Any]:
    """
    Phase 2: Generate teaching evaluation summary for completed question
    
    Flow:
    1. Analyze the complete question conversation
    2. Generate teaching-style evaluation summary
    3. Store summary for later topic evaluation
    4. Determine if more questions needed or topic complete
    """
    from .firebase_service import QuestionBankService
    
    try:
        current_question = state.get("current_question", {})
        current_topic = get_current_topic(state)
        user_id = state.get("user_id", "default_user")
        topic_id = state.get("current_topic_id", current_topic.lower().replace(' ', '_'))
        
        if not current_question or not current_topic:
            logger.warning("No current question or topic in question_summary_node")
            return {"action": "error", "message": "No active question to summarize"}
        
        # Generate comprehensive question evaluation
        question_evaluation = await evaluate_question_conversation(state, current_question)
        
        # Store question summary locally in state
        topic_summaries = state.get("topic_question_summaries", [])
        summary_data = {
            "question_id": current_question["id"],
            "question_text": current_question["text"],
            "conversation_turns": len(current_question.get("conversation_history", [])),
            "summary": question_evaluation["summary"],
            "performance_level": question_evaluation["performance_level"],
            "areas_of_strength": question_evaluation["areas_of_strength"],
            "areas_for_improvement": question_evaluation["areas_for_improvement"],
            "teaching_moments": question_evaluation["teaching_moments"],
            "understanding_depth": question_evaluation.get("understanding_depth", "moderate"),
            "engagement_quality": question_evaluation.get("engagement_quality", "good"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        topic_summaries.append(summary_data)
        state["topic_question_summaries"] = topic_summaries
        
        # Store summary in Firebase for persistence
        question_service = QuestionBankService()
        await question_service.store_question_summary(
            user_id, topic_id, current_question["id"], summary_data
        )
        
        # Mark question as used in Firebase
        await question_service.mark_question_used(user_id, topic_id, current_question["id"])
        
        # Clear current question from state
        state["current_question"] = None
        
        # Determine next action based on session settings
        questions_answered = len(topic_summaries)
        max_questions = state.get("session_settings", {}).get("max_questions_per_topic", 7)
        
        # Check if user requested to move to next topic
        last_user_input = state.get("user_input", "").lower()
        next_topic_signals = ["next topic", "move to next", "next subject", "done with this topic"]
        user_wants_next_topic = any(signal in last_user_input for signal in next_topic_signals)
        
        logger.info(f"Topic {current_topic}: {questions_answered}/{max_questions} questions completed")
        
        if questions_answered >= max_questions or user_wants_next_topic:
            return {
                "action": "topic_complete",
                "questions_completed": questions_answered,
                "summary": question_evaluation["summary"],
                "performance_level": question_evaluation["performance_level"],
                "completion_reason": "max_questions_reached" if questions_answered >= max_questions else "user_requested"
            }
        else:
            return {
                "action": "next_question",
                "questions_completed": questions_answered,
                "summary": question_evaluation["summary"],
                "performance_level": question_evaluation["performance_level"]
            }
            
    except Exception as e:
        logger.error(f"Error in question_summary_node: {e}")
        return {
            "action": "error",
            "message": "Error summarizing question. Please try again.",
            "error": str(e)
        }


async def enhanced_scoring_node(state: GraphState) -> Dict[str, Any]:
    """
    Phase 2: Aggregate question summaries and provide topic-level FSRS score
    
    Flow:
    1. Collect all question summaries for current topic
    2. Generate comprehensive topic evaluation using LLM
    3. Calculate FSRS score and update Firebase
    4. Determine session continuation
    """
    from .firebase_service import firebase_service
    
    try:
        current_topic = get_current_topic(state)
        question_summaries = state.get("topic_question_summaries", [])
        user_id = state.get("user_id", "default_user")
        
        if not current_topic:
            logger.warning("No current topic in enhanced_scoring_node")
            return {"action": "session_complete", "message": "No topic to score"}
        
        if not question_summaries:
            logger.warning(f"No question summaries for topic {current_topic}")
            # Provide default scoring if no questions were completed
            topic_score = 3  # Neutral score
        else:
            # Generate comprehensive topic evaluation from summaries
            topic_evaluation = await generate_topic_evaluation_from_summaries(current_topic, question_summaries)
            topic_score = topic_evaluation["fsrs_score"]
            
            # Store topic evaluation in state
            topic_evaluations = state.get("topic_evaluations", {})
            topic_evaluations[current_topic] = topic_evaluation
            state["topic_evaluations"] = topic_evaluations
        
        # Update Firebase with score if this is a due item
        session_type = state.get("session_type", "custom_topics")
        if session_type == "due_items" and user_id != "default_user":
            try:
                await firebase_service.update_task_after_review(
                    user_id, 
                    current_topic, 
                    topic_score,
                    {
                        "session_type": session_type,
                        "question_types": [summary.get("question_type", "conversational") for summary in question_summaries],
                        "questions_completed": len(question_summaries),
                        "topic_evaluation": topic_evaluation if question_summaries else None
                    }
                )
                logger.info(f"Updated Firebase score for {current_topic}: {topic_score}")
            except Exception as e:
                logger.error(f"Error updating Firebase score: {e}")
        
        # Update topic scores in state
        topic_scores = state.get("topic_scores", {})
        topic_scores[current_topic] = topic_score
        state["topic_scores"] = topic_scores
        
        # Move to next topic
        advance_to_next_topic(state)
        
        # Clear question summaries for next topic
        state["topic_question_summaries"] = []
        
        # Determine next action
        remaining_topics = get_remaining_topics(state)
        
        if remaining_topics:
            next_topic = remaining_topics[0] if remaining_topics else None
            logger.info(f"Moving to next topic: {next_topic}")
            return {
                "action": "next_topic",
                "topic_completed": current_topic,
                "topic_score": topic_score,
                "next_topic": next_topic,
                "questions_completed": len(question_summaries),
                "remaining_topics": len(remaining_topics)
            }
        else:
            logger.info("All topics completed, ending session")
            return {
                "action": "session_complete",
                "final_topic": current_topic,
                "topic_score": topic_score,
                "questions_completed": len(question_summaries),
                "total_topics_completed": len(state.get("topic_scores", {}))
            }
            
    except Exception as e:
        logger.error(f"Error in enhanced_scoring_node: {e}")
        return {
            "action": "error",
            "message": "Error scoring topic. Please try again.",
            "error": str(e)
        }


# ================================================================================================
# PHASE 2: SUPPORTING FUNCTIONS
# ================================================================================================

def handle_skip_request(state: GraphState) -> Dict[str, Any]:
    """Handle user request to skip current question"""
    return {
        "action": "question_complete",
        "completion_reason": "user_skip",
        "message": "Skipping this question as requested."
    }


def record_user_response_to_question(state: GraphState, user_input: str) -> None:
    """Record user's response in the current question's conversation history"""
    current_question = state.get("current_question", {})
    if not current_question:
        return
    
    conversation_history = current_question.get("conversation_history", [])
    conversation_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    current_question["conversation_history"] = conversation_history
    state["current_question"] = current_question


def record_ai_response_to_question(state: GraphState, ai_response: str) -> None:
    """Record AI's response in the current question's conversation history"""
    current_question = state.get("current_question", {})
    if not current_question:
        return
    
    conversation_history = current_question.get("conversation_history", [])
    conversation_history.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    current_question["conversation_history"] = conversation_history
    state["current_question"] = current_question


async def determine_conversation_action(state: GraphState, current_question: Dict, user_input: str) -> Dict:
    """Use LLM to determine if conversation should continue or complete"""
    
    conversation_history = current_question.get("conversation_history", [])
    question_text = current_question.get("text", "")
    
    # Format conversation for LLM analysis
    formatted_history = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""
You are analyzing a conversation between an AI tutor and student about a specific question.

QUESTION: {question_text}
CONVERSATION HISTORY:
{formatted_history}

LATEST USER RESPONSE: {user_input}

Determine if this conversation about this specific question should:
1. CONTINUE - More discussion needed (unclear answer, opportunity for deeper exploration, natural flow suggests more)
2. COMPLETE - Natural endpoint reached (solid understanding demonstrated, user signals readiness, sufficient exploration)

Consider:
- Quality and completeness of user's understanding shown
- Natural conversation flow and momentum 
- User signals about readiness to continue
- Teaching opportunities for deeper learning
- Length of conversation (avoid dragging it out unnecessarily)

Return JSON:
{{
    "action": "continue_conversation|question_complete",
    "reasoning": "Why this decision was made",
    "follow_up_focus": "What to explore next (if continuing)",
    "completion_evidence": "What shows understanding is sufficient (if complete)"
}}
"""

    try:
        response = call_ai_with_json_output(prompt)
        
        # Validate response
        if not response.get("action") or response["action"] not in ["continue_conversation", "question_complete"]:
            response["action"] = "continue_conversation"  # Default to continue
        
        response.setdefault("reasoning", "Continuing natural conversation flow")
        response.setdefault("follow_up_focus", "understanding")
        response.setdefault("completion_evidence", "")
        
        return response
        
    except Exception as e:
        logger.error(f"Error determining conversation action: {e}")
        return {
            "action": "continue_conversation",
            "reasoning": "Fallback due to analysis error",
            "follow_up_focus": "clarification"
        }


async def evaluate_question_conversation(state: GraphState, current_question: Dict) -> Dict:
    """Generate comprehensive evaluation of a completed question conversation"""
    
    conversation_history = current_question.get("conversation_history", [])
    question_text = current_question.get("text", "")
    question_type = current_question.get("question_type", "conversational")
    
    # Format conversation for analysis
    formatted_conversation = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""
You are an expert educational evaluator analyzing a completed conversation between an AI tutor and student.

QUESTION: {question_text}
QUESTION TYPE: {question_type}
COMPLETE CONVERSATION:
{formatted_conversation}

Provide a comprehensive teaching evaluation summary focusing on:

1. **Overall Performance**: How well did the student demonstrate understanding?
2. **Areas of Strength**: What did they do well? What concepts did they grasp clearly?
3. **Areas for Improvement**: What could be developed further? Any misconceptions?
4. **Teaching Moments**: Key insights or learning opportunities that emerged
5. **Understanding Depth**: How deep was their comprehension? (surface/moderate/deep)
6. **Engagement Quality**: How engaged and thoughtful were their responses?

This evaluation will be used to aggregate topic-level understanding, so be specific and actionable.

Return JSON:
{{
    "summary": "1-2 sentence overall performance summary",
    "performance_level": "excellent|good|satisfactory|needs_improvement|poor",
    "areas_of_strength": ["specific strength 1", "specific strength 2"],
    "areas_for_improvement": ["specific area 1", "specific area 2"],
    "teaching_moments": ["insight 1", "insight 2"],
    "understanding_depth": "surface|moderate|deep",
    "engagement_quality": "excellent|good|moderate|low",
    "misconceptions_identified": ["misconception 1", "misconception 2"],
    "learning_evidence": "Specific evidence of learning that occurred"
}}
"""

    try:
        response = call_ai_with_json_output(prompt)
        
        # Validate and provide defaults
        response.setdefault("summary", "Student engaged with the topic appropriately")
        response.setdefault("performance_level", "satisfactory")
        response.setdefault("areas_of_strength", ["participated in discussion"])
        response.setdefault("areas_for_improvement", ["could explore topic further"])
        response.setdefault("teaching_moments", ["opportunity for deeper learning"])
        response.setdefault("understanding_depth", "moderate")
        response.setdefault("engagement_quality", "good")
        response.setdefault("misconceptions_identified", [])
        response.setdefault("learning_evidence", "Engaged in meaningful dialogue about the topic")
        
        return response
        
    except Exception as e:
        logger.error(f"Error evaluating question conversation: {e}")
        return {
            "summary": "Completed conversation about the topic",
            "performance_level": "satisfactory",
            "areas_of_strength": ["engaged with material"],
            "areas_for_improvement": ["continue exploring concepts"],
            "teaching_moments": ["opportunity for deeper learning"],
            "understanding_depth": "moderate",
            "engagement_quality": "good",
            "misconceptions_identified": [],
            "learning_evidence": "Participated in educational conversation"
        }


async def generate_topic_evaluation_from_summaries(current_topic: str, question_summaries: List[Dict]) -> Dict:
    """Generate comprehensive topic evaluation by aggregating question summaries"""
    
    if not question_summaries:
        # Default evaluation for topics with no completed questions
        return {
            "topic": current_topic,
            "fsrs_score": 3,
            "overall_performance": "incomplete",
            "summary": "Topic was not fully explored due to no completed questions",
            "strengths": [],
            "improvements": [],
            "understanding_level": 2.5,
            "questions_completed": 0
        }
    
    # Format summaries for LLM analysis
    formatted_summaries = "\n\n".join([
        f"QUESTION {i+1}: {summary['question_text']}\n"
        f"Performance: {summary['performance_level']}\n"
        f"Summary: {summary['summary']}\n"
        f"Strengths: {', '.join(summary['areas_of_strength'])}\n"
        f"Improvements: {', '.join(summary['areas_for_improvement'])}\n"
        f"Understanding Depth: {summary.get('understanding_depth', 'moderate')}"
        for i, summary in enumerate(question_summaries)
    ])
    
    prompt = f"""
You are an expert educational evaluator aggregating individual question performances into a comprehensive topic evaluation.

TOPIC: {current_topic}
QUESTIONS COMPLETED: {len(question_summaries)}

INDIVIDUAL QUESTION SUMMARIES:
{formatted_summaries}

Based on the student's performance across all questions for this topic, provide:

1. **Overall Topic Understanding**: Aggregate performance level
2. **FSRS Score**: Integer 0-5 for spaced repetition (0=failed, 1=hard, 2=good, 3=easy, 4=very easy, 5=perfect)
3. **Comprehensive Summary**: Overall performance across all questions
4. **Aggregated Strengths**: Common strengths across questions
5. **Areas for Development**: Patterns of improvement areas
6. **Understanding Level**: Numerical 0-5 representing depth of comprehension

Consider:
- Consistency across questions
- Depth of understanding demonstrated
- Quality of engagement
- Evidence of learning progression
- Readiness for spaced repetition intervals

Return JSON:
{{
    "topic": "{current_topic}",
    "fsrs_score": 0-5,
    "overall_performance": "excellent|good|satisfactory|needs_improvement|poor",
    "summary": "Comprehensive 2-3 sentence evaluation summary",
    "strengths": ["aggregated strength 1", "aggregated strength 2"],
    "improvements": ["development area 1", "development area 2"],
    "understanding_level": 0.0-5.0,
    "questions_completed": {len(question_summaries)},
    "consistency_across_questions": "high|moderate|low",
    "learning_progression_observed": "strong|moderate|minimal|none",
    "readiness_for_review": "ready|needs_reinforcement|requires_reteaching"
}}
"""

    try:
        response = call_ai_with_json_output(prompt)
        
        # Validate FSRS score
        fsrs_score = response.get("fsrs_score", 3)
        if not isinstance(fsrs_score, int) or fsrs_score < 0 or fsrs_score > 5:
            fsrs_score = 3
        response["fsrs_score"] = fsrs_score
        
        # Validate understanding level
        understanding_level = response.get("understanding_level", 3.0)
        if not isinstance(understanding_level, (int, float)) or understanding_level < 0 or understanding_level > 5:
            understanding_level = 3.0
        response["understanding_level"] = float(understanding_level)
        
        # Provide defaults
        response.setdefault("topic", current_topic)
        response.setdefault("overall_performance", "satisfactory")
        response.setdefault("summary", f"Student completed {len(question_summaries)} questions on {current_topic}")
        response.setdefault("strengths", ["engaged with topic material"])
        response.setdefault("improvements", ["continue practicing concepts"])
        response.setdefault("questions_completed", len(question_summaries))
        response.setdefault("consistency_across_questions", "moderate")
        response.setdefault("learning_progression_observed", "moderate")
        response.setdefault("readiness_for_review", "ready")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating topic evaluation: {e}")
        return {
            "topic": current_topic,
            "fsrs_score": 3,
            "overall_performance": "satisfactory",
            "summary": f"Completed {len(question_summaries)} questions on {current_topic}",
            "strengths": ["participated in topic discussion"],
            "improvements": ["continue practicing concepts"],
            "understanding_level": 3.0,
            "questions_completed": len(question_summaries),
            "consistency_across_questions": "moderate",
            "learning_progression_observed": "moderate",
            "readiness_for_review": "ready"
        }
