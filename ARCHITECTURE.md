# Autonomous Treasurer - System Architecture

## Admin Dashboard Architecture

```mermaid
graph TB
    subgraph Frontend["🖥️ Frontend (Vue.js)"]
        Dashboard["Admin Dashboard<br/>(DashboardView)"]
        Login["Login View"]
        Dashboard -->|Displays| Stats["📊 Financial Stats<br/>• Balance<br/>• Monthly Burn<br/>• Runway Months"]
        Dashboard -->|Shows| Logs["📋 Transaction Logs<br/>• Status<br/>• Vendor<br/>• Amount<br/>• Hash"]
        Dashboard -->|Manages| Settings["⚙️ Settings<br/>• Approval Limit"]
    end

    subgraph Backend["🔧 Backend (FastAPI)"]
        Auth["🔐 Authentication<br/>(JWT Tokens)"]
        DashboardAPI["GET /api/dashboard<br/>GET /api/dashboard/logs"]
        SettingsAPI["GET /api/settings/limit<br/>POST /api/settings/limit"]
        InvoiceAPI["POST /api/process-invoice"]
        
        Auth -->|Validates| DashboardAPI
        Auth -->|Validates| SettingsAPI
        Auth -->|Validates| InvoiceAPI
    end

    subgraph Processing["⚙️ Business Logic"]
        SagaOrch["SagaOrchestrator<br/>(Payment Orchestration)"]
        InvoiceParser["InvoiceParser<br/>(AI Analysis)"]
        ApprovalQueue["Approval Queue<br/>(Pending Approvals)"]
        
        InvoiceAPI -->|Parse| InvoiceParser
        InvoiceParser -->|Execute| SagaOrch
        SagaOrch -->|Requires Approval?| ApprovalQueue
    end

    subgraph Storage["💾 Data Storage"]
        Redis["⚡ Redis<br/>• Daily Logs<br/>• Approval Queue<br/>• Settings Cache"]
        PostgreSQL["🗄️ PostgreSQL<br/>• Transactions<br/>• Users<br/>• Config"]
    end

    subgraph Blockchain["🔗 Blockchain"]
        Web3["Web3 Integration<br/>(Soneium Network)"]
        MNEE["MNEE Token<br/>Balance Check"]
    end

    DashboardAPI -->|Fetch Live| Redis
    DashboardAPI -->|Fallback| PostgreSQL
    SettingsAPI -->|Read/Write| Redis
    SettingsAPI -->|Sync| PostgreSQL
    
    SagaOrch -->|Save TX| PostgreSQL
    SagaOrch -->|Log Event| Redis
    SagaOrch -->|Check Balance| Web3
    Web3 -->|Query| MNEE
    
    Dashboard -->|API Calls| DashboardAPI
    Dashboard -->|Update Limit| SettingsAPI
    Dashboard -->|View Approvals| ApprovalQueue
    
    Login -->|Auth| Auth
```

## Transaction Flow with Admin Dashboard

```mermaid
sequenceDiagram
    actor Admin as Admin User
    participant FE as Dashboard (Frontend)
    participant API as FastAPI Backend
    participant Parser as Invoice Parser
    participant Saga as Saga Orchestrator
    participant DB as PostgreSQL
    participant Cache as Redis
    participant BC as Blockchain

    Admin->>FE: Login
    FE->>API: POST /token
    API->>DB: Verify Credentials
    API-->>FE: JWT Token
    
    Admin->>FE: View Dashboard
    FE->>API: GET /api/dashboard/logs
    API->>Cache: lrange treasury:daily_logs
    alt Redis has data
        Cache-->>API: Return logs
    else Redis empty
        API->>DB: Query TransactionModel
        DB-->>API: Historical data
    end
    API-->>FE: Logs + Stats
    FE-->>Admin: Display Transactions

    Admin->>FE: Update Approval Limit
    FE->>API: POST /api/settings/limit
    API->>Cache: SET system:approval_limit
    Cache-->>API: Updated
    API-->>FE: Success
    FE-->>Admin: ✅ Limit Updated

    Note over Admin,BC: When Invoice Arrives
    
    FE->>API: POST /api/process-invoice
    API->>Parser: parse_invoice_text()
    Parser-->>API: {vendor, amount}
    
    API->>Saga: execute_payment_saga()
    Saga->>BC: Check Balance
    BC-->>Saga: MNEE Balance
    
    alt Amount > Approval Limit
        Saga->>Cache: lpush treasury:approvals
        Saga-->>API: REQUIRES_APPROVAL
        API-->>FE: {status: PAUSED_FOR_APPROVAL}
        FE-->>Admin: 🛑 Approval Needed
    else Amount <= Limit
        Saga->>BC: Send Payment
        BC-->>Saga: tx_hash
        Saga->>DB: Save Transaction
        Saga->>Cache: Log to redis
        Saga-->>API: SUCCESS
        API-->>FE: {status: PAID, tx_hash}
        FE-->>Admin: ✅ Payment Sent
    end
    
    Admin->>FE: View Updated Logs
    FE->>API: GET /api/dashboard/logs
    API-->>FE: Latest transaction
    FE-->>Admin: Transaction appears in logs
```

## Admin Dashboard Data Model

```mermaid
erDiagram
    ADMIN ||--o{ TRANSACTION : "views"
    ADMIN ||--o{ SYSTEMCONFIG : "updates"
    TRANSACTION ||--o{ APPROVAL : "may_require"
    
    ADMIN {
        string username PK
        string hashed_password
        timestamp created_at
    }
    
    TRANSACTION {
        int id PK
        string vendor
        float amount
        string status "CONFIRMED, FAILED, REQUIRES_APPROVAL"
        string tx_hash "Blockchain hash"
        float balance_snapshot "Balance at time"
        timestamp timestamp
    }
    
    APPROVAL {
        string id PK
        string vendor
        float amount
        string status "PENDING, APPROVED, REJECTED"
        timestamp created_at
    }
    
    SYSTEMCONFIG {
        string key PK "approval_limit"
        string value "Numeric limit"
        timestamp updated_at
    }
```

## API Endpoints for Admin Dashboard

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/` | GET | ❌ | Health check |
| `/token` | POST | ❌ | Login (get JWT) |
| `/api/dashboard` | GET | ✅ | Get treasury stats |
| `/api/dashboard/logs` | GET | ✅ | View transaction history |
| `/api/settings/limit` | GET | ✅ | Get approval limit |
| `/api/settings/limit` | POST | ✅ | Update approval limit |
| `/api/process-invoice` | POST | ✅ | Submit invoice for processing |

