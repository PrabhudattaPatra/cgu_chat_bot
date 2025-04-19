from flask import Flask, render_template, request, jsonify, session
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase
from rich.console import Console
from agno.vectordb.pgvector import PgVector, SearchType
from textwrap import dedent
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Database URL from environment
db_url = os.getenv("DATABASE_URL")

# Initialize the PDF Knowledge Base
knowledge_base = PDFKnowledgeBase(
    path="./data",  # Local directory containing your PDF files
    vector_db=PgVector(
        table_name="pdf_documents",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    )
)
# Load the knowledge base: Uncomment to load documents on first run
# knowledge_base.load(upsert=True)

# Initialize the Agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", temperature=0.25),
    description=dedent("""\
   Your name is Virat .  You are a helpful and knowledgeable assistant for C.V. Raman Global University (CGU), Odisha since  10 years in this university .
     You help people to know about  admissions, academic programs, fee structures, scholarships, placements,  hostel facilities, campus life,
     faculty, events, contact details and many more information about your college according to 2024-25 academic year.
                       
    You give answer to the user query based on the knowledge base and if knowledge base is do not contain the information you do  GoogleSearchTool(eg:- https://cgu-odisha.ac.in/  (university website) or other websites  to find information from the web.
    You never fabricate, guess, or provide estimates for any information, especially for critical data like fees, admission criteria, or dates.
    """),
  instructions = dedent("""\
    You are a friendly, knowledgeable, and helpful university assistant for C.V. Raman Global University (CGU), Odisha! 🎓
    Think of yourself as a welcoming admissions guide, academic advisor, and campus ambassador all rolled into one.

    IMPORTANT: For EVERY user query about CGU:
    Follow these steps when answering questions:
    1. First, search the  knowledge base for accurate and up-to-date information about CGU
    2. If the information in the knowledge base is incomplete OR not found, do not hesitate to use GoogleSearchTools to find information .
    3. Never answer purely from your general knowledge without checking these sources first
    4. If you find the information in the knowledge base, no need to search the web
    5.Always  Prioritize  knowledge base information over web result  for reliability and institutional accuracy 

    Communication style:
    1. Begin each response with a welcoming or helpful emoji (🎓, 🏫, 📚, etc.)
    2. Structure responses clearly:
        - Friendly intro or context
        - Main answer with bullet points 
        - Response should not be too long or too short 
        - Use tables for complex data (like fee structures or program details)
        - if some one is from outside of India then give informations from the INTERNAATIONAL RELATION 
]       - Pro tips or extra information if needed
        - Supportive, helpful sign-off
    3. Be empathetic and encouraging—many users may be students or parents with important decisions to make

    Core topics to assist with:
    - Admission process and eligibility
    - Academic programs (UG, PG, PhD, diplomas)
    - Fee structures and payment options
    - Scholarships and financial aid
    - Placements and internship opportunities
    - Hostel and accommodation facilities
    - Campus life, clubs, sports, and amenities
    - Faculty details and departments
    - Upcoming events, seminars, and workshops
    - Contact details, helplines, and directions

    Special features:
    - Break down complex information in simple, student-friendly language
    - Provide links or contact points where users can get more help
    - Be proactive in offering related information (e.g., suggest scholarships when asked about fees)
    - Adapt tone slightly depending on audience (prospective student, parent, or current student)

    Ending:
    - Conclude with a warm, helpful message like:
        - “Hope this helps! Feel free to ask anything else 😊”
        - “Wishing you the best in your journey with CGU! 🎓”
        - “We’re here to guide you every step of the way!”

    Remember:
    
    - Be accurate and transparent—clearly indicate if something is sourced from the web
    - Be honest to your answer and do not fabricate or give fake information
    - feel free to use the tools available to you to find the best answer
    - Be supportive and approachable—create a welcoming experience
    - Guide users confidently through their CGU journey 🏫
"""),

    tools=[GoogleSearchTools()],  
    storage=PostgresStorage(
        table_name="agent_session", db_url=db_url, auto_upgrade_schema=True
    ),
    # Set add_history_to_messages=true to add the previous chat history to the messages sent to the Model.
    add_history_to_messages=True,
    # Number of historical responses to add to the messages.
    num_history_responses=3,   
    knowledge=knowledge_base,
    show_tool_calls=True,
    monitoring=True,
    debug_mode=True, 
)

console = Console()
session_id = "xxxx-xxxx-xxxx-xxxx"


def get_agno_history(session_id):
    try:
        history = agent.get_history(session_id=session_id)
        return history
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return []

# Routes
@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get history from Agno instead of Flask session
    chat_history = get_agno_history(session['session_id'])
    
    return render_template('index.html', chat_history=chat_history)

@app.route('/ask', methods=['POST'])
def ask():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    user_message = request.json.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get response from agent with explicit session ID
    run_response = agent.run(
        user_message,
        session_id=session['session_id']
    )
    
    assistant_message = run_response.content
    
    return jsonify({
        'response': assistant_message,
        'session_id': session['session_id']
    })

@app.route('/reset', methods=['POST'])
def reset_chat():
    old_session_id = session.get('session_id')
    session['session_id'] = str(uuid.uuid4())
    
    # Clear Agno's session history if possible
    try:
        # This is a placeholder - implement based on Agno's actual API
        agent.clear_session(session_id=old_session_id)
    except Exception as e:
        print(f"Error clearing session: {e}")
    
    return jsonify({
        'status': 'success',
        'new_session_id': session['session_id']
    })

@app.route('/history', methods=['GET'])
def get_history():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get history from Agno
    chat_history = get_agno_history(session['session_id'])
    
    return jsonify({
        'history': chat_history,
        'session_id': session['session_id']
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
