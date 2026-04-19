# Diagnostic Endpoints - Complete API Reference

## Overview

The Diagnostic System is an intelligent learning assistant that analyzes student input to identify learning challenges and provide personalized improvement recommendations. It uses a **multi-agent architecture** with text classification, topic extraction, and recommendation generation.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│             STUDENT INPUT (textarea)                 │
└────────────────────┬────────────────────────────────┘
                     ↓
         ┌──────────────────────────┐
         │ Text Classifier Agent    │
         │ (weakness|confusion|     │
         │  progression|irrelevant) │
         └────────┬─────────────────┘
                  ↓
         ┌──────────────────────────┐
         │ Topic Extractor Agent    │
         │ (Identify topics from    │
         │  student input + RAG)    │
         └────────┬─────────────────┘
                  ↓
         ┌──────────────────────────┐
         │ Recommendation Engine    │
         │ (Generate structured    │
         │  improvement plan)      │
         └────────┬─────────────────┘
                  ↓
     ┌───────────────────────────────────────┐
     │ PERSONALIZED RECOMMENDATIONS          │
     │ • Weakness identified                 │
     │ • Root cause analysis                 │
     │ • Step-by-step improvement plan       │
     │ • Study strategies                    │
     │ • Related resources (quiz/chat)       │
     └───────────────────────────────────────┘
```

## Core Features

### 1. **Intelligent Text Classification**
- Classifies input into: `weakness`, `confusion`, `progression`, or `irrelevant`
- Returns confidence score (0.0-1.0)
- Automatic fallback for irrelevant inputs with canned response

### 2. **Topic Extraction**
- Extracts 1-5 relevant topics from free-form student input
- Uses LLM + RAG to identify related chapters/concepts
- Handles vague or incomplete descriptions

### 3. **Personalized Recommendations**
- Identifies specific weakness or learning gap
- Analyzes root causes
- Provides structured improvement plan with steps
- Suggests proven study strategies
- Defines success metrics and timeline

### 4. **Resource Integration**
- Links to related Quiz topics
- Suggests Chat discussions
- Points to Flashcard sets
- All integrated with existing learning platform

## API Endpoints

### 1. POST `/api/diagnostic/analyze`

**Main diagnostic analysis endpoint**

#### Request
```json
{
  "input_text": "I'm really struggling with understanding circuits and I don't know how current flows through resistors",
  "session_id": "optional-session-id"
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_text` | string | Yes | Student's learning concern (10-2000 chars) |
| `session_id` | string | No | Optional session ID for tracking |

#### Response (Success)
```json
{
  "classification": "weakness",
  "confidence": 0.95,
  "status": "success",
  "identified_topics": ["Electric Circuits", "Current Flow", "Resistance"],
  "recommendation": {
    "weakness_identified": "Student struggles with understanding current flow through resistive circuits",
    "root_cause": "Likely missing conceptual understanding of voltage-current relationship",
    "severity": "medium",
    "improvement_steps": [
      {
        "step": 1,
        "title": "Review Fundamental Concepts",
        "description": "Start by understanding what electric current is at the atomic level",
        "resources": ["Chapter 2.1: Current Basics", "Video: What is Electric Current"],
        "estimated_time": "1-2 hours"
      },
      {
        "step": 2,
        "title": "Learn Ohm's Law",
        "description": "Understand the relationship between voltage, current, and resistance (V = IR)",
        "resources": ["Chapter 2.2: Ohm's Law", "Interactive Simulator"],
        "estimated_time": "1-2 hours"
      },
      {
        "step": 3,
        "title": "Practice Simple Calculations",
        "description": "Solve basic circuit problems using Ohm's Law",
        "resources": ["Practice Quiz: Ohm's Law", "Worked Examples"],
        "estimated_time": "1 hour"
      },
      {
        "step": 4,
        "title": "Analyze Complex Circuits",
        "description": "Apply concepts to more complex circuit configurations",
        "resources": ["Chapter 3: Circuit Analysis", "Advanced Problems"],
        "estimated_time": "2-3 hours"
      }
    ],
    "study_strategies": [
      {
        "strategy": "Active Recall",
        "description": "Test yourself on concepts without looking at notes",
        "implementation": "Close your textbook and try to explain current flow from memory, then verify"
      },
      {
        "strategy": "Spaced Repetition",
        "description": "Review material at increasing intervals",
        "implementation": "Review today, then 3 days later, then 1 week later, then 2 weeks"
      },
      {
        "strategy": "Feynman Technique",
        "description": "Explain concepts in simple language as if teaching someone else",
        "implementation": "Write a simple explanation of Ohm's Law like you're teaching a 10-year-old"
      },
      {
        "strategy": "Problem-Based Learning",
        "description": "Start with real problems and work backwards to theory",
        "implementation": "Solve actual circuit problems, then read theory to understand why"
      }
    ],
    "timeline": "1-2 weeks for solid understanding",
    "success_metrics": [
      "Score 80%+ on practice quiz on Ohm's Law",
      "Correctly solve 5 different circuit problems",
      "Explain current flow concept to study group peer",
      "Complete advanced circuit analysis assignment"
    ],
    "key_concepts": ["Current", "Voltage", "Resistance", "Ohm's Law", "Circuit Analysis"]
  },
  "related_resources": [
    {
      "type": "quiz",
      "title": "Quiz on Electric Circuits",
      "link": "/api/quiz/generate?topic=Electric%20Circuits",
      "description": "Test your knowledge"
    },
    {
      "type": "chat",
      "title": "Learn about Circuits",
      "link": "/api/chat/ask",
      "description": "Chat with tutor about Circuits"
    },
    {
      "type": "flashcard",
      "title": "Flashcards for Circuit Basics",
      "link": "/flashcards.html",
      "description": "Practice key terms and concepts"
    }
  ],
  "session_id": "diag-abc123",
  "timestamp": "2026-04-17T10:30:00"
}
```

#### Response (Irrelevant/Canned)
```json
{
  "classification": "irrelevant",
  "confidence": 0.85,
  "status": "canned_response",
  "identified_topics": [],
  "canned_response": "Sorry, I'm unable to provide answers on this topic. Please ask something related to your coursework or learning goals.",
  "related_resources": [],
  "session_id": "diag-def456",
  "timestamp": "2026-04-17T10:31:00"
}
```

#### Error Response
```json
{
  "detail": "Input text must be at least 10 characters long"
}
```

---

### 2. GET `/api/diagnostic/history/{session_id}`

**Retrieve diagnostic analysis history for a session**

#### Parameters
| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| `session_id` | string | URL | Session identifier |

#### Response
```json
{
  "session_id": "diag-abc123",
  "records": [
    {
      "input": "I'm struggling with circuits...",
      "classification": "weakness",
      "timestamp": "2026-04-17T10:30:00"
    },
    {
      "input": "I'm confused about Ohm's law",
      "classification": "confusion",
      "timestamp": "2026-04-17T11:00:00"
    }
  ],
  "total": 2
}
```

---

### 3. POST `/api/diagnostic/feedback`

**Submit feedback on diagnostic recommendations**

#### Request
```json
{
  "session_id": "diag-abc123",
  "feedback_text": "The recommendations were very helpful and I've already started on step 1",
  "helpful": true
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session identifier |
| `feedback_text` | string | Yes | User's feedback |
| `helpful` | boolean | Yes | Was the recommendation helpful? |

#### Response
```json
{
  "status": "success",
  "message": "Thank you for your feedback!",
  "session_id": "diag-abc123",
  "timestamp": "2026-04-17T10:35:00"
}
```

---

### 4. GET `/api/diagnostic/health`

**Health check for diagnostic service**

#### Response
```json
{
  "status": "healthy",
  "service": "diagnostic",
  "timestamp": "2026-04-17T10:30:00"
}
```

---

### 5. POST `/api/diagnostic/test`

**Test the diagnostic system (for debugging)**

#### Response
```json
{
  "status": "success",
  "test_input": "I'm really struggling with understanding how circuits work...",
  "classification": "weakness",
  "confidence": 0.92,
  "identified_topics": ["Electric Circuits", "Current Flow"],
  "recommendation_exists": true,
  "message": "Diagnostic system is working correctly"
}
```

---

## Classification Types

### 1. **WEAKNESS** 
- Student identifies specific topic/concept they struggle with
- Example: "I don't understand photosynthesis"
- Response: Detailed improvement plan with steps

### 2. **CONFUSION**
- Student expresses confusion about a concept
- Example: "Why do we need both light and dark reactions?"
- Response: Explanation + improvement strategies

### 3. **PROGRESSION**
- Student shares learning progress or improvement
- Example: "I've been getting better at solving equations"
- Response: Suggestions for next level learning

### 4. **IRRELEVANT**
- Input unrelated to studies/learning
- Example: "What's the weather like?"
- Response: Canned response redirecting to study topics

---

## Request Examples

### Using JavaScript (Frontend)

```javascript
// Basic diagnostic call
const result = await analyzeDiagnostic(
  "I'm really confused about how photosynthesis works. I understand the light reactions but I can't grasp the Calvin cycle."
);

// With session ID
const result = await analyzeDiagnostic(
  "I struggle with quadratic equations",
  "user-session-123"
);

// Get history
const history = await getDiagnosticHistory("user-session-123");

// Submit feedback
await submitDiagnosticFeedback(
  "diag-abc123",
  "Very helpful! I'm already on step 2",
  true
);
```

### Using cURL

```bash
# Analyze diagnostic input
curl -X POST http://localhost:8000/api/diagnostic/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "input_text": "I struggle with understanding circuits",
    "session_id": "user-123"
  }'

# Get history
curl -X GET http://localhost:8000/api/diagnostic/history/user-123 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Submit feedback
curl -X POST http://localhost:8000/api/diagnostic/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "session_id": "diag-abc123",
    "feedback_text": "Very helpful recommendations",
    "helpful": true
  }'

# Health check
curl http://localhost:8000/api/diagnostic/health
```

---

## Response Structure Details

### Recommendation Object

```json
{
  "weakness_identified": "String describing the identified weakness",
  "root_cause": "Analysis of why this weakness exists",
  "severity": "low | medium | high",
  "improvement_steps": [
    {
      "step": 1,
      "title": "Step title",
      "description": "Detailed description of what to do",
      "resources": ["Resource 1", "Resource 2"],
      "estimated_time": "1-2 hours"
    }
  ],
  "study_strategies": [
    {
      "strategy": "Strategy name",
      "description": "How the strategy works",
      "implementation": "Specific steps to implement"
    }
  ],
  "timeline": "Expected time frame for improvement",
  "success_metrics": ["Metric 1", "Metric 2"],
  "key_concepts": ["Concept 1", "Concept 2"]
}
```

### Related Resources

```json
{
  "type": "quiz | chat | flashcard",
  "title": "Resource title",
  "link": "URL or endpoint",
  "description": "What this resource offers"
}
```

---

## Data Flow

```
1. Student fills diagnostic textarea
   ↓
2. Frontend sends to POST /api/diagnostic/analyze
   ↓
3. Backend:
   a. Text Classifier → Classify input type + confidence
   b. Topic Extractor → Extract relevant topics
   c. Check if irrelevant → Return canned response if needed
   d. Recommendation Engine → Generate improvement plan
   e. Resource Linker → Get related quiz/chat/flashcard resources
   ↓
4. Response returned with full recommendations
   ↓
5. Frontend displays:
   - Classification badge
   - Identified topics
   - Improvement steps
   - Study strategies
   - Related resources
   - Feedback buttons
   ↓
6. Student can submit feedback or click resources
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Analysis complete |
| 400 | Bad request | Input too short |
| 401 | Unauthorized | Token missing/invalid |
| 500 | Server error | LLM API failure |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Performance Characteristics

### Typical Response Time

| Component | Time |
|-----------|------|
| Text Classification | 500-1000ms |
| Topic Extraction | 300-800ms |
| Recommendation Generation | 1000-3000ms |
| Resource Discovery | 100-200ms |
| **Total** | **1.9-5.0 seconds** |

### Rate Limiting
- No rate limit currently implemented
- Can be added at `/api/diagnostic/analyze` endpoint

---

## Best Practices

### For Students
1. **Be specific** - Describe exactly what you're struggling with
2. **Provide context** - Mention the topic or chapter
3. **Share your attempt** - Describe what you've already tried
4. **Use examples** - "I don't understand how X works in Y situation"

### For Developers
1. **Store session_id** - Track user sessions for history
2. **Collect feedback** - Use feedback to improve LLM prompts
3. **Monitor latency** - Log response times for optimization
4. **Handle errors** - Always provide user-friendly error messages
5. **Cache results** - Consider caching recommendations for similar inputs

---

## Example Workflow

### Student Scenario 1: Topic Weakness

**Student Input:**
```
"I'm really struggling with understanding the concept of photosynthesis. 
I can memorize the equation but I don't understand why plants need light 
and where the oxygen comes from."
```

**Classification:** `weakness` (confidence: 0.96)

**Identified Topics:** ["Photosynthesis", "Plant Biology", "Cellular Respiration"]

**Recommendation Includes:**
- Root cause: Missing conceptual understanding of light-dependent reactions
- Step 1: Review light absorption by chlorophyll
- Step 2: Learn the electron transport chain
- Step 3: Understand the role of water molecules
- Step 4: Practice with diagrams
- Strategies: Active recall, spaced repetition, visual learning
- Timeline: 1-2 weeks
- Success metrics: Score 85%+ on photosynthesis quiz

---

### Student Scenario 2: Confused Concept

**Student Input:**
```
"I don't understand why we need both mitochondria and chloroplasts in plant cells. 
What's the difference? Both seem to produce energy."
```

**Classification:** `confusion` (confidence: 0.93)

**Identified Topics:** ["Cellular Organelles", "Photosynthesis", "Cellular Respiration"]

**Recommendation Includes:**
- Root cause: Misconception about organelle functions
- Clarification: Chloroplasts capture energy, mitochondria release it
- Step 1: Understand energy forms (light vs chemical)
- Step 2: Study each process separately
- Step 3: Compare and contrast
- Suggested study strategy: Venn diagram comparison

---

### Student Scenario 3: Irrelevant Input

**Student Input:**
```
"What's your favorite movie?"
```

**Classification:** `irrelevant` (confidence: 0.99)

**Response:** Canned message redirecting to study topics

---

## Integration with Other Modules

### With Chat System
- Link to chat discussions on specific topics
- Use chat for follow-up questions on recommendations

### With Quiz System
- Generate quizzes on identified topics
- Use quiz results to measure success metrics

### With Flashcard System
- Create flashcards for key concepts
- Track flashcard performance as progress indicator

---

## Troubleshooting

### Common Issues

1. **"Input too short" error**
   - Solution: Provide at least 10 characters of detail

2. **All inputs classified as "irrelevant"**
   - Solution: Check if OPENROUTER_API_KEY is set
   - Fallback: System will use keyword-based classification

3. **Long response times (>5 seconds)**
   - Check network latency
   - Verify LLM API is responsive
   - Consider caching for similar inputs

4. **Canned response instead of recommendations**
   - Input may be too vague or off-topic
   - Try being more specific about your learning concern

---

## Future Enhancements

- [ ] Voice input support
- [ ] Multi-language support
- [ ] Learning style detection
- [ ] Progress tracking over time
- [ ] Integration with calendar for scheduling
- [ ] Real-time collaborative diagnostics
- [ ] AI-powered study group matching
- [ ] Predictive weakness detection
