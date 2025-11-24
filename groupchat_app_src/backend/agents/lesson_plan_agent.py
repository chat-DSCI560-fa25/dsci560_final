"""
Lesson Plan Agent
Handles semantic search and recommendations for lesson plans using RAG (Retrieval-Augmented Generation).
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import chromadb
from sentence_transformers import SentenceTransformer
import chromadb
import re
from llm import chat_completion

class LessonPlanAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="LessonPlanAgent",
            description="Finds and recommends lesson plans using semantic search and LLM summarization."
        )
        self.keywords = [
            "lesson", "curriculum", "plan", "activity", "worksheet", "experiment", "project", "grade", "subject", "topic", "find", "recommend", "search"
        ]

    async def can_handle(self, user_message: str, context: Dict[str, Any]) -> tuple[bool, float]:
        message_lower = user_message.lower()
        # Simple keyword-based detection for now
        matches = sum(1 for kw in self.keywords if kw in message_lower)
        if matches >= 2:
            return True, 0.8
        elif matches == 1:
            return True, 0.5
        return False, 0.0

    async def execute(self, user_message: str, context: Dict[str, Any], session) -> Dict[str, Any]:
        chroma_client = chromadb.PersistentClient(path="chromadb_data")
        collection = chroma_client.get_or_create_collection(name="lesson_plans")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = embedder.encode(user_message)
        # Extract grade/subject/topic from query
        grade = None
        subject = None
        topic = None
        grade_match = re.search(r'grade\s*(\d+)', user_message.lower())
        if grade_match:
            grade = int(grade_match.group(1))
        for subj in ['biology', 'chemistry', 'physics', 'math', 'science', 'english', 'history']:
            if subj in user_message.lower():
                subject = subj
        # Query vector DB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        docs = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        distances = results.get('distances', [])
        # Always show top 5 results with their similarity scores
        response_lines = []
        def flatten_meta(meta):
            while isinstance(meta, list) and len(meta) > 0:
                meta = meta[0]
            return meta
        def flatten_score(score):
            if isinstance(score, list) and len(score) > 0:
                return score[0]
            return score
        def flatten_doc(doc):
            if isinstance(doc, list) and len(doc) > 0:
                return doc[0]
            return doc if doc else ""
        
        def truncate_text(text, max_length=600):
            """Truncate text to max_length, trying to break at sentence or word boundaries."""
            if not text:
                return ""
            if len(text) <= max_length:
                return text
            # Try to break at sentence boundary first
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            last_sentence = max(last_period, last_exclamation, last_question)
            
            if last_sentence > max_length * 0.6:  # If we found a sentence end reasonably close
                truncated = truncated[:last_sentence + 1]
            else:
                # Fall back to word boundary
                last_space = truncated.rfind(' ')
                if last_space > max_length * 0.7:
                    truncated = truncated[:last_space]
            return truncated + "..."
        
        async def summarize_lesson_plan(doc_content: str, user_query: str) -> str:
            """Use LLM to generate a concise summary of the lesson plan."""
            if not doc_content or len(doc_content) < 100:
                return doc_content
            
            # Take first 1000 chars for summarization to avoid token limits
            content_preview = doc_content[:1000] if len(doc_content) > 1000 else doc_content
            
            try:
                summary = await chat_completion([
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes lesson plans concisely. Provide a 2-3 sentence summary highlighting the key learning objectives and activities. Do not include phrases like 'Here is a summary' or 'This lesson plan' - just provide the summary directly."
                    },
                    {
                        "role": "user",
                        "content": f"User is looking for: {user_query}\n\nLesson plan content:\n{content_preview}\n\nProvide a concise 2-3 sentence summary of this lesson plan."
                    }
                ], temperature=0.3, max_tokens=150)
                # Clean up any redundant prefixes the LLM might add
                summary = summary.strip()
                # Remove common prefixes
                prefixes_to_remove = [
                    "Here is a 2-3 sentence summary of the lesson plan:",
                    "Here is a summary:",
                    "Summary:",
                    "This lesson plan",
                    "The lesson plan"
                ]
                for prefix in prefixes_to_remove:
                    if summary.startswith(prefix):
                        summary = summary[len(prefix):].strip()
                        if summary.startswith(":"):
                            summary = summary[1:].strip()
                return summary
            except Exception as e:
                # Fall back to truncation if LLM fails
                return truncate_text(doc_content, max_length=500)
        
        for i, (doc_list, meta, dist) in enumerate(zip(docs, metadatas, distances)):
            meta = flatten_meta(meta)
            score = flatten_score(dist)
            doc_content = flatten_doc(doc_list)
            
            # Use full document content if available, otherwise fall back to snippet
            raw_text = doc_content if doc_content else (meta.get('snippet', '') if isinstance(meta, dict) else '')
            
            # Generate LLM summary for better readability
            if raw_text and len(raw_text) > 200:
                display_text = await summarize_lesson_plan(raw_text, user_message)
            else:
                display_text = raw_text
            
            if isinstance(meta, dict):
                filename = meta.get('filename', 'Unknown')
                # Format with explicit spacing - use multiple newlines and visual separators
                # Format: Number, filename on one line, then summary on next lines with spacing
                formatted_entry = f"\n[{i+1}] {filename}\n\n{display_text}\n"
                response_lines.append(formatted_entry)
            else:
                formatted_entry = f"\n[{i+1}] [Unrecognized format]\n\n{display_text}\n"
                response_lines.append(formatted_entry)
        
        if response_lines:
            # Join with clear visual separators between entries
            # Use multiple newlines and separator line for clear distinction
            separator = "\n" + ("=" * 60) + "\n"
            response = "Top lesson plans found:\n" + separator.join(response_lines)
        else:
            response = "No relevant lesson plans found."
        return {
            "success": True,
            "message": response,
            "data": metadatas,
            "actions": ["lesson_plan_search"]
        }

    async def get_capabilities(self) -> List[str]:
        return [
            "Semantic search for lesson plans",
            "Curriculum alignment",
            "Smart recommendations",
            "Document retrieval"
        ]
