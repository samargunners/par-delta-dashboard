name: "🚀 New Feature / Module"
description: "Checklist for starting a new Par-Delta feature or module"
title: "[Feature] <replace_with_feature_name>"
labels: ["feature", "par-delta"]
assignees: ["samarpatel"]

body:
  - type: markdown
    attributes:
      value: |
        ## 🚀 New Feature / Module Checklist (Par-Delta)

        **Owner:** Samar Patel  
        **Date Created:** <!-- auto-fill when issue created -->  
        **Feature Name:** <replace_with_feature_name>  
        **Linked GitHub Epic/Issue:** (if applicable)  

  - type: markdown
    attributes:
      value: |
        ### 1. Proposal & Design Doc ✅
        - [ ] Problem statement written  
        - [ ] Inputs/outputs defined  
        - [ ] Risks noted  
        - [ ] Success metrics defined  
        - [ ] Diagram of flow added  
        📄 File: `docs/features/<feature_name>_design.md`

        ### 2. Design Review ✅
        - [ ] Reviewed by Samar Patel  
        - [ ] Peer/AI feedback captured  
        - [ ] Trade-offs & mitigations logged  

        ### 3. Subsystem Specs ✅
        - [ ] Break into components  
        - [ ] Define API contracts / table schemas  
        - [ ] Create `/scripts/<feature_name>/README.md`  
        - [ ] SQL migration file prepared  

        ### 4. Backlog & Planning ✅
        - [ ] GitHub Epic created  
        - [ ] Stories/tickets created  
        - [ ] Acceptance criteria written  

        ### 5. Development (TDD-lite) ✅
        - [ ] Unit tests written first (`pytest`)  
        - [ ] Mock data prepared  
        - [ ] Core logic implemented  
        - [ ] Local run verified  

        ### 6. Code Review & Merge ✅
        - [ ] PR opened in GitHub  
        - [ ] All checks pass (lint, tests, CI)  
        - [ ] PR reviewed (self + AI suggestions applied)  
        - [ ] Docs updated  

        ### 7. CI/CD & Staging ✅
        - [ ] GitHub Actions pipeline green  
        - [ ] Tested on staging Supabase DB  
        - [ ] Tested on local/staging Streamlit  
        - [ ] Performance baseline checked  

        ### 8. Production Release ✅
        - [ ] Prod Supabase migration applied  
        - [ ] Prod Streamlit deployed  
        - [ ] Feature flags/env vars set correctly  
        - [ ] Rollback plan documented  

        ### 9. Monitoring & Iteration ✅
        - [ ] Logs monitored (Supabase, Streamlit)  
        - [ ] Alerts configured  
        - [ ] Post-release validation done  
        - [ ] Backlog updated with improvements  

        ---

        ### 📊 Status Tracker

        | Phase                  | Status | Notes |
        |-------------------------|--------|-------|
        | Proposal                | ☐      |       |
        | Design Review           | ☐      |       |
        | Subsystem Specs         | ☐      |       |
        | Planning                | ☐      |       |
        | Development             | ☐      |       |
        | Code Review & Merge     | ☐      |       |
        | CI/CD & Staging         | ☐      |       |
        | Release                 | ☐      |       |
        | Monitoring & Iteration  | ☐      |       |
