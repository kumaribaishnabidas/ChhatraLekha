# ChhatraLekha — Examination & Result Moderation Workflow

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Multi-Stage Assessment & Moderation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Faculty as Teacher / Instructor
    participant ExamService as Examination Service
    actor Head as Head of Dept / Examination Controller
    actor Principal as Principal / University Registrar
    participant Audit as Hash-Chained Audit Trail
    participant Wallet as Student Wallet & Transcripts
    
    Faculty->>ExamService: POST /api/v1/examinations (Create Assessment: Max Marks, Passing Marks)
    ExamService-->>Faculty: Assessment Scheduled
    
    Note over Faculty: Students sit for examination / submit project
    
    Faculty->>ExamService: POST /api/v1/examinations/{id}/marks (Enter Marks per Student)
    ExamService->>ExamService: Validate Marks <= Max Marks & Non-Negative
    Faculty->>ExamService: POST /api/v1/examinations/{id}/submit-moderation
    
    Head->>ExamService: GET /api/v1/examinations/{id}/moderation-queue
    ExamService-->>Head: Score Distribution, Mean, Standard Deviation, Outliers
    Head->>ExamService: POST /api/v1/examinations/{id}/moderate (Apply Scaling or Approve Raw)
    
    Principal->>ExamService: Review Final Result Sheet
    Principal->>ExamService: POST /api/v1/examinations/{id}/publish (Final Authorization)
    ExamService->>Audit: Append Signed Event (EXAM_RESULTS_PUBLISHED, approver=Principal)
    ExamService->>Wallet: Generate Verifiable Transcripts & Update GPA/CGPA
    ExamService-->>Wallet: Results Live on Student Dashboard & Parent Portal
```

---

## 2. Integrity Safeguards

1. **Role-Segregated Moderation:**
   - Teachers cannot independently publish final semester grades without Departmental / Controller approval.
   - AI tools may suggest statistical summaries (bell curve, standard deviation), but **AI must never automatically approve or publish academic results**.
2. **Immutable Result Records:**
   - Published transcripts receive an opaque SHA-256 verification token.
   - Any post-publication grade correction requires a formal Academic Council review ticket and produces a new sealed transcript version (`v2`), preserving `v1` in the audit ledger.
