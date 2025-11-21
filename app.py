from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
import importlib
import os
import re
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from typing import Callable, Dict, List, Optional, Iterator

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Detect available AI providers
AI_PROVIDER = None
OPENAI_CLIENT = None
GROQ_CLIENT = None
OLLAMA_AVAILABLE = False
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "txt",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "zip",
}

TEXTUAL_EXTENSIONS = {
    "txt",
    "md",
    "csv",
    "json",
    "py",
    "js",
    "ts",
    "java",
    "c",
    "cpp",
    "html",
    "css",
    "xml",
    "yaml",
    "yml",
    "tex",
    "sql",
}

DEFAULT_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.65"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.2-11b-instruct")  # Updated: llama-3.1-70b-versatile was decommissioned
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Updated to 2025 model
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "6"))
MAX_ATTACHMENT_CONTEXT_CHARS = int(os.getenv("ATTACHMENT_CONTEXT_CHARS", "1200"))
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # Optional: Tavily API for better search

try:
    sp = importlib.import_module("sympy")
    _SYMPY_SYMBOLS = sp.symbols("x y z a b c n k t")
    SYMPY_LOCALS = {str(symbol): symbol for symbol in _SYMPY_SYMBOLS}
    SYMPY_LOCALS.update({key.upper(): value for key, value in SYMPY_LOCALS.items()})
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    sp = None
    SYMPY_LOCALS = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Try OpenAI
try:
    from openai import OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        OPENAI_CLIENT = OpenAI(api_key=api_key)
        AI_PROVIDER = "openai"
except ImportError:
    pass

# Try Groq (free tier available)
try:
    from openai import OpenAI as GroqClient
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        GROQ_CLIENT = GroqClient(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        if not AI_PROVIDER:  # Use Groq if OpenAI not available
            AI_PROVIDER = "groq"
except ImportError:
    pass

# Check Ollama (completely free, local)
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        OLLAMA_AVAILABLE = True
        if not AI_PROVIDER:
            AI_PROVIDER = "ollama"
except:
    pass

class QuestionAnsweringAI:
    def __init__(self):
        self.history = []
        self.provider = AI_PROVIDER
        self.openai_client = OPENAI_CLIENT
        self.groq_client = GROQ_CLIENT
        self.ollama_available = OLLAMA_AVAILABLE
        self.max_history = CHAT_HISTORY_LIMIT
        self.temperature = DEFAULT_TEMPERATURE
        self.enable_web_search = ENABLE_WEB_SEARCH
        self.tavily_api_key = TAVILY_API_KEY
    
    def answer_question(self, question: str):
        """Answer any question using AI - tries multiple free providers"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_year = datetime.now().year
        
        # Handle greetings simply and directly
        if self._is_greeting(question):
            greeting_response = self._handle_greeting(question)
            self._record_history(question, greeting_response, timestamp, "greeting")
            return {
                "answer": greeting_response,
                "timestamp": timestamp,
                "error": False,
                "provider": "greeting"
            }
        
        # Check if question needs current/recent information
        needs_current_info = self._needs_current_info(question)
        web_search_results = ""
        
        if needs_current_info and self.enable_web_search:
            try:
                web_search_results = self._search_web(question)
                if web_search_results:
                    question = f"{question}\n\n[Current Information from Web Search ({current_year}):\n{web_search_results}\n\nIMPORTANT: Use this web search information as your primary source. It is more recent than your training data.]"
            except Exception as e:
                print(f"Web search failed for question: {e}")
                # Continue without web search - don't block the response
        
        system_prompt = f"""You are EDU AI, a friendly and helpful AI assistant with access to current information up to {current_year}.

Current Date: {current_date}
Current Year: {current_year}

CRITICAL INSTRUCTIONS:
- Your training data may have knowledge cutoff dates that are OLDER than {current_date}
- When web search results are provided in the user's question, you MUST prioritize and use them over your training data
- Web search results are more recent and accurate than your training knowledge for current events
- ALWAYS acknowledge when using web search results vs training data
- If information conflicts, trust web search results over training data
- When you lack current information and no web search is provided, admit your knowledge may be outdated
- Be conversational and friendly, especially for casual questions

WEB SEARCH USAGE:
- If the user's question contains "[Current Information from Web Search", those are REAL-TIME search results
- USE those results as your primary source of information
- Cite the sources from web search results when available
- Mention that the information comes from recent web search if applicable

KNOWLEDGE LIMITS:
- If asked about recent events (after your training cutoff) and no web search provided, say: "My knowledge may be outdated. Let me search for the latest information."
- Always be honest about when information might be outdated
- For time-sensitive questions (prices, dates, current status), emphasize checking web search results

Guidelines:
- Use step-by-step reasoning for complex topics
- Give direct answers for simple questions
- Cite references when helpful
- Keep responses appropriate to the question's complexity
- Be friendly and approachable
- Keep privacy in mind"""
        
        messages = self._build_messages(question, system_prompt)
        
        # Give local symbolic tools a chance before spending API calls
        tool_result = self._maybe_answer_with_tools(question)
        if tool_result:
            self._record_history(question, tool_result["answer"], timestamp, tool_result["provider"])
            return {
                "answer": tool_result["answer"],
                "timestamp": timestamp,
                "error": False,
                "provider": tool_result["provider"]
            }
        
        providers_to_try: List[tuple[str, Callable[[], Optional[str]]]] = []
        
        if self.groq_client:
            providers_to_try.append(("groq", lambda msgs=messages: self._try_groq(msgs)))
        if self.openai_client:
            providers_to_try.append(("openai", lambda msgs=messages: self._try_openai(msgs)))
        if self.ollama_available:
            providers_to_try.append(("ollama", lambda msgs=messages: self._try_ollama(msgs)))
        
        if not providers_to_try:
            return {
                "answer": """🔧 No AI Provider Available

To use this app for FREE, choose one option:

1. **Ollama (Recommended - 100% Free)**
   - Download: https://ollama.ai
   - Install and run: ollama pull llama2
   - No API key needed!

2. **Groq (Free API)**
   - Get free API key: https://console.groq.com
   - Add GROQ_API_KEY to .env file

3. **OpenAI (Paid)**
   - Add OPENAI_API_KEY to .env file""",
                "timestamp": timestamp,
                "error": True
            }
        
        # Try each provider until one works
        last_error = None
        for provider_name, provider_func in providers_to_try:
            try:
                answer = provider_func()
                if answer:
                    self.provider = provider_name
                    self._record_history(question, answer, timestamp, provider_name)
                    return {
                        "answer": answer,
                        "timestamp": timestamp,
                        "error": False,
                        "provider": provider_name
                    }
            except Exception as e:
                last_error = e
                continue  # Try next provider
        
        # If all providers failed, return error
        return self._handle_error(last_error, timestamp)
    
    def _record_history(self, question: str, answer: str, timestamp: str, provider: str) -> None:
        self.history.append({
            "question": question,
            "answer": answer,
            "timestamp": timestamp,
            "provider": provider
        })
        # Trim history to avoid unbounded growth
        if len(self.history) > 100:
            self.history = self.history[-100:]
    
    def _build_messages(self, question: str, system_prompt: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        history_slice = self.history[-self.max_history :]
        for turn in history_slice:
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": turn["answer"]})
        messages.append({"role": "user", "content": question})
        return messages
    
    def _maybe_answer_with_tools(self, question: str) -> Optional[Dict[str, str]]:
        if not question or sp is None:
            return None
        
        symbolic = self._try_symbolic_math(question)
        if symbolic:
            return {"answer": symbolic, "provider": "sympy-tool"}
        return None
    
    def _try_symbolic_math(self, question: str) -> Optional[str]:
        if sp is None:
            return None
        
        lowered = question.lower()
        triggers = ("solve", "calculate", "compute", "simplify", "integrate", "differentiate", "derivative", "expand", "factor")
        if not any(word in lowered for word in triggers):
            return None
        
        expression = self._extract_expression(question)
        if not expression:
            return None
        
        try:
            if ("solve" in lowered or "equation" in lowered) and "=" in expression:
                lhs, rhs = expression.split("=", 1)
                eq = sp.Eq(
                    sp.sympify(lhs, locals=SYMPY_LOCALS),
                    sp.sympify(rhs, locals=SYMPY_LOCALS),
                )
                solution = sp.solve(eq, dict=True)
                if solution:
                    return self._format_sympy_result("Equation solution", solution)
            
            expr_obj = sp.sympify(expression, locals=SYMPY_LOCALS)
            var = self._guess_variable(expression)
            
            if "integrate" in lowered or "∫" in question:
                integrated = sp.integrate(expr_obj, var)
                return self._format_sympy_result(f"∫ {expression} d{var}", integrated)
            
            if any(word in lowered for word in ("differentiate", "derivative")):
                derivative = sp.diff(expr_obj, var)
                return self._format_sympy_result(f"d/d{var} ({expression})", derivative)
            
            simplified = sp.simplify(expr_obj)
            return self._format_sympy_result("Simplified expression", simplified)
        except Exception:
            return None
    
    def _extract_expression(self, text: str) -> Optional[str]:
        math_keywords = [
            "solve",
            "calculate",
            "compute",
            "evaluate",
            "simplify",
            "integrate",
            "differentiate",
            "derivative",
            "expand",
            "factor",
        ]
        for keyword in math_keywords:
            pattern = re.compile(rf"{keyword}[^\S\r\n]*[:\-]?\s*(.+)", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                expression = match.group(1).strip()
                # Use only the first line to avoid capturing entire paragraphs
                return expression.splitlines()[0].strip()
        return None
    
    def _guess_variable(self, expression: str):
        if sp is None:
            return None
        candidates = re.findall(r"[a-zA-Z]", expression)
        for cand in candidates:
            cand_lower = cand.lower()
            if cand in SYMPY_LOCALS:
                return SYMPY_LOCALS[cand]
            if cand_lower in SYMPY_LOCALS:
                return SYMPY_LOCALS[cand_lower]
        return SYMPY_LOCALS.get("x") or sp.symbols("x")
    
    def _format_sympy_result(self, title: str, result) -> str:
        try:
            pretty_output = sp.pretty(result)
        except Exception:
            pretty_output = str(result)
        
        numeric_line = ""
        if hasattr(result, "evalf"):
            try:
                numeric_line = f"\n≈ {result.evalf()}"
            except Exception:
                numeric_line = ""
        return f"""🧮 {title}
{pretty_output}{numeric_line}

Solved exactly with SymPy before calling any external AI API."""
    
    def _is_greeting(self, question: str) -> bool:
        """Detect if the question is a greeting or simple conversation"""
        question_lower = question.lower().strip()
        
        # Common greetings
        greetings = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
            "greetings", "howdy", "what's up", "sup", "yo", "hi there", "hello there",
            "hey there", "good day", "morning", "afternoon", "evening",
            "how are you", "how's it going", "how do you do", "nice to meet you",
            "pleased to meet you", "how have you been", "what's going on"
        ]
        
        # Check if it's just a greeting (short and matches greeting patterns)
        if len(question_lower.split()) <= 5:  # Short phrases
            if any(greeting in question_lower for greeting in greetings):
                return True
        
        # Check exact matches
        if question_lower in greetings:
            return True
        
        # Check if it starts with a greeting
        for greeting in greetings:
            if question_lower.startswith(greeting) and len(question_lower.split()) <= 8:
                return True
        
        return False
    
    def _handle_greeting(self, question: str) -> str:
        """Handle greetings with friendly, simple responses"""
        question_lower = question.lower().strip()
        current_time = datetime.now().hour
        
        # Time-based greeting
        if current_time < 12:
            time_greeting = "Good morning"
        elif current_time < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        # Simple, friendly responses
        responses = [
            f"{time_greeting}! I'm EDU AI, your intelligent assistant. How can I help you today?",
            f"Hello! I'm here to help. What would you like to know?",
            f"Hi there! I'm EDU AI, ready to answer your questions. What can I assist you with?",
            f"Hey! Great to meet you. I'm EDU AI - ask me anything!",
            f"Hello! I'm your AI assistant. Feel free to ask me any questions!"
        ]
        
        # Return a friendly greeting response
        import random
        return random.choice(responses)
    
    def _needs_current_info(self, question: str) -> bool:
        """Determine if question needs current/recent information"""
        # Don't search for greetings
        if self._is_greeting(question):
            return False
            
        question_lower = question.lower()
        current_keywords = [
            # Time-based keywords
            "current", "latest", "recent", "now", "today", "2025", "2024", "2026",
            "news", "update", "happening", "trending", "newest", "latest news",
            "what's new", "recent developments", "current events", "breaking",
            "this year", "this month", "recently", "as of", "up to date",
            # Action/change keywords
            "announce", "release", "launch", "introduce", "unveil", "reveal",
            "price", "cost", "worth", "value", "stock", "market",
            # Status keywords
            "status", "state", "condition", "situation", "circumstance",
            # Question types that often need current info
            "who is", "who are", "what is the current", "what are the latest",
            "when did", "when will", "how much is", "how many are",
            # Domain-specific that change frequently
            "election", "president", "leader", "government", "policy",
            "technology", "software", "app", "version", "update",
            "sport", "game", "match", "score", "tournament",
            "weather", "forecast", "temperature"
        ]
        return any(keyword in question_lower for keyword in current_keywords)
    
    def _search_web(self, query: str, max_results: int = 5) -> str:
        """Search the web for current information"""
        try:
            # Try Tavily API first (better quality, requires API key)
            if self.tavily_api_key:
                tavily_result = self._search_tavily(query, max_results)
                if tavily_result:
                    return tavily_result
            
            # Fallback to DuckDuckGo (free, no API key needed)
            ddg_result = self._search_duckduckgo(query, max_results)
            if ddg_result:
                return ddg_result
            
            # If both fail, return empty (caller should handle gracefully)
            return ""
        except Exception as e:
            print(f"Web search error: {e}")
            # Don't raise - return empty string so AI can still respond
            return ""
    
    def _search_tavily(self, query: str, max_results: int = 5) -> str:
        """Search using Tavily API (better quality results)"""
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": True
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Include answer if available
                if data.get("answer"):
                    results.append(f"Summary: {data['answer']}")
                
                # Include top results
                for result in data.get("results", [])[:max_results]:
                    title = result.get("title", "")
                    url = result.get("url", "")
                    content = result.get("content", "")
                    if content:
                        results.append(f"- {title} ({url}): {content[:200]}...")
                
                return "\n".join(results) if results else ""
        except Exception as e:
            print(f"Tavily search error: {e}")
            return ""
    
    def _search_duckduckgo(self, query: str, max_results: int = 5) -> str:
        """Search using DuckDuckGo (free, no API key)"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                # Use text search for general queries
                results = list(ddgs.text(query, max_results=max_results))
                
                if not results:
                    # Try news search if no text results (better for current events)
                    try:
                        news_results = list(ddgs.news(query, max_results=max_results))
                        if news_results:
                            results = news_results
                    except Exception:
                        pass
                
                if not results:
                    return ""
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result.get("title", "")
                    url = result.get("href", "") or result.get("url", "")
                    body = result.get("body", "") or result.get("snippet", "") or result.get("description", "")
                    if body:
                        formatted_results.append(
                            f"{i}. {title} ({url})\n   {body[:400]}..."
                        )
                    elif title:  # Include even if no body
                        formatted_results.append(
                            f"{i}. {title} ({url})"
                        )
                
                return "\n\n".join(formatted_results) if formatted_results else ""
        except ImportError:
            # Fallback: try to install or use alternative
            print("duckduckgo-search package not found. Install with: pip install duckduckgo-search")
            try:
                # Use DuckDuckGo HTML search as fallback
                search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
                response = requests.get(search_url, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                if response.status_code == 200:
                    # Simple extraction (basic fallback)
                    return f"Web search performed for: {query}\n(Install duckduckgo-search package for better results: pip install duckduckgo-search)"
            except Exception:
                pass
            return ""
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            # Try to continue - maybe it's a temporary issue
            return ""
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for msg in messages:
            role = msg["role"].capitalize()
            lines.append(f"{role}:\n{msg['content']}")
        lines.append("Assistant:")
        return "\n\n".join(lines)
    
    def _try_ollama(self, messages: List[Dict[str, str]]):
        """Try Ollama (free, local)"""
        try:
            prompt = self._messages_to_prompt(messages)
            # 1) Try smaller / lighter models first (better for low-RAM machines)
            preferred_models = [
                "llama3.2:1b",  # small, light model
                "llama3.2",
                "phi",
                "mistral",
                "llama2",
                "llama3.1:8b",  # large model – will be used only if it fits in RAM
            ]

            # Helper to call Ollama
            def call_ollama(model_name: str):
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
                # If model not found, return None so we can try another
                if response.status_code in (400, 404):
                    return None
                # Other errors should raise
                response.raise_for_status()

            # Try preferred models first
            for m in preferred_models:
                try:
                    answer = call_ollama(m)
                    if answer:
                        return answer
                except Exception:
                    continue

            # 2) As a fallback, ask Ollama which models exist and use the first one
            try:
                tags_resp = requests.get("http://localhost:11434/api/tags", timeout=10)
                if tags_resp.status_code == 200:
                    data = tags_resp.json()
                    models = data.get("models", [])
                    if models:
                        first_model = models[0].get("name") or models[0].get("model")
                        if first_model:
                            answer = call_ollama(first_model)
                            if answer:
                                return answer
            except Exception:
                pass

            raise Exception(
                "Ollama is running but no usable model was found. "
                "Open a terminal and run: ollama pull llama3.1:8b"
            )
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama not running. Start it or install from https://ollama.ai")
    
    def _try_groq(self, messages: List[Dict[str, str]]):
        """Try Groq (free API tier) with fallback models"""
        # List of models to try in order
        models_to_try = [
            GROQ_MODEL,  # User's preferred model or default
            "llama-3.2-11b-instruct",  # Stable default
            "llama-3.2-3b-instruct",  # Smaller fallback
            "llama-3.3-70b-versatile",  # Larger model if available
            "mixtral-8x7b-32768",  # Alternative model
        ]
        
        last_error = None
        for model in models_to_try:
            try:
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=2048
                )
                return response.choices[0].message.content
            except Exception as e:
                error_str = str(e).lower()
                # If model is decommissioned or not found, try next
                if "decommissioned" in error_str or "not found" in error_str or "invalid" in error_str:
                    last_error = e
                    continue
                # For other errors, raise immediately
                raise
        
        # If all models failed, raise the last error
        if last_error:
            raise Exception(f"All Groq models failed. Last error: {str(last_error)}. Available models: llama-3.2-11b-instruct, llama-3.2-3b-instruct, llama-3.3-70b-versatile")
        raise Exception("No Groq models available")
    
    def _try_openai(self, messages: List[Dict[str, str]]):
        """Try OpenAI"""
        response = self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1500
        )
        return response.choices[0].message.content
    
    def stream_answer(self, question: str) -> Iterator[str]:
        """Stream answer chunks as they're generated"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_year = datetime.now().year
        
        # Handle greetings simply and directly
        if self._is_greeting(question):
            greeting_response = self._handle_greeting(question)
            yield f"data: {json.dumps({'type': 'chunk', 'content': greeting_response, 'provider': 'greeting'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'provider': 'greeting'})}\n\n"
            return
        
        # Check if question needs current/recent information
        needs_current_info = self._needs_current_info(question)
        web_search_results = ""
        
        if needs_current_info and self.enable_web_search:
            # Send a message that we're searching
            yield f"data: {json.dumps({'type': 'status', 'content': '🔍 Searching for current information...', 'provider': 'web-search'})}\n\n"
            try:
                web_search_results = self._search_web(question)
                if web_search_results:
                    question = f"{question}\n\n[Current Information from Web Search ({current_year}):\n{web_search_results}\n\nIMPORTANT: Use this web search information as your primary source. It is more recent than your training data.]"
            except Exception as e:
                print(f"Web search failed for question: {e}")
                # Continue without web search - don't block the response
        
        system_prompt = f"""You are EDU AI, a friendly and helpful AI assistant with access to current information up to {current_year}.

Current Date: {current_date}
Current Year: {current_year}

CRITICAL INSTRUCTIONS:
- Your training data may have knowledge cutoff dates that are OLDER than {current_date}
- When web search results are provided in the user's question, you MUST prioritize and use them over your training data
- Web search results are more recent and accurate than your training knowledge for current events
- ALWAYS acknowledge when using web search results vs training data
- If information conflicts, trust web search results over training data
- When you lack current information and no web search is provided, admit your knowledge may be outdated
- Be conversational and friendly, especially for casual questions

WEB SEARCH USAGE:
- If the user's question contains "[Current Information from Web Search", those are REAL-TIME search results
- USE those results as your primary source of information
- Cite the sources from web search results when available
- Mention that the information comes from recent web search if applicable

KNOWLEDGE LIMITS:
- If asked about recent events (after your training cutoff) and no web search provided, say: "My knowledge may be outdated. Let me search for the latest information."
- Always be honest about when information might be outdated
- For time-sensitive questions (prices, dates, current status), emphasize checking web search results

Guidelines:
- Use step-by-step reasoning for complex topics
- Give direct answers for simple questions
- Cite references when helpful
- Keep responses appropriate to the question's complexity
- Be friendly and approachable
- Keep privacy in mind"""
        
        messages = self._build_messages(question, system_prompt)
        
        # Try symbolic tools first (non-streaming, but fast)
        tool_result = self._maybe_answer_with_tools(question)
        if tool_result:
            yield f"data: {json.dumps({'type': 'chunk', 'content': tool_result['answer'], 'provider': tool_result['provider']})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'provider': tool_result['provider']})}\n\n"
            return
        
        # Try streaming providers in order
        providers_to_try = []
        if self.groq_client:
            providers_to_try.append(("groq", lambda msgs=messages: self._stream_groq(msgs)))
        if self.openai_client:
            providers_to_try.append(("openai", lambda msgs=messages: self._stream_openai(msgs)))
        if self.ollama_available:
            providers_to_try.append(("ollama", lambda msgs=messages: self._stream_ollama(msgs)))
        
        if not providers_to_try:
            error_msg = """🔧 No AI Provider Available

To use this app for FREE, choose one option:

1. **Ollama (Recommended - 100% Free)**
   - Download: https://ollama.ai
   - Install and run: ollama pull llama2
   - No API key needed!

2. **Groq (Free API)**
   - Get free API key: https://console.groq.com
   - Add GROQ_API_KEY to .env file

3. **OpenAI (Paid)**
   - Add OPENAI_API_KEY to .env file"""
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
            return
        
        # Try each provider until one works
        last_error = None
        full_answer = ""
        provider_name = None
        
        for provider_name, stream_func in providers_to_try:
            try:
                for chunk in stream_func():
                    if chunk:
                        full_answer += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'provider': provider_name})}\n\n"
                
                # Success - record and finish
                self.provider = provider_name
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._record_history(question, full_answer, timestamp, provider_name)
                yield f"data: {json.dumps({'type': 'done', 'provider': provider_name})}\n\n"
                return
            except Exception as e:
                last_error = e
                continue
        
        # All providers failed
        error_msg = str(last_error) if last_error else "Unknown error"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    
    def _stream_groq(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream from Groq with fallback models"""
        # List of models to try in order
        models_to_try = [
            GROQ_MODEL,  # User's preferred model or default
            "llama-3.2-11b-instruct",  # Stable default
            "llama-3.2-3b-instruct",  # Smaller fallback
            "llama-3.3-70b-versatile",  # Larger model if available
            "mixtral-8x7b-32768",  # Alternative model
        ]
        
        last_error = None
        for model in models_to_try:
            try:
                stream = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=2048,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return  # Success - exit after streaming
            except Exception as e:
                error_str = str(e).lower()
                # If model is decommissioned or not found, try next
                if "decommissioned" in error_str or "not found" in error_str or "invalid" in error_str:
                    last_error = e
                    continue
                # For other errors, raise immediately
                raise
        
        # If all models failed, raise the last error
        if last_error:
            raise Exception(f"All Groq models failed. Last error: {str(last_error)}. Available models: llama-3.2-11b-instruct, llama-3.2-3b-instruct, llama-3.3-70b-versatile")
        raise Exception("No Groq models available")
    
    def _stream_openai(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream from OpenAI"""
        stream = self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1500,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _stream_ollama(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream from Ollama"""
        prompt = self._messages_to_prompt(messages)
        preferred_models = [
            "llama3.2:1b",
            "llama3.2",
            "phi",
            "mistral",
            "llama2",
            "llama3.1:8b",
        ]
        
        for model_name in preferred_models:
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": True
                    },
                    stream=True,
                    timeout=120
                )
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    return
                            except json.JSONDecodeError:
                                continue
                    return
                elif response.status_code in (400, 404):
                    continue  # Try next model
                else:
                    response.raise_for_status()
            except requests.exceptions.ConnectionError:
                raise Exception("Ollama not running. Start it or install from https://ollama.ai")
            except Exception:
                continue
        
        # Fallback: try any available model
        try:
            tags_resp = requests.get("http://localhost:11434/api/tags", timeout=10)
            if tags_resp.status_code == 200:
                data = tags_resp.json()
                models = data.get("models", [])
                if models:
                    first_model = models[0].get("name") or models[0].get("model")
                    if first_model:
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={"model": first_model, "prompt": prompt, "stream": True},
                            stream=True,
                            timeout=120
                        )
                        if response.status_code == 200:
                            for line in response.iter_lines():
                                if line:
                                    try:
                                        data = json.loads(line)
                                        if "response" in data:
                                            yield data["response"]
                                        if data.get("done", False):
                                            return
                                    except json.JSONDecodeError:
                                        continue
        except Exception:
            pass
        
        raise Exception("Ollama is running but no usable model was found.")
    
    def _handle_error(self, error, timestamp):
        error_message = str(error) if error else "Unknown error"
        error_message_lower = error_message.lower()
        
        # Handle specific API errors
        # Treat as true quota exceeded only when the provider explicitly says so,
        # not for every generic 429 status code.
        if (
            "insufficient_quota" in error_message_lower
            or "you exceeded your current quota" in error_message_lower
        ):
            user_message = """⚠️ API Quota Exceeded

Your OpenAI API key has exceeded its quota or billing limit. 

To fix this:
1. Check your OpenAI account billing: https://platform.openai.com/account/billing
2. Add payment method or increase your quota
3. Verify your API key has available credits

Alternatively, use a FREE option:
- Install Ollama: https://ollama.ai (100% free, local)
- Get Groq API key: https://console.groq.com (free tier)"""
        elif "401" in error_message or "invalid_api_key" in error_message_lower:
            user_message = """🔑 Invalid API Key

Your API key is invalid or expired.

To fix this:
1. Check your API key
2. Make sure the key in your .env file is correct
3. Ensure the key hasn't been revoked

Or use a FREE option:
- Install Ollama: https://ollama.ai (no API key needed!)
- Get Groq API key: https://console.groq.com"""
        elif "rate_limit" in error_message_lower or "429" in error_message:
            user_message = """⏱️ Rate Limit Exceeded

You're making requests too quickly. Please wait a moment and try again."""
        else:
            user_message = f"Error: {error_message}\n\n💡 Try using a FREE option:\n- Ollama: https://ollama.ai\n- Groq: https://console.groq.com"
        
        return {
            "answer": user_message,
            "timestamp": timestamp,
            "error": True
        }
    
    def get_history(self):
        """Return conversation history"""
        return self.history

# Initialize AI
ai = QuestionAnsweringAI()

@app.route('/')
def index():
    return render_template(
        'index.html',
        provider=ai.provider,
        ollama_available=ai.ollama_available,
        groq_available=bool(ai.groq_client),
        openai_available=bool(ai.openai_client),
        supabase_url=SUPABASE_URL,
        supabase_anon_key=SUPABASE_ANON_KEY,
        auth_required=bool(SUPABASE_URL and SUPABASE_ANON_KEY)
    )

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files for PWA"""
    return send_from_directory('static', filename)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    attachments = data.get('attachments', [])
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    attachment_context = _build_attachment_context(attachments)
    question_payload = question + attachment_context
    
    result = ai.answer_question(question_payload)
    result["attachments"] = attachments
    return jsonify(result)

@app.route('/ask/stream', methods=['POST'])
def ask_stream():
    data = request.get_json()
    question = data.get('question', '')
    attachments = data.get('attachments', [])
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    attachment_context = _build_attachment_context(attachments)
    question_payload = question + attachment_context
    
    def generate():
        try:
            for chunk in ai.stream_answer(question_payload):
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/history', methods=['GET'])
def history():
    return jsonify({"history": ai.get_history()})

@app.route('/clear', methods=['POST'])
def clear():
    ai.history = []
    return jsonify({"status": "History cleared"})


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _build_attachment_context(attachments: List[Dict[str, str]]) -> str:
    if not attachments:
        return ""
    
    context_blocks = []
    for att in attachments:
        label = att.get("name", "file")
        url = att.get("url", "")
        snippet = _load_attachment_snippet(url)
        entry_lines = [f"- {label} ({url})"]
        if snippet:
            entry_lines.append("Excerpt:\n" + snippet)
        context_blocks.append("\n".join(entry_lines))
    
    if not context_blocks:
        return ""
    
    return "\n\nAttachments Provided:\n" + "\n\n".join(context_blocks)


def _load_attachment_snippet(url: str) -> Optional[str]:
    if not url or "/uploads/" not in url:
        return None
    
    relative_part = url.split("/uploads/", 1)[-1]
    safe_relative = os.path.normpath(relative_part).replace("\\", os.sep)
    if safe_relative.startswith(".."):
        return None
    
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_relative)
    if not os.path.isfile(file_path):
        return None
    
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext not in TEXTUAL_EXTENSIONS:
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            snippet = file.read(MAX_ATTACHMENT_CONTEXT_CHARS + 1)
    except Exception:
        return None
    
    truncated = len(snippet) > MAX_ATTACHMENT_CONTEXT_CHARS
    snippet = snippet[:MAX_ATTACHMENT_CONTEXT_CHARS].strip()
    if not snippet:
        return None
    
    if truncated:
        snippet += "\n...[truncated]..."
    return snippet


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_name = f"{timestamp}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)
    
    return jsonify({
        "name": filename,
        "url": f"/uploads/{unique_name}",
        "type": file.mimetype or "application/octet-stream",
        "size": os.path.getsize(file_path)
    })


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

if __name__ == '__main__':
    print("🤖 AI Question Answering System Starting...")
    print(f"✅ Using AI Provider: {AI_PROVIDER or 'None (configure one below)'}")
    print("\n💡 FREE Options Available:")
    if OLLAMA_AVAILABLE:
        print("   ✅ Ollama detected (100% FREE)")
    else:
        print("   ⚠️  Ollama not running - Install from https://ollama.ai")
    if GROQ_CLIENT:
        print("   ✅ Groq API configured (FREE tier)")
    else:
        print("   ⚠️  Groq not configured - Get free key: https://console.groq.com")
    if OPENAI_CLIENT:
        print("   ✅ OpenAI configured (PAID)")
    print("\n🌐 Visit http://localhost:5000 to use the app")
    app.run(debug=True, port=5000)
