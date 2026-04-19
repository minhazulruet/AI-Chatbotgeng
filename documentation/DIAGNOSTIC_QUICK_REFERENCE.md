# Diagnostic System - Quick Reference Guide

## 🚀 Quick Start

### 1. Frontend (Student View)

```
User navigates to: /diagnostics.html
    ↓
Fills textarea with learning concern
    ↓
Clicks "Analyze My Learning"
    ↓
Gets personalized improvement plan
    ↓
Submits feedback (helpful/not helpful)
```

### 2. Example Student Inputs

**Weakness:**
```
"I struggle with understanding how to solve differential equations. 
I can follow the steps but I don't understand why those steps work."
```

**Confusion:**
```
"I'm confused about the difference between mitosis and meiosis. 
They both seem to involve cell division so I keep mixing them up."
```

**Progression:**
```
"I've been practicing Python for 3 weeks and I'm getting better at 
writing functions. What should I focus on next to keep improving?"
```

---

## 📡 API Quick Reference

### Main Endpoint
```bash
POST /api/diagnostic/analyze
```

### Quick Request
```javascript
const result = await analyzeDiagnostic(
  "I don't understand how to factor polynomials"
);
```

### Quick Response
```json
{
  "classification": "weakness",
  "confidence": 0.95,
  "identified_topics": ["Polynomials", "Algebra"],
  "recommendation": { ... },
  "related_resources": [ ... ]
}
```

---

## 🏗️ Backend Architecture

### Services

**File:** `backend/app/services/diagnostic_service.py`

- **TextClassifier**: Classifies input type (weakness/confusion/progression/irrelevant)
- **TopicExtractor**: Extracts relevant topics using LLM + RAG
- **RecommendationEngine**: Generates structured improvement plan
- **DiagnosticTeam**: Main orchestrator (coordinates all agents)

### API Router

**File:** `backend/app/api/diagnostic.py`

```python
# Main endpoints
POST /api/diagnostic/analyze         # Analyze student input
GET  /api/diagnostic/history/{id}   # Get history
POST /api/diagnostic/feedback       # Submit feedback
GET  /api/diagnostic/health         # Health check
POST /api/diagnostic/test           # Test system
```

---

## 🎨 Frontend Implementation

### Files

**HTML:** `frontend/diagnostics.html`
- Beautiful textarea with examples
- Real-time character counter
- Responsive layout
- Results display area

**JavaScript:** `frontend/js/diagnostics.js`
- Form handling and validation
- API calls to backend
- Result rendering
- Feedback submission

**API Client:** `frontend/js/api.js`
- `analyzeDiagnostic(text, sessionId)`
- `getDiagnosticHistory(sessionId)`
- `submitDiagnosticFeedback(sessionId, text, helpful)`

---

## 🔧 Configuration

### Required Environment Variables
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Required for LLM calls
OPENAI_API_KEY=sk-xxxxx             # Optional fallback
```

### Models Used
- **Text Classification**: GPT-4o-mini (temperature: 0.3)
- **Topic Extraction**: GPT-4o-mini (temperature: 0.3)
- **Recommendations**: GPT-4o-mini (temperature: 0.7)

---

## 📊 Response Structure

### Classification Types
```python
WEAKNESS    = "weakness"      # Identifies topic struggle
CONFUSION   = "confusion"     # Doesn't understand concept
PROGRESSION = "progression"   # Sharing improvement
IRRELEVANT  = "irrelevant"   # Off-topic
```

### Recommendation Object
```json
{
  "weakness_identified": "...",
  "root_cause": "...",
  "severity": "low|medium|high",
  "improvement_steps": [
    {
      "step": 1,
      "title": "...",
      "description": "...",
      "resources": [],
      "estimated_time": "..."
    }
  ],
  "study_strategies": [
    {
      "strategy": "...",
      "description": "...",
      "implementation": "..."
    }
  ],
  "timeline": "...",
  "success_metrics": [],
  "key_concepts": []
}
```

---

## 🧪 Testing

### Test Endpoint
```bash
POST http://localhost:8000/api/diagnostic/test
```

### Example Test Input
```
"I'm really struggling with understanding how circuits work and I don't 
understand the relationship between current and voltage."
```

### Expected Output
```json
{
  "status": "success",
  "classification": "weakness",
  "confidence": 0.92,
  "identified_topics": ["Electric Circuits", "Current", "Voltage"],
  "recommendation_exists": true,
  "message": "Diagnostic system is working correctly"
}
```

---

## ⚡ Performance Tips

### Response Times
- **Classification**: 500-1000ms
- **Topic Extraction**: 300-800ms
- **Recommendations**: 1000-3000ms
- **Total**: ~2-5 seconds

### Optimization
1. Cache LLM responses for similar inputs
2. Pre-load RAG system on startup
3. Use connection pooling for API calls
4. Consider async processing for large batches

---

## 🐛 Debugging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Health
```bash
curl http://localhost:8000/api/diagnostic/health
```

### Check Service
```bash
curl -X POST http://localhost:8000/api/diagnostic/test
```

### Common Issues

| Problem | Solution |
|---------|----------|
| All inputs "irrelevant" | Check OPENROUTER_API_KEY |
| Slow responses | Check LLM API status |
| No topics extracted | Ensure RAG system loaded |
| Canned response | Input may be too vague |

---

## 📚 Integration Points

### With Chat System
```javascript
// Link in recommendations
"Chat with tutor about " + topic
```

### With Quiz System
```javascript
// Generate quiz on topic
"/api/quiz/generate?topic=" + topic
```

### With Flashcards
```javascript
// Link to flashcard system
"/flashcards.html"
```

---

## 💾 Data Storage

Currently using **in-memory storage** for:
- Diagnostic history
- Feedback submissions

**For Production:**
- Implement database storage
- Add user_id tracking
- Create analytics dashboard
- Export progress reports

---

## 🔐 Security

### Authentication
- All endpoints require Bearer token
- Token checked in API middleware
- Session IDs prevent data leakage

### Validation
- Input length: 10-2000 characters
- Output sanitization (no SQL injection risk)
- XSS protection in frontend

### Privacy
- Session-based tracking
- Feedback stored separately
- Can be deleted by user

---

## 📈 Monitoring

### Key Metrics
- Classification accuracy
- Recommendation helpfulness (via feedback)
- Average response time
- Topic extraction coverage
- Error rate

### Logging Points
- Input received
- Classification result
- Topics extracted
- Recommendation generated
- Feedback submitted

---

## 🚀 Deployment

### Pre-deployment Checklist
- [ ] Environment variables set
- [ ] RAG system initialized
- [ ] LLM API key verified
- [ ] Database configured
- [ ] Logging configured
- [ ] CORS properly set
- [ ] Frontend assets deployed

### Production Configuration
```python
# Disable hot-reload
uvicorn run(reload=False)

# Set proper CORS origins
allow_origins=["https://yourdomain.com"]

# Enable rate limiting
from slowapi import Limiter
```

---

## 🎓 Learning Resources

### For Understanding the System
1. Read `DIAGNOSTIC_ENDPOINTS.md` - Complete API reference
2. Check `diagnostic_service.py` - Implementation details
3. Review `diagnostics.html` - UI structure
4. Study `diagnostics.js` - Frontend logic

### For Extending the System
1. Add new classification types in `InputClassification` enum
2. Customize LLM prompts in agent classes
3. Add database storage for history
4. Implement analytics dashboard

---

## 📝 Common Code Snippets

### Initialize Diagnostic Team
```python
from app.services.diagnostic_service import get_diagnostic_team

team = get_diagnostic_team()
result = team.process_diagnostic_input(student_input, session_id)
```

### Call Diagnostic API from Frontend
```javascript
// Analyze
const result = await analyzeDiagnostic("My learning concern");

// Check result
if (result.status === 'success') {
  displayRecommendations(result.recommendation);
} else {
  displayCannedResponse(result.canned_response);
}

// Get history
const history = await getDiagnosticHistory(sessionId);

// Submit feedback
await submitDiagnosticFeedback(sessionId, "Text", true);
```

### Error Handling
```javascript
try {
  const result = await analyzeDiagnostic(text);
  // Process result
} catch (error) {
  console.error('Diagnostic error:', error);
  showErrorMessage('Failed to analyze input');
}
```

---

## 🔄 Future Enhancements

- [ ] Voice input support
- [ ] Multi-language diagnostics
- [ ] Learning style detection
- [ ] Progress tracking dashboard
- [ ] Predictive weakness detection
- [ ] Study group recommendations
- [ ] Calendar-based study planning
- [ ] Mobile app support

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Read DIAGNOSTIC_ENDPOINTS.md
3. Review server logs
4. Run test endpoint
5. Check LLM API status
