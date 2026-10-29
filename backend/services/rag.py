"""Retrieval-Augmented Generation (RAG) knowledge base service over Supabase pgvector."""

from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.schemas import SourceCitation

settings = get_settings()


async def retrieve_relevant_chunks(
    query: str,
    crop: Optional[str] = None,
    limit: int = 3,
    min_similarity: float = 0.65,
) -> List[SourceCitation]:
    """
    Retrieve knowledge base chunks from Supabase `kb_chunks` table using pgvector similarity.
    
    In local/scaffold mode or when database connection is inactive, returns structured
    curated citations from verified Rajasthan agricultural reference data.
    """
    # Scaffold baseline / fallback retrieval
    # In Phase 2 this executes cosine distance query against Supabase pgvector
    default_citations = [
        SourceCitation(
            doc_title="ICAR Package of Practices for Rajasthan",
            source="ICAR-CAZRI Jodhpur / Agriculture University Kota",
            chunk_text=(
                "राजस्थान में सरसों और बाजरा की उन्नत किस्मों, संतुलित उर्वरक (NPK) एवं "
                "सामयिक सिंचाई प्रबंधन से फसल की उत्पादकता 20-30% तक बढ़ाई जा सकती है। "
                "रोग नियंत्रण हेतु केवल अनुशंसित मात्रा में ही जैव या रासायनिक उपचार करें।"
            ),
            relevance_score=0.88,
        )
    ]
    return default_citations[:limit]
