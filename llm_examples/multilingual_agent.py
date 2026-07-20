from typing import Iterable

from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama

# Our multilingual knowledge base
documents = [
    Document(
        page_content="The company policy allows for up to 20 days of paid time off per year. Employees must request time off at least two weeks in advance.",
        metadata={"language": "English", "source": "HR_Policy_EN"},
    ),
    Document(
        page_content="Employees are entitled to 10 paid sick days per year. A doctor's note is required for absences longer than three consecutive days.",
        metadata={"language": "English", "source": "HR_Policy_EN_Sick"},
    ),
    Document(
        page_content="The company provides 12 weeks of paid parental leave for new parents, including adoption and foster placements. Leave must be taken within the first year after the child's arrival.",
        metadata={"language": "English", "source": "HR_Policy_EN_Parental"},
    ),
    Document(
        page_content="Employees may take up to 5 paid bereavement days following the death of an immediate family member, and up to 2 paid days for extended family.",
        metadata={"language": "English", "source": "HR_Policy_EN_Bereavement"},
    ),
    Document(
        page_content="La politique de l'entreprise accorde jusqu'a 20 jours de conges payes par an. Les employes doivent en faire la demande au moins deux semaines a l'avance.",
        metadata={"language": "French", "source": "HR_Policy_FR"},
    ),
    Document(
        page_content="El soporte tecnico esta disponible 24/7. Para problemas urgentes, llame al numero de emergencia en lugar de enviar un correo electronico.",
        metadata={"language": "Spanish", "source": "IT_Policy_ES"},
    ),
]

prompt = ChatPromptTemplate.from_template(
    """
You are a helpful assistant.
Use the retrieved context to answer the user's question.
The context may be in a different language than the question.
Answer in the same language as the user's question.

Context:
{context}

Question:
{question}

Answer:
""".strip()
)

# Helper function to combine our retrieved documents into a single string
def format_docs(docs: Iterable[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

# A model trained to map different languages to the same vector space
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Load the documents into a local Chroma vector database
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="multilingual_hr_docs",
)

# Set up the retriever to fetch the top 2 most relevant chunks
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Initialize local LLM
llm = ChatOllama(model="llama3:8b", temperature=0)

# Build the pipeline
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Test 1: English query hitting Spanish context
query_en = "How do I handle urgent IT issues?"
print(f"User: {query_en}")
print(f"AI: {rag_chain.invoke(query_en)}")
print("-" * 50)

# Test 2: French query hitting French/English context
query_fr = "Combien de jours de conges payes puis-je prendre ?"
print(f"User: {query_fr}")
print(f"AI: {rag_chain.invoke(query_fr)}")
print("-" * 50)

# Test 3: Spanish query hitting English-only sick leave policy
query_es = "Cuantos dias de baja por enfermedad tengo?"
print(f"User: {query_es}")
print(f"AI: {rag_chain.invoke(query_es)}")