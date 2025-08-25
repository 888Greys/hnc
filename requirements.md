Requirement Document

1. Background
HNC is a law firm specializing in family trust and wealth management with over 10 years of experience in handling wills and trusts.
 The firm currently operates entirely on manual processes, requiring repetitive back-and-forth communication to create accurate legal documents. This has resulted in time wastage and inefficiency.
The proposed AI solution aims to automate document generation, streamline workflows, and reduce the repetitive workload for lawyers.

2. Project Goals
Remove tedious manual processes involved in document preparation.


Reduce back-and-forth revisions by producing near-complete drafts from the start.


Allow quick data input via voice or text.


Generate legally compliant documents (aligned with Kenya Law) from pre-existing templates.


Maintain high security and data privacy.


Deliver a functional prototype to validate feasibility.



3. AI System Scope
3.1 Data Collection & Client Bio
AI should capture and store:
Bio Data:


Full client name


Marital status (spouse details)


Children’s details


Financial Data:


Assets and liabilities


Sources of income


Economic Context:


Economic standing and asset distribution preferences


Client Objectives:


Examples: Selling land, creating a trust, setting up a will


Available Options & Consequences:


E.g., implications of creating a trust vs. selling an asset


Existing Tool:
The current manual questionnaire template will be digitized as the primary data collection tool.



3.2 Proposal & Outcome Generation
The AI should be able to:
Take collected data → Search the internal database and Kenya Law (open source)


Generate an initial proposal based on:


Past proposals


Predefined templates (simple, intermediate, complex trust deeds)


Refine proposal internally


Send to client for review


Apply final refinements → Produce final legal document ready for signing


Primary goal: Get the client to sign and pay the service fee.

3.3 Document Types to be Generated
Will


Living Will


Share Transfer Will



4. Functional Requirements
4.1 AI Functionalities
Document Generation: From templates, customized based on client input.


Search & Retrieval: Pull relevant clauses, rules, and precedents from Kenya Law and internal database.


Proposal Refinement: Step-by-step improvement before client review.


User Profiles: Store client records for easy retrieval.


4.2 User Interface
Login System:


Tracks login history


Identifies if one user is accessing another’s account


Primary Device: Laptop


Prototype: Interactive workflow model to be built for testing feasibility.


4.3 Security & Privacy
All client data must remain internal.


No public publishing of data, even during AI training.


Open-source law data can be used, but client data must remain enclosed.



5. Non-Functional Requirements
Performance: Generate complete draft documents with minimal processing time.


Accuracy: Ensure legal compliance with Kenya Law.


Usability: Simple for lawyers to adopt with minimal training.


Scalability: Future-proof for additional document types.



6. Out of Scope
No integration with external systems (current workflows are fully manual).



7. Deliverables & Timeline
Deliverable
Due Date
Notes
First Manual  templates
11th September 2025
Will be based on existing questionnaire and deed templates
Workflow demonstration
Post-11th September 2025
Showcase prototype and document flow
Prototype testing
TBD
Internal validation before full deployment


8. Risks & Considerations
Lawyers may need time to adapt to AI workflows.


Ensuring 100% accuracy in legal documents is critical before client delivery.


AI must handle sensitive financial and personal data securely.
