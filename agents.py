from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL  = "openai/gpt-oss-20b"


model = ChatGroq(
    model = MODEL, 
    temperature =0.5, 
    api_key= API_KEY 
)

def technical_agent(question:str) -> str:
    """Technical Agent - Agent which is specialized for technical tasks  """
    llm = model 
    prompt =f""" You are a Technical Support Agent
    Your Job - 
    1. Help the users with the authentication errors , API issues and software setup and software Installation , 
    2. Explain the solution in simple step by step 
    3. The language should be easy to understand , Never use vague or double meaning words 
    4. Do not fabricate or create the information other than the information provided by the user
    
    Customer_question :{question}

    Return the helpful answer along with the above parameters 
    """
    return llm.invoke(prompt).content

def billing_agent (question:str) -> str :
    """Billing agent , The agent will be responsible for all the billing related information"""
    llm = model
    prompt = f"""You are a Billing Support Agent
    
    Your Job - To give information about the billing policy 
    1. Starter plan - $5 per month 
    2. Pro plan - $10 per month 
    3. Exclusive paln - $20 per month 
    Refund requests will be carefully reviewed by the billing team 
    The response to the query should be polite and decent . 
    Never ask for passwords and credit card numbers from the user to get the details . 

    Customer_question :{question}
    """
    return llm.invoke(prompt).content

def general_agent(question:str) -> str:
    """ General agent - The agent will be responsible for the general Q/A queries for procedures and policy"""
    llm = model 
    prompt = f""" You are a simple general agent 
    Your Job - 
    1. Be polite and decent when addressing the user query .
    2. If the question consists of any technical details and billing details , 
    Please promptly reply that this will be handled by the appropriate specialist

    Customer_question:{question}

    Return with a proper response 

    """
    return llm.invoke(prompt).content

def reviewer_agent (question:str, draft:str) -> str :
    """Reviewer agent- The agent will be responsible for the reviewing of the text and provide some certain changes require for the final answer"""
    llm = model 
    prompt = f"""You are a reviewer agent in a production support Customer system 
    Your Job - 
    check the draft answer for - 
    1. clarity 
    2. Preservation 
    3. unsafe requests / like showing Password numbers and CVV 
    4. Unnnecessary complexity or vague words 

    Rewrite the answer if needed .  
    Customer_question :{question}
    Draft :{draft}

    return only the improved answer , Don't come up with the data if you don't have any information about it . 
    
    """
    return llm.invoke(prompt).content 