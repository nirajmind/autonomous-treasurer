### **Inspiration**

As a freelancer currently navigating the job market, managing "runway" isn't just a business metric—it's personal survival. I realized that while I have plenty of AI tools to *summarize* my financial situation, I have zero tools that can actually *manage* it.

Current AI agents are "read-only." They can tell you an invoice is due, but they can't pay it because traditional banking APIs are too closed and friction-heavy for autonomous agents. I wanted to build "The Autonomous Treasurer" to bridge this gap: a tool that uses the programmable nature of **MNEE** to give an AI agent the power to act as a responsible, reliable "Fractional CFO" for the gig economy.

### **What it does**

**The Autonomous Treasurer** is an agentic workflow that manages accounts payable for freelancers and small businesses.

* **Invoice Ingestion:** It monitors an inbox for incoming invoices (PDFs/Images) and uses AI to extract vendor details, due dates, and amounts.  
* **Policy & Validation:** It checks the invoice against a user-defined monthly budget. If the amount is within the "safe limit" (e.g., \<$50), it proceeds autonomously. If it's suspicious or high-value, it pauses for human approval.  
* **MNEE Payments:** It executes the payment directly on-chain using the MNEE stablecoin, ensuring instant, low-fee settlement.  
* **Runway Dashboard:** A Vue.js frontend visualizes the user's real-time financial health, showing exactly how many months of runway remain based on the agent's spending activity.

### **How we built it**

We prioritized **reliability over hype**, using a robust stack designed for financial correctness:

* **The Brain (AI):** We used **LangChain** and OpenAI to build the agent capable of parsing unstructured invoice data and making policy decisions.  
* **The Hands (Settlement):** We utilized **Web3.py** to interact with the MNEE smart contracts on Ethereum, treating the stablecoin as a programmable settlement layer.  
* **The Heart (Reliability):** Crucially, we implemented the **SAGA Design Pattern** in our Python backend. This ensures that every payment is a multi-step transaction with compensatable actions. If an on-chain transaction fails, the local database rolls back perfectly—no "ghost" payments or lost funds.  
* **Frontend:** Built with **Vue.js** for a reactive, clean user interface.

### **Challenges we ran into**

* **The "Hallucination" Risk:** LLMs can sometimes misread numbers (e.g., reading a generic ID "2025" as a price "$2025"). We had to implement strict validation layers and regex fail-safes before the agent could authorize any MNEE transaction.  
* **Syncing States:** Bridging the asynchronous world of Blockchain (waiting for confirmations) with the synchronous world of an API was tricky. The SAGA pattern helped us manage these states without blocking the user experience.

### **Accomplishments that we're proud of**

* **Bringing "Senior" Tech to a Hackathon:** Successfully implementing the **SAGA pattern** for transaction management. Most hackathon projects ignore error handling; ours treats it as a first-class citizen.  
* **True Autonomy:** Seeing the first successful end-to-end flow where an invoice was emailed, parsed, and paid in MNEE without a single human click.  
* **Bridging Web2 and Web3:** Creating a seamless experience where a standard PDF invoice results in a crypto-native settlement.

### **What we learned**

* **Stablecoins are the missing link for Agents:** Volatile crypto makes automated payments risky. MNEE's stability is what makes "Autonomous Finance" actually viable for business operations.  
* **Trust is UI:** The most important part of the app wasn't the payment itself, but the "Audit Log" that showed the human exactly *why* the agent made a decision.

### **What's next for The Autonomous Treasurer**

* **DeFi Yield Integration:** Programming the agent to automatically move "idle" runway funds into a yield-bearing MNEE protocol when no bills are due.  
* **Multi-Sig Support:** Adding a layer where the AI proposes a transaction and the human signs it, for larger organizations.  
* **Accounting Integrations:** Automatically syncing the MNEE payment metadata with tools like Xero or QuickBooks.