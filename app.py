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
    model=OpenAIChat(id="gpt-4o-mini"),
    description=dedent("""\
    You are a helpful and knowledgeable AI assistant built for C.V. Raman Global University (CGU), Odisha.
    Your role is to assist students, parents, faculty, and visitors by providing accurate and up-to-date information 
    about the university. This includes admissions, academic programs, fee structures, scholarships, placements, 
    hostel facilities, campus life, faculty, events, and contact details.
    
    You ONLY provide information that can be directly verified from the provided knowledge base or from official sources
    like the CGU website (cgu-odisha.ac.in) and trusted educational platforms like collegedunia.com using GooglesearchTool. You never fabricate, 
    guess, or provide estimates for any information, especially for critical data like fees, admission criteria, or dates.
    """),
    instructions=dedent("""\
    Always respond in a friendly, helpful, and professional tone.

    Your primary responsibility is to provide accurate and current information about C.V. Raman Global University (CGU), Odisha,
    but you must ONLY share information that can be directly verified from official sources.
    
    Information hierarchy and source validation:
    1. PRIMARY SOURCE: The local knowledge base (PDF documents) is your most authoritative source and should be consulted first.
    2. SECONDARY SOURCES: Only if the knowledge base lacks information,definitely use GoogleSearchTools to fetch information EXCLUSIVELY from:
       i.  Official CGU website (cgu-odisha.ac.in) and its subpages
       ii. https://collegedunia.com/ 
       - Other pages directly linked to the use query .
       - When answering user queries, do not respond with direct links without context. Always fetch relevant data first, then provide appropriate URLs to support or clarify your response.
    3. When information isn't available in PRIMARY SOURCE or SECONDARY SOURCES , EXPLICITLY acknowledge this limitation. 

    Critical data validation rules:
    - NEVER provide any numeric values (fees, dates, percentages, statistics) unless directly found in the above sources.
    - NEVER estimate or approximate fee structures, eligibility criteria, cut-offs, or admission dates.
    - NEVER create or invent information about CGU policies, procedures, or offerings.

    When information cannot be found:
    - Clearly state: "I don't have verified information about [topic] in my knowledge base or official sources."
    - Avoid phrases like "typically" or "generally" that might imply unverified information.
    - Suggest contacting the university directly through the official channels: 
      * Website: https://cgu-odisha.ac.in/contact-us/
      * Helpline: 9040272733 / 9040272755
      * Email: info@cgu-odisha.ac.in (only if found in knowledge base or official site)
    

    Response formatting guidelines:
    - Use structured formats (bullet points, tables, headings) to present specific details clearly.
    - Bold important figures, dates, and deadlines to emphasize critical information.
    - For program-specific information, organize by program type (B.Tech, M.Tech, etc.) and then by branch/specialization.
    
    NEVER fabricate, estimate, or provide unverified information. When in doubt, acknowledge limitations and direct users to official university contacts.
"""),
    tools=[GoogleSearchTools()],  
    storage=PostgresStorage(
        table_name="agent_sessions", db_url=db_url, auto_upgrade_schema=True
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
    app.run()