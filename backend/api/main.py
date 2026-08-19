import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import genu_chat, health, rag, search
from backend.config import get_config
from backend.database.db import init_db
from backend.database.nosql.base import NoSQLRepository
from backend.factory import ServiceFactory
from backend.services.graph import GraphService
from backend.services.llm import LLMService
from backend.services.opensearch import OpenSearchInterface
from backend.services.rdf import RDFService

logger = structlog.get_logger()

config = get_config()
app = FastAPI(title="FDE Template API", description="FDE Modular AI PoC Platform", version="0.1.0")

# Initialize services
graph_service: GraphService | None = None
rdf_service: RDFService | None = None
llm_service: LLMService | None = None
nosql_service: NoSQLRepository | None = None
opensearch_service: OpenSearchInterface | None = None


def get_graph_service() -> GraphService | None:
    return graph_service


def get_rdf_service() -> RDFService | None:
    return rdf_service


def get_llm_service() -> LLMService | None:
    return llm_service


def get_nosql_service() -> NoSQLRepository | None:
    return nosql_service


def get_opensearch_service() -> OpenSearchInterface | None:
    return opensearch_service


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])

if config.graph_enabled or config.rdf_enabled:
    from backend.api.routes import graph

    app.include_router(graph.router, prefix="/graph", tags=["graph"])

if config.nosql_enabled:
    from backend.api.routes import nosql

    app.include_router(nosql.router, prefix="/nosql", tags=["nosql"])

if config.opensearch_enabled:
    from backend.api.routes import opensearch

    app.include_router(opensearch.router, prefix="/opensearch", tags=["opensearch"])

# GenU Chat API (Phase 9)
app.include_router(genu_chat.router, prefix="/chat", tags=["chat"])


@app.on_event("startup")
async def startup_event():
    global graph_service, rdf_service, llm_service, nosql_service, opensearch_service

    logger.info("Backend startup", config=config.model_dump())
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))

    # Initialize services based on configuration
    graph_service = ServiceFactory.create_graph_service(config)
    if graph_service:
        logger.info("Graph service initialized", engine=config.graph_engine)

    rdf_service = ServiceFactory.create_rdf_service(config)
    if rdf_service:
        logger.info("RDF service initialized", engine=config.rdf_engine)

    llm_service = ServiceFactory.create_llm_service(config)
    if llm_service:
        logger.info("LLM service initialized", provider=config.llm_provider)

    nosql_service = ServiceFactory.create_nosql_service(config)
    if nosql_service:
        logger.info("NoSQL service initialized", engine=config.nosql_engine)

    opensearch_service = ServiceFactory.create_opensearch_service(config)
    if opensearch_service:
        logger.info("OpenSearch service initialized", url=config.opensearch_url)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
