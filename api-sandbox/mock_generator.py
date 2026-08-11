import random
import json
import datetime

def resolve_ref(schema: dict, spec: dict):
    """Resolve a $ref pointer like '#/components/schemas/ChatResponse'."""
    ref_path = schema["$ref"]
    if ref_path.startswith("#/"):
        parts = ref_path[2:].split("/")
        current = spec
        for part in parts:
            current = current[part]
        return current
    return schema

def generate_value(schema: dict, spec: dict = None):
    """Generate a realistic mock value based on JSON schema type."""
    if spec is None:
        spec = {}

    if "$ref" in schema:
        return generate_value(resolve_ref(schema, spec), spec)

    schema_type = schema.get("type", "string")

    if schema_type == "string":
        if schema.get("format") == "email":
            return f"user{random.randint(1, 999)}@example.com"
        if schema.get("format") == "date-time":
            return datetime.datetime.now().isoformat()
        return "sample string"

    if schema_type == "integer":
        return random.randint(1, 100)

    if schema_type == "number":
        return round(random.uniform(1.0, 100.0), 2)

    if schema_type == "boolean":
        return random.choice([True, False])

    if schema_type == "array":
        items_schema = schema.get("items", {"type": "string"})
        return [generate_value(items_schema, spec) for _ in range(random.randint(1, 3))]

    if schema_type == "object":
        result = {}
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            result[prop_name] = generate_value(prop_schema, spec)
        return result

    return None

def generate_response(schema: dict, spec: dict = None):
    """Generate a full mock response for a response schema."""
    if not schema:
        return {"message": "success"}
    return generate_value(schema, spec)
