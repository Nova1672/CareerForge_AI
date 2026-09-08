# CareerForge AI

CareerForge AI is a RAG-based Agentic AI Interview Preparation and Evaluation System built using IBM watsonx Orchestrate.

It is designed to conduct personalized mock interviews, evaluate candidate answers, provide structured feedback, and generate a final preparation roadmap.

## Problem Statement

**PS 22 — Interview Trainer Agent**

Traditional interview preparation is often generic and does not adapt to a candidate’s role, skills, experience, or project background.

CareerForge AI addresses this by creating a personalized interview workflow with answer evaluation and improvement feedback.

## Key Features

- Personalized interview questions based on role, skills, and experience
- One-question-at-a-time interview flow
- RAG-based interview knowledge retrieval
- 1–10 answer evaluation framework
- Strength and weakness identification
- Improved example answers
- Candidate Fact Grounding to reduce hallucination risk
- Final interview performance summary
- Preparation roadmap

## Technology Stack

- IBM watsonx Orchestrate
- GPT-OSS 120B via Groq
- Retrieval-Augmented Generation (RAG)
- CareerForge Interview Knowledge Base
- IBM watsonx.ai
- IBM Granite `granite-4-h-small`
- IBM Cloud

## System Workflow

Candidate Profile  
↓  
CareerForge AI  
↓  
RAG Retrieval  
↓  
Interview Knowledge Base  
↓  
GPT-OSS 120B via Groq  
↓  
Personalized Interview Question  
↓  
Candidate Answer  
↓  
Answer Evaluation  
↓  
Feedback and Improved Answer  
↓  
Next Question  
↓  
Final Performance Report

## RAG Knowledge Base

CareerForge uses a custom knowledge source called:

**CareerForge Interview Knowledge Base**

It contains interview-preparation content related to:

- Data Science
- Machine Learning
- Python
- Pandas
- NumPy
- SQL
- Classification concepts
- Evaluation metrics
- Behavioral and HR interviews
- Answer evaluation rubric
- Interview scoring guidance

RAG retrieval was tested successfully using the predefined 1–10 answer evaluation rubric.

## Answer Evaluation Framework

CareerForge evaluates candidate answers using the following scale:

- **9–10:** Technically accurate, relevant, complete, with strong reasoning
- **7–8:** Mostly correct with minor omissions
- **5–6:** Basic understanding but important details are missing
- **3–4:** Limited understanding with major omissions
- **1–2:** Mostly incorrect, irrelevant, or unsupported

## Candidate Fact Grounding

CareerForge includes Candidate Fact Grounding rules.

These rules prioritize candidate-provided information and instruct the agent not to invent:

- Project results
- Evaluation metrics
- Dataset details
- Features
- Tools
- Models
- Business impact
- Candidate achievements

When information is missing, placeholders should be used instead of fabricated facts.

This reduces hallucination risk, but does not completely eliminate hallucinations because the final response still depends on the underlying language model.

## IBM Granite Validation

IBM Granite was tested separately using IBM watsonx.ai Prompt Lab.

Model used:

`granite-4-h-small`

Granite successfully generated a relevant Data Scientist interview question while following candidate fact restrictions.

### Important Architecture Note

The deployed CareerForge AI agent uses:

**GPT-OSS 120B via Groq**

IBM Granite was used as a separate validation component and does not power the deployed CareerForge agent.

## Deployment

CareerForge AI was successfully deployed to the Live environment in IBM watsonx Orchestrate.

The deployed agent was tested with a final-year Computer Science student profile preparing for a Data Scientist internship.

The agent successfully generated personalized interview questions and evaluated candidate responses.

## Token Usage

IBM watsonx Orchestrate FinOps dashboard results for the last 7 days:

- Total Tokens: **68.9K**
- Input Tokens: **56.9K**
- Output Tokens: **12.0K**
- LLM Calls: **63**
- CareerForge AI Share: **100%**

## Project Limitations

- Some hallucination risk still remains
- IBM Granite was not available as the production model in the current watsonx Orchestrate tenant
- Resume parsing is not yet automated
- Voice interviews are not currently implemented
- Coding interview support is not yet included

## Future Scope

- Resume parsing
- Job Description matching
- Voice-based mock interviews
- Coding interview support
- Interview analytics dashboard
- Stronger hallucination safeguards
- Direct IBM Granite integration if available
- Multi-agent interview panels
- Multilingual interview preparation

## Project Status

- CareerForge Agent: Completed
- RAG Integration: Verified
- RAG Retrieval: Verified
- Live Deployment: Verified
- Personalized Interview Generation: Verified
- Answer Evaluation: Verified
- IBM Granite Validation: Completed

## Author

**Suraj Patil**
