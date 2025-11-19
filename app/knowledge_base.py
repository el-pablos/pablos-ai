"""
Knowledge base for fullstack development.
Contains best practices, common patterns, and solutions for various tech stacks.
"""

from typing import Dict, List, Optional

# Frontend Technologies Knowledge Base
FRONTEND_KNOWLEDGE = {
    "react": {
        "description": "Library JavaScript untuk building UI",
        "best_practices": [
            "Gunakan functional components dengan hooks",
            "Implement proper state management (useState, useContext, Redux)",
            "Optimize dengan React.memo, useMemo, useCallback",
            "Follow component composition pattern",
            "Use proper key props dalam lists"
        ],
        "common_patterns": [
            "Custom hooks untuk reusable logic",
            "Context API untuk global state",
            "Error boundaries untuk error handling",
            "Lazy loading dengan React.lazy dan Suspense"
        ],
        "common_issues": {
            "infinite_loop": "Cek dependency array di useEffect, jangan lupa []",
            "state_not_updating": "State updates are async, gunakan callback form",
            "performance": "Gunakan React DevTools Profiler, implement memoization"
        }
    },
    "vue": {
        "description": "Progressive JavaScript framework",
        "best_practices": [
            "Gunakan Composition API untuk better code organization",
            "Implement proper reactivity dengan ref dan reactive",
            "Use computed properties untuk derived state",
            "Follow single file component structure"
        ],
        "common_patterns": [
            "Composables untuk reusable logic",
            "Pinia untuk state management",
            "Provide/Inject untuk dependency injection"
        ]
    },
    "nextjs": {
        "description": "React framework dengan SSR dan SSG",
        "best_practices": [
            "Gunakan App Router (Next.js 13+) untuk better performance",
            "Implement proper data fetching (Server Components, RSC)",
            "Optimize images dengan next/image",
            "Use proper caching strategies"
        ],
        "common_patterns": [
            "Server Components untuk data fetching",
            "Client Components untuk interactivity",
            "API Routes untuk backend logic",
            "Middleware untuk authentication"
        ]
    },
    "typescript": {
        "description": "Typed superset of JavaScript",
        "best_practices": [
            "Define proper types dan interfaces",
            "Avoid 'any' type, gunakan 'unknown' kalau perlu",
            "Use generics untuk reusable code",
            "Enable strict mode di tsconfig"
        ],
        "common_issues": {
            "type_errors": "Cek type definitions, gunakan type guards",
            "any_type": "Replace dengan proper types atau unknown"
        }
    }
}

# Backend Technologies Knowledge Base
BACKEND_KNOWLEDGE = {
    "nodejs": {
        "description": "JavaScript runtime untuk backend",
        "best_practices": [
            "Use async/await untuk asynchronous operations",
            "Implement proper error handling dengan try-catch",
            "Use environment variables untuk config",
            "Implement proper logging"
        ],
        "frameworks": {
            "express": "Minimalist web framework",
            "fastify": "Fast and low overhead framework",
            "nestjs": "Progressive Node.js framework dengan TypeScript"
        }
    },
    "python": {
        "description": "High-level programming language",
        "frameworks": {
            "fastapi": {
                "description": "Modern, fast web framework",
                "best_practices": [
                    "Use Pydantic untuk data validation",
                    "Implement async endpoints untuk better performance",
                    "Use dependency injection",
                    "Auto-generate OpenAPI docs"
                ]
            },
            "django": {
                "description": "High-level web framework",
                "best_practices": [
                    "Follow MVT pattern",
                    "Use Django ORM properly",
                    "Implement proper migrations",
                    "Use Django REST framework untuk APIs"
                ]
            },
            "flask": {
                "description": "Lightweight WSGI framework",
                "best_practices": [
                    "Use blueprints untuk modular code",
                    "Implement proper error handling",
                    "Use Flask extensions wisely"
                ]
            }
        }
    },
    "go": {
        "description": "Statically typed, compiled language",
        "best_practices": [
            "Follow Go conventions (gofmt, golint)",
            "Use goroutines untuk concurrency",
            "Implement proper error handling",
            "Use interfaces untuk abstraction"
        ]
    },
    "rust": {
        "description": "Systems programming language",
        "best_practices": [
            "Understand ownership dan borrowing",
            "Use Result type untuk error handling",
            "Leverage Rust's type system",
            "Use cargo untuk dependency management"
        ]
    }
}

# Database Knowledge Base
DATABASE_KNOWLEDGE = {
    "postgresql": {
        "description": "Advanced open-source relational database",
        "best_practices": [
            "Use proper indexing untuk query optimization",
            "Implement connection pooling",
            "Use transactions untuk data consistency",
            "Regular VACUUM dan ANALYZE"
        ],
        "common_patterns": [
            "Use JSONB untuk semi-structured data",
            "Implement proper foreign keys",
            "Use views untuk complex queries",
            "Partitioning untuk large tables"
        ]
    },
    "redis": {
        "description": "In-memory data structure store",
        "best_practices": [
            "Use proper data structures (strings, hashes, lists, sets)",
            "Implement proper expiration policies",
            "Use pipelining untuk batch operations",
            "Monitor memory usage"
        ],
        "use_cases": [
            "Caching",
            "Session storage",
            "Rate limiting",
            "Real-time analytics"
        ]
    },
    "mysql": {
        "description": "Popular open-source relational database",
        "best_practices": [
            "Use InnoDB engine",
            "Proper indexing strategy",
            "Optimize queries dengan EXPLAIN",
            "Regular backups"
        ]
    }
}

# DevOps Knowledge Base
DEVOPS_KNOWLEDGE = {
    "docker": {
        "description": "Container platform",
        "best_practices": [
            "Use multi-stage builds untuk smaller images",
            "Don't run as root user",
            "Use .dockerignore",
            "Minimize layers",
            "Use specific image tags, avoid 'latest'"
        ],
        "common_commands": [
            "docker build -t name:tag .",
            "docker run -d -p 8080:80 name:tag",
            "docker-compose up -d",
            "docker logs container_name"
        ]
    },
    "kubernetes": {
        "description": "Container orchestration platform",
        "best_practices": [
            "Use namespaces untuk isolation",
            "Implement resource limits",
            "Use ConfigMaps dan Secrets",
            "Implement health checks",
            "Use Helm untuk package management"
        ]
    },
    "cicd": {
        "description": "Continuous Integration/Deployment",
        "best_practices": [
            "Automate testing",
            "Use proper branching strategy",
            "Implement proper rollback mechanisms",
            "Monitor deployments"
        ],
        "tools": ["GitHub Actions", "GitLab CI", "Jenkins", "CircleCI"]
    },
    "git": {
        "description": "Version control system",
        "best_practices": [
            "Write meaningful commit messages",
            "Use feature branches",
            "Regular commits dengan atomic changes",
            "Use .gitignore properly"
        ],
        "common_workflows": [
            "Git Flow",
            "GitHub Flow",
            "Trunk-based development"
        ]
    }
}

# Design Patterns and Best Practices
DESIGN_PATTERNS = {
    "solid_principles": {
        "S": "Single Responsibility - Satu class satu tanggung jawab",
        "O": "Open/Closed - Open for extension, closed for modification",
        "L": "Liskov Substitution - Subclass harus bisa replace parent class",
        "I": "Interface Segregation - Jangan force client implement unused methods",
        "D": "Dependency Inversion - Depend on abstractions, not concretions"
    },
    "common_patterns": {
        "singleton": "Ensure class has only one instance",
        "factory": "Create objects without specifying exact class",
        "observer": "Define one-to-many dependency between objects",
        "strategy": "Define family of algorithms, make them interchangeable",
        "decorator": "Add behavior to objects dynamically"
    },
    "api_design": {
        "rest": [
            "Use proper HTTP methods (GET, POST, PUT, DELETE)",
            "Use meaningful resource names",
            "Implement proper status codes",
            "Version your API",
            "Use pagination untuk large datasets"
        ],
        "graphql": [
            "Design schema carefully",
            "Implement proper resolvers",
            "Use DataLoader untuk N+1 problem",
            "Implement proper error handling"
        ]
    }
}

# Common Solutions and Troubleshooting
COMMON_SOLUTIONS = {
    "performance": {
        "database": [
            "Add proper indexes",
            "Use query optimization",
            "Implement caching",
            "Use connection pooling",
            "Consider read replicas"
        ],
        "frontend": [
            "Code splitting",
            "Lazy loading",
            "Image optimization",
            "Minimize bundle size",
            "Use CDN"
        ],
        "backend": [
            "Implement caching",
            "Use async operations",
            "Optimize algorithms",
            "Use load balancing",
            "Implement rate limiting"
        ]
    },
    "security": {
        "best_practices": [
            "Never store passwords in plain text",
            "Use HTTPS",
            "Implement proper authentication",
            "Validate and sanitize input",
            "Use environment variables untuk secrets",
            "Implement CORS properly",
            "Regular security updates"
        ]
    },
    "debugging": {
        "tips": [
            "Use proper logging",
            "Implement error tracking (Sentry, etc)",
            "Use debugger tools",
            "Check logs systematically",
            "Reproduce issue consistently",
            "Use monitoring tools"
        ]
    }
}


def get_knowledge_for_topic(topic: str) -> Optional[Dict]:
    """
    Get knowledge base for a specific topic.

    Args:
        topic: Topic name (e.g., 'react', 'nodejs', 'docker')

    Returns:
        Knowledge dict or None if not found
    """
    topic_lower = topic.lower()

    # Search in all knowledge bases
    all_knowledge = {
        **FRONTEND_KNOWLEDGE,
        **BACKEND_KNOWLEDGE,
        **DATABASE_KNOWLEDGE,
        **DEVOPS_KNOWLEDGE
    }

    return all_knowledge.get(topic_lower)


def search_knowledge(query: str) -> List[str]:
    """
    Search for relevant knowledge based on query.

    Args:
        query: Search query

    Returns:
        List of relevant topics
    """
    query_lower = query.lower()
    relevant_topics = []

    # Search in all knowledge bases
    all_knowledge = {
        **FRONTEND_KNOWLEDGE,
        **BACKEND_KNOWLEDGE,
        **DATABASE_KNOWLEDGE,
        **DEVOPS_KNOWLEDGE
    }

    # Split query into keywords
    keywords = query_lower.split()

    for topic, data in all_knowledge.items():
        # Check if topic name matches any keyword
        if any(keyword in topic for keyword in keywords):
            relevant_topics.append(topic)
            continue

        # Check if any keyword appears in the topic data
        data_str = str(data).lower()
        if any(keyword in data_str for keyword in keywords):
            relevant_topics.append(topic)

    return relevant_topics


def is_coding_query(message: str) -> bool:
    """
    Detect if a message is a coding-related query.

    Args:
        message: User message

    Returns:
        True if coding-related, False otherwise
    """
    coding_keywords = [
        # Programming languages
        'python', 'javascript', 'typescript', 'java', 'go', 'rust', 'php', 'ruby',
        # Frameworks
        'react', 'vue', 'angular', 'nextjs', 'django', 'flask', 'fastapi', 'express',
        'nestjs', 'spring', 'laravel',
        # Databases
        'sql', 'postgres', 'mysql', 'mongodb', 'redis', 'database',
        # DevOps
        'docker', 'kubernetes', 'k8s', 'ci/cd', 'git', 'github', 'gitlab',
        # General coding terms
        'code', 'coding', 'program', 'bug', 'error', 'function', 'class', 'api',
        'frontend', 'backend', 'fullstack', 'deploy', 'server', 'client'
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in coding_keywords)


def get_relevant_knowledge(query: str) -> str:
    """
    Get relevant knowledge base content for a query.

    Args:
        query: User query

    Returns:
        Formatted knowledge base content
    """
    if not is_coding_query(query):
        return ""

    relevant_topics = search_knowledge(query)

    if not relevant_topics:
        return ""

    knowledge_text = "📚 **Knowledge Base yang Relevan:**\n\n"

    for topic in relevant_topics[:3]:  # Limit to top 3 topics
        topic_data = get_knowledge_for_topic(topic)
        if topic_data:
            knowledge_text += f"**{topic.upper()}:**\n"
            if 'description' in topic_data:
                knowledge_text += f"{topic_data['description']}\n"
            if 'best_practices' in topic_data:
                knowledge_text += "Best practices:\n"
                for practice in topic_data['best_practices'][:3]:
                    knowledge_text += f"- {practice}\n"
            knowledge_text += "\n"

    return knowledge_text

