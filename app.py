from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

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
    
    def answer_question(self, question):
        """Answer any question using AI - tries multiple free providers"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = """You are EDU AI, a meticulous research assistant.
Primary directives:
- Excel at advanced mathematics, step-by-step derivations, and symbolic reasoning
- Handle complex science, engineering, and programming questions with citations or references when relevant
- Support confidential or sensitive research: never store, log, or share user data beyond the current session
- When information is unknown or uncertain, clearly state limitations before offering best-effort reasoning
- Present answers with structured sections, bullet points, or equations for clarity

Always prioritize correctness, transparency, and privacy."""
        
        # Try providers in order: Groq (fast + math) -> OpenAI -> Ollama (local fallback)
        providers_to_try = []

        if self.groq_client:
            providers_to_try.append(("groq", self._try_groq))
        if self.openai_client:
            providers_to_try.append(("openai", self._try_openai))
        if self.ollama_available:
            providers_to_try.append(("ollama", self._try_ollama))
        
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
                answer = provider_func(question, system_prompt)
                if answer:
                    self.provider = provider_name
                    # Store in history
                    self.history.append({
                        "question": question,
                        "answer": answer,
                        "timestamp": timestamp,
                        "provider": provider_name
                    })
                    
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
    
    def _try_ollama(self, question, system_prompt):
        """Try Ollama (free, local)"""
        try:
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
                        "prompt": f"{system_prompt}\n\nUser: {question}\nAssistant:",
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
    
    def _try_groq(self, question, system_prompt):
        """Try Groq (free API tier)"""
        response = self.groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Free tier model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    
    def _try_openai(self, question, system_prompt):
        """Try OpenAI"""
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
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

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    attachments = data.get('attachments', [])
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    attachment_text = ""
    if attachments:
        formatted_attachments = [
            f"- {att.get('name', 'file')} ({att.get('url', '')})"
            for att in attachments
        ]
        attachment_text = "\n\nAttachments:\n" + "\n".join(formatted_attachments)
    
    result = ai.answer_question(question + attachment_text)
    result["attachments"] = attachments
    return jsonify(result)

@app.route('/history', methods=['GET'])
def history():
    return jsonify({"history": ai.get_history()})

@app.route('/clear', methods=['POST'])
def clear():
    ai.history = []
    return jsonify({"status": "History cleared"})


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
