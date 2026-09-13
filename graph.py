from typing import TypedDict, Literal 
from langgraph.graph import StateGraph, START, END 

from agents import (technical_agent, billing_agent,general_agent, reviewer_agent)

class SupportState(TypedDict):
    question:str
    route:str 
    draft:str 
    final_answer:str 
    blocked:bool 
    trace:list[str]

def guardrail_node(state:SupportState):
    """ A simple deterministic layer to block the unsafe content , In the real system it would include moderation 
    , PII redaction , permissions and policy checks . 
    """

    question= state['question'].lower()
    dangerous_phrases =[
        'give me the full password',
        'steal password',
        'give me the credit card number',
        'give me the CVV number', 
        'Steal the password'
    ]
    blocked = any(phrase in question for phrase in dangerous_phrases)
    trace = state.get('trace',[])+['Guardrail has checked the request']
    if blocked :
        return {
            "blocked":True , 
            "final_answer":("I can't help with requests involving passwords, stolen credentials, "
                "or full payment-card information."), 
            "trace":trace 
        }
    else :
        return {
            "blocked":False, 
            "trace" :trace

        }

def after_guardrail (state:SupportState)-> Literal["route", "end"]:
    if state["blocked"]:
        return "end"
    return "route"

def router_node (state:SupportState):
    """ We are using a simple router to route the request to the appropriate agent based on the question content .
    Production systems should not use an LLM for every decision.
    If a rule is simple and predictable, normal Python code is often
    cheaper, faster and easier to test.
    """
    question = state['question'].lower()
    technical_words =["error", "bug", "login", "api", "install"]
    billing_words = ["price", "pricing", "payment", "refund", "bill"]
    if any(word in question for word in technical_words):
        route="technical"
    elif any(word in question for word in billing_words):
        route="billing"
    else:
        route="general"
    return {
        "route":route, 
        "trace":state.get('trace',[])+[f"Router path:{route}"]
    }

def choose_agent(state:SupportState) -> Literal["technical_agent", "billing_agent", "general_agent"]:
    if state['route']=='technical':
        return "technical_agent"
    if state['route']=='billing':
        return "billing_agent"
    if state['route']=='general':
        return "general_agent"

def technical_node(state:SupportState) -> str:
    answer = technical_agent(state['question'])
    return {
        'draft':answer, 
        'trace' :state.get('trace', []) +["Technical agent created a draft"]
    }
def billing_node(state:SupportState) -> str:
    answer = billing_agent(state['question'])
    return {
        'draft':answer, 
        'trace':state.get('trace', [])+["Billing agent created a draft"]
    }
def general_node(state:SupportState)-> str:
    answer = general_agent(state['question'])
    return {
        'draft':answer, 
        'trace':state.get('trace', []) + ["General agent created a draft "]
    }
def reviewer_node(state:SupportState) -> str:
    answer = reviewer_agent(question= state['question'], draft = state['draft'])
    return {
        'final_answer':answer, 
        'trace':state.get('trace',[])+ ['Final answer for the Query ']
    }

builder = StateGraph(SupportState)
builder.add_node('guardrail', guardrail_node)
builder.add_node('route',router_node)
builder.add_node('technical_node', technical_node)
builder.add_node('billing_node', billing_node)
builder.add_node('general_node', general_node)
builder.add_node('reviewer_node', reviewer_node)

builder.add_edge(START, 'guardrail')
builder.add_conditional_edges(
    'guardrail', 
    after_guardrail, 
    {
        'route':'route',
        'end':END
    },
)
builder.add_conditional_edges(
    'route', 
    choose_agent,
    {
        'technical_agent':'technical_node',
        'billing_agent':'billing_node',
        'general_agent':'general_node'

    },
)
builder.add_edge('technical_node', 'reviewer_node')
builder.add_edge('billing_node', 'reviewer_node')
builder.add_edge('general_node', 'reviewer_node')

builder.add_edge('reviewer_node', END)

support_graph = builder.compile()

def run_workflow(question:str):
    initial_state:SupportState={
        'question':question, 
        'route':'',
        'draft':'', 
        'final_answer':'', 
        'blocked':False, 
        'trace':[]

    }
    result = support_graph.invoke(initial_state)
    return {
        "route":result.get('route','blocked'),
        'final_answer':result['final_answer'], 
        'trace':result.get('trace',[]),

    }









