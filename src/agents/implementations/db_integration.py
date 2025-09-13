 # agents/implemtations/db_integration.py
import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.framework import APIA_BaseAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage
from utils.memory import AgentMemory
from agents.specialized import APIA_SpecializedAgent

logger = logging.getLogger(name)

class APIA_DBIntegrationAgent(APIA_SpecializedAgent):
"""
Database Integration Agent for handling database schema design, queries, and optimization.

This agent specializes in database-related tasks such as:
- Designing database schemas
- Creating database migrations
- Writing optimized queries
- Setting up data models
- Implementing database integrations
"""

async def _initialize_domain_resources(self):
    """Initialize database integration resources."""
    # Initialize database types
    self._db_types = ["sql", "nosql", "graph", "timeseries"]
    
    # Initialize supported databases
    self._supported_databases = {
        "sql": ["postgresql", "mysql", "sqlite", "sqlserver"],
        "nosql": ["mongodb", "dynamodb", "cosmosdb"],
        "graph": ["neo4j", "neptune"],
        "timeseries": ["influxdb", "timeseriesdb"]
    }
    
    # Initialize schema templates
    self._schema_templates = {
        "user": {
            "sql": """


CREATE TABLE users (
id SERIAL PRIMARY KEY,
username VARCHAR(50) UNIQUE NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
password_hash VARCHAR(100) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
"nosql": """
{
"users": {
"username": "string",
"email": "string",
"password_hash": "string",
"created_at": "date",
"updated_at": "date"
}
}
"""
},
"product": {
"sql": """
CREATE TABLE products (
id SERIAL PRIMARY KEY,
name VARCHAR(100) NOT NULL,
description TEXT,
price DECIMAL(10, 2) NOT NULL,
inventory_count INTEGER NOT NULL DEFAULT 0,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
"nosql": """
{
"products": {
"name": "string",
"description": "string",
"price": "number",
"inventory_count": "number",
"created_at": "date",
"updated_at": "date"
}
}
"""
}
}

# Initialize query templates
    self._query_templates = {
        "sql": {
            "select": "SELECT {fields} FROM {table} WHERE {condition};",
            "insert": "INSERT INTO {table} ({fields}) VALUES ({values});",
            "update": "UPDATE {table} SET {field_values} WHERE {condition};",
            "delete": "DELETE FROM {table} WHERE {condition};"
        },
        "nosql": {
            "find": "db.{collection}.find({query})",
            "insert": "db.{collection}.insertOne({document})",
            "update": "db.{collection}.updateOne({query}, {update})",
            "delete": "db.{collection}.deleteOne({query})"
        }
    }
    
    logger.info(f"DB Integration Agent ({self.id}) initialized domain resources")

async def _register_skills(self):
    """Register database integration skills."""
    await super()._register_skills()
    
    # Register database-specific skills
    self._skill_registry.update({
        "design_schema": {
            "name": "Design Database Schema",
            "description": "Design a database schema for a specific domain",
            "examples": [
                "Design a database schema for an e-commerce application",
                "Create a data model for a user management system"
            ]
        },
        "create_migration": {
            "name": "Create Database Migration",
            "description": "Create a database migration script",
            "examples": [
                "Create a migration to add a new table",
                "Generate a migration script to modify an existing schema"
            ]
        },
        "optimize_query": {
            "name": "Optimize Database Query",
            "description": "Optimize a database query for better performance",
            "examples": [
                "Optimize a slow SQL query",
                "Improve the performance of a MongoDB aggregation"
            ]
        }
    })

async def _handle_domain_task(self, context: A2ATaskContext, subtask_id: str, 
                             subtask_description: str) -> A2ATaskResult:
    """
    Handle database integration tasks.
    
    Args:
        context: Task context
        subtask_id: ID of the subtask
        subtask_description: Description of the subtask
        
    Returns:
        Task result with generated schema, queries, or migrations
    """
    # Analyze the task to determine what needs to be created
    task_analysis = self._analyze_db_task(subtask_description)
    
    # Determine the appropriate database type and system
    db_type, db_system = self._determine_database(context, task_analysis)
    
    # Handle different task types
    if task_analysis["task_type"] == "schema_design":
        # Generate schema
        schema = self._generate_schema(task_analysis, db_type, db_system)
        documentation = self._generate_schema_documentation(task_analysis, schema, db_type, db_system)
        
        # Simulate work time
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Database schema design completed for {task_analysis['domain']}")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"schema_{subtask_id}",
                    description=f"Database Schema for {task_analysis['domain']}",
                    parts=[
                        A2ATextPart(text=schema)
                    ]
                ),
                A2AArtifact(
                    name=f"schema_docs_{subtask_id}",
                    description="Schema Documentation",
                    parts=[
                        A2ATextPart(text=documentation)
                    ]
                )
            ]
        )
    
    elif task_analysis["task_type"] == "query_optimization":
        # Generate optimized query
        original_query = task_analysis.get("original_query", "SELECT * FROM users WHERE id = 1")
        optimized_query = self._optimize_query(original_query, db_type, db_system)
        explanation = self._generate_optimization_explanation(original_query, optimized_query, db_type)
        
        # Simulate work time
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Query optimization completed")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"optimized_query_{subtask_id}",
                    description="Optimized Database Query",
                    parts=[
                        A2ATextPart(text=optimized_query)
                    ]
                ),
                A2AArtifact(
                    name=f"optimization_explanation_{subtask_id}",
                    description="Query Optimization Explanation",
                    parts=[
                        A2ATextPart(text=explanation)
                    ]
                )
            ]
        )
    
    elif task_analysis["task_type"] == "migration":
        # Generate migration
        migration = self._generate_migration(task_analysis, db_type, db_system)
        
        # Simulate work time
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Database migration created")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"migration_{subtask_id}",
                    description="Database Migration Script",
                    parts=[
                        A2ATextPart(text=migration)
                    ]
                )
            ]
        )
    
    else:
        # Default to schema design
        schema = self._generate_schema(task_analysis, db_type, db_system)
        documentation = self._generate_schema_documentation(task_analysis, schema, db_type, db_system)
        
        # Simulate work time
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        return A2ATaskResult(
            status="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2ATextPart(text=f"Database task completed")]
            ),
            artifacts=[
                A2AArtifact(
                    name=f"schema_{subtask_id}",
                    description=f"Database Schema",
                    parts=[
                        A2ATextPart(text=schema)
                    ]
                ),
                A2AArtifact(
                    name=f"schema_docs_{subtask_id}",
                    description="Schema Documentation",
                    parts=[
                        A2ATextPart(text=documentation)
                    ]
                )
            ]
        )

def _analyze_db_task(self, task_description: str) -> Dict[str, Any]:
    """
    Analyze a database task to determine its requirements.
    
    Args:
        task_description: Description of the task
        
    Returns:
        Dictionary with task analysis
    """
    # Simple keyword-based analysis
    task_lower = task_description.lower()
    
    # Determine task type
    task_type = "schema_design"  # Default
    if "query" in task_lower and ("optimize" in task_lower or "performance" in task_lower):
        task_type = "query_optimization"
    elif "migration" in task_lower or "upgrade" in task_lower or "update schema" in task_lower:
        task_type = "migration"
    
    # Determine domain
    domain = "generic"  # Default
    domain_keywords = {
        "user": ["user", "account", "profile", "authentication"],
        "product": ["product", "item", "inventory", "catalog"],
        "order": ["order", "purchase", "transaction", "payment"],
        "content": ["content", "article", "post", "blog"],
        "analytics": ["analytics", "metrics", "statistics", "reporting"]
    }
    
    for key, keywords in domain_keywords.items():
        if any(keyword in task_lower for keyword in keywords):
            domain = key
            break
    
    # Extract entities
    entities = []
    common_entities = ["user", "product", "order", "customer", "account", 
                      "transaction", "payment", "invoice", "item", "category"]
    
    for entity in common_entities:
        if entity in task_lower:
            entities.append(entity)
    
    # If no entities found, use domain as entity
    if not entities and domain != "generic":
        entities.append(domain)
    
    # Extract original query if present
    original_query = None
    if task_type == "query_optimization" and "```" in task_description:
        # Try to extract query from code block
        parts = task_description.split("```")
        if len(parts) >= 3:
            original_query = parts[1].strip()
    
    return {
        "task_type": task_type,
        "domain": domain,
        "entities": entities,
        "original_query": original_query
    }

def _determine_database(self, context: A2ATaskContext, 
                       task_analysis: Dict[str, Any]) -> Tuple[str, str]:
    """
    Determine the appropriate database type and system for the task.
    
    Args:
        context: Task context
        task_analysis: Analysis of the task
        
    Returns:
        Tuple of (database_type, database_system)
    """
    # Check if database type and system are specified in context
    db_type = None
    db_system = None
    
    if context.metadata:
        db_type = context.metadata.get("db_type")
        db_system = context.metadata.get("db_system")
    
    if context.get_data_parts():
        data = context.get_data_parts()[0]
        if "db_type" in data:
            db_type = data["db_type"]
        if "db_system" in data:
            db_system = data["db_system"]
    
    # If not specified, determine based on task
    if not db_type:
        task_lower = context.get_text_parts()[0].lower() if context.get_text_parts() else ""
        
        # Check for database type keywords
        if any(kw in task_lower for kw in ["sql", "relational", "postgres", "mysql"]):
            db_type = "sql"
        elif any(kw in task_lower for kw in ["nosql", "document", "mongo", "dynamo"]):
            db_type = "nosql"
        elif any(kw in task_lower for kw in ["graph", "neo4j", "neptune"]):
            db_type = "graph"
        elif any(kw in task_lower for kw in ["time series", "timeseries", "influx"]):
            db_type = "timeseries"
        else:
            # Default to SQL for schema design, NoSQL for others
            db_type = "sql" if task_analysis["task_type"] == "schema_design" else "nosql"
    
    # If database system not specified, pick a default based on type
    if not db_system:
        if db_type == "sql":
            db_system = "postgresql"
        elif db_type == "nosql":
            db_system = "mongodb"
        elif db_type == "graph":
            db_system = "neo4j"
        elif db_type == "timeseries":
            db_system = "influxdb"
    
    return db_type, db_system

def _generate_schema(self, task_analysis: Dict[str, Any], 
                    db_type: str, db_system: str) -> str:
    """
    Generate a database schema based on task analysis.
    
    Args:
        task_analysis: Analysis of the task
        db_type: Type of database (sql, nosql, etc.)
        db_system: Specific database system
        
    Returns:
        Generated schema
    """
    domain = task_analysis["domain"]
    entities = task_analysis["entities"]
    
    # If we have a template for this domain, use it
    if domain in self._schema_templates and db_type in self._schema_templates[domain]:
        return self._schema_templates[domain][db_type]
    
    # Otherwise, generate a schema based on entities
    if db_type == "sql":
        return self._generate_sql_schema(entities, db_system)
    elif db_type == "nosql":
        return self._generate_nosql_schema(entities, db_system)
    else:
        # Default to SQL
        return self._generate_sql_schema(entities, db_system)

def _generate_sql_schema(self, entities: List[str], db_system: str) -> str:
    """Generate a SQL schema for the given entities."""
    schema = ""
    
    for entity in entities:
        # Capitalize entity name for table name
        table_name = f"{entity}s"
        
        schema += f"""


CREATE TABLE {table_name} (
id SERIAL PRIMARY KEY,
name VARCHAR(100) NOT NULL,
description TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

"""

# If we have multiple entities, create relationships
    if len(entities) > 1:
        for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                entity1 = entities[i]
                entity2 = entities[j]
                
                # Create a many-to-many relationship table
                schema += f"""

CREATE TABLE {entity1}_{entity2} (
{entity1}_id INTEGER REFERENCES {entity1}s(id),
{entity2}_id INTEGER REFERENCES {entity2}s(id),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY ({entity1}_id, {entity2}_id)
);

"""

return schema

def _generate_nosql_schema(self, entities: List[str], db_system: str) -> str:
    """Generate a NoSQL schema for the given entities."""
    schema = "{\n"
    
    for entity in entities:
        # Pluralize entity name for collection name
        collection_name = f"{entity}s"
        
        schema += f"""  "{collection_name}": {{
"name": "string",
"description": "string",
"created_at": "date",
"updated_at": "date"

}}"""

# Add comma if not the last entity
        if entity != entities[-1]:
            schema += ",\n"
        else:
            schema += "\n"
    
    schema += "}"
    
    return schema

def _generate_schema_documentation(self, task_analysis: Dict[str, Any], 
                                  schema: str, db_type: str, db_system: str) -> str:
    """
    Generate documentation for the database schema.
    
    Args:
        task_analysis: Analysis of the task
        schema: Generated schema
        db_type: Type of database
        db_system: Specific database system
        
    Returns:
        Schema documentation in Markdown format
    """
    domain = task_analysis["domain"]
    entities = task_analysis["entities"]
    
    docs = f"""# Database Schema Documentation


This document provides documentation for the {domain.capitalize()} database schema.

Database Type: {db_type.upper()}
Database System: {db_system.capitalize()}
Entities

"""

for entity in entities:
        docs += f"""
{entity.capitalize()}

The {entity.capitalize()} entity represents a {entity} in the system.

"""

if db_type == "sql":
            docs += f"""
Table: {entity}s
Column	Type	Description
id	SERIAL	Primary key
name	VARCHAR(100)	Name of the {entity}
description	TEXT	Description of the {entity}
created_at	TIMESTAMP	Creation timestamp
updated_at	TIMESTAMP	Last update timestamp

"""
elif db_type == "nosql":
docs += f"""

Collection: {entity}s
{{
  "name": "string",
  "description": "string",
  "created_at": "date",
  "updated_at": "date"
}}

"""

# If we have multiple entities, document relationships
    if len(entities) > 1 and db_type == "sql":
        docs += """
Relationships

"""

for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                entity1 = entities[i]
                entity2 = entities[j]
                
                docs += f"""
{entity1.capitalize()} - {entity2.capitalize()}

Many-to-many relationship between {entity1}s and {entity2}s.

Table: {entity1}_{entity2}
Column	Type	Description
{entity1}_id	INTEGER	Foreign key to {entity1}s
{entity2}_id	INTEGER	Foreign key to {entity2}s
created_at	TIMESTAMP	Creation timestamp

"""

docs += """
Schema Definition
"""
        
        docs += schema
        
        docs += """

"""

return docs

def _optimize_query(self, original_query: str, db_type: str, db_system: str) -> str:
    """
    Optimize a database query.
    
    Args:
        original_query: Original query to optimize
        db_type: Type of database
        db_system: Specific database system
        
    Returns:
        Optimized query
    """
    # Simple optimization for SQL queries
    if db_type == "sql":
        # Check if it's a SELECT * query
        if "SELECT *" in original_query:
            # Replace with specific columns
            optimized = original_query.replace("SELECT *", "SELECT id, name, created_at")
            return optimized
        
        # Check if it's missing an index hint
        if "WHERE" in original_query and "INDEX" not in original_query.upper():
            # Add index hint
            optimized = original_query.replace("WHERE", "WHERE /* USE INDEX (idx_column) */")
            return optimized
        
        # Check if it's missing a LIMIT
        if "LIMIT" not in original_query.upper():
            # Add LIMIT
            optimized = original_query.strip()
            if optimized.endswith(";"):
                optimized = optimized[:-1]
            optimized += " LIMIT 100;"
            return optimized
    
    # Simple optimization for NoSQL queries
    elif db_type == "nosql":
        # Check if it's a find without projection
        if "find(" in original_query and "{}" in original_query and "projection" not in original_query:
            # Add projection
            optimized = original_query.replace("find({}", "find({}, {_id: 1, name: 1, created_at: 1}")
            return optimized
        
        # Check if it's missing a limit
        if "limit" not in original_query:
            # Add limit
            optimized = original_query.strip()
            if optimized.endswith(")"):
                optimized = optimized[:-1]
            optimized += ").limit(100)"
            return optimized
    
    # If no optimization applied, return original
    return original_query

def _generate_optimization_explanation(self, original_query: str, 
                                     optimized_query: str, db_type: str) -> str:
    """
    Generate an explanation for the query optimization.
    
    Args:
        original_query: Original query
        optimized_query: Optimized query
        db_type: Type of database
        
    Returns:
        Explanation in Markdown format
    """
    explanation = """# Query Optimization Explanation

Original Query
"""
        explanation += original_query
        explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
Optimized Query
"""
        explanation += optimized_query
        explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
Optimization Techniques Applied

"""

# Explain SQL optimizations
    if db_type == "sql":
        if "SELECT id, name, created_at" in optimized_query and "SELECT *" in original_query:
            explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
1. Specific Column Selection

Problem: The original query uses SELECT * which retrieves all columns from the table. This can be inefficient, especially for tables with many columns or large text/blob fields.

Solution: The optimized query explicitly selects only the needed columns (id, name, created_at). This reduces the amount of data transferred and processed.

"""

if "/* USE INDEX" in optimized_query:
            explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
2. Index Hint

Problem: The database might not be using the most efficient index for this query.

Solution: The optimized query includes an index hint to suggest which index the database should use. This can significantly improve performance for queries on large tables.

"""

if "LIMIT 100" in optimized_query and "LIMIT" not in original_query.upper():
            explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
3. Result Limiting

Problem: The original query doesn't limit the number of results, which could potentially return a very large result set.

Solution: The optimized query adds a LIMIT 100 clause to restrict the number of results. This prevents excessive data transfer and processing for queries that only need to display a subset of results.

"""

# Explain NoSQL optimizations
    elif db_type == "nosql":
        if "{_id: 1, name: 1, created_at: 1}" in optimized_query:
            explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
1. Projection

Problem: The original query retrieves all fields for each document. This can be inefficient, especially for documents with many fields or large embedded documents.

Solution: The optimized query uses projection to specify exactly which fields to return (_id, name, created_at). This reduces the amount of data transferred and processed.

"""

if "limit(100)" in optimized_query and "limit" not in original_query:
            explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
2. Result Limiting

Problem: The original query doesn't limit the number of results, which could potentially return a very large result set.

Solution: The optimized query adds a limit(100) method to restrict the number of results. This prevents excessive data transfer and processing for queries that only need to display a subset of results.

"""

explanation += """
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
Performance Impact

The optimized query should perform better than the original query in the following ways:

Reduced Data Transfer: By selecting only necessary columns/fields, less data needs to be transferred from the database to the application.

Improved Query Execution: Using appropriate indexes and limiting result sets allows the database to execute the query more efficiently.

Lower Resource Usage: Both the database server and application will use fewer resources (memory, CPU) when processing the optimized query.

Additional Recommendations

For further optimization, consider:

Indexing: Ensure that columns/fields used in WHERE clauses and JOIN conditions are properly indexed.

Query Caching: Implement caching for frequently executed queries.

Database Monitoring: Use database monitoring tools to identify slow queries and bottlenecks.

Regular Maintenance: Perform regular database maintenance tasks like statistics updates and index rebuilds.
"""

return explanation
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

def _generate_migration(self, task_analysis: Dict[str, Any],
db_type: str, db_system: str) -> str:
"""
Generate a database migration script.

Args:
     task_analysis: Analysis of the task
     db_type: Type of database
     db_system: Specific database system
     
 Returns:
     Migration script
 """
 domain = task_analysis["domain"]
 entities = task_analysis["entities"]
 
 # Generate a simple migration script
 if db_type == "sql":
     migration = f"""-- Migration: Add new fields to {domain} tables
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

-- Generated at {datetime.now().isoformat()}

"""

for entity in entities:
            migration += f"""
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

-- Add new fields to {entity}s table
ALTER TABLE {entity}s ADD COLUMN status VARCHAR(50) DEFAULT 'active';
ALTER TABLE {entity}s ADD COLUMN last_modified_by VARCHAR(100);
ALTER TABLE {entity}s ADD COLUMN version INTEGER DEFAULT 1;

-- Add index for status field
CREATE INDEX idx_{entity}s_status ON {entity}s(status);

"""

return migration
    
    elif db_type == "nosql":
        migration = f"""// Migration: Add new fields to {domain} collections
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

// Generated at {datetime.now().isoformat()}

"""

for entity in entities:
            migration += f"""
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

// Add new fields to {entity}s collection
db.{entity}s.updateMany(
{{}},
{{
$set: {{
status: "active",
version: 1
}},
$currentDate: {{
lastModified: true
}}
}}
);

// Create index for status field
db.{entity}s.createIndex({{ status: 1 }});

"""

return migration
    
    else:
        # Default to SQL
        return self._generate_migration(task_analysis, "sql", db_system)
