from enum import StrEnum


class IngestionPhase(StrEnum):
    STORAGE_READ = "storage_read"
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VECTOR_SYNC = "vector_sync"
    DATABASE = "database"
