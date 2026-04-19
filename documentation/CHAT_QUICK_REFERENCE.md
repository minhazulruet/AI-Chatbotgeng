# Chat System - Quick Reference

## 🚀 Quick Start (30 seconds)

### 1. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. Open Chat
Go to: `http://localhost:8000/chat.html`

### 3. Ask a Question
Type: "What is Ohm's law?"

Done! ✅

---

## 📝 Common Questions

### Q1: How do I ask a technical question?
Be specific and clear:
- ❌ "Tell me about electricity"
- ✅ "What is the relationship between voltage, current, and resistance?"

### Q2: How do I get better answers?
1. Use more specific questions
2. Increase context chunks (Settings → up to 5)
3. Make sure context is enabled

### Q3: What does the quality score mean?
- ⭐⭐⭐ **0.8+**: Excellent - answer grounded in textbook
- ⭐⭐ **0.6-0.8**: Good - relevant with clear explanation
- ⭐ **0.4-0.6**: Fair - basic answer with some context
- ❌ **<0.4**: Poor - limited context

### Q4: Can I use this offline?
The LLM (explanations) requires OpenRouter API key. RAG retrieval works offline if vector store is ready.

### Q5: How do I submit feedback?
After getting a response, you can rate it (1-5 stars) and add comments.

---

## 🔧 API Examples

### Example 1: Simple Query (Browser Console)
```javascript
// In browser developer console
const response = await fetch('http://localhost:8000/api/chat/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'What is a circuit?',
        top_k: 3
    })
});
const data = await response.json();
console.log(data.explanation);
```

### Example 2: Python Script
```python
import requests

response = requests.post(
    'http://localhost:8000/api/chat/ask',
    json={
        'message': 'Explain Kirchhoff\'s current law',
        'session_id': 'my-session',
        'top_k': 5
    }
)

data = response.json()
print(f"Q: {data['query']}")
print(f"A: {data['explanation']}")
print(f"Score: {data['quality_score']:.0%}")
```

### Example 3: Batch Multiple Questions
```python
import requests

questions = [
    'What is a circuit?',
    'What is Ohm\'s law?',
    'Explain series and parallel circuits'
]

response = requests.post(
    'http://localhost:8000/api/chat/batch-ask',
    json=[{'message': q} for q in questions]
)

for i, answer in enumerate(response.json()):
    print(f"\nQ{i+1}: {answer['query']}")
    print(f"A: {answer['explanation'][:200]}...")
```

### Example 4: With Session Tracking
```python
import requests

session_id = 'user-12345'

# Question 1
r1 = requests.post(
    'http://localhost:8000/api/chat/ask',
    json={'message': 'What is voltage?', 'session_id': session_id}
)

# Question 2 (same session)
r2 = requests.post(
    'http://localhost:8000/api/chat/ask',
    json={'message': 'How does voltage relate to current?', 'session_id': session_id}
)

# Get history
history = requests.get(
    f'http://localhost:8000/api/chat/conversation-history/{session_id}'
).json()

print(f"Conversation history: {history['total_turns']} turns")
```

---

## 🎯 Settings

### Context Chunks (top_k)
- **1**: Fastest, minimal context
- **3**: Balanced (default)
- **5**: Slowest, most comprehensive

### Include Context
- **ON**: Shows textbook references (helpful for learning)
- **OFF**: Only explanation (faster, less educational)

### Clear History
- Clears current conversation
- Starts fresh session
- Useful for testing

---

## ⚡ Performance Tips

| Scenario | Recommendation |
|----------|---|
| Quick answers | top_k=1, disable context |
| Learning mode | top_k=5, enable context |
| Mobile/slow internet | top_k=1 |
| Batch processing | Use `/api/chat/batch-ask` |

---

## 🐛 Common Issues & Fixes

### "Response is taking too long"
```javascript
// Reduce context chunks
setTopK(1)

// Or disable context
// In API call, set include_context: false
```

### "No contexts found"
```bash
# Check RAG system
curl http://localhost:8000/api/rag/health

# Rebuild index if needed
python backend/app/scripts/build_rag_index.py
```

### "LLM errors"
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Or use fallback
export OPENAI_API_KEY=sk-...
```

### "Generic answers"
- Use more specific questions
- Increase top_k for more context
- Check context relevance scores

---

## 📊 Architecture at a Glance

```
Question
   ↓
[Context Agent] → RAG Retrieval (BM25 + semantic)
   ↓
[Explainer Agent] → GPT-4o-mini (LLM explanation)
   ↓
[Validator] → Quality Scoring (0.0-1.0)
   ↓
Response with:
- Explanation
- Contexts
- Quality Score
- Session ID
```

---

## 🔗 Useful Links

- [Full API Documentation](CHAT_ENDPOINTS.md)
- [Integration Guide](CHAT_INTEGRATION.md)
- [RAG Architecture](RAG_ARCHITECTURE.md)
- [API Base URL](http://localhost:8000)
- [OpenRouter Docs](https://openrouter.ai/docs)

---

## 📱 Mobile-Friendly Tips

For better mobile experience:
1. Set top_k=1 (less bandwidth)
2. Disable context in settings
3. Use shorter questions
4. Clear history between sessions

---

## 💡 Pro Tips

### Tip 1: Multi-turn Learning
Start with basic question, then ask follow-ups:
- Q1: "What is resistance?"
- Q2: "How does it relate to Ohm's law?"
- Q3: "Give me a real-world example"

### Tip 2: Citation Checking
Look at "Referenced Textbook Content" section to:
- Verify answers are from official textbook
- See original context
- Follow up with instructor

### Tip 3: Feedback Matters
- Rate each answer (1-5)
- Add notes on what was helpful/missing
- Helps improve future responses

### Tip 4: Context vs Speed
- Studying: Enable context, top_k=5
- Testing: Disable context, top_k=1
- Practice: Balanced, top_k=3

---

## 🤔 FAQ

**Q: Is my data private?**
A: Queries and responses are logged for improvement. Don't share personal information.

**Q: Can it do other subjects?**
A: Currently focused on circuit analysis. Uses content from loaded textbook.

**Q: Why sometimes generic answers?**
A: When RAG can't find relevant content, LLM uses general knowledge.

**Q: Can I export chat history?**
A: See `/api/chat/conversation-history/{session_id}` - manually export JSON.

**Q: Is there an API rate limit?**
A: Currently unlimited for development. Production needs rate limiting.

**Q: How accurate are answers?**
A: Accuracy depends on:
- Textbook quality (ground truth)
- RAG retrieval accuracy (content matching)
- LLM reasoning (explanation quality)

---

## 📞 Need Help?

Check:
1. [Integration Guide](CHAT_INTEGRATION.md) - Detailed setup
2. [API Documentation](CHAT_ENDPOINTS.md) - All endpoints
3. Troubleshooting section above
4. Server logs: `tail -f server.log`

---

**Happy Learning! 🎓**
