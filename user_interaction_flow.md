# User Interaction Flow with Multiple Agents

```mermaid
flowchart TD
    Start([Application Start]) --> Init[Initialize Pygame & Screen]
    Init --> CheckAPI{API Key Available?}
    CheckAPI -->|No| Error[Display Error & Exit]
    CheckAPI -->|Yes| LoadAgents[Load Predefined Agents:<br/>- Utilitarian Dr. Sam Iqbal<br/>- Restorative Amara Ndlovu<br/>- Meritocratic Jamie Reyes<br/>- Rawlsian Jordan Chex]
    LoadAgents --> LoadCustom{CSV File Exists?}
    LoadCustom -->|Yes| LoadCustomAgent[Load Latest Custom Advocate]
    LoadCustom -->|No| CreateAgents
    LoadCustomAgent --> CreateAgents[Create JusticeAgent Instances]
    CreateAgents --> InitChat[Initialize ChatGUI<br/>with Toggle Switches for Each Agent]
    InitChat --> ChatState[CHAT State]

    ChatState --> UserAction{User Action}

    UserAction -->|Click Toggle Switch| ToggleAgent[Toggle Agent On/Off<br/>Green = Active, Red = Inactive]
    ToggleAgent --> ChatState

    UserAction -->|Click Create Advocate| SwitchToCreation[Switch to CREATION State]
    SwitchToCreation --> CreationState[CREATION State]

    UserAction -->|Type Message + Enter| ValidateInput{Input Not Empty?}
    ValidateInput -->|Empty| ChatState
    ValidateInput -->|Has Text| CheckActiveAgents{Any Agents Active?}

    CheckActiveAgents -->|No| ShowError[Display: 'No agents are active']
    ShowError --> ChatState

    CheckActiveAgents -->|Yes| CreateSession[Generate New Session ID]
    CreateSession --> SaveUserMessage[Save User Message to Memory<br/>for ALL Active Agents<br/>session_id, 'User', 'user', content]
    SaveUserMessage --> ProcessCustom{Is Custom Agent Active?}

    ProcessCustom -->|Yes| CustomResponse[Custom Agent Generates Response<br/>with session_id context]
    CustomResponse --> SaveCustomReply[Save Custom Agent Reply to Memory]
    SaveCustomReply --> ProcessOthers[Process Other Active Agents]

    ProcessCustom -->|No| ProcessOthers

    ProcessOthers --> LoopAgents{More Active Agents?}
    LoopAgents -->|Yes| NextAgent[Next Agent Generates Response<br/>Builds context from shared session_id<br/>Sees messages from User + All Agents]
    NextAgent --> SaveAgentReply[Save Agent Reply to Memory]
    SaveAgentReply --> AddToHistory[Add to Chat History]
    AddToHistory --> LoopAgents

    LoopAgents -->|No| DisplayMessages[Display Messages in GUI<br/>One at a time with 5-second delay]
    DisplayMessages --> ChatState

    CreationState --> FillForm[User Fills Form:<br/>1. Framework Name<br/>2. Justice Definition<br/>3. Core Values<br/>4. Tone/Personality]
    FillForm --> ClickSave{Click Save Button?}
    ClickSave -->|No| FillForm
    ClickSave -->|Yes| ValidateForm{All Fields Filled?}
    ValidateForm -->|No| FillForm
    ValidateForm -->|Yes| BuildPrompt[Build System Prompt from Answers]
    BuildPrompt --> SaveCSV[Save to advocates.csv]
    SaveCSV --> CreateNewAgent[Create New AgentProfile<br/>Create JusticeAgent Instance]
    CreateNewAgent --> ReinitGUI[Re-initialize ChatGUI<br/>with Updated Agent List]
    ReinitGUI --> ChatState

    ChatState --> QuitEvent{Pygame QUIT Event?}
    QuitEvent -->|No| ChatState
    QuitEvent -->|Yes| ClearDB[Clear Database on Exit]
    ClearDB --> End([Application End])
```

## Agent Response Generation Detail

```mermaid
sequenceDiagram
    participant User
    participant MainLoop
    participant Memory
    participant Agent1
    participant Agent2
    participant AgentN
    participant LLM

    User->>MainLoop: Type Message + Press Enter
    MainLoop->>MainLoop: Generate session_id
    MainLoop->>Memory: Save User Message (all active agents)

    alt Custom Agent Active
        MainLoop->>Agent1: generate_response(session_id)
        Agent1->>Memory: get_recent(session_id) - Last 12 turns
        Memory-->>Agent1: History with [Agent]: messages
        Agent1->>Agent1: Build context with system prompt
        Agent1->>LLM: Generate response (max_tokens)
        LLM-->>Agent1: Response text
        Agent1->>Memory: Save response to memory
        Agent1-->>MainLoop: Response
        MainLoop->>MainLoop: Add to chat_history
    end

    loop For Each Other Active Agent
        MainLoop->>AgentN: generate_response(session_id)
        AgentN->>Memory: get_recent(session_id) - Last 12 turns
        Note over Memory,AgentN: Agent sees:<br/>- User messages<br/>- All agents' responses<br/>- From same session_id
        Memory-->>AgentN: Context history
        AgentN->>AgentN: Build context with own system prompt
        AgentN->>LLM: Generate response (max_tokens)
        LLM-->>AgentN: Response text
        AgentN->>Memory: Save response to memory
        AgentN-->>MainLoop: Response
        MainLoop->>MainLoop: Add to chat_history
    end

    MainLoop->>User: Display messages sequentially (5s delay)
```

## Memory & Context Sharing

```mermaid
graph LR
    subgraph "Session ID: abc-123"
        U1[User: Question about justice]
        A1[Agent1: Utilitarian Response]
        A2[Agent2: Restorative Response]
        A3[Agent3: Meritocratic Response]
    end

    subgraph "Shared Memory Database"
        DB[(justice_memory.db<br/>session_id, agent, role, content)]
    end

    subgraph "Agent 1 Context Building"
        C1[Get Recent Messages<br/>session_id='abc-123'<br/>Last 12 turns]
        C1 --> Build1[Build Context:<br/>User: Question<br/>Agent1: Response<br/>Agent2: Response<br/>Agent3: Response]
        Build1 --> LLM1[LLM with System Prompt]
    end

    U1 --> DB
    A1 --> DB
    A2 --> DB
    A3 --> DB
    DB --> C1

    style DB fill:#e1f5ff
    style C1 fill:#fff4e1
```

## Key Interaction Points

1. **Agent Activation**: Users toggle agents on/off via switches in the top-left
2. **Shared Context**: All active agents see the same conversation via shared
   `session_id`
3. **Sequential Responses**: Custom agent responds first (if active), then
   others sequentially
4. **Memory Window**: Each agent sees the last 12 turns (30-minute rolling
   window)
5. **Message Display**: Messages shown one at a time with 5-second intervals
6. **Custom Advocate Creation**: Users can create new agents that join the
   conversation
