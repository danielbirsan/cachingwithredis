from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

driver = GraphDatabase.driver(URI, auth=AUTH)


def run_query(query, parameters=None):
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    except Exception as e:
        print(f"Query failed: {e}")
        return []


def setup_constraints():
    print("Setting up constraints...")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
    ]
    for q in constraints:
        run_query(q)


try:
    driver.verify_connectivity()
    print("[OK] Successfully connected to Neo4j!")
except Exception as e:
    print(f"[ERROR] Connection error: {e}")
    exit()

#######################################################################################

# Reset Database
clear_query = "MATCH (n) DETACH DELETE n"
run_query(clear_query)
print("Database cleared/reset.")


setup_constraints()

# Synthetic Data
json_data = [
    # --- AI & MACHINE LEARNING ---
    {
        "role": "AI Ethics Consultant",
        "description": "Advises organizations on the ethical implications, fairness, and compliance of AI systems.",
        "domain": "AI & Machine Learning",
        "must_have_skills": [
            "AI Ethics",
            "Data Privacy",
            "Risk Assessment",
            "Regulatory Compliance",
        ],
        "nice_to_have_skills": ["Python", "GDPR", "Philosophy", "Bias Mitigation"],
        "skill_relationships": [
            {
                "source": "AI Ethics",
                "target": "Artificial Intelligence",
                "type": "GOVERNS",
            },
            {
                "source": "Bias Mitigation",
                "target": "Machine Learning",
                "type": "IMPROVES",
            },
            {"source": "GDPR", "target": "Data Privacy", "type": "REGULATES"},
        ],
    },
    {
        "role": "AI/ML Engineer",
        "description": "Designs and builds artificial intelligence models and integrates them into scalable applications.",
        "domain": "AI & Machine Learning",
        "must_have_skills": ["Python", "TensorFlow", "PyTorch", "MLOps"],
        "nice_to_have_skills": ["Docker", "Kubernetes", "AWS SageMaker", "NLP"],
        "skill_relationships": [
            {"source": "TensorFlow", "target": "Deep Learning", "type": "IMPLEMENTS"},
            {"source": "MLOps", "target": "DevOps", "type": "ADAPTS_FOR_ML"},
            {"source": "PyTorch", "target": "Python", "type": "IS_LIBRARY_OF"},
        ],
    },
    {
        "role": "Machine Learning Engineer",
        "description": "Specializes in creating self-running software that automates predictive models.",
        "domain": "AI & Machine Learning",
        "must_have_skills": ["Python", "Scikit-Learn", "Deep Learning", "Mathematics"],
        "nice_to_have_skills": ["Apache Spark", "Hadoop", "Reinforcement Learning"],
        "skill_relationships": [
            {"source": "Scikit-Learn", "target": "Python", "type": "IS_LIBRARY_OF"},
            {
                "source": "Reinforcement Learning",
                "target": "Machine Learning",
                "type": "IS_TYPE_OF",
            },
        ],
    },
    # --- BLOCKCHAIN ---
    {
        "role": "Blockchain Developer",
        "description": "Develops decentralized applications (dApps) and smart contracts on blockchain platforms.",
        "domain": "Blockchain",
        "must_have_skills": ["Solidity", "Smart Contracts", "Ethereum", "Web3.js"],
        "nice_to_have_skills": ["Rust", "Hyperledger", "Cryptography", "Go"],
        "skill_relationships": [
            {"source": "Solidity", "target": "Ethereum", "type": "COMPILES_ON"},
            {
                "source": "Smart Contracts",
                "target": "Blockchain",
                "type": "EXECUTES_ON",
            },
            {"source": "Web3.js", "target": "JavaScript", "type": "IS_LIBRARY_OF"},
        ],
    },
    # --- CLOUD COMPUTING ---
    {
        "role": "Cloud Architect",
        "description": "Designs and oversees the implementation of complex cloud computing strategies.",
        "domain": "Cloud Computing",
        "must_have_skills": ["AWS", "Azure", "Cloud Architecture", "Terraform"],
        "nice_to_have_skills": [
            "Google Cloud Platform",
            "Kubernetes",
            "Cost Management",
        ],
        "skill_relationships": [
            {
                "source": "Terraform",
                "target": "Infrastructure as Code",
                "type": "IMPLEMENTS",
            },
            {"source": "AWS", "target": "Cloud Computing", "type": "PROVIDES"},
        ],
    },
    {
        "role": "Cloud Migration Specialist",
        "description": "Manages the transition of data, applications, and processes from on-premise to the cloud.",
        "domain": "Cloud Computing",
        "must_have_skills": [
            "Cloud Migration",
            "AWS Migration Hub",
            "Hybrid Cloud",
            "Networking",
        ],
        "nice_to_have_skills": ["Docker", "Python", "Project Management"],
        "skill_relationships": [
            {"source": "AWS Migration Hub", "target": "AWS", "type": "IS_SERVICE_OF"},
            {
                "source": "Hybrid Cloud",
                "target": "Cloud Architecture",
                "type": "IS_STRATEGY_OF",
            },
        ],
    },
    {
        "role": "Cloud Security Analyst",
        "description": "Monitors cloud environments to detect and respond to security threats.",
        "domain": "Cloud Computing",
        "must_have_skills": [
            "SIEM",
            "Cloud Security Posture Management",
            "IAM",
            "Vulnerability Scanning",
        ],
        "nice_to_have_skills": ["Splunk", "Python", "Compliance Standards"],
        "skill_relationships": [
            {"source": "IAM", "target": "Security", "type": "CONTROLS_ACCESS"},
            {"source": "SIEM", "target": "Threat Detection", "type": "ENABLES"},
        ],
    },
    {
        "role": "Cloud Security Engineer",
        "description": "Builds and maintains secure cloud infrastructure and implements security controls.",
        "domain": "Cloud Computing",
        "must_have_skills": ["AWS Security", "Encryption", "Firewalls", "Python"],
        "nice_to_have_skills": ["DevSecOps", "Kubernetes Security", "Compliance"],
        "skill_relationships": [
            {"source": "DevSecOps", "target": "DevOps", "type": "SECURES"},
            {"source": "Encryption", "target": "Data Privacy", "type": "ENFORCES"},
        ],
    },
    {
        "role": "Cloud Solutions Analyst",
        "description": "Analyzes business requirements to recommend appropriate cloud services and solutions.",
        "domain": "Cloud Computing",
        "must_have_skills": [
            "Cloud Basics",
            "Requirement Analysis",
            "Cost Estimation",
            "Communication",
        ],
        "nice_to_have_skills": ["AWS Certified Practitioner", "Jira", "Agile"],
        "skill_relationships": [
            {
                "source": "Requirement Analysis",
                "target": "Business Intelligence",
                "type": "SUPPORTS",
            },
        ],
    },
    {
        "role": "Cloud Solutions Architect",
        "description": "Designs specific cloud-based applications and services for clients.",
        "domain": "Cloud Computing",
        "must_have_skills": [
            "Microservices",
            "Serverless",
            "API Gateway",
            "System Design",
        ],
        "nice_to_have_skills": ["NoSQL", "CI/CD", "Docker"],
        "skill_relationships": [
            {
                "source": "Serverless",
                "target": "Cloud Computing",
                "type": "IS_MODEL_OF",
            },
            {"source": "API Gateway", "target": "Microservices", "type": "EXPOSES"},
        ],
    },
    {
        "role": "Cloud Solutions Intern",
        "description": "Assists cloud teams with basic deployment, monitoring, and documentation tasks.",
        "domain": "Cloud Computing",
        "must_have_skills": ["Linux Basics", "Cloud Fundamentals", "Python", "Bash"],
        "nice_to_have_skills": ["Git", "SQL", "Networking Basics"],
        "skill_relationships": [
            {"source": "Bash", "target": "Linux", "type": "SCRIPTING_FOR"},
        ],
    },
    {
        "role": "Cloud Support Engineer",
        "description": "Provides troubleshooting and technical support for cloud service customers.",
        "domain": "Cloud Computing",
        "must_have_skills": [
            "Troubleshooting",
            "Linux",
            "Networking",
            "Customer Service",
        ],
        "nice_to_have_skills": ["Scripting", "DNS", "Load Balancing"],
        "skill_relationships": [
            {"source": "DNS", "target": "Networking", "type": "RESOLVES_NAMES_IN"},
        ],
    },
    # --- CYBERSECURITY ---
    {
        "role": "Cybersecurity Analyst",
        "description": "Protects an organization by monitoring networks for security breaches.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "Network Security",
            "Incident Response",
            "Firewalls",
            "SIEM Tools",
        ],
        "nice_to_have_skills": ["Ethical Hacking", "Forensics", "Python"],
        "skill_relationships": [
            {
                "source": "Incident Response",
                "target": "Security Operations",
                "type": "IS_PHASE_OF",
            },
            {"source": "SIEM Tools", "target": "Log Analysis", "type": "AUTOMATES"},
        ],
    },
    {
        "role": "Cybersecurity Engineer",
        "description": "Designs and implements secure network solutions to defend against cyberattacks.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "Penetration Testing",
            "Cryptography",
            "Network Architecture",
            "Linux",
        ],
        "nice_to_have_skills": ["C++", "Reverse Engineering", "CISSP"],
        "skill_relationships": [
            {
                "source": "Penetration Testing",
                "target": "Vulnerability Assessment",
                "type": "VALIDATES",
            },
            {
                "source": "Cryptography",
                "target": "Information Security",
                "type": "UNDERLIES",
            },
        ],
    },
    {
        "role": "Data Privacy Officer",
        "description": "Ensures the organization complies with data protection laws like GDPR and CCPA.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "GDPR",
            "Privacy Law",
            "Compliance Auditing",
            "Risk Management",
        ],
        "nice_to_have_skills": [
            "Legal Knowledge",
            "Information Security",
            "Communication",
        ],
        "skill_relationships": [
            {"source": "GDPR", "target": "EU Law", "type": "IS_A_PART_OF"},
            {"source": "Privacy Law", "target": "Data Governance", "type": "GUIDES"},
        ],
    },
    {
        "role": "IT Security Analyst",
        "description": "Analyzes and assesses vulnerabilities in IT infrastructure.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "Vulnerability Assessment",
            "Antivirus Management",
            "Patch Management",
            "TCP/IP",
        ],
        "nice_to_have_skills": ["PowerShell", "Wireshark", "NIST Framework"],
        "skill_relationships": [
            {"source": "Wireshark", "target": "Packet Analysis", "type": "PERFORMS"},
            {
                "source": "Patch Management",
                "target": "System Administration",
                "type": "MAINTAINS",
            },
        ],
    },
    {
        "role": "IT Security Consultant",
        "description": "Advises clients on how to best protect their IT assets from threats.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "Security Auditing",
            "ISO 27001",
            "Risk Analysis",
            "Consulting",
        ],
        "nice_to_have_skills": [
            "Penetration Testing",
            "Cloud Security",
            "Presentation Skills",
        ],
        "skill_relationships": [
            {"source": "ISO 27001", "target": "Security Standards", "type": "DEFINES"},
        ],
    },
    {
        "role": "Network Security Engineer",
        "description": "Specializes in the provisioning, deployment, and configuration of network security hardware.",
        "domain": "Cybersecurity",
        "must_have_skills": [
            "Firewall Configuration",
            "VPN",
            "IDS/IPS",
            "Cisco Security",
        ],
        "nice_to_have_skills": ["Python", "SD-WAN", "Zero Trust"],
        "skill_relationships": [
            {"source": "IDS/IPS", "target": "Network Traffic", "type": "MONITORS"},
            {"source": "VPN", "target": "Remote Access", "type": "SECURES"},
        ],
    },
    # --- DATA & ANALYTICS ---
    {
        "role": "Data Analyst",
        "description": "Interprets data and turns it into information which can offer ways to improve a business.",
        "domain": "Data & Analytics",
        "must_have_skills": ["SQL", "Excel", "Data Visualization", "Critical Thinking"],
        "nice_to_have_skills": ["Python", "R", "Tableau", "Power BI"],
        "skill_relationships": [
            {
                "source": "Tableau",
                "target": "Data Visualization",
                "type": "IS_TOOL_FOR",
            },
            {"source": "SQL", "target": "Database", "type": "QUERIES"},
        ],
    },
    {
        "role": "Data Analyst Intern",
        "description": "Supports data teams by cleaning data and creating basic reports.",
        "domain": "Data & Analytics",
        "must_have_skills": [
            "Excel",
            "Basic SQL",
            "Mathematics",
            "Attention to Detail",
        ],
        "nice_to_have_skills": ["Python Basics", "Power BI"],
        "skill_relationships": [
            {"source": "Excel", "target": "Spreadsheet", "type": "IS_SOFTWARE_FOR"},
        ],
    },
    {
        "role": "Data Analytics Manager",
        "description": "Leads a team of analysts and oversees data strategies and reporting.",
        "domain": "Data & Analytics",
        "must_have_skills": [
            "Team Leadership",
            "Business Intelligence",
            "Strategic Planning",
            "Advanced SQL",
        ],
        "nice_to_have_skills": [
            "Machine Learning Concepts",
            "Budgeting",
            "Project Management",
        ],
        "skill_relationships": [
            {
                "source": "Business Intelligence",
                "target": "Decision Making",
                "type": "DRIVES",
            },
        ],
    },
    {
        "role": "Data Engineer",
        "description": "Builds pipelines to process and transport large datasets.",
        "domain": "Data & Analytics",
        "must_have_skills": ["Python", "SQL", "Spark", "Airflow"],
        "nice_to_have_skills": ["Kafka", "Snowflake", "Hadoop"],
        "skill_relationships": [
            {"source": "Spark", "target": "Big Data", "type": "PROCESSES"},
            {"source": "Airflow", "target": "Python", "type": "WRITTEN_IN"},
        ],
    },
    {
        "role": "Data Governance Analyst",
        "description": "Ensures high data quality, integrity, and availability across the organization.",
        "domain": "Data & Analytics",
        "must_have_skills": [
            "Data Quality",
            "Master Data Management",
            "Data Cataloging",
            "SQL",
        ],
        "nice_to_have_skills": ["Collibra", "Informatica", "Regulatory Compliance"],
        "skill_relationships": [
            {
                "source": "Master Data Management",
                "target": "Data Consistency",
                "type": "ENSURES",
            },
        ],
    },
    {
        "role": "Data Scientist",
        "description": "Analyzes complex data to help make better business decisions.",
        "domain": "Data & Analytics",
        "must_have_skills": ["Python", "Pandas", "Scikit-Learn", "Statistics"],
        "nice_to_have_skills": ["Tableau", "Spark", "BigQuery", "TensorFlow"],
        "skill_relationships": [
            {"source": "Pandas", "target": "Python", "type": "IS_LIBRARY_OF"},
            {
                "source": "Statistics",
                "target": "Data Science",
                "type": "IS_FOUNDATION_OF",
            },
        ],
    },
    {
        "role": "Database Administrator",
        "description": "Responsible for the performance, integrity, and security of a database.",
        "domain": "Data & Analytics",
        "must_have_skills": [
            "SQL Server",
            "Oracle",
            "Database Tuning",
            "Backup & Recovery",
        ],
        "nice_to_have_skills": ["Cloud Databases", "Shell Scripting", "NoSQL"],
        "skill_relationships": [
            {"source": "Database Tuning", "target": "Performance", "type": "OPTIMIZES"},
            {
                "source": "Backup & Recovery",
                "target": "Disaster Recovery",
                "type": "ENABLES",
            },
        ],
    },
    {
        "role": "Database Analyst",
        "description": "Focuses on analyzing database structures and data trends within databases.",
        "domain": "Data & Analytics",
        "must_have_skills": ["SQL", "Data Modeling", "ER Diagrams", "Reporting"],
        "nice_to_have_skills": ["PL/SQL", "T-SQL", "ETL Tools"],
        "skill_relationships": [
            {
                "source": "ER Diagrams",
                "target": "Database Design",
                "type": "VISUALIZES",
            },
        ],
    },
    # --- DEVELOPMENT & SOFTWARE ENGINEERING ---
    {
        "role": "DevOps Engineer",
        "description": "Introduces processes, tools, and methodologies to balance needs throughout the software development life cycle.",
        "domain": "DevOps",
        "must_have_skills": ["CI/CD", "Docker", "Jenkins", "Linux"],
        "nice_to_have_skills": [
            "Kubernetes",
            "Ansible",
            "Terraform",
            "Monitoring (Prometheus)",
        ],
        "skill_relationships": [
            {"source": "Jenkins", "target": "CI/CD", "type": "AUTOMATES"},
            {
                "source": "Ansible",
                "target": "Configuration Management",
                "type": "PERFORMS",
            },
        ],
    },
    {
        "role": "DevSecOps Engineer",
        "description": "Integrates security practices into the DevOps pipeline.",
        "domain": "DevOps",
        "must_have_skills": ["DevOps", "SAST/DAST", "Container Security", "Automation"],
        "nice_to_have_skills": ["Python", "SonarQube", "Compliance as Code"],
        "skill_relationships": [
            {"source": "SAST/DAST", "target": "Code Security", "type": "ANALYZES"},
            {"source": "SonarQube", "target": "Code Quality", "type": "MEASURES"},
        ],
    },
    {
        "role": "Front-end Developer",
        "description": "Implements visual elements that users see and interact with in a web application.",
        "domain": "Development",
        "must_have_skills": ["HTML5", "CSS3", "JavaScript", "React/Vue/Angular"],
        "nice_to_have_skills": ["TypeScript", "SASS", "Webpack"],
        "skill_relationships": [
            {"source": "TypeScript", "target": "JavaScript", "type": "SUPERSET_OF"},
            {"source": "SASS", "target": "CSS", "type": "EXTENDS"},
        ],
    },
    {
        "role": "Full-stack Developer",
        "description": "Works on both the client-side and server-side of the application.",
        "domain": "Development",
        "must_have_skills": ["JavaScript", "Node.js", "React", "SQL/NoSQL"],
        "nice_to_have_skills": ["Docker", "AWS", "GraphQL"],
        "skill_relationships": [
            {"source": "Node.js", "target": "JavaScript", "type": "RUNS_SERVER_SIDE"},
            {"source": "GraphQL", "target": "REST API", "type": "ALTERNATIVE_TO"},
        ],
    },
    {
        "role": "Mobile App Developer",
        "description": "Specializes in mobile technology such as building apps for Google's Android, Apple's iOS and Microsoft's Windows Phone platforms.",
        "domain": "Development",
        "must_have_skills": ["Swift", "Kotlin", "React Native", "Flutter"],
        "nice_to_have_skills": ["Objective-C", "Java", "Firebase"],
        "skill_relationships": [
            {"source": "Swift", "target": "iOS", "type": "DEVELOPS_FOR"},
            {"source": "Kotlin", "target": "Android", "type": "DEVELOPS_FOR"},
            {"source": "Flutter", "target": "Cross-Platform", "type": "ENABLES"},
        ],
    },
    {
        "role": "QA Automation Engineer",
        "description": "Writes scripts and creates automation environments for repeated tests.",
        "domain": "Quality Assurance",
        "must_have_skills": ["Selenium", "Python/Java", "TestNG", "CI/CD"],
        "nice_to_have_skills": ["Appium", "JMeter", "Cucumber"],
        "skill_relationships": [
            {"source": "Selenium", "target": "Web Testing", "type": "AUTOMATES"},
            {"source": "Cucumber", "target": "BDD", "type": "IMPLEMENTS"},
        ],
    },
    {
        "role": "Software Architect",
        "description": "Makes high-level design choices and dictates technical standards.",
        "domain": "Development",
        "must_have_skills": [
            "System Design",
            "Design Patterns",
            "Cloud Architecture",
            "Leadership",
        ],
        "nice_to_have_skills": ["Microservices", "Scalability", "Security"],
        "skill_relationships": [
            {
                "source": "Design Patterns",
                "target": "Software Engineering",
                "type": "GUIDES",
            },
        ],
    },
    {
        "role": "Software Developer",
        "description": "Designs, tests, and develops software to meet user needs.",
        "domain": "Development",
        "must_have_skills": ["Java/C#/Python", "OOP", "Git", "SQL"],
        "nice_to_have_skills": ["Agile", "Unit Testing", "API Design"],
        "skill_relationships": [
            {"source": "OOP", "target": "Programming Paradigm", "type": "IS_A"},
            {"source": "Git", "target": "Version Control", "type": "MANAGES"},
        ],
    },
    {
        "role": "Software Development Intern",
        "description": "Assists software engineers with coding, testing, and debugging.",
        "domain": "Development",
        "must_have_skills": [
            "Programming Basics",
            "Data Structures",
            "Algorithms",
            "Git",
        ],
        "nice_to_have_skills": ["Web Development Basics", "Communication"],
        "skill_relationships": [
            {
                "source": "Data Structures",
                "target": "Computer Science",
                "type": "FUNDAMENTAL_OF",
            },
        ],
    },
    {
        "role": "Software Engineer",
        "description": "Applies engineering principles to software creation.",
        "domain": "Development",
        "must_have_skills": [
            "Data Structures",
            "Algorithms",
            "System Design",
            "One Major Language",
        ],
        "nice_to_have_skills": ["Distributed Systems", "Concurrency", "Cloud"],
        "skill_relationships": [
            {"source": "Algorithms", "target": "Efficiency", "type": "OPTIMIZES"},
        ],
    },
    {
        "role": "Software Tester",
        "description": "Executes manual and automated tests to ensure software quality.",
        "domain": "Quality Assurance",
        "must_have_skills": [
            "Manual Testing",
            "Bug Tracking (Jira)",
            "Test Case Design",
        ],
        "nice_to_have_skills": ["SQL", "Basic Automation", "API Testing"],
        "skill_relationships": [
            {"source": "Jira", "target": "Bug Tracking", "type": "MANAGES"},
        ],
    },
    {
        "role": "UI Developer",
        "description": "Translates creative software design concepts into functional interfaces.",
        "domain": "Development",
        "must_have_skills": [
            "HTML/CSS",
            "JavaScript",
            "Responsive Design",
            "UI Frameworks",
        ],
        "nice_to_have_skills": [
            "Adobe XD/Figma",
            "Animation Libraries",
            "Accessibility",
        ],
        "skill_relationships": [
            {
                "source": "Responsive Design",
                "target": "Mobile Compatibility",
                "type": "ENSURES",
            },
        ],
    },
    # --- IT MANAGEMENT & BUSINESS ANALYSIS ---
    {
        "role": "Business Analyst",
        "description": "Bridges the gap between IT and the business using data analytics.",
        "domain": "Business Analysis",
        "must_have_skills": [
            "Requirements Gathering",
            "Stakeholder Management",
            "Process Modeling",
            "SQL",
        ],
        "nice_to_have_skills": ["Tableau", "UML", "Agile"],
        "skill_relationships": [
            {"source": "UML", "target": "Process Modeling", "type": "STANDARDIZES"},
            {
                "source": "Stakeholder Management",
                "target": "Project Success",
                "type": "CRITICAL_FOR",
            },
        ],
    },
    {
        "role": "IT Analyst",
        "description": "Evaluates systems and processes to recommend improvements for IT infrastructure.",
        "domain": "Business Analysis",
        "must_have_skills": [
            "System Analysis",
            "Documentation",
            "Problem Solving",
            "Basic Networking",
        ],
        "nice_to_have_skills": ["ITIL", "Visio", "Database Basics"],
        "skill_relationships": [
            {
                "source": "ITIL",
                "target": "IT Service Management",
                "type": "FRAMEWORK_FOR",
            },
        ],
    },
    {
        "role": "IT Analyst Trainee",
        "description": "Learning to analyze IT systems and business requirements.",
        "domain": "Business Analysis",
        "must_have_skills": [
            "Analytical Skills",
            "Communication",
            "Office Suite",
            "Basic IT Knowledge",
        ],
        "nice_to_have_skills": ["SQL Basics", "Process Flowcharting"],
        "skill_relationships": [
            {"source": "Office Suite", "target": "Documentation", "type": "USED_FOR"},
        ],
    },
    {
        "role": "IT Asset Manager",
        "description": "Manages the lifecycle of IT assets (hardware and software).",
        "domain": "IT Management",
        "must_have_skills": [
            "Asset Management",
            "Inventory Control",
            "Licensing",
            "ITAM Tools",
        ],
        "nice_to_have_skills": ["Finance Basics", "Contract Negotiation", "ServiceNow"],
        "skill_relationships": [
            {"source": "Licensing", "target": "Software Compliance", "type": "ENSURES"},
        ],
    },
    {
        "role": "IT Auditor",
        "description": "Examines IT systems to ensure they comply with laws and regulations.",
        "domain": "IT Management",
        "must_have_skills": [
            "Auditing Standards",
            "Risk Assessment",
            "Compliance",
            "Report Writing",
        ],
        "nice_to_have_skills": ["CISA", "COBIT", "Cybersecurity Basics"],
        "skill_relationships": [
            {"source": "CISA", "target": "IT Auditing", "type": "CERTIFIES"},
            {"source": "COBIT", "target": "IT Governance", "type": "FRAMEWORK_FOR"},
        ],
    },
    {
        "role": "IT Business Analyst",
        "description": "Focuses specifically on the technical requirements of business problems.",
        "domain": "Business Analysis",
        "must_have_skills": [
            "SDLC",
            "User Stories",
            "Jira/Confluence",
            "Data Analysis",
        ],
        "nice_to_have_skills": ["SQL", "Wireframing", "Scrum"],
        "skill_relationships": [
            {"source": "User Stories", "target": "Agile Development", "type": "DRIVES"},
        ],
    },
    {
        "role": "IT Business Continuity Manager",
        "description": "Develops plans to ensure IT operations can continue after a disaster.",
        "domain": "IT Management",
        "must_have_skills": [
            "Disaster Recovery Planning",
            "Risk Management",
            "Crisis Management",
            "Backup Strategies",
        ],
        "nice_to_have_skills": ["ISO 22301", "Cloud Redundancy", "Communication"],
        "skill_relationships": [
            {
                "source": "ISO 22301",
                "target": "Business Continuity",
                "type": "STANDARD_FOR",
            },
        ],
    },
    {
        "role": "IT Change Manager",
        "description": "Oversees the lifecycle of all changes to the IT environment.",
        "domain": "IT Management",
        "must_have_skills": [
            "Change Management (ITIL)",
            "Impact Analysis",
            "Stakeholder Communication",
            "ServiceNow",
        ],
        "nice_to_have_skills": ["Project Management", "Risk Assessment"],
        "skill_relationships": [
            {
                "source": "Change Management",
                "target": "System Stability",
                "type": "PROTECTS",
            },
        ],
    },
    {
        "role": "IT Compliance Officer",
        "description": "Ensures IT systems meet external regulatory and internal policy requirements.",
        "domain": "IT Management",
        "must_have_skills": [
            "Regulatory Compliance",
            "Policy Development",
            "Auditing",
            "SOX/HIPAA",
        ],
        "nice_to_have_skills": ["Legal Basics", "Security Frameworks", "Reporting"],
        "skill_relationships": [
            {
                "source": "SOX",
                "target": "Financial Reporting",
                "type": "REGULATES_IT_IN",
            },
        ],
    },
    {
        "role": "IT Compliance Specialist",
        "description": "Executes compliance checks and prepares documentation for audits.",
        "domain": "IT Management",
        "must_have_skills": [
            "Compliance Testing",
            "Documentation",
            "Risk Controls",
            "Attention to Detail",
        ],
        "nice_to_have_skills": ["IT General Controls", "Data Privacy"],
        "skill_relationships": [
            {
                "source": "Compliance Testing",
                "target": "Audit Readiness",
                "type": "ENSURES",
            },
        ],
    },
    {
        "role": "IT Consultant",
        "description": "External advisor helping companies improve their IT structure and efficiency.",
        "domain": "IT Management",
        "must_have_skills": [
            "Strategic Planning",
            "Solution Architecture",
            "Communication",
            "Problem Solving",
        ],
        "nice_to_have_skills": [
            "Sales",
            "Industry Knowledge",
            "Digital Transformation",
        ],
        "skill_relationships": [
            {
                "source": "Digital Transformation",
                "target": "Business Growth",
                "type": "ACCELERATES",
            },
        ],
    },
    {
        "role": "IT Governance Manager",
        "description": "Ensures IT strategy aligns with business strategy and delivers value.",
        "domain": "IT Management",
        "must_have_skills": [
            "IT Strategy",
            "COBIT",
            "Performance Management",
            "Board Reporting",
        ],
        "nice_to_have_skills": ["Risk Management", "Financial Management"],
        "skill_relationships": [
            {
                "source": "IT Strategy",
                "target": "Business Goals",
                "type": "ALIGNS_WITH",
            },
        ],
    },
    {
        "role": "IT Procurement Analyst",
        "description": "Analyzes spending and sourcing for IT hardware and software.",
        "domain": "IT Management",
        "must_have_skills": [
            "Spend Analysis",
            "Vendor Management",
            "Excel",
            "Contract Analysis",
        ],
        "nice_to_have_skills": ["Negotiation", "SAP/ERP"],
        "skill_relationships": [
            {"source": "Spend Analysis", "target": "Cost Reduction", "type": "ENABLES"},
        ],
    },
    {
        "role": "IT Procurement Coordinator",
        "description": "Handles administrative tasks related to purchasing IT equipment.",
        "domain": "IT Management",
        "must_have_skills": [
            "Purchase Orders",
            "Vendor Communication",
            "Organization",
            "Record Keeping",
        ],
        "nice_to_have_skills": ["Inventory Basics", "Accounting Basics"],
        "skill_relationships": [
            {
                "source": "Purchase Orders",
                "target": "Procurement Process",
                "type": "INITIATES",
            },
        ],
    },
    {
        "role": "IT Procurement Manager",
        "description": "Leads the strategy for sourcing IT goods and services.",
        "domain": "IT Management",
        "must_have_skills": [
            "Strategic Sourcing",
            "Contract Negotiation",
            "Vendor Relationship Management",
            "Budgeting",
        ],
        "nice_to_have_skills": ["Legal Contracts", "Supply Chain"],
        "skill_relationships": [
            {
                "source": "Strategic Sourcing",
                "target": "Vendor Selection",
                "type": "GUIDES",
            },
        ],
    },
    {
        "role": "IT Procurement Specialist",
        "description": "Executes purchasing of IT assets and services.",
        "domain": "IT Management",
        "must_have_skills": [
            "Purchasing",
            "Negotiation",
            "SLA Monitoring",
            "Tech Knowledge",
        ],
        "nice_to_have_skills": ["E-procurement Tools", "Asset Management"],
        "skill_relationships": [
            {
                "source": "SLA Monitoring",
                "target": "Vendor Performance",
                "type": "TRACKS",
            },
        ],
    },
    {
        "role": "IT Project Coordinator",
        "description": "Assists project managers with scheduling, documentation, and coordination.",
        "domain": "IT Management",
        "must_have_skills": [
            "Scheduling",
            "Documentation",
            "Communication",
            "Meeting Management",
        ],
        "nice_to_have_skills": ["MS Project", "Jira", "Agile Basics"],
        "skill_relationships": [
            {
                "source": "MS Project",
                "target": "Project Planning",
                "type": "FACILITATES",
            },
        ],
    },
    {
        "role": "IT Project Manager",
        "description": "Plans, executes, and closes IT projects on time and within budget.",
        "domain": "IT Management",
        "must_have_skills": [
            "Project Management (PMP)",
            "Agile/Scrum",
            "Risk Management",
            "Budgeting",
        ],
        "nice_to_have_skills": [
            "Jira",
            "Stakeholder Management",
            "Technical Background",
        ],
        "skill_relationships": [
            {
                "source": "Agile",
                "target": "Software Development",
                "type": "METHODOLOGY_FOR",
            },
            {"source": "PMP", "target": "Project Management", "type": "CERTIFIES"},
        ],
    },
    {
        "role": "IT Quality Analyst",
        "description": "Ensures IT processes and deliverables meet quality standards.",
        "domain": "IT Management",
        "must_have_skills": [
            "Quality Assurance",
            "Process Improvement",
            "Six Sigma",
            "Auditing",
        ],
        "nice_to_have_skills": ["ISO 9001", "Statistical Analysis"],
        "skill_relationships": [
            {
                "source": "Six Sigma",
                "target": "Process Improvement",
                "type": "METHODOLOGY_FOR",
            },
        ],
    },
    {
        "role": "IT Risk Analyst",
        "description": "Identifies and assesses risks to IT systems and data.",
        "domain": "IT Management",
        "must_have_skills": [
            "Risk Assessment",
            "Risk Frameworks (NIST)",
            "Data Analysis",
            "Reporting",
        ],
        "nice_to_have_skills": ["Cybersecurity Basics", "Compliance"],
        "skill_relationships": [
            {
                "source": "Risk Assessment",
                "target": "Mitigation Strategy",
                "type": "INFORMS",
            },
        ],
    },
    {
        "role": "IT Sales Manager",
        "description": "Manages a team of sales reps selling IT products or services.",
        "domain": "Sales & Training",
        "must_have_skills": ["Sales Management", "CRM", "Forecasting", "Leadership"],
        "nice_to_have_skills": ["Technical Knowledge", "Negotiation", "B2B Sales"],
        "skill_relationships": [
            {"source": "CRM", "target": "Customer Relationships", "type": "MANAGES"},
        ],
    },
    {
        "role": "IT Sales Representative",
        "description": "Sells IT hardware, software, or services to clients.",
        "domain": "Sales & Training",
        "must_have_skills": [
            "Sales",
            "Communication",
            "Product Knowledge",
            "Networking",
        ],
        "nice_to_have_skills": ["Cold Calling", "CRM Tools", "Presentation"],
        "skill_relationships": [
            {
                "source": "Product Knowledge",
                "target": "Sales Success",
                "type": "INCREASES",
            },
        ],
    },
    {
        "role": "IT Trainer",
        "description": "Teaches technical skills and software usage to employees or clients.",
        "domain": "Sales & Training",
        "must_have_skills": [
            "Teaching",
            "Curriculum Development",
            "Presentation Skills",
            "Technical Expertise",
        ],
        "nice_to_have_skills": [
            "E-learning Tools",
            "Video Editing",
            "Certification in Training",
        ],
        "skill_relationships": [
            {
                "source": "Curriculum Development",
                "target": "Learning Outcomes",
                "type": "STRUCTURES",
            },
        ],
    },
    {
        "role": "IT Trainer Assistant",
        "description": "Supports IT trainers in preparing materials and conducting sessions.",
        "domain": "Sales & Training",
        "must_have_skills": [
            "Organization",
            "Communication",
            "Basic IT Skills",
            "Presentation Support",
        ],
        "nice_to_have_skills": ["LMS Management", "Documentation"],
        "skill_relationships": [
            {
                "source": "LMS Management",
                "target": "Training Delivery",
                "type": "SUPPORTS",
            },
        ],
    },
    {
        "role": "IT Trainer Specialist",
        "description": "Expert trainer focusing on specialized or advanced IT topics.",
        "domain": "Sales & Training",
        "must_have_skills": [
            "Specialized Tech Knowledge",
            "Adult Learning Theory",
            "Workshop Facilitation",
            "Mentoring",
        ],
        "nice_to_have_skills": ["Instructional Design", "Virtual Training Platforms"],
        "skill_relationships": [
            {
                "source": "Adult Learning Theory",
                "target": "Training Effectiveness",
                "type": "MAXIMIZES",
            },
        ],
    },
    # --- INFRASTRUCTURE & SUPPORT ---
    {
        "role": "IT Helpdesk Support",
        "description": "First point of contact for technical issues, resolving basic problems.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Troubleshooting",
            "Windows/MacOS",
            "Ticketing Systems",
            "Customer Service",
        ],
        "nice_to_have_skills": ["Active Directory", "Office 365", "Hardware Repair"],
        "skill_relationships": [
            {
                "source": "Ticketing Systems",
                "target": "Issue Tracking",
                "type": "MANAGES",
            },
        ],
    },
    {
        "role": "IT Service Desk Analyst",
        "description": "Manages incidents and service requests, often more advanced than helpdesk.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Incident Management",
            "ITIL Foundations",
            "Remote Support Tools",
            "Active Directory",
        ],
        "nice_to_have_skills": [
            "ServiceNow",
            "Powershell Basics",
            "Knowledge Base Management",
        ],
        "skill_relationships": [
            {
                "source": "Active Directory",
                "target": "User Management",
                "type": "CENTRALIZES",
            },
        ],
    },
    {
        "role": "IT Support Analyst",
        "description": "Provides technical support and maintenance for computer systems.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Hardware Troubleshooting",
            "Software Installation",
            "Network Basics",
            "OS Support",
        ],
        "nice_to_have_skills": [
            "Scripting",
            "Mobile Device Management (MDM)",
            "Virtualization",
        ],
        "skill_relationships": [
            {"source": "MDM", "target": "Mobile Security", "type": "ENFORCES"},
        ],
    },
    {
        "role": "IT Support Specialist",
        "description": "Specializes in supporting specific systems or high-level user issues.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Advanced Troubleshooting",
            "System Configuration",
            "VPN Support",
            "Documentation",
        ],
        "nice_to_have_skills": ["Server Basics", "VoIP", "Security Basics"],
        "skill_relationships": [
            {"source": "VoIP", "target": "Telephony", "type": "ENABLES_OVER_IP"},
        ],
    },
    {
        "role": "Network Administrator Trainee",
        "description": "Entry-level role learning to manage and maintain networks.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Networking Fundamentals",
            "TCP/IP",
            "Cabling",
            "Basic Routing",
        ],
        "nice_to_have_skills": ["Cisco CCNA", "Linux Basics"],
        "skill_relationships": [
            {"source": "TCP/IP", "target": "Internet", "type": "PROTOCOL_OF"},
        ],
    },
    {
        "role": "Network Engineer",
        "description": "Plans and implements computer networks (LAN, WAN, WLAN).",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Routing & Switching",
            "Cisco IOS",
            "Firewall Configuration",
            "Network Protocols (BGP/OSPF)",
        ],
        "nice_to_have_skills": ["Python for Automation", "SDN", "Load Balancing"],
        "skill_relationships": [
            {"source": "BGP", "target": "Routing", "type": "PROTOCOL_FOR"},
            {"source": "SDN", "target": "Network Management", "type": "MODERNIZES"},
        ],
    },
    {
        "role": "System Administrator",
        "description": "Installs and maintains the performance of servers and computer systems.",
        "domain": "Infrastructure & Support",
        "must_have_skills": [
            "Linux/Windows Server",
            "Virtualization (VMware)",
            "Scripting (Bash/PowerShell)",
            "User Management",
        ],
        "nice_to_have_skills": ["Cloud Basics", "Backup Tools", "Monitoring (Nagios)"],
        "skill_relationships": [
            {"source": "VMware", "target": "Virtualization", "type": "PROVIDES"},
            {"source": "PowerShell", "target": "Windows Automation", "type": "ENABLES"},
        ],
    },
    # --- UX & DESIGN ---
    {
        "role": "UX Designer",
        "description": "Designs products that provide meaningful and relevant experiences to users.",
        "domain": "UX & Design",
        "must_have_skills": [
            "Wireframing",
            "Prototyping",
            "Figma/Sketch",
            "User Empathy",
        ],
        "nice_to_have_skills": ["HTML/CSS", "User Testing", "Information Architecture"],
        "skill_relationships": [
            {"source": "Figma", "target": "Prototyping", "type": "IS_TOOL_FOR"},
            {
                "source": "Information Architecture",
                "target": "Navigation",
                "type": "ORGANIZES",
            },
        ],
    },
    {
        "role": "UX Research Assistant",
        "description": "Helps recruit participants and organize data for UX studies.",
        "domain": "UX & Design",
        "must_have_skills": [
            "Data Entry",
            "Note Taking",
            "Organization",
            "Observation",
        ],
        "nice_to_have_skills": ["Survey Tools", "Data Analysis", "Psychology Basics"],
        "skill_relationships": [
            {"source": "Survey Tools", "target": "User Feedback", "type": "COLLECTS"},
        ],
    },
    {
        "role": "UX Researcher",
        "description": "Conducts research to understand user behaviors, needs, and motivations.",
        "domain": "UX & Design",
        "must_have_skills": [
            "User Interviews",
            "Usability Testing",
            "Data Analysis",
            "Persona Creation",
        ],
        "nice_to_have_skills": ["Quantitative Research", "Eye Tracking", "A/B Testing"],
        "skill_relationships": [
            {
                "source": "Usability Testing",
                "target": "Product Design",
                "type": "VALIDATES",
            },
            {"source": "A/B Testing", "target": "Conversion Rate", "type": "OPTIMIZES"},
        ],
    },
]

print(f"Processing {len(json_data)} roles...")


for entry in json_data:
    print(f"  -> Processing Role: {entry['role']}")

    role_query = """
    MERGE (r:Role {name: $role_name})
    SET r.description = $desc
    
    MERGE (d:Domain {name: $domain_name})
    MERGE (r)-[:IN_DOMAIN]->(d)
    """
    run_query(
        role_query,
        {
            "role_name": entry["role"],
            "desc": entry["description"],
            "domain_name": entry["domain"],
        },
    )

    for skill in entry["must_have_skills"]:
        must_have_query = """
        MATCH (r:Role {name: $role_name})
        MERGE (s:Skill {name: $skill_name})
        MERGE (r)-[:REQUIRES {level: 'Mandatory'}]->(s)
        """
        run_query(must_have_query, {"role_name": entry["role"], "skill_name": skill})

    for skill in entry["nice_to_have_skills"]:
        nice_to_have_query = """
        MATCH (r:Role {name: $role_name})
        MERGE (s:Skill {name: $skill_name})
        MERGE (r)-[:RECOMMENDS {level: 'Optional'}]->(s)
        """
        run_query(nice_to_have_query, {"role_name": entry["role"], "skill_name": skill})

    if "skill_relationships" in entry:
        for rel in entry["skill_relationships"]:
            safe_rel_type = rel["type"].strip().replace(" ", "_").upper()

            rel_query = f"""
            MERGE (a:Skill {{name: $source}})
            MERGE (b:Skill {{name: $target}})
            MERGE (a)-[:{safe_rel_type}]->(b)
            """
            run_query(rel_query, {"source": rel["source"], "target": rel["target"]})


print("[OK] Tech Recruiter Ontology created successfully!")
driver.close()
