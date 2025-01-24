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

question = " You’ve managed projects before; describe a situation where you had to adjust your project plan due to unforeseen circumstances. How did you re-allocate resources and maintain stakeholder communication during this change, and what metrics did you use to track the impact of this adjustment?"
template = """
      *   **Expected Approach:** The candidate should describe a specific project example where a change occurred. They should explain the 
original plan, the nature of the unforeseen circumstance, and the steps taken to re-allocate resources (e.g., shifting team members, re-
prioritizing tasks) and maintain communication (e.g., updated timelines, regular meetings, specific notifications of changed aspects) with both 
internal and external stakeholders. The response should include specific metrics like schedule variance, budget adjustments, client satisfaction 
scores to show how they tracked progress and the impact of these changes. The answer should demonstrate clear decision making, 
communication effectiveness, and adaptation.
        *  **Criteria:** Must include an specific example, clearly stating the initial plan, the unexpected event, mitigation strategies,  and metrics 
used to track impacts of changes. The user should show how they took charge by actively re-assessing and acting on the project to minimise 
the losses
"""

agent = Agent(
    model = Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv('GEMINI_API_KEY')),
    storage=SqlAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
    # memory=AgentMemory(db=vector_db,create_session_summary=True, create_user_memories=True),
    add_history_to_messages=True,
    num_history_responses=3,
    description=(
        "You are a professional interviewer who is supposed to evaluate people based on their resume."
        f"The question asked is {question}."
        f"The expected answer template is {template}."
                 ),
    instructions="See if the person if answering the right way similar to template. If the person isnt able to answer or the answer is deviating from the required ans guide him/her toward the ans.If he says 'no' then no need to ask further just output 'correct'.Dont add any unnecessary text.",
    debug_mode=True
)
while True:
    prompt = input("What is your question?\n")
    if(prompt == "exit"):
        break
    run: RunResponse = agent.run(prompt)
    print(run.content)