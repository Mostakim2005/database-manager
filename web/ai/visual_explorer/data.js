/**
 * ==========================================================================
 * AI Architecture & Ecosystem Explorer - Modular Data Repository
 * ==========================================================================
 * This file contains the complete structured dataset for the visual explorer.
 * Any developer or future AI can modify, extend, or add nodes here easily.
 */

window.AI_DATA = {
  // Mode 1: Core Fast-Track Concepts (The User's direct journey)
  coreJourney: [
    {
      id: "ai",
      title: "Artificial Intelligence (AI)",
      badge: "Core Root",
      layman: "Computer programs designed to solve problems and make decisions that usually require human intelligence.",
      analogy: "The word 'Vehicle'. Anything that moves you without walking (bikes, trains, skateboards, sports cars) is a vehicle. AI is the broad family name for any machine exhibiting smart behavior.",
      tech: "Computational mechanisms performing cognitive functions including heuristic search (A*), constraint satisfaction (CSP), formal logic, and probabilistic inference. Function f: P* -> A."
    },
    {
      id: "ml",
      title: "Machine Learning (ML)",
      badge: "Core Discipline",
      layman: "Instead of writing strict rules by hand, you feed the computer millions of examples, and it discovers the rules by itself.",
      analogy: "Learning to write essays by reading 1,000 past student essays rather than memorizing a 5,000-rule grammar manual.",
      tech: "Empirical risk minimization adjusting model weights theta to minimize loss L(f_theta(x), y). Covers Supervised, Unsupervised, and Reinforcement Learning."
    },
    {
      id: "llm",
      title: "Large Language Models (LLM)",
      badge: "Foundation Brain",
      layman: "An ultra-smart text predictor trained on the internet that can write code, answer questions, and debate ideas.",
      analogy: "A student with photographic memory who read every book in the world library. When you write the start of a sentence, they instantly know how to finish it.",
      tech: "Autoregressive causal Transformer decoders trained on 10^12+ tokens with multi-head self-attention: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V."
    },
    {
      id: "chatbot",
      title: "Chatbots vs. Foundation Models",
      badge: "User Interface",
      layman: "The foundation model is the raw thinking brain; the chatbot is just the chat window and customer service desk you talk to.",
      analogy: "The singer performing in a recording studio is the Foundation Model; the speaker in your car playing the music is the Chatbot.",
      tech: "Application layer managing conversational state buffers, chat-template formatting (<|im_start|>), token streaming via Server-Sent Events (SSE), and session history."
    },
    {
      id: "frontier_models",
      title: "Frontier Models: DeepSeek, Claude, GPT",
      badge: "State-of-the-Art",
      layman: "The world's leading intelligence engines competing at the frontier. Claude excels at coding precision, DeepSeek achieved breakthrough efficiency at low cost, and OpenAI pioneered reasoning.",
      analogy: "Olympic decathletes: one sprints with raw power (GPT-4o), one is a chess strategist (Claude 3.7), and one designed lightweight shoes to match the record at 1/10th the cost (DeepSeek-R1).",
      tech: "DeepSeek-V3 (671B MoE with 37B active parameters), DeepSeek-R1 (large-scale GRPO reinforcement learning), and Claude 3.7 Sonnet (hybrid reasoning with dynamic thinking budgets)."
    },
    {
      id: "openrouter",
      title: "APIs & OpenRouter",
      badge: "API Gateway",
      layman: "The digital bridge connecting software to AI models. OpenRouter is a universal travel-booking adapter: one account lets you call 200+ different AI models.",
      analogy: "A universal power adapter plug. Instead of carrying 10 different plugs for foreign countries, you plug everything into one universal block.",
      tech: "OpenAI-compatible reverse proxy (https://openrouter.ai/api/v1) aggregating multiple model providers with automated load balancing, latency routing, and unified billing."
    },
    {
      id: "harness",
      title: "Agent Harness (Execution Framework)",
      badge: "Safety & Runtime",
      layman: "The safety cage, toolbox, and monitor around an AI. It gives the AI hands to run terminal commands, and stops it if it gets stuck.",
      analogy: "A driver's ed car. The student holds the steering wheel, but the instructor on the passenger side has the emergency brake and guides the route.",
      tech: "Supervisory runtime managing context window compaction, tool dispatch via JSON-RPC/subprocesses, sandbox isolation (Docker/VM), and benchmark scoring (SWE-bench)."
    },
    {
      id: "mcp",
      title: "Model Context Protocol (MCP)",
      badge: "Universal Protocol",
      layman: "The USB-C cable for AI. It connects any AI model to any database, Git repo, or tool using one standard protocol.",
      analogy: "The USB socket on your laptop. Before USB, every mouse, printer, and keyboard had different custom plugs. USB unified them all.",
      tech: "Anthropic's open JSON-RPC 2.0 standard decoupling Client hosts from external Servers over stdio or SSE transport. Exposes tools/call, resources/read, and prompts/get."
    },
    {
      id: "skills_agents",
      title: "Instruction Sets, Skills, Agents & Sub-Agents",
      badge: "Autonomous Architecture",
      layman: "Instructions set the permanent rules; Skills are specialized manuals; Agents are the workers using tools in a loop; Sub-agents are helpers handling research in the background.",
      analogy: "A science project: Instructions are the teacher's rubric; Skills are the lab manual; the Agent is the group leader; Sub-agents are teammates running errands.",
      tech: "5-layer encapsulation: Frozen Weights -> System Prompt Tokens -> SKILL.md Playbooks -> ReAct Loop State Machine -> Isolated Context Sub-Agents."
    },
    {
      id: "claude_code_antigravity",
      title: "Coding Agents: Antigravity & Claude Code",
      badge: "Frontier Applications",
      layman: "AI partners that don't just chat, but actively navigate your project, edit files, run tests in the terminal, and fix bugs autonomously.",
      analogy: "A senior pair programmer sitting beside you with their hands on the keyboard, writing code while you direct the overall strategy.",
      tech: "Agentic SWE platforms executing ReAct loops. Claude Code operates natively in CLI terminals; Antigravity provides a complete IDE environment with multi-agent orchestration."
    }
  ],

  // Mode 2: Horizontal Sister Domains (Included in Complex View)
  horizontalDomains: [
    {
      id: "cv",
      title: "Computer Vision (CV)",
      category: "Perception",
      layman: "Giving computers eyes to recognize faces, read street signs for self-driving cars, and detect fractures in medical X-rays.",
      analogy: "Your brain's visual cortex processing photons captured by your eyes.",
      tech: "Convolutional Neural Networks (CNNs) and Vision Transformers (ViT) solving object detection (YOLO), semantic segmentation, and Segment Anything (SAM)."
    },
    {
      id: "diffusion",
      title: "Diffusion Models (Media Generation)",
      category: "Generative Media",
      layman: "The engine behind Midjourney, FLUX, and Sora. It starts with television static noise and slowly clears it away until a crisp image emerges.",
      analogy: "A sculptor starting with a rough block of stone, chipping away tiny flakes until a smooth statue remains.",
      tech: "Reverses a Markov Gaussian noise addition process via score-based matching: q(x_t | x_{t-1}) = N(x_t; sqrt(1-beta_t)x_{t-1}, beta_t I)."
    },
    {
      id: "classical_ml",
      title: "Tabular ML (XGBoost & Trees)",
      category: "Spreadsheet Analytics",
      layman: "The workhorse algorithms banks and companies use on spreadsheets to detect credit card fraud or predict house prices.",
      analogy: "A committee of math teachers reviewing your attendance, quiz scores, and homework to predict your final exam grade.",
      tech: "Gradient Boosted Decision Trees (XGBoost, LightGBM, CatBoost) iteratively fitting weak learners to loss gradients."
    },
    {
      id: "robotics",
      title: "Robotics & Control Systems",
      category: "Physical Actuation",
      layman: "Giving machines physical bodies so they can walk, grasp objects, and navigate rooms without bumping into walls.",
      analogy: "Your physical muscles and nervous system coordinating to pick up a pencil.",
      tech: "Feedback control theory (PID, MPC), state estimation (Kalman filters), SLAM, and kinematic actuator modeling."
    },
    {
      id: "symbolic",
      title: "Symbolic AI & Knowledge Graphs",
      category: "Formal Logic",
      layman: "AI that follows giant rulebooks written by human experts. It doesn't guess with probabilities; it follows strict mathematical logic.",
      analogy: "A strict tax filing manual or legal flowchart where every step must be followed to the letter.",
      tech: "Ontologies, first-order predicate calculus, semantic web RDF triples, and formal inference engines."
    }
  ],

  // The 5 Layers of Agent Architecture
  agentStack: [
    {
      level: 5,
      name: "Sub-Agents (Child Workers)",
      badge: "Concurrency",
      analogy: "Teammates sent to the library to grab a single fact so the leader's desk doesn't get buried under 50 heavy books.",
      tech: "Child execution threads instantiated with isolated context buffers, executing scoped missions (research, testing) without context pollution.",
      code: "invoke_subagent({ TypeName: 'research', Role: 'Security Scanner', Prompt: 'Audit auth.py' })"
    },
    {
      level: 4,
      name: "The AI Agent (ReAct Loop)",
      badge: "Autonomous Worker",
      analogy: "The project leader holding the assignment sheet, walking to the lab bench, and recording data.",
      tech: "Event loop state machine: State_{t+1} = Execute(Model(State_t, Tools)). Manages tool dispatch, scratchpads, and self-correction.",
      code: "while not goal_achieved:\n  res = llm.generate(msgs, tools=tools)\n  if res.tool_call: msgs.append(execute(res.tool_call))\n  else: return res.text"
    },
    {
      level: 3,
      name: "Skills & MCP Tools",
      badge: "Capabilities & Knowledge",
      analogy: "The specialized recipe book and chef's knives pulled out only when baking pastries.",
      tech: "Procedural playbooks (SKILL.md) and JSON-RPC 2.0 tool schemas declaring parameters and return types.",
      code: "{\n  \"name\": \"replace_file_content\",\n  \"parameters\": { \"TargetFile\": \"string\", \"ReplacementContent\": \"string\" }\n}"
    },
    {
      level: 2,
      name: "Instruction Sets (System Prompt)",
      badge: "Persona & Rules",
      analogy: "The printed job description and safety rules given to an employee on day one.",
      tech: "Conditioning tokens at context index 0 establishing role boundaries, formatting constraints, and safety refusals.",
      code: "{\n  \"role\": \"system\",\n  \"content\": \"You are Antigravity, an AI software engineer. Verify edits with tests.\"\n}"
    },
    {
      level: 1,
      name: "Foundation Model (Weights)",
      badge: "Raw Intelligence",
      analogy: "A genius student with photographic memory locked in a soundproof room. Knows everything, but can only speak when asked.",
      tech: "Stateless floating-point weight tensors performing autoregressive forward matrix multiplications.",
      code: "logits = model(tokens)\nnext_token = sample(softmax(logits / temperature))"
    }
  ],

  // The 5 Pipelines
  pipelines: [
    {
      id: "training",
      name: "1. Model Design & Training",
      steps: [
        { name: "Data Ingestion", desc: "Crawling 15T+ tokens from web, books, code; deduplication via MinHash.", tech: "SentencePiece, BPE" },
        { name: "Pre-Training", desc: "Next-token prediction across 10,000+ GPUs for months.", tech: "Distributed AdamW, Megatron-LM" },
        { name: "SFT & Alignment", desc: "Instruction tuning and Reinforcement Learning (RLHF / GRPO).", tech: "GRPO, DPO, RLHF" },
        { name: "Quantization & Serving", desc: "Compressing weights to INT8/FP4 for low-latency inference.", tech: "vLLM, TensorRT-LLM, AWQ" }
      ]
    },
    {
      id: "consumer",
      name: "2. Consumer Chatbot Streaming",
      steps: [
        { name: "Prompt Submission", desc: "User types question in web UI; packages history into JSON payload.", tech: "React, HTTP/2 POST" },
        { name: "KV-Cache Lookup", desc: "Checks GPU memory for cached past conversation tokens.", tech: "PagedAttention, Radix Cache" },
        { name: "Next-Token Generation", desc: "Forward pass calculates logits; samples next token.", tech: "FlashAttention, Softmax" },
        { name: "SSE Streaming", desc: "Tokens stream to browser incrementally as Server-Sent Events.", tech: "HTTP SSE" }
      ]
    },
    {
      id: "enterprise",
      name: "3. Enterprise & Corporate RAG",
      steps: [
        { name: "SSO & Input Guardrails", desc: "Authenticates employee via Okta; redacts PII and passwords.", tech: "Okta, Presidio" },
        { name: "Hybrid RAG Search", desc: "Queries company vector DB and keyword index for private docs.", tech: "Qdrant, BM25, Cross-Encoder" },
        { name: "Private VPC Execution", desc: "Executes model inside secure HIPAA/SOC2 cloud VPC.", tech: "AWS Bedrock, Azure OpenAI" },
        { name: "Output Guardrails & Audit", desc: "Verifies facts against retrieved docs and logs audit trail.", tech: "Langfuse, Arize Phoenix" }
      ]
    },
    {
      id: "mcp",
      name: "4. Model Context Protocol (MCP)",
      steps: [
        { name: "Host Initialization", desc: "Antigravity/Claude Code reads config and launches MCP clients.", tech: "JSON config" },
        { name: "Server Handshake", desc: "Client discovers tools over stdio/SSE using JSON-RPC 2.0.", tech: "JSON-RPC 2.0" },
        { name: "Tool Dispatch", desc: "Agent issues tools/call with JSON arguments to MCP server.", tech: "stdio / HTTP SSE" },
        { name: "Result Injection", desc: "MCP server returns stdout/diff; injected back to LLM context.", tech: "ReAct loop" }
      ]
    },
    {
      id: "gpu",
      name: "5. Inside the GPU Tensor Engine",
      steps: [
        { name: "Continuous Batching", desc: "Dynamically merges concurrent requests at token boundaries.", tech: "vLLM Orca Scheduler" },
        { name: "RoPE Rotation", desc: "Applies rotary positional embeddings to Query and Key tensors.", tech: "RoPE Complex Matrices" },
        { name: "Attention Matrix Math", desc: "Tensor cores execute QK^T / sqrt(d) dot product multiplications.", tech: "NVIDIA Tensor Cores" },
        { name: "Softmax & Logit Sampling", desc: "Converts output vector to probabilities and selects token.", tech: "Top-P / Temperature" }
      ]
    }
  ]
};
