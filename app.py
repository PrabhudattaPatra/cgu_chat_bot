from flask import Flask, render_template, request, jsonify, session
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase
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
# Load the knowledge base: Comment out after first run
# knowledge_base.load(upsert=True)

# Initialize the Agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini" , temperature=0.25),
    description=dedent("""\
   Your name is Virat .  You are a helpful and knowledgeable assistant for C.V. Raman Global University (CGU), Odisha since  10 years in this university .
     You help people to know about  admissions, academic programs, fee structures, scholarships, placements,  hostel facilities, campus life,
     faculty, events, contact details and many more information about your college . 
    """),
  instructions = dedent("""\
    You are a friendly, knowledgeable, and helpful university assistant for C.V. Raman Global University (CGU), Odisha! 🎓
    Think of yourself as a welcoming admissions guide, academic advisor, and campus ambassador all rolled into one.

    Follow these steps when answering questions:
    1. First, search the  knowledge base for accurate and up-to-date information about CGU
    2. If the information in the knowledge base is incomplete OR if the user asks something better answered through web data , use the web search(GoogleSearchTool) to fill in the gaps
    3. If you find the information in the knowledge base, no need to search the web
    4.Always  Prioritize  knowledge base information over web result  for reliability and institutional accuracy 
    5. Use the web only to supplement for:
        - Latest news, event updates, placement stats
        - External rankings, press releases, or collaborative programs
        - Additional context or verification
                         
    Communication style:
    1. Begin each response with a welcoming or helpful emoji (🎓, 🏫, 📚, etc.)
    2. Structure responses clearly:
        - Friendly intro or context
        - Main answer with bullet points or paragraphs
        - Use tables for complex data (like fee structures or program details)
        - Use this link (https://cgu-odisha.ac.in/CVRCEVIRTUALTOURWEB/CVRCEVIRTUALTOURWEB/) additionaly to show the campus virtual tour if user asks about campus life
        - Pro tips or extra information if needed
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
    add_history_to_messages=True,
    knowledge=knowledge_base,
    show_tool_calls=True,
    monitoring=True,
)

# Routes
@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/ask', methods=['POST'])
def ask():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    
    user_message = request.json.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Add user message to chat history
    session['chat_history'].append({'role': 'user', 'content': user_message})
    
    # Get response from agent
    run_response = agent.run(user_message)
    assistant_message = run_response.content
    
    # Add assistant message to chat history
    session['chat_history'].append({'role': 'assistant', 'content': assistant_message})
    session.modified = True
    
    return jsonify({
        'response': assistant_message
    })

@app.route('/reset', methods=['POST'])
def reset_chat():
    session['chat_history'] = []
    session['session_id'] = str(uuid.uuid4())
    return jsonify({'status': 'success'})



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
