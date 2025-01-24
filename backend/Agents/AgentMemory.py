from phi.model.google import Gemini
from phi.agent import Agent, RunResponse, AgentMemory
import os
from dotenv import load_dotenv
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.vectordb.lancedb import LanceDb
from phi.vectordb.search import SearchType
from phi.embedder.sentence_transformer import SentenceTransformerEmbedder
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from phi.knowledge.llamaindex import LlamaIndexKnowledgeBase
load_dotenv()

question = """Explain how understanding the "Threat of New Entrants" within Porter's Five Forces framework can inform the development of a go-tomarket strategy."""
template = """
The candidate should begin by defining "Threat of New Entrants" within the context of Porter's Five Forces, explaining 
how it refers to the likelihood of new companies entering the market. They should then explain how understanding this threat—such as high 
barriers to entry (e.g., high capital requirements, strong regulations) vs. low barriers (e.g., ease of technology adoption, low initial investment)—
can directly influence a go-to-market strategy. For example, if the threat of new entrants is high, the candidate should suggest strategies 
focused on building strong brand loyalty, aggressively capturing market share, or establishing intellectual property barriers. Conversely, if the 
threat is low, the strategy might focus on efficiency and cost leadership. The answer should demonstrate an understanding that this analysis is 
not done in isolation, but rather as part of the overall market assessment.
"""
criteria = """
The response should correctly define the threat of new entrants, demonstrate how analyzing this threat impacts 
strategic decisions, and provide concrete examples of how this understanding informs market strategy development. The candidate should 
also demonstrate understanding that this concept does not exist in vacuum, and should be assessed with other concepts like the bargaining 
power of buyers and suppliers.
"""

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv('GEMINI_API_KEY')),
    storage=SqlAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
    # memory=AgentMemory(db=vector_db, create_session_summary=True, create_user_memories=True),
    add_history_to_messages=True,
    num_history_responses=3,
    description=(
        "You are a professional interviewer tasked with evaluating candidates based on their resumes. "
        f"The question asked is: '{question}'. "
        f"The expected approach for the answer should follow this template: '{template}'. "
        f"The criteria for judging the answer includes: '{criteria}'. "
        "Consider factors such as relevance, clarity, completeness, and how well the candidate's experience aligns with the question. "
        "Be mindful of potential misunderstandings or misinterpretations of the question by the candidate. "
        "Your goal is to assess their ability to articulate their qualifications effectively while providing constructive feedback."
    ),
    instructions=(
        "If the candidate's response does not meet expectations or lacks key details, provide gentle guidance with very small hints that steer them toward the correct answer. "
        "Avoid giving away the answer directly; instead, ask probing questions or suggest areas they might elaborate on. "
        "In cases where a candidate appears to misunderstand the question, clarify it without leading them too much. "
        "If a candidate provides an answer that is partially correct but missing critical elements, acknowledge what they did well while encouraging them to expand on their response. "
        "Once you determine that a candidate's answer meets the necessary criteria—demonstrating sufficient understanding, relevance, and detail—respond with 'correct' without any unnecessary text. "
        "Do not include any unnecessary text or commentary in your response; keep it concise and focused solely on the evaluation outcome."
    ),
    debug_mode=True
)

while True:
    prompt = input("What is your question?\n")
    if(prompt == "exit"):
        break
    run: RunResponse = agent.run(prompt)
    print(run.content)