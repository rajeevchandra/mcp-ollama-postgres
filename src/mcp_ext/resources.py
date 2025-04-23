from sqlalchemy import inspect, text
from db.connection import SessionLocal, engine
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("postgres")

@mcp.resource("table://list")
def list_tables():
    inspector = inspect(engine)
    return inspector.get_table_names()

@mcp.tool("sql://query")
def run_query(query: str) -> list[dict]:
    with SessionLocal() as session:
        result = session.execute(text(query))
        return [dict(row._mapping) for row in result]
